"""
PDF处理器 - 智能文本提取
支持多种方案：marker-pdf（深度学习）、OCR（扫描件）
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
# import pdfplumber
from pdf2image import convert_from_path
import os

# 导入工具模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from utils.config import Config
from .ocr_processor import OCRProcessor

logger = setup_logger(__name__)

class PDFProcessor:
    """PDF智能处理器（优先使用marker-pdf）"""
    
    def __init__(self, use_marker: bool = True, use_ocr: bool = True):  # OCR默认开启，无需手动指定即可自动启用OCR功能
        """
        初始化PDF处理器
        
        Args:
            use_marker: 是否尝试使用marker-pdf（深度学习方案）
            use_ocr: 是否在需要时自动使用OCR
        """
        self.use_marker = use_marker
        self.use_ocr = use_ocr
        self.marker_models = None
        self.ocr_processor = None
        
        # 设置环境变量以优化内存使用
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        
        # 初始化OCR处理器
        if use_ocr:
            try:
                self.ocr_processor = OCRProcessor()
                logger.success("✓ OCR处理器初始化成功")
            except Exception as e:
                logger.warning(f"OCR处理器初始化失败，将不使用OCR: {e}")
                self.use_ocr = False
        
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
                "method": "marker|ocr"
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
    
    def _extract_with_marker(self, pdf_path: Path) -> Dict:
        """使用Marker进行智能PDF解析（深度学习方案）- 内存优化版"""
        logger.info("使用Marker进行智能PDF解析...")
        
        try:
            logger.info("准备调用convert_single_pdf函数...")
            logger.info(f"参数：pdf_path={str(pdf_path)}, marker_models={self.marker_models}")
            
            # 关键修改：添加内存优化参数
            result = self.convert_single_pdf(
                str(pdf_path),
                self.marker_models,
                max_pages=None,        # 处理所有页面
                langs=None,            # 自动检测语言
                batch_multiplier=1,    # 批处理倍数（控制内存使用）
            )
            
            logger.info("convert_single_pdf函数调用成功，开始处理返回值...")
            
            # 灵活处理convert_single_pdf的返回值
            if isinstance(result, tuple):
                # 打印调试信息，查看返回值数量
                logger.info(f"convert_single_pdf返回了 {len(result)} 个值")
                
                # 根据返回值数量进行处理
                if len(result) >= 3:
                    full_text, images, metadata = result[0], result[1], result[2]
                elif len(result) == 2:
                    full_text, metadata = result
                    images = {}
                elif len(result) == 1:
                    full_text = result[0]
                    images = {}
                    metadata = {}
                else:
                    # 空元组
                    full_text = ""
                    images = {}
                    metadata = {}
            else:
                # 如果返回的不是元组，直接作为文本处理
                full_text = result
                images = {}
                metadata = {}
            
            # Marker返回的是markdown格式，需要按页分割
            pages = []
            page_texts = full_text.split("\n---\n")  # Marker用---分隔页面
            
            for i, page_text in enumerate(page_texts, 1):
                pages.append({
                    "page": i,
                    "text": page_text,
                    "images": images.get(i, []),
                    "has_text": len(page_text.strip()) > 0
                })
            
            logger.success(f"✓ Marker提取完成: {len(pages)} 页，共 {len(full_text)} 字符")
            
            return {
                "text": full_text,
                "pages": pages,
                "metadata": metadata,
                "method": "marker"
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Marker提取过程出错: {e}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise  # 重新抛出异常，让上层处理回退
    
    # def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict:
    #     """
    #     使用pdfplumber提取文本（传统方案）
    #     """
    #     logger.info("使用pdfplumber进行文本提取...")
    #     
    #     pages = []
    #     full_text = []
    #     
    #     try:
    #         with pdfplumber.open(pdf_path) as pdf:
    #             metadata = pdf.metadata or {}
    #             
    #             for i, page in enumerate(pdf.pages, 1):
    #                 text = page.extract_text() or ""
    #                 images = page.images or []
    #                 
    #                 pages.append({
    #                     "page": i,
    #                     "text": text,
    #                     "images": images,
    #                     "has_text": len(text.strip()) > 50  # 超过50字符认为有文本
    #                 })
    #                 
    #                 full_text.append(text)
    #                 
    #                 logger.debug(f"  页面 {i}: {len(text)} 字符, {len(images)} 个图片")
    #         
    #         full_text_str = "\n\n".join(full_text)
    #         logger.success(f"✓ pdfplumber提取完成: {len(pages)} 页，共 {len(full_text_str)} 字符")
    #         
    #         return {
    #             "text": full_text_str,
    #             "pages": pages,
    #             "metadata": metadata,
    #             "method": "pdfplumber"
    #         }
    #         
    #     except Exception as e:
    #         logger.error(f"pdfplumber提取失败: {e}")
    #         raise
    
    def process(self, file_path: Path) -> Dict[str, Any]:
        """
        处理PDF文件（统一接口）
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            包含markdown内容和元数据的字典
        """
        try:
            # 提取文本
            result = self.extract_text(file_path)
            
            # 转换为统一格式
            return {
                'markdown': result.get('text', ''),
                'metadata': {
                    'file_name': file_path.name,
                    'file_type': 'pdf',
                    'method': result.get('method', 'unknown'),
                    'pages': len(result.get('pages', [])),
                    'raw_metadata': result.get('metadata', {})
                },
                'success': True,
                'pages': result.get('pages', []),
                'raw_result': result
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