"""
PDF处理器 - 智能文本提取
支持多种方案：marker-pdf（深度学习）、pdfplumber（传统）、OCR（扫描件）
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
import pdfplumber
from pdf2image import convert_from_path
import os

# 导入工具模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from utils.config import Config

logger = setup_logger(__name__)

class PDFProcessor:
    """PDF智能处理器（优先使用marker-pdf）"""
    
    def __init__(self, use_marker: bool = True):
        """
        初始化PDF处理器
        
        Args:
            use_marker: 是否尝试使用marker-pdf（深度学习方案）
        """
        self.use_marker = use_marker
        self.marker_models = None
        
        # 设置环境变量以优化内存使用
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        
        if use_marker:
            try:
                logger.info("正在加载Marker模型（首次运行会自动下载）...")
                from marker.convert import convert_single_pdf
                from marker.models import load_all_models
                
                self.marker_models = load_all_models()
                self.convert_single_pdf = convert_single_pdf
                logger.success("✓ Marker模型加载成功")
            except Exception as e:
                logger.warning(f"Marker模型加载失败，将使用传统方法: {e}")
                self.use_marker = False
    
    def extract_text(self, pdf_path: Path) -> Dict[str, any]:
        """
        提取PDF文本（自动选择最佳方案）
        
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
                "method": "marker|pdfplumber|ocr"
            }
        """
        logger.info(f"开始处理PDF: {pdf_path.name}")
        
        # 方案1: 尝试使用Marker（最智能，支持复杂布局）
        if self.use_marker and self.marker_models:
            try:
                return self._extract_with_marker(pdf_path)
            except Exception as e:
                logger.warning(f"Marker提取失败，回退到传统方法: {e}")
        
        # 方案2: 使用pdfplumber（传统文本提取）
        return self._extract_with_pdfplumber(pdf_path)
    
    def _extract_with_marker(self, pdf_path: Path) -> Dict:
        """使用Marker进行智能PDF解析（深度学习方案）- 内存优化版"""
        logger.info("使用Marker进行智能PDF解析...")
        
        try:
            # 关键修改：添加内存优化参数
            full_text, images, metadata = self.convert_single_pdf(
                str(pdf_path),
                self.marker_models,
                max_pages=None,        # 处理所有页面
                langs=None,            # 自动检测语言
                batch_multiplier=1,    # 批处理倍数（控制内存使用）
                # ⭐ 关键内存优化参数
                workers=1,             # 使用单线程，避免多进程内存爆炸
            )
            
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
            logger.error(f"Marker提取过程出错: {e}")
            raise  # 重新抛出异常，让上层处理回退
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict:
        """使用pdfplumber提取文本（传统方案）"""
        logger.info("使用pdfplumber进行文本提取...")
        
        pages = []
        full_text = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata or {}
                
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    images = page.images or []
                    
                    pages.append({
                        "page": i,
                        "text": text,
                        "images": images,
                        "has_text": len(text.strip()) > 50  # 超过50字符认为有文本
                    })
                    
                    full_text.append(text)
                    
                    logger.debug(f"  页面 {i}: {len(text)} 字符, {len(images)} 个图片")
            
            full_text_str = "\n\n".join(full_text)
            logger.success(f"✓ pdfplumber提取完成: {len(pages)} 页，共 {len(full_text_str)} 字符")
            
            return {
                "text": full_text_str,
                "pages": pages,
                "metadata": metadata,
                "method": "pdfplumber"
            }
            
        except Exception as e:
            logger.error(f"pdfplumber提取失败: {e}")
            raise
    
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