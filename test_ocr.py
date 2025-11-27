#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PDF处理器的OCR功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from src.layer1_preprocessing.pdf_processor import PDFProcessor
from utils.logger import setup_logger

logger = setup_logger("test_ocr")

def test_pdf_ocr():
    """测试PDF处理器的OCR功能"""
    # 设置PDF文件路径
    # 请将此路径替换为您要测试的PDF文件路径
    pdf_path = Path("D:\codeC\VsCodeP\dita-converter\1593893244082.pdf")
    
    if not pdf_path.exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        return False
    
    try:
        logger.info("\n=== 初始化PDF处理器（启用OCR） ===")
        # 创建PDF处理器实例，启用OCR功能
        processor = PDFProcessor(use_marker=True, use_ocr=True)
        
        logger.info("\n=== 开始提取PDF文本 ===")
        result = processor.extract_text(pdf_path)
        
        logger.info("\n=== 提取结果 ===")
        logger.info(f"方法: {result['method']}")
        logger.info(f"总页数: {len(result['pages'])}")
        logger.info(f"总字符数: {len(result['text'])}")
        
        # 显示前500个字符作为示例
        logger.info("\n=== 文本示例（前500字符） ===")
        logger.info(result['text'][:500] + "...")
        
        # 检查是否使用了OCR
        if result['method'] == 'ocr':
            logger.success("✅ 成功使用OCR提取文本")
        elif result['method'] == 'marker':
            logger.info("ℹ️ 使用Marker提取文本（Marker已包含OCR功能）")
        elif result['method'] == 'pdfplumber':
            logger.info("ℹ️ 使用pdfplumber提取文本（文本质量良好，无需OCR）")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_pdf_ocr()
