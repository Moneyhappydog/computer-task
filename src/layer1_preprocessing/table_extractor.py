import logging
from pathlib import Path
from typing import List
import torch
from PIL import Image
from pdf2image import convert_from_path
from transformers import DetrImageProcessor, TableTransformerForObjectDetection

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TableExtractorTATR:
    def __init__(self):
        """
        初始化微软 Table Transformer 模型
        模型权重: microsoft/table-transformer-detection
        """
        logger.info("正在加载 Microsoft Table Transformer 模型...")
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            # 加载特征提取器和模型
            self.processor = DetrImageProcessor.from_pretrained("microsoft/table-transformer-detection")
            self.model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
            self.model.to(self.device)
            logger.info(f"✅ 模型加载成功 (运行设备: {self.device})")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise e

    def extract(self, pdf_path: str, output_dir: str, threshold: float = 0.9, padding: int = 30) -> List[str]:
        """
        Args:
            pdf_path: PDF路径
            output_dir: 输出目录
            threshold: 置信度阈值 (0.0 - 1.0)，建议 0.9 以过滤误检
            padding: 截图外扩像素，TATR 框有时贴得很紧，建议给 30px
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        # 1. PDF 转高清图片 (DPI 200 足够检测，太高会慢)
        logger.info(f"正在转换 PDF: {pdf_path.name}")
        try:
            images = convert_from_path(str(pdf_path), dpi=200)
        except Exception as e:
            logger.error(f"PDF 转图片失败 (请检查 poppler 是否安装): {e}")
            return []

        # 2. 逐页检测
        for i, image in enumerate(images):
            page_num = i + 1
            
            # 预处理图片
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            # 模型推理
            with torch.no_grad():
                outputs = self.model(**inputs)

            # 后处理：将模型输出转换为坐标 (Rescale to original image size)
            target_sizes = torch.tensor([image.size[::-1]]).to(self.device) # (height, width)
            results = self.processor.post_process_object_detection(outputs, threshold=threshold, target_sizes=target_sizes)[0]

            if len(results['boxes']) > 0:
                logger.info(f"Page {page_num}: 检测到 {len(results['boxes'])} 个表格")

            # 3. 裁剪并保存
            for idx, (score, label, box) in enumerate(zip(results['scores'], results['labels'], results['boxes'])):
                # label 0 是 'table' (表格), label 1 是 'table rotated' (旋转表格)
                # 我们通常只关心 label 0，或者都保留
                if score < threshold:
                    continue
                
                # 转换坐标为整数
                box = [round(i, 2) for i in box.tolist()]
                x0, y0, x1, y1 = box
                
                # 应用 Padding (防止切掉边框线)
                width, height = image.size
                crop_box = (
                    max(0, int(x0) - padding),
                    max(0, int(y0) - padding),
                    min(width, int(x1) + padding),
                    min(height, int(y1) + padding)
                )
                
                # 裁剪
                table_img = image.crop(crop_box)
                
                # 保存
                filename = f"p{page_num}_table_{idx+1}_conf{score:.2f}.png"
                save_path = output_dir / filename
                table_img.save(save_path)
                saved_paths.append(str(save_path))

        logger.info(f"全部完成，共提取 {len(saved_paths)} 张表格图片。")
        return saved_paths

# --- 使用示例 ---
if __name__ == "__main__":
    extractor = TableExtractorTATR()
    
    # 运行提取
    extractor.extract(
        pdf_path="data/input/2023CVPR-CoMFormer.pdf",       # 你的 PDF 文件
        output_dir="data/output/2023CVPR-CoMFormer_test_tables", 
        threshold=0.85,            # 置信度，如果漏检可调低至 0.7
        padding=30                 # 留白大小
    )