"""
PDF处理器 - 智能文本提取
支持多种方案：marker-pdf（深度学习）、OCR（扫描件）
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
# import pdfplumber
from pdf2image import convert_from_path
import os
import base64
import json
import re
import difflib
from io import BytesIO
import fitz
import tempfile
import shutil

# 导入工具模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from utils.config import Config
from .ocr_processor import OCRProcessor
from .image_extractor import ImageExtractor
from .formula_extractor import GPTFormulaExtractorJSON
from .table_extractor import TableExtractor
import concurrent.futures

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = setup_logger(__name__)

class PDFProcessor:
    """PDF智能处理器（集成Marker、OCR、表格提取、公式提取）"""
    
    def __init__(self, use_marker: bool = True, use_ocr: bool = True, 
                 use_table: bool = True, use_formula: bool = True, api_key: str = None):
        """
        初始化PDF处理器
        
        Args:
            use_marker: 是否尝试使用marker-pdf（深度学习方案）
            use_ocr: 是否在需要时自动使用OCR
            use_table: 是否启用专门的表格提取
            use_formula: 是否启用专门的公式提取
            api_key: OpenAI API Key (用于表格和公式提取)
        """
        self.use_marker = use_marker
        self.use_ocr = use_ocr
        self.use_table = use_table
        self.use_formula = use_formula
        self.api_key = api_key
        
        self.marker_models = None
        self.ocr_processor = None
        self.table_extractor = None
        self.formula_extractor = None
        
        # 设置环境变量以优化内存使用
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        
        # 1. 初始化OCR处理器
        if use_ocr:
            try:
                self.ocr_processor = OCRProcessor()
                logger.success("✓ OCR处理器初始化成功")
            except Exception as e:
                logger.warning(f"OCR处理器初始化失败，将不使用OCR: {e}")
                self.use_ocr = False
        
        
        # 3. 初始化表格提取器
        if self.use_table:
            try:
                # 注意：TableExtractor会加载模型，占用显存
                self.table_extractor = TableExtractor(api_key=self.api_key)
                logger.success("✓ 表格提取器初始化成功")
            except Exception as e:
                logger.warning(f"表格提取器初始化失败: {e}")
                self.use_table = False

        # 4. 初始化公式提取器 (API轻量级)
        if self.use_formula:
            try:
                self.formula_extractor = GPTFormulaExtractorJSON(api_key=self.api_key)
                logger.success("✓ 公式提取器初始化成功")
            except Exception as e:
                logger.warning(f"公式提取器初始化失败: {e}")
                self.use_formula = False
        
        # 初始化 OpenAI Client (用于分页修复)
        self.client = None
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key, base_url="https://api.openai.com/v1")
            except Exception as e:
                logger.warning(f"OpenAI Client 初始化失败: {e}")

        # 5. 初始化Marker模型 (最后加载，占用最大显存)
        if self.use_marker:
            try:
                logger.info("正在加载Marker模型（首次运行会自动下载）...")
                from marker.convert import convert_single_pdf
                from marker.models import load_all_models
                
                self.marker_models = load_all_models()
                self.convert_single_pdf = convert_single_pdf
                logger.success("✓ Marker模型加载成功")
            except Exception as e:
                logger.warning(f"Marker模型加载失败，将使用OCR方法: {e}")
                self.use_marker = False
    
    def extract_text(self, pdf_path: Path) -> Dict[str, any]:
        """
        提取PDF文本（仅使用marker+ocr组合方案）
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            {
                "text": "完整文本内容",
                "pages": [
                    {"page": 1, "text": "第一页文本", "images": [], "has_text": True},
                    ...
                ],
                "metadata": {"title": "...", "author": "...", ...},
                "method": "marker|ocr",
                "image_mapping": {"old_path": "new_path", ...},
                "image_dir": "保存图片的目录"
            }
        """
        logger.info(f"开始处理PDF: {pdf_path.name}")
        
        # 方案1: 尝试使用Marker（最智能，支持复杂布局）
        if self.use_marker and self.marker_models:
            try:
                marker_result = self._extract_with_marker(pdf_path)
                logger.info("Marker提取完成")
            except Exception as e:
                logger.warning(f"Marker提取失败: {e}")
                marker_result = None
        else:
            marker_result = None
        
        # 方案2: 无论marker是否成功，都使用OCR进行提取
        if self.use_ocr and self.ocr_processor:
            try:
                logger.info("使用OCR进行文本提取...")
                ocr_result = self._extract_with_ocr(pdf_path)
                logger.info("OCR提取完成")
            except Exception as e:
                logger.warning(f"OCR提取失败: {e}")
                ocr_result = None
        else:
            ocr_result = None
        
        # # 方案3: 使用pdfplumber作为最终备选
        # pdfplumber_result = self._extract_with_pdfplumber(pdf_path)
        
        # 选择最佳结果
        results = [r for r in [marker_result, ocr_result] if r]
        if not results:
            raise Exception("所有提取方法都失败了")
        
        # 按文本长度选择最佳结果
        best_result = max(results, key=lambda x: len(x["text"]))
        logger.info(f"最终使用 {best_result['method']} 提取方案，文本长度: {len(best_result['text'])} 字符")
        
        return best_result
    
    def _extract_with_marker(self, pdf_path: Path, session_id: Optional[str] = None) -> Dict:
        """使用Marker进行智能PDF解析（深度学习方案）- 内存优化版 + 强制分页"""
        logger.info("使用Marker进行智能PDF解析（强制分页模式）...")
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # 1. 拆分PDF
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            logger.info(f"PDF共 {num_pages} 页，正在拆分处理...")
            
            full_text_parts = []
            all_images = {}
            all_metadata = {}
            
            for i in range(num_pages):
                page_num = i + 1
                page_pdf_path = temp_dir / f"page_{page_num}.pdf"
                
                # 保存单页PDF
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                new_doc.save(page_pdf_path)
                new_doc.close()
                
                logger.info(f"正在处理第 {page_num}/{num_pages} 页...")
                
                # 调用Marker处理单页
                try:
                    result = self.convert_single_pdf(
                        str(page_pdf_path),
                        self.marker_models,
                        max_pages=None,
                        langs=None,
                        batch_multiplier=1,
                    )
                except Exception as e:
                    logger.warning(f"第 {page_num} 页 Marker 处理失败: {e}")
                    result = ""
                
                # 解析结果
                page_text = ""
                page_images = {}
                page_meta = {}
                
                if isinstance(result, tuple):
                    if len(result) >= 3:
                        page_text, page_images, page_meta = result[0], result[1], result[2]
                    elif len(result) == 2:
                        page_text, page_meta = result
                    elif len(result) == 1:
                        page_text = result[0]
                else:
                    page_text = str(result) if result else ""
                
                # 1. OCR 兜底机制：如果Marker结果为空，尝试OCR
                if not page_text.strip() and self.use_ocr and self.ocr_processor:
                    logger.warning(f"第 {page_num} 页 Marker 提取为空，尝试使用 OCR 兜底...")
                    try:
                        # OCRProcessor.ocr_pdf 返回列表，我们只需要第一页
                        ocr_results = self.ocr_processor.ocr_pdf(page_pdf_path)
                        if ocr_results:
                            page_text = ocr_results[0].get("text", "")
                            logger.info(f"OCR 兜底成功，提取了 {len(page_text)} 个字符")
                    except Exception as e:
                        logger.warning(f"OCR 兜底失败: {e}")

                # 处理图片键名冲突
                # Marker通常返回 image_name -> PIL Image (例如 0_image_0.png)
                # 我们需要重命名图片以包含页码信息，并去除多余的前缀
                renamed_images = {}
                for img_name, img_obj in page_images.items():
                    # 去除可能存在的 "0_" 前缀 (Marker处理单页时常出现)
                    clean_name = img_name
                    if clean_name.startswith("0_"):
                        clean_name = clean_name[2:]
                    
                    new_name = f"page_{page_num}_{clean_name}"
                    renamed_images[new_name] = img_obj
                    
                    # 更新文本中的引用
                    if img_name in page_text:
                        page_text = page_text.replace(img_name, new_name)
                
                # 2. 图片引用补全：防止图片丢失
                for new_name in renamed_images.keys():
                    if new_name not in page_text:
                        logger.info(f"补全第 {page_num} 页丢失的图片引用: {new_name}")
                        page_text += f"\n\n![]({new_name})\n"
                
                all_images.update(renamed_images)
                if page_meta:
                    all_metadata.update(page_meta) # 简单合并
                
                # 3. 强制页面标记：确保分页结构完整
                final_page_text = f"<!-- Page {page_num} -->\n{page_text}"
                full_text_parts.append(final_page_text)
            
            doc.close()
            
            # 合并文本
            full_text = "\n---\n".join(full_text_parts)
            
            # 提取并保存图片
            image_mapping = {}
            image_dir = None
            doc_name = pdf_path.stem
            
            if all_images:
                try:
                    extractor = ImageExtractor()
                    result_dict = extractor.extract_and_save_images(
                        images=all_images,
                        doc_name=doc_name
                    )
                    image_mapping = result_dict['image_mapping']
                    image_dir = result_dict['image_dir']
                    
                    # 修正Markdown中的图片路径
                    full_text = extractor.fix_markdown_image_paths(full_text, image_mapping)
                    
                    logger.success(f"✓ 提取并保存了 {len(image_mapping)} 张图片到: {image_dir}")
                except Exception as e:
                    logger.warning(f"图片提取失败: {e}")
            
            # 构建页面列表
            pages = []
            for i, page_text in enumerate(full_text_parts, 1):
                pages.append({
                    "page": i,
                    "text": page_text,
                    "images": {}, # 图片已经在上面统一处理了
                    "has_text": len(page_text.strip()) > 0
                })
            
            logger.success(f"✓ Marker提取完成: {len(pages)} 页，共 {len(full_text)} 字符")
            
            return {
                "text": full_text,
                "pages": pages,
                "metadata": all_metadata,
                "method": "marker",
                "image_mapping": image_mapping,
                "image_dir": str(image_dir) if image_dir else None
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Marker提取过程出错: {e}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise  # 重新抛出异常，让上层处理回退
        finally:
            # 清理临时目录
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")
    

    def process(self, file_path: Path) -> Dict[str, Any]:
        """
        处理PDF文件（并行执行多模态提取）
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            包含markdown内容和元数据的字典
        """
        try:
            doc_name = file_path.stem
            from utils.config import Config
            output_dir = Path(Config.OUTPUT_DIR) / doc_name / "layer1"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🚀 开始多模态处理流程: {doc_name}")
            
            # 定义任务结果容器
            text_result = None
            formula_future = None
            table_result = []
            
            # 使用线程池并行运行 API 密集型任务 (公式提取)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                
                # 1. 提交公式提取任务 (IO密集型，适合并行)
                if self.use_formula and self.formula_extractor:
                    logger.info("📤 提交公式提取任务到后台线程...")
                    # 修正：在提交任务前设置路径，避免竞态条件
                    # 结果将保存在 output_dir/formulas/page_x.json (即 layer1/formulas/)
                    self.formula_extractor.output_base_dir = output_dir
                    
                    formula_future = executor.submit(
                        self.formula_extractor.extract_formulas, 
                        file_path, 
                        "formulas" 
                    )
                
                # 2. 执行文本提取 (CPU/GPU密集型，主线程执行)
                # 提取文本（extract_text 内部已经调用了 fix_markdown_image_paths）
                text_result = self.extract_text(file_path)
                markdown_text = text_result.get('text', '')
                
                # 3. 执行表格提取 (GPU密集型，在Marker之后执行以避免显存冲突)
                if self.use_table and self.table_extractor:
                    logger.info("📊 开始表格提取任务...")
                    try:
                        # 修正：表格输出到 layer1 的父目录 (即 data/output/{doc_name}/)
                        # 这样会生成 data/output/{doc_name}/tables 和 data/output/{doc_name}/figures
                        doc_output_dir = output_dir.parent
                        table_result = self.table_extractor.extract(
                            str(file_path), 
                            str(doc_output_dir)
                        )
                        logger.success(f"✓ 表格提取完成: {len(table_result)} 个项目")
                    except Exception as e:
                        logger.error(f"表格提取失败: {e}")
                
                # 4. 等待公式提取完成
                if formula_future:
                    logger.info("⏳ 等待公式提取完成...")
                    try:
                        formula_future.result() # 等待完成，如果有异常会在这里抛出
                        logger.success("✓ 公式提取任务完成")
                    except Exception as e:
                        logger.error(f"公式提取任务异常: {e}")

            # 保存Markdown文件
            markdown_file = output_dir / f"{doc_name}.md"
            markdown_file.write_text(markdown_text, encoding='utf-8')
            logger.info(f"✓ 已保存Markdown到: {markdown_file}")
            
            # 汇总所有元数据
            final_metadata = {
                'file_name': file_path.name,
                'file_type': 'pdf',
                'method': text_result.get('method', 'unknown'),
                'pages': len(text_result.get('pages', [])),
                'raw_metadata': text_result.get('metadata', {}),
                'image_dir': text_result.get('image_dir'),
                'image_count': len(text_result.get('image_mapping', {})),
                'output_file': str(markdown_file),
                'has_tables': len(table_result) > 0,
                'has_formulas': self.use_formula, # 简单标记，具体看文件
                'layer1_dir': str(output_dir)
            }
            
            # 转换为统一格式
            return {
                'markdown': markdown_text,
                'metadata': final_metadata,
                'success': True,
                'pages': text_result.get('pages', []),
                'raw_result': text_result,
                'image_mapping': text_result.get('image_mapping', {}),
                'image_dir': text_result.get('image_dir'),
                'tables': table_result
            }
            
        except Exception as e:
            logger.error(f"❌ PDF处理失败: {e}")
            return {
                'markdown': '',
                'metadata': {
                    'file_name': file_path.name,
                    'file_type': 'pdf',
                    'error': str(e)
                },
                'success': False,
                'error': str(e)
            }
    
    def _find_split_point(self, text: str, anchor_text: str) -> int:
        """
        在文本中寻找切分点（支持模糊匹配）
        返回切分点的索引，如果未找到返回-1
        """
        if not anchor_text or not text:
            return -1
            
        # 1. 尝试精确匹配
        idx = text.find(anchor_text)
        if idx != -1:
            return idx + len(anchor_text)
            
        # 2. 尝试忽略空白字符的匹配
        # 构建字符到原始索引的映射
        text_chars = []
        text_indices = []
        for i, char in enumerate(text):
            if not char.isspace():
                text_chars.append(char)
                text_indices.append(i)
        
        clean_text = "".join(text_chars)
        clean_anchor = "".join(c for c in anchor_text if not c.isspace())
        
        if not clean_anchor:
            return -1

        # 在清洗后的文本中查找
        clean_idx = clean_text.find(clean_anchor)
        if clean_idx != -1:
            # 找到匹配结束位置在clean_text中的索引
            clean_end = clean_idx + len(clean_anchor)
            # 映射回原始文本的索引
            if clean_end > 0 and clean_end <= len(text_indices):
                return text_indices[clean_end - 1] + 1
        
        # 3. 如果还是找不到，尝试只匹配锚点文本的后半部分（容错）
        if len(clean_anchor) > 20:
            partial_anchor = clean_anchor[len(clean_anchor)//2:]
            clean_idx = clean_text.find(partial_anchor)
            if clean_idx != -1:
                clean_end = clean_idx + len(partial_anchor)
                if clean_end > 0 and clean_end <= len(text_indices):
                    return text_indices[clean_end - 1] + 1

        # 4. 最后的手段：使用difflib在一定范围内寻找最佳匹配
        # 为了性能，我们只在文本的前10000个字符中搜索（假设分页点不会偏离太远）
        search_window_size = 10000 
        search_text = clean_text[:search_window_size]
        
        s = difflib.SequenceMatcher(None, search_text, clean_anchor)
        match = s.find_longest_match(0, len(search_text), 0, len(clean_anchor))
        
        # 如果找到了足够长的匹配（例如匹配了锚点的60%以上）
        if match.size > len(clean_anchor) * 0.6:
             clean_end = match.a + match.size
             if clean_end > 0 and clean_end <= len(text_indices):
                return text_indices[clean_end - 1] + 1
                    
        return -1

    def _fix_pagination_with_ai(self, text: str, pdf_path: Path) -> str:
        """
        使用AI根据PDF页面图像修复Markdown的分页
        """
        logger.info("🔄 正在生成PDF页面快照以辅助分页...")
        try:
            # 1. 将PDF转换为图片 (低分辨率即可，主要看文字布局)
            images = convert_from_path(str(pdf_path), dpi=72)
            
            # 2. 构造Prompt
            # 为了节省Token，我们不发送整个文本，而是请求AI找出每一页的"最后一句独特文本"
            # 然后我们在本地进行切分
            
            user_content = [
                {"type": "text", "text": "I have a long Markdown text extracted from this PDF, but it lost page breaks. "
                                         "I need to split it back into pages.\n"
                                         "Please look at each PDF page image provided below, and identify the **last unique sentence or phrase** (10-20 words) that appears at the very bottom of that page's main text body (ignore footers/page numbers if possible, unless they are the only anchor).\n"
                                         "Return a JSON list: `[{\"page\": 1, \"last_text\": \"...\"}, {\"page\": 2, \"last_text\": \"...\"}, ...]`\n"
                                         "Ensure the text you quote exists exactly in the document."}
            ]
            
            # 添加图片 (限制数量以防超限，假设前20页)
            max_pages = 20
            if len(images) > max_pages:
                logger.warning(f"文档过长 ({len(images)}页)，仅处理前 {max_pages} 页的分页修复")
                images = images[:max_pages]
                
            for i, img in enumerate(images):
                # 转base64
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=70)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}
                })
                user_content.append({"type": "text", "text": f"Page {i+1}"})

            # 3. 调用API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that helps recover document structure. Return only JSON."},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            result = json.loads(response.choices[0].message.content)
            anchors = result.get("pages", [])
            if not anchors and isinstance(result, list): # 兼容直接返回列表的情况
                anchors = result
                
            # 4. 应用切分
            # 这是一个简单的贪婪匹配
            current_text = text
            final_parts = []
            
            for anchor in anchors:
                last_text = anchor.get("last_text", "").strip()
                if not last_text: continue
                
                # 使用增强的查找方法
                split_point_relative = self._find_split_point(current_text, last_text)
                
                if split_point_relative != -1:
                    # 找到切分点
                    page_content = current_text[:split_point_relative]
                    final_parts.append(page_content)
                    current_text = current_text[split_point_relative:]
                    logger.debug(f"✅ 第 {anchor['page']} 页切分成功，锚点: '{last_text[:20]}...'")
                else:
                    logger.warning(f"⚠️ 无法在文本中找到第 {anchor['page']} 页的锚点文本: '{last_text}'")
                    logger.warning(f"   当前文本开头(前100字符): {current_text[:100].replace(chr(10), ' ')}")
                    # 如果找不到，可能需要跳过或保留在下一页
            
            # 添加剩余部分
            if current_text.strip():
                final_parts.append(current_text)
                
            return "\n\n---\n\n".join(final_parts)

        except Exception as e:
            logger.error(f"AI分页修复过程出错: {e}")
            return text # 返回原文本

    def _extract_with_ocr(self, pdf_path: Path) -> Dict:
        """
        使用OCR进行文本提取（扫描件方案）
        """
        logger.info("使用OCR进行文本提取...")
        
        try:
            # 调用OCR处理器
            ocr_results = self.ocr_processor.ocr_pdf(pdf_path)
            
            # 转换为统一格式
            pages = []
            full_text = []
            
            for page_result in ocr_results:
                page_num = page_result["page"]
                text = page_result["text"]
                
                pages.append({
                    "page": page_num,
                    "text": text,
                    "images": [],
                    "has_text": len(text.strip()) > 0
                })
                
                full_text.append(text)
            
            full_text_str = "\n\n".join(full_text)
            
            logger.success(f"✓ OCR提取完成: {len(pages)} 页，共 {len(full_text_str)} 字符")
            
            return {
                "text": full_text_str,
                "pages": pages,
                "metadata": {
                    "ocr_used": True,
                    "engine": "tesseract"
                },
                "method": "ocr"
            }
            
        except Exception as e:
            logger.error(f"OCR提取失败: {e}")
            raise
    
    def needs_ocr(self, result: Dict) -> bool:
        """
        判断是否需要OCR
        
        Args:
            result: extract_text的返回结果
            
        Returns:
            True表示需要OCR，False表示不需要
        """
        # Marker已经包含OCR功能
        if result["method"] == "marker":
            return False
        
        # 检查平均每页文本量
        total_chars = sum(len(p["text"]) for p in result["pages"])
        avg_chars_per_page = total_chars / len(result["pages"]) if result["pages"] else 0
        
        # 平均每页少于100字符，建议OCR
        if avg_chars_per_page < 100:
            logger.info(f"平均每页仅 {avg_chars_per_page:.0f} 字符，建议使用OCR")
            return True
        
        logger.info(f"平均每页 {avg_chars_per_page:.0f} 字符，文本质量良好")
        return False