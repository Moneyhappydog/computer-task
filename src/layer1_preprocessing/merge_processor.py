import json
import os
from pathlib import Path
import logging
from typing import List, Optional
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

class MarkdownJsonMerger:
    """
    智能合并器：将 Marker 生成的 Markdown 与 GPT 提取的 JSON 公式/表格合并
    """
    def __init__(self, api_key: str):
        if not API_DEPS_AVAILABLE:
            raise ImportError("请安装 openai: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        # 使用 gpt-4o-mini 进行文本合并，速度快且极便宜
        self.model = "gpt-4o-mini" 

    def merge_document(self, md_path: Path, json_dir: Path, output_path: Path):
        """
        主流程：读取MD -> 切分页面 -> 逐页合并 JSON -> 拼接保存
        """
        if not md_path.exists():
            logger.error(f"Markdown 文件不存在: {md_path}")
            return

        # 1. 读取原始 Markdown
        raw_md = md_path.read_text(encoding='utf-8')
        
        # 2. 利用 Marker 的分页符切分页面
        # 注意：pdf_processor.py 中提到 marker 用 "\n---\n" 分隔页面
        md_pages = raw_md.split("\n---\n")
        logger.info(f"📚 原始文档共切分为 {len(md_pages)} 页")

        merged_pages = []

        # 3. 逐页处理
        for i, page_text in enumerate(md_pages):
            page_num = i + 1
            json_path = json_dir / f"page_{page_num}.json"
            
            logger.info(f"🔄 正在处理第 {page_num} 页合并...")

            if json_path.exists():
                # 如果有 JSON 数据，进行智能合并
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # 只有当 JSON 里确实有提取到东西时才调用 AI
                    if json_data.get("extracted_items"):
                        refined_text = self._ai_merge_page(page_text, json_data, page_num)
                        merged_pages.append(refined_text)
                    else:
                        logger.info(f"   ⚠️ 第 {page_num} 页 JSON 为空，保留原始内容")
                        merged_pages.append(page_text)
                        
                except Exception as e:
                    logger.error(f"   ❌ 第 {page_num} 页合并失败: {e}，保留原始内容")
                    merged_pages.append(page_text)
            else:
                # 如果没有 JSON（比如封面或目录页没公式），保留原样
                logger.info(f"   ⚠️ 第 {page_num} 页无 JSON 数据，保留原始内容")
                merged_pages.append(page_text)

        # 4. 重新拼接并保存
        final_md = "\n\n---\n\n".join(merged_pages)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_md, encoding='utf-8')
        logger.info(f"✅ 最终文档已保存至: {output_path}")

    def _ai_merge_page(self, raw_text: str, json_data: dict, page_num: int) -> str:
        """
        调用 LLM 将 JSON 数据“注入”到 Markdown 文本中
        """
        items_str = json.dumps(json_data['extracted_items'], ensure_ascii=False, indent=2)
        
        # System Prompt: 核心指令
        system_prompt = (
            "You are a document reconstruction assistant. "
            "Your goal is to merge a raw Markdown text (which may contain OCR errors, broken formulas, or missing tables) "
            "with a structured JSON containing high-quality extracted formulas and tables.\n"
            "Rules:\n"
            "1. Keep the narrative text from the Raw Markdown as the skeleton.\n"
            "2. When you see a broken formula or a placeholder in the Raw Markdown that corresponds to an item in the JSON, "
            "REPLACE it with the high-quality content from the JSON.\n"
            "3. For 'display_formula', use LaTeX block format $$ ... $$.\n"
            "4. For 'table', replace the text representation with the LaTeX array provided in the JSON.\n"
            "5. Do not delete paragraphs of text. Only fix the math and tables.\n"
            "6. Output ONLY the merged Markdown content."
        )

        user_content = (
            f"--- PAGE {page_num} RAW MARKDOWN ---\n"
            f"{raw_text}\n\n"
            f"--- PAGE {page_num} HIGH-QUALITY JSON DATA ---\n"
            f"{items_str}"
        )

        response = self.client.chat.completions.create(
            model=self.model, # 使用 mini 模型，便宜且足够聪明处理文本替换
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1
        )

        return response.choices[0].message.content

# --- 运行入口 ---
if __name__ == "__main__":
    # 使用 response/gpt.py 中的 API Key
    
    # 定义路径
    doc_name = "2023CVPR-CoMFormer"
    
    # 1. 原始 Markdown (来自 pdf_processor.py 的输出)
    input_md = Path(f"data/output/{doc_name}/layer1/{doc_name}.md")
    
    # 2. JSON 文件夹 (来自 formula_extractor2.py 的输出)
    json_dir = Path(f"data/output_json/{doc_name}")
    
    # 3. 最终输出路径
    output_md = Path(f"data/output/{doc_name}/final_merged.md")

    if input_md.exists() and json_dir.exists():
        merger = MarkdownJsonMerger(api_key=openai_api_key)
        merger.merge_document(input_md, json_dir, output_md)
    else:
        print(f"❌ 找不到输入文件。\nMD存在: {input_md.exists()}\nJSON目录存在: {json_dir.exists()}")