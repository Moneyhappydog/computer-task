import logging
from pathlib import Path
from typing import List, Dict, Any
import torch
from PIL import Image
from pdf2image import convert_from_path
from transformers import DetrImageProcessor, TableTransformerForObjectDetection
import base64
from io import BytesIO
import json
import sys

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 尝试导入 OpenAI
try:
    from openai import OpenAI
    from response.gpt import openai_api_key
    API_DEPS_AVAILABLE = True
except ImportError:
    API_DEPS_AVAILABLE = False
    openai_api_key = None

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TableExtractorTATR:
    def __init__(self, api_key: str = None):
        """
        初始化微软 Table Transformer 模型 和 OpenAI 客户端
        """
        # 1. 初始化 TATR 模型
        logger.info("正在加载 Microsoft Table Transformer 模型...")
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.processor = DetrImageProcessor.from_pretrained("microsoft/table-transformer-detection")
            self.model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
            self.model.to(self.device)
            logger.info(f"✅ TATR 模型加载成功 (运行设备: {self.device})")
        except Exception as e:
            logger.error(f"❌ TATR 模型加载失败: {e}")
            raise e

        # 2. 初始化 OpenAI (用于过滤非表格图片)
        self.client = None
        if api_key and API_DEPS_AVAILABLE:
            self.client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI Client 已加载 (将启用智能过滤功能)")
        else:
            logger.warning("⚠️ 未提供 API Key 或未安装 openai，将跳过智能过滤 (可能会误检流程图)")

    def _image_to_base64(self, image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def _verify_is_table(self, image: Image.Image) -> Dict[str, Any]:
        """
        使用 gpt-4o-mini 判断图片是否真的是表格
        返回: {'is_table': bool, 'type': str}
        """
        if not self.client:
            return {'is_table': True, 'type': 'assumed_table'} # 没 API 就默认全是表格

        try:
            base64_img = self._image_to_base64(image)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # 使用 mini 模型，极快且便宜
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a document layout classifier. Determine if the image is a 'Table' (structured data with rows/columns) or a 'Figure' (chart, graph, diagram, flowchart, plot). Return JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Is this image a Table or a Figure? Respond in JSON: {\"type\": \"table\" or \"figure\", \"confidence\": 0-1}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            is_table = result.get('type', '').lower() == 'table'
            return {'is_table': is_table, 'type': result.get('type', 'unknown')}

        except Exception as e:
            logger.warning(f"⚠️ AI 验证失败: {e}，默认视为表格")
            return {'is_table': True, 'type': 'error_fallback'}

    def extract(self, pdf_path: str, output_dir: str, threshold: float = 0.9, padding: int = 30) -> List[Dict]:
        """
        执行提取并过滤
        Returns:
            List of dicts: [{'path': str, 'page': int, 'is_table': bool, 'type': str}]
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        
        # 创建两个文件夹：tables (真表格) 和 figures (误检的图)
        table_dir = output_dir / "tables"
        figure_dir = output_dir / "figures" # 存放被剔除的流程图
        table_dir.mkdir(parents=True, exist_ok=True)
        figure_dir.mkdir(parents=True, exist_ok=True)
        
        extracted_items = []
        
        logger.info(f"正在转换 PDF: {pdf_path.name}")
        try:
            images = convert_from_path(str(pdf_path), dpi=200)
        except Exception as e:
            logger.error(f"PDF 转图片失败: {e}")
            return []

        for i, image in enumerate(images):
            page_num = i + 1
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)

            target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
            results = self.processor.post_process_object_detection(outputs, threshold=threshold, target_sizes=target_sizes)[0]

            if len(results['boxes']) > 0:
                logger.info(f"Page {page_num}: TATR 初步检测到 {len(results['boxes'])} 个目标")

            for idx, (score, box) in enumerate(zip(results['scores'], results['boxes'])):
                if score < threshold: continue
                
                # 1. 裁剪
                box = [round(i, 2) for i in box.tolist()]
                x0, y0, x1, y1 = box
                width, height = image.size
                crop_box = (
                    max(0, int(x0) - padding),
                    max(0, int(y0) - padding),
                    min(width, int(x1) + padding),
                    min(height, int(y1) + padding)
                )
                cropped_img = image.crop(crop_box)
                
                # 2. AI 智能分类 (这是解决你问题的关键步骤)
                check_result = self._verify_is_table(cropped_img)
                is_real_table = check_result['is_table']
                img_type = check_result['type']
                
                # 3. 根据分类结果保存到不同目录
                save_dir = table_dir if is_real_table else figure_dir
                prefix = "table" if is_real_table else "figure"
                
                filename = f"p{page_num}_{prefix}_{idx+1}.png"
                save_path = save_dir / filename
                cropped_img.save(save_path)
                
                log_icon = "✅" if is_real_table else "🗑️"
                logger.info(f"  {log_icon} [P{page_num}] 检测为 {img_type} -> 保存至 {save_dir.name}")
                
                extracted_items.append({
                    "path": str(save_path),
                    "page": page_num,
                    "is_table": is_real_table, # 只有 True 的才应该喂给后续的表格转写 AI
                    "type": img_type
                })

        logger.info(f"处理完成。真表格: {len([x for x in extracted_items if x['is_table']])}，误检图表: {len([x for x in extracted_items if not x['is_table']])}")
        return extracted_items

# --- 使用示例 ---
if __name__ == "__main__":
    # 使用 response/gpt.py 中的 API Key
    extractor = TableExtractorTATR(api_key=openai_api_key)
    
    results = extractor.extract(
        pdf_path="data/input/2023CVPR-CoMFormer.pdf",
        output_dir="data/output/2023CVPR-CoMFormer_smart_tables",
        threshold=0.85
    )
    
    # 后续处理建议：
    # valid_tables = [item['path'] for item in results if item['is_table']]
    # 只有 valid_tables 列表里的图片，才发送给 GPT-4o 进行 Markdown 转换