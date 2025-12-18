import json
import os
import re
import logging
import base64
from pathlib import Path
from typing import List, Dict, Optional, Any
from io import BytesIO
from PIL import Image

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import Config

# 尝试导入 OpenAI
try:
    from openai import OpenAI
    from response.gpt import openai_api_key
    API_DEPS_AVAILABLE = True
except ImportError:
    API_DEPS_AVAILABLE = False
    openai_api_key = None

logger = logging.getLogger(__name__)

class ContentFusionProcessor:
    """
    内容融合处理器 (Layer 1.5)
    功能：将 Layer 1 提取的 文本(Markdown) + 公式(JSON) + 表格(Images) 融合为高质量 Markdown
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or openai_api_key
        if self.api_key and API_DEPS_AVAILABLE:
            # 强制使用 OpenAI 官方接口，因为我们需要多模态能力 (GPT-4o)
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.openai.com/v1")
            logger.info("✅ [Fusion] OpenAI Client 初始化成功")
        else:
            logger.error("❌ [Fusion] 未提供 API Key 或未安装 openai，无法进行多模态融合")
            self.client = None

    def _image_to_base64(self, image_path: Path) -> str:
        """读取本地图片并转换为 Base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图片读取失败 {image_path}: {e}")
            return ""

    def fuse_document(self, doc_name: str) -> Dict[str, Any]:
        """
        对指定文档进行多模态融合
        
        Args:
            doc_name: 文档名称 (如 "2023CVPR-CoMFormer")
            
        Returns:
            Dict: 包含融合后的 markdown 和元数据
        """
        if not self.client:
            raise RuntimeError("OpenAI Client 未初始化，无法执行融合")

        # 1. 路径准备
        base_output_dir = Path(Config.OUTPUT_DIR) / doc_name
        layer1_dir = base_output_dir / "layer1"
        md_file = layer1_dir / f"{doc_name}.md"
        formulas_dir = layer1_dir / "formulas"
        tables_dir = base_output_dir / "tables"
        
        if not md_file.exists():
            raise FileNotFoundError(f"找不到 Layer 1 的 Markdown 文件: {md_file}")

        logger.info(f"🚀 开始文档融合: {doc_name}")
        
        # 2. 读取并切分 Markdown
        raw_text = md_file.read_text(encoding='utf-8')
        # Marker 通常用 "\n---\n" 分页，但也可能没有，视情况而定
        # 这里我们假设 Marker 输出了分页符。如果没有，可能需要按长度切分或视为第1页
        pages = raw_text.split("\n---\n")
        if len(pages) == 1 and "---" not in raw_text:
            logger.warning("未检测到分页符，将整个文档视为第 1 页处理")
        
        fused_pages = []
        
        # 3. 逐页处理
        for i, page_text in enumerate(pages):
            page_num = i + 1
            logger.info(f"📄 正在融合第 {page_num} 页...")
            
            # 3.1 获取该页的公式数据
            page_formulas = []
            formula_file = formulas_dir / f"page_{page_num}.json"
            if formula_file.exists():
                try:
                    with open(formula_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        page_formulas = data.get("extracted_items", [])
                except Exception as e:
                    logger.warning(f"读取公式文件失败 {formula_file}: {e}")
            
            # 3.2 获取该页的表格图片
            # 假设表格命名格式: p{page_num}_table_{idx}.png
            page_tables = []
            if tables_dir.exists():
                # 查找所有以 p{page_num}_table 开头的文件
                for table_file in tables_dir.glob(f"p{page_num}_table_*.png"):
                    page_tables.append(table_file)
            
            # 3.3 获取该页引用的图片 (Figures)
            page_figures = []
            # 查找 Markdown 中的图片链接: ![alt](path)
            # 路径通常是相对路径，如 ../images/xxx.png
            matches = re.findall(r'!\[.*?\]\((.*?)\)', page_text)
            for img_path_str in matches:
                # 过滤掉表格图片（如果表格图片也被引用了的话，通常表格在 tables/ 目录，而 figures 在 images/ 目录）
                if "tables/" in img_path_str:
                    continue
                    
                try:
                    # 解析图片绝对路径
                    # md_file 在 layer1/xxx.md
                    # img_path_str 如 ../images/xxx.png
                    img_full_path = (md_file.parent / img_path_str).resolve()
                    
                    if img_full_path.exists():
                        page_figures.append(img_full_path)
                    else:
                        # 尝试直接在 images 目录查找 (容错)
                        images_dir = base_output_dir / "images" # data/output/{doc}/images
                        img_name = Path(img_path_str).name
                        alt_path = images_dir / img_name
                        if alt_path.exists():
                            page_figures.append(alt_path)
                except Exception as e:
                    logger.warning(f"无法解析图片路径: {img_path_str} - {e}")

            # 3.4 调用 AI 进行融合
            fused_text = self._process_single_page(
                page_num=page_num,
                text=page_text,
                formulas=page_formulas,
                table_paths=page_tables,
                figure_paths=page_figures,
                doc_name=doc_name
            )
            
            fused_pages.append(fused_text)
        
        # 4. 合并结果并保存
        final_markdown = "\n\n---\n\n".join(fused_pages)
        
        # 保存到 layer2 目录 (或者 layer1_fused)
        output_dir = base_output_dir / "layer2_semantic"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{doc_name}_fused.md"
        output_file.write_text(final_markdown, encoding='utf-8')
        
        logger.info(f"✨ 文档融合完成! 已保存至: {output_file}")
        
        return {
            "success": True,
            "output_file": str(output_file),
            "pages_processed": len(pages)
        }

    def _process_single_page(
        self, 
        page_num: int, 
        text: str, 
        formulas: List[Dict], 
        table_paths: List[Path],
        figure_paths: List[Path],
        doc_name: str
    ) -> str:
        """
        调用 GPT-4o 融合单页内容
        """
        # 构造 Prompt
        system_prompt = (
            "You are an expert document editor. Your task is to refine the provided Markdown text "
            "by integrating high-quality extracted formulas and tables.\n"
            "Rules:\n"
            "1. **Text Refinement**: Fix OCR errors in the text based on context.\n"
            "2. **Formula Integration**: The provided JSON contains accurate formulas extracted from this page. "
            "   Replace any garbled math text in the Markdown with the correct LaTeX from the JSON. "
            "   Ensure inline formulas use $...$ and display formulas use $$...$$.\n"
            "3. **Table Integration**: The provided images are tables found on this page. "
            "   - ONLY replace **existing text-based representations** of tables (often broken or messy) with the provided image links.\n"
            "   - Do **NOT** insert a table image if there is no corresponding text table or placeholder in the markdown. Do NOT hallucinate tables.\n"
            "   - Format: `![filename](path/to/table.png)`. Use the filename as the alt text (e.g., `![p1_table_0.png](...)`).\n"
            "   - IMPORTANT: Use the relative path provided in the user prompt for the image.\n"
            "4. **Figure Context & Preservation**: \n"
            "   - I have provided the figures (images) that appear on this page for context.\n"
            "   - **STRICTLY FORBIDDEN**: Do NOT move, reorder, or remove existing image links (figures). Keep them exactly where they are in the text flow.\n"
            "   - You may correct the text around them (captions, references) but do not touch the image link itself.\n"
            "5. **Output**: Return ONLY the refined Markdown text. Do not include 'Here is the refined text' or markdown code blocks."
        )
        
        # 构造用户消息
        user_content = [
            {"type": "text", "text": f"### Page {page_num} Raw Markdown:\n\n{text}\n\n"}
        ]
        
        # 添加公式信息
        if formulas:
            formulas_str = json.dumps(formulas, ensure_ascii=False, indent=2)
            user_content.append({"type": "text", "text": f"### Extracted Formulas (JSON):\n{formulas_str}\n\n"})
        else:
            user_content.append({"type": "text", "text": "### Extracted Formulas: None\n\n"})
            
        # 添加表格信息 (图片 + 路径说明)
        if table_paths:
            user_content.append({"type": "text", "text": "### Extracted Tables (Images):\nI will provide the table images below. Please replace corresponding text tables with these images.\n"})
            
            for table_path in table_paths:
                # 计算相对路径: 从 layer2_semantic/xxx.md 到 tables/xxx.png
                # layer2_semantic 在 data/output/{doc}/layer2_semantic
                # tables 在 data/output/{doc}/tables
                # 相对路径应为: ../tables/{filename}
                # 用户要求: "表格的前缀也按image来" -> 可能是指路径前缀或者Alt Text
                # 这里我们保持路径正确性 (../tables/), 但在 Prompt 中强调 Alt Text 使用文件名
                relative_path = f"../tables/{table_path.name}"
                
                base64_img = self._image_to_base64(table_path)
                if base64_img:
                    user_content.append({"type": "text", "text": f"Image Path to use: `{relative_path}`"})
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_img}"}
                    })
        else:
            user_content.append({"type": "text", "text": "### Extracted Tables: None\n"})

        # 添加插图信息 (Figures) - 仅供上下文参考
        if figure_paths:
            user_content.append({"type": "text", "text": "### Page Figures (Context Only):\nThese images are already linked in the markdown. I provide them here so you can see them to correct captions or text context.\n"})
            for fig_path in figure_paths:
                base64_img = self._image_to_base64(fig_path)
                if base64_img:
                    user_content.append({"type": "text", "text": f"Figure: `{fig_path.name}`"})
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_img}"}
                    })

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ 第 {page_num} 页融合失败: {e}")
            return text # 失败则返回原文

# 测试代码
if __name__ == "__main__":
    # 简单的测试入口
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=str, required=True, help="文档名称 (例如 2023CVPR-CoMFormer)")
    args = parser.parse_args()
    
    processor = ContentFusionProcessor()
    processor.fuse_document(args.doc)
