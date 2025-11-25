"""
测试Layer 1 - PDF处理和OCR
"""
from pathlib import Path
from src.utils.config import Config
from src.layer1_preprocessing import PDFProcessor, OCRProcessor

def test_pdf_processor():
    """测试PDF处理器"""
    print("\n" + "="*70)
    print("🧪 测试PDF处理器")
    print("="*70)
    
    # 检查是否有测试PDF
    test_pdf = Config.INPUT_DIR / "test.pdf"
    
    if not test_pdf.exists():
        print(f"⚠️  测试PDF不存在: {test_pdf}")
        print(f"\n请执行以下步骤：")
        print(f"1. 在 {Config.INPUT_DIR} 目录放一个PDF文件")
        print(f"2. 将PDF文件重命名为 test.pdf")
        print(f"3. 重新运行此测试")
        return False
    
    print(f"✅ 找到测试文件: {test_pdf.name}")
    
    # 创建处理器（先不用Marker，用传统方法测试）
    print("\n正在初始化PDF处理器（使用pdfplumber）...")
    processor = PDFProcessor(use_marker=False)
    
    # 提取文本
    print("开始提取PDF文本...")
    result = processor.extract_text(test_pdf)
    
    # 显示结果
    print(f"\n✅ 提取完成！")
    print(f"  提取方法: {result['method']}")
    print(f"  总页数: {len(result['pages'])}")
    print(f"  总字符数: {len(result['text'])}")
    print(f"  元数据: {result['metadata']}")
    
    # 显示前100字符
    print(f"\n📄 文本预览（前100字符）:")
    print("-" * 70)
    print(result['text'][:100])
    print("-" * 70)
    
    # 判断是否需要OCR
    needs_ocr = processor.needs_ocr(result)
    print(f"\n{'⚠️' if needs_ocr else '✅'}  是否需要OCR: {needs_ocr}")
    
    return True

def test_ocr_processor():
    """测试OCR处理器（需要先安装Tesseract）"""
    print("\n" + "="*70)
    print("🧪 测试OCR处理器")
    print("="*70)
    
    try:
        processor = OCRProcessor()
        print("✅ OCR处理器初始化成功")
        print("   如需测试OCR功能，请准备扫描件PDF")
        return True
    except Exception as e:
        print(f"⚠️  OCR初始化失败: {e}")
        print("   这是正常的，如果不需要OCR可以忽略")
        return False

if __name__ == "__main__":
    print("🧪 开始测试 Layer 1 功能...\n")
    
    # 先测试配置
    from test_config import test_config
    if not test_config():
        print("\n❌ 配置测试失败，请先修复配置问题")
        exit(1)
    
    # 测试PDF处理
    test_pdf_processor()
    
    # 测试OCR（可选）
    test_ocr_processor()
    
    print("\n" + "="*70)
    print("✅ Layer 1 测试完成！")
    print("="*70)