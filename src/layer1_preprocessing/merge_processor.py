import json
import os
from pathlib import Path
import logging
from typing import List, Dict
import sys
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
    全能合并器：将 Marker 基础文本 + GPT 公式 JSON + Table Transformer 表格图片 合并为最终 Markdown
    """
    def __init__(self, api_key: str):
        if not API_DEPS_AVAILABLE:
            raise ImportError("请安装 openai: pip install openai")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # 性价比之王，足够处理排版

    def merge_all(self, md_path: Path, json_dir: Path, table_data: List[Dict], output_path: Path):
        """
        Args:
            md_path: marker 生成的原始 MD
            json_dir: 公式 JSON 所在目录
            table_data: table_extractor 返回的列表 [{'page':1, 'path':'...', 'is_table':True}, ...]
            output_path: 最终保存路径
        """
        if not md_path.exists():
            logger.error(f"Markdown 文件不存在: {md_path}")
            return

        raw_md = md_path.read_text(encoding='utf-8')
        md_pages = raw_md.split("\n---\n") # Marker 的分页符
        
        merged_pages = []

        # 将表格数据按页码索引，方便查找
        tables_by_page = {}
        for item in table_data:
            if item['is_table']: # 只处理真表格
                p = item['page']
                if p not in tables_by_page: tables_by_page[p] = []
                tables_by_page[p].append(item['path'])

        # 逐页处理
        for i, page_text in enumerate(md_pages):
            page_num = i + 1
            json_path = json_dir / f"page_{page_num}.json"
            
            # 获取当前页的素材
            page_tables = tables_by_page.get(page_num, [])
            page_formulas = []
            
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        page_formulas = data.get("extracted_items", [])
                except:
                    pass

            # 如果这一页既没公式也没表格，直接保留原文，省钱
            if not page_formulas and not page_tables:
                logger.info(f"   ⏩ 第 {page_num} 页无特殊元素，保留原文")
                merged_pages.append(page_text)
                continue

            # 调用 AI 进行组装
            logger.info(f"   🧠 AI 正在组装第 {page_num} 页 (公式: {len(page_formulas)}, 表格: {len(page_tables)})...")
            refined_text = self._ai_assemble_page(page_text, page_formulas, page_tables, page_num)
            merged_pages.append(refined_text)

        # 保存
        final_md = "\n\n---\n\n".join(merged_pages)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_md, encoding='utf-8')
        logger.success(f"🎉 最终完美文档已生成: {output_path}")

    def _ai_assemble_page(self, raw_text: str, formulas: List, tables: List[str], page_num: int) -> str:
        """
        核心 Prompt：让 AI 把文字、公式、图片拼在一起
        """
        # 构造上下文
        formula_context = json.dumps(formulas, ensure_ascii=False)
        table_context = "\n".join([f"- Table Image Path: {t}" for t in tables])
        
        system_prompt = (
            "You are an expert document reconstruction assistant. "
            "Your task is to fix a raw OCR Markdown page by integrating high-quality extracted formulas and table images.\n\n"
            "**Inputs provided:**\n"
            "1. Raw Markdown (contains text errors and placeholders).\n"
            "2. Formula List (JSON with LaTeX).\n"
            "3. Table Image List (file paths).\n\n"
            "**Instructions:**\n"
            "1. **Text:** Keep the main narrative text from Raw Markdown. Fix obvious OCR typos if context allows.\n"
            "2. **Formulas:** When you see a broken formula or placeholder in text, REPLACE it with the correct LaTeX from the Formula List.\n"
            "3. **Tables:** When you encounter a place where a table should be (often indicated by messy text or headers), "
            "INSERT the corresponding image using Markdown syntax: `![](<path>)`. "
            "Do NOT try to reconstruct the table text manually; just use the image.\n"
            "4. **Output:** Return ONLY the final clean Markdown content."
        )

        user_content = (
            f"--- PAGE {page_num} RAW TEXT ---\n{raw_text}\n\n"
            f"--- FORMULA DATA ---\n{formula_context}\n\n"
            f"--- AVAILABLE TABLE IMAGES ---\n{table_context}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
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