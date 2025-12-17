import logging
import base64
import json
import os
from pathlib import Path
from io import BytesIO
import sys

import fitz  # PyMuPDF
from PIL import Image

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

class GPTFormulaExtractorJSON:
    """
    GPT-4o 整页公式提取器 (JSON版)
    说明：不进行图片裁剪，而是直接识别图片内容，将公式及上下文提取为 JSON 数据。
    """
    def __init__(self, output_base_dir: Path = None, api_key: str = None):
        if output_base_dir is None:
            output_base_dir = "data/output_json"
        self.output_base_dir = Path(output_base_dir)
        
        if api_key:
            if API_DEPS_AVAILABLE:
                self.client = OpenAI(api_key=api_key)
                logger.info("✅ [API] OpenAI Client 已初始化")
            else:
                logger.error("❌ 已提供 API Key 但未安装 openai，请运行 pip install openai")
                self.client = None
        else:
            self.client = None

    def _pdf_page_to_base64(self, page, zoom=2.0) -> str:
        """
        将 PDF 页面转为 Base64 字符串
        """
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        return f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

    def extract_formulas(self, pdf_path: Path, doc_name: str):
        """
        主流程：读取 PDF -> GPT-4o 识别 -> 保存 JSON
        """
        if not self.client:
            raise ValueError("需要配置 api_key 并安装 openai")

        logger.info(f"🚀 开始 GPT-4o 语义提取: {pdf_path}")
        
        # 准备输出目录: data/output_json/doc_name/
        doc_out_dir = self.output_base_dir / doc_name
        doc_out_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(pdf_path)

        # --- System Prompt 设计 ---
        # 核心指令：要求区分独立公式和行内公式，并按 JSON 格式返回
        system_prompt = (
            "You are an expert mathematical document digitizer. "
            "Your task is to extract mathematical content from the provided document image. "
            "Return the result strictly as a JSON object with a single key 'extracted_items'. "
            "The value of 'extracted_items' must be a list of objects. "
            "\n\n"
            "Rules for extraction:\n"
            "1. **Display Formulas** (equations on their own line): "
            "   Create an item with {'type': 'display_formula', 'content': '...latex code...'}.\n"
            "2. **Inline Formulas** (equations embedded in text): "
            "   Create an item with {'type': 'inline_text', 'content': '...text segment...'}. "
            "   For inline formulas, DO NOT extract just the math symbol. "
            "   Instead, extract the whole sentence or text block containing the formula to preserve context. "
            "   Convert the math parts within that text to LaTeX (e.g., using $...$).\n"
            "3. Ignore headers, footers, and page numbers.\n"
            "4. Output strictly valid JSON."
        )

        for i, page in enumerate(doc):
            page_idx = i + 1
            # if page_idx > 2: break # 调试用：限制页数
            
            logger.info(f"📄 正在处理第 {page_idx} 页...")
            
            try:
                # 1. 转图片
                img_base64 = self._pdf_page_to_base64(page)

                # 2. 调用 API
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract all formulas and relevant text from this page."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": img_base64,
                                        "detail": "high" # 高精度模式对于看清小公式至关重要
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1, # 低温度保证输出格式稳定
                    response_format={"type": "json_object"} # 强制 JSON
                )

                content = response.choices[0].message.content
                
                # 3. 验证并保存 JSON
                try:
                    json_data = json.loads(content)
                    
                    # 构造保存路径: page_1.json
                    json_path = doc_out_dir / f"page_{page_idx}.json"
                    
                    # 写入文件（美化格式）
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                        
                    item_count = len(json_data.get("extracted_items", []))
                    logger.info(f"✅ 第 {page_idx} 页提取完成，包含 {item_count} 个条目 -> {json_path}")
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ 第 {page_idx} 页 API 返回了非 JSON 格式数据: {content[:100]}...")
                    # 即使解析失败，也把原始内容存下来以便排查
                    with open(doc_out_dir / f"page_{page_idx}_error.txt", 'w', encoding='utf-8') as f:
                        f.write(content)

            except Exception as e:
                logger.error(f"❌ 第 {page_idx} 页处理异常: {e}")
        
        doc.close()
        logger.info(f"✨ 全部处理完成！结果目录: {doc_out_dir}")

# --- 运行入口 ---
if __name__ == "__main__":
    # 使用 response/gpt.py 中的 API Key
    
    # 输入 PDF 路径
    pdf_file = Path("data/input/2023CVPR-CoMFormer.pdf")
    
    if pdf_file.exists():
        extractor = GPTFormulaExtractorJSON(api_key=openai_api_key)
        extractor.extract_formulas(
            pdf_file,
            doc_name=pdf_file.stem
        )
    else:
        print(f"文件不存在: {pdf_file}")