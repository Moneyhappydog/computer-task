"""
文件路由器
根据文件类型自动选择合适的处理器
"""
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .pdf_processor import PDFProcessor
from .word_processor import WordProcessor
from .ocr_processor import OCRProcessor

logger = logging.getLogger(__name__)

class FileRouter:
    """文件路由器 - Layer 1 统一入口"""
    
    def __init__(self):
        """初始化所有处理器"""
        logger.info("🚀 初始化文件路由器...")
        
        self.processors = {
            'pdf': PDFProcessor(),
            'word': WordProcessor(),
            'ocr': OCRProcessor()
        }
        
        self.file_type_map = {
            '.pdf': 'pdf',
            '.docx': 'word',
            '.doc': 'word',
            '.png': 'ocr',
            '.jpg': 'ocr',
            '.jpeg': 'ocr',
            '.tiff': 'ocr',
            '.bmp': 'ocr'
        }
        
        logger.info("✅ 文件路由器初始化完成")
    
    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        处理文件（自动识别类型）
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理结果字典
        """
        if not file_path.exists():
            logger.error(f"❌ 文件不存在: {file_path}")
            return {
                'success': False,
                'error': 'File not found'
            }
        
        # 识别文件类型
        file_ext = file_path.suffix.lower()
        processor_type = self.file_type_map.get(file_ext)
        
        if not processor_type:
            logger.error(f"❌ 不支持的文件格式: {file_ext}")
            return {
                'success': False,
                'error': f'Unsupported file format: {file_ext}'
            }
        
        logger.info(f"📂 检测到文件类型: {processor_type} ({file_path.name})")
        
        # 选择处理器
        processor = self.processors[processor_type]
        
        # 处理文件
        result = processor.process(file_path)
        
        # 添加文件信息
        result['file_path'] = str(file_path)
        result['file_type'] = processor_type
        
        return result
    
    def get_supported_formats(self) -> list:
        """获取支持的文件格式"""
        return list(self.file_type_map.keys())


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("file_router")
    
    router = FileRouter()
    
    print("📋 支持的文件格式:")
    for fmt in router.get_supported_formats():
        print(f"  • {fmt}")
    
    # 测试处理
    test_files = [
        Path("data/input/test.pdf"),
        Path("data/input/test.docx"),
        Path("data/input/test.png")
    ]
    
    for file_path in test_files:
        if file_path.exists():
            print(f"\n{'='*70}")
            print(f"测试: {file_path.name}")
            print('='*70)
            
            result = router.process_file(file_path)
            
            if result['success']:
                print(f"✅ 处理成功")
                print(f"类型: {result['file_type']}")
                print(f"Markdown长度: {len(result['markdown'])} 字符")
            else:
                print(f"❌ 处理失败: {result.get('error')}")