"""
OCR处理器 - 基于Tesseract的文本识别
用于处理扫描件PDF和图片型PDF
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import gc

# 导入工具模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from utils.config import Config

logger = setup_logger(__name__)

class OCRProcessor:
    """OCR文本识别处理器"""
    
    def __init__(self, engine: str = "tesseract"):
        """
        初始化OCR处理器
        
        Args:
            engine: OCR引擎类型，目前仅支持'tesseract'
        """
        self.engine = engine
        
        # 设置Tesseract路径
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
        self.lang = Config.OCR_LANG
        
        logger.info(f"✓ OCR引擎初始化: {engine} (语言: {self.lang})")
    
    def ocr_pdf(self, pdf_path: Path, pages: Optional[List[int]] = None, batch_size: int = 5) -> List[Dict]:
        """
        对PDF执行OCR识别（内存优化：分批处理）
        
        Args:
            pdf_path: PDF文件路径
            pages: 要处理的页码列表（None表示处理全部页面）
            batch_size: 批处理大小（每次处理的页数，避免内存溢出）
            
        Returns:
            [
                {"page": 1, "text": "识别的文本", "method": "ocr"},
                {"page": 2, "text": "...", "method": "ocr"},
                ...
            ]
        """
        logger.info(f"开始OCR识别: {pdf_path.name}")
        
        # 获取PDF总页数
        try:
            from pdf2image.pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(pdf_path, poppler_path=Config.POPPLER_PATH)
            total_pages = info.get('Pages', 0)
            logger.info(f"PDF总页数: {total_pages}")
        except Exception as e:
            logger.warning(f"无法获取PDF页数: {e}")
            total_pages = None
        
        # 确定要处理的页面范围
        if pages:
            page_list = pages
        elif total_pages:
            page_list = list(range(1, total_pages + 1))
        else:
            page_list = None
        
        # 分批处理以节省内存
        results = []
        
        if page_list:
            # 按批次处理
            for i in range(0, len(page_list), batch_size):
                batch_pages = page_list[i:i + batch_size]
                logger.info(f"处理批次: 页 {batch_pages[0]}-{batch_pages[-1]}")
                
                batch_results = self._ocr_pdf_batch(pdf_path, batch_pages)
                results.extend(batch_results)
                
                # 清理内存
                gc.collect()
        else:
            # 全部处理（适用于页数未知的情况）
            results = self._ocr_pdf_batch(pdf_path, None)
        
        logger.success(f"✓ OCR识别完成: {len(results)} 页")
        return results
    
    def _ocr_pdf_batch(self, pdf_path: Path, pages: Optional[List[int]]) -> List[Dict]:
        """
        对PDF的一批页面执行OCR
        
        Args:
            pdf_path: PDF文件路径
            pages: 页码列表
            
        Returns:
            OCR结果列表
        """
        try:
            # 转换PDF为图像（300 DPI高分辨率）
            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=pages[0] if pages else None,
                last_page=pages[-1] if pages else None,
                poppler_path=Config.POPPLER_PATH,
                thread_count=1  # ⭐ 使用单线程避免内存爆炸
            )
        except Exception as e:
            logger.error(f"PDF转图像失败: {e}")
            logger.info("提示：请确保已安装poppler-utils")
            return []
        
        # 对每页图像执行OCR
        results = []
        start_page = pages[0] if pages else 1
        
        for i, image in enumerate(images, start=start_page):
            text = self._ocr_image(image)
            results.append({
                "page": i,
                "text": text,
                "method": "ocr"
            })
            logger.debug(f"  页面 {i}: OCR完成 ({len(text)} 字符)")
            
            # 释放图像内存
            del image
        
        # 清理图像列表
        del images
        gc.collect()
        
        return results
    
    def _ocr_image(self, image: Image.Image) -> str:
        """
        对单张图片执行OCR
        
        Args:
            image: PIL图像对象
            
        Returns:
            识别出的文本
        """
        try:
            if self.engine == "tesseract":
                return pytesseract.image_to_string(image, lang=self.lang)
            else:
                raise NotImplementedError(f"OCR引擎 {self.engine} 暂未实现")
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return ""
    
    def process(self, file_path: Path) -> Dict[str, Any]:
        """
        处理图片文件（统一接口）
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            包含markdown内容和元数据的字典
        """
        try:
            # OCR识别
            text = self.ocr_image_file(file_path)
            
            return {
                'markdown': text,
                'metadata': {
                    'file_name': file_path.name,
                    'file_type': 'image',
                    'method': 'ocr',
                    'engine': self.engine
                },
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ OCR处理失败: {e}")
            return {
                'markdown': '',
                'metadata': {
                    'file_name': file_path.name,
                    'file_type': 'image',
                    'error': str(e)
                },
                'success': False,
                'error': str(e)
            }
    
    def ocr_image_file(self, image_path: Path) -> str:
        """
        对图片文件执行OCR
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            识别出的文本
        """
        logger.info(f"识别图片: {image_path.name}")
        
        try:
            image = Image.open(image_path)
            text = self._ocr_image(image)
            logger.success(f"✓ 识别完成: {len(text)} 字符")
            
            # 释放图像内存
            del image
            gc.collect()
            
            return text
        except Exception as e:
            logger.error(f"图片OCR失败: {e}")
            return ""