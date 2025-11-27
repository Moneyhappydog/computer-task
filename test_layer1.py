"""
测试Layer 1 - PDF和Word文档预处理
详细测试每一层功能，支持用户自定义输入文件
"""
from pathlib import Path
import argparse
import sys
from src.utils.config import Config
from src.layer1_preprocessing import PDFProcessor, OCRProcessor, WordProcessor


def validate_file_exists(file_path: str) -> Path:
    """验证文件是否存在
    
    Args:
        file_path: 文件路径字符串
        
    Returns:
        Path对象
        
    Raises:
        FileNotFoundError: 文件不存在时抛出异常
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    if not path.is_file():
        raise IsADirectoryError(f"不是文件: {file_path}")
    return path


def test_pdf_processor(pdf_path: Path) -> bool:
    """测试PDF处理器
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        bool: 测试是否通过
    """
    print("\n" + "="*70)
    print("🧪 测试PDF处理器")
    print("="*70)
    
    print(f"✅ 测试文件: {pdf_path.name}")
    print(f"📁 文件路径: {pdf_path}")
    
    # 测试1: 使用marker提取（启用OCR）
    print("\n1️⃣  测试Marker提取（深度学习方案，启用OCR）...")
    processor_marker = PDFProcessor(use_marker=True, use_ocr=True)
    result_marker = processor_marker.process(pdf_path)
    
    if result_marker['success']:
        print("✅ Marker提取成功!")
        print(f"   提取方法: {result_marker['metadata']['method']}")
        print(f"   总页数: {result_marker['metadata']['pages']}")
        print(f"   总字符数: {len(result_marker['markdown'])}")
        print(f"   元数据: {result_marker['metadata'].get('raw_metadata', {})}")
        
        # 显示完整提取内容
        print(f"\n📄 Marker提取完整内容:")
        print("=" * 70)
        print(result_marker['markdown'])
        print("=" * 70)
    else:
        print(f"⚠️  Marker提取失败: {result_marker.get('error')}")
    
    # 测试2: 使用OCR提取（扫描件方案）
    print("\n2️⃣  测试OCR提取（扫描件方案）...")
    processor_ocr = PDFProcessor(use_marker=False, use_ocr=True)
    result_ocr = processor_ocr.process(pdf_path)
    
    if result_ocr['success']:
        print("✅ OCR提取成功!")
        print(f"   提取方法: {result_ocr['metadata']['method']}")
        print(f"   总页数: {result_ocr['metadata']['pages']}")
        print(f"   总字符数: {len(result_ocr['markdown'])}")
        print(f"   元数据: {result_ocr['metadata'].get('raw_metadata', {})}")
        
        # 显示完整提取内容
        print(f"\n📄 OCR提取完整内容:")
        print("=" * 70)
        print(result_ocr['markdown'])
        print("=" * 70)
        
        # 测试3: 判断是否需要OCR
        extract_result = processor_ocr.extract_text(pdf_path)
        needs_ocr = processor_ocr.needs_ocr(extract_result)
        print(f"\n3️⃣  OCR需求检测:")
        print(f"   {'⚠️ 需要OCR' if needs_ocr else '✅ 不需要OCR'} (扫描件/纯文本判断)")
    else:
        print(f"❌ OCR提取失败: {result_ocr.get('error')}")
        return False
    
    # 测试4: 比较提取方法
    if result_marker['success'] and result_ocr['success']:
        print("\n5️⃣  提取结果比较:")
        marker_chars = len(result_marker['markdown'])
        ocr_chars = len(result_ocr['markdown'])
        diff = abs(marker_chars - ocr_chars) / max(marker_chars, ocr_chars) * 100
        print(f"   Marker提取字符数: {marker_chars}")
        print(f"   OCR提取字符数: {ocr_chars}")
        print(f"   字符数差异: {diff:.1f}%")
    
    return True


def test_word_processor(word_path: Path) -> bool:
    """测试Word处理器
    
    Args:
        word_path: Word文件路径
        
    Returns:
        bool: 测试是否通过
    """
    print("\n" + "="*70)
    print("🧪 测试Word处理器")
    print("="*70)
    
    print(f"✅ 测试文件: {word_path.name}")
    print(f"📁 文件路径: {word_path}")
    
    # 创建处理器
    processor = WordProcessor()
    
    # 检查格式是否支持
    if not processor.is_supported(word_path):
        print(f"❌ 文件格式不支持: {word_path.suffix}")
        return False
    
    # 处理文档
    print("\n1️⃣  开始处理Word文档...")
    result = processor.process(word_path)
    
    if not result['success']:
        print(f"❌ Word处理失败: {result.get('error')}")
        return False
    
    # 显示处理结果
    print("✅ Word处理成功!")
    print(f"   总段落数: {result['metadata']['paragraphs']}")
    print(f"   总表格数: {result['metadata']['tables']}")
    print(f"   总图片数: {result['metadata']['images']}")
    print(f"   标题统计: {result['metadata']['headings']}")
    print(f"   总字符数: {len(result['markdown'])}")
    
    # 显示完整提取内容
    print(f"\n📄 Word提取完整内容:")
    print("=" * 70)
    print(result['markdown'])
    print("=" * 70)
    
    # 详细分析提取结果
    print("\n2️⃣  提取结果详细分析:")
    
    # 检查标题提取
    has_headings = any(result['metadata']['headings'].values())
    print(f"   {'✅' if has_headings else '⚠️'} 标题提取: {'检测到标题' if has_headings else '未检测到标题'}")
    
    # 检查列表提取
    has_lists = "- " in result['markdown'] or "1. " in result['markdown']
    print(f"   {'✅' if has_lists else '⚠️'} 列表提取: {'检测到列表' if has_lists else '未检测到列表'}")
    
    # 检查表格提取
    has_tables = result['metadata']['tables'] > 0
    print(f"   {'✅' if has_tables else '⚠️'} 表格提取: {'检测到表格' if has_tables else '未检测到表格'}")
    
    # 检查格式转换
    has_bold = "**" in result['markdown']
    has_italic = "*" in result['markdown']
    print(f"   {'✅' if (has_bold or has_italic) else '⚠️'} 格式转换: {'检测到加粗/斜体' if (has_bold or has_italic) else '未检测到加粗/斜体'}")
    
    return True


def test_ocr_processor():
    """测试OCR处理器（需要先安装Tesseract）
    
    Returns:
        bool: 测试是否通过
    """
    print("\n" + "="*70)
    print("🧪 测试OCR处理器")
    print("="*70)
    
    try:
        processor = OCRProcessor()
        print("✅ OCR处理器初始化成功!")
        print(f"   语言: {processor.lang}")
        return True
    except Exception as e:
        print(f"⚠️  OCR初始化失败: {e}")
        print("   这是正常的，如果不需要OCR可以忽略")
        print("   如需使用OCR，请确保已安装Tesseract并配置正确路径")
        return False


def run_tests(pdf_path: Path = None, word_path: Path = None) -> None:
    """运行所有测试
    
    Args:
        pdf_path: PDF文件路径（可选）
        word_path: Word文件路径（可选）
    """
    print("🧪 开始测试 Layer 1 功能...\n")
    
    # 先测试配置
    from test_config import test_config
    if not test_config():
        print("\n❌ 配置测试失败，请先修复配置问题")
        sys.exit(1)
    
    # 测试PDF处理
    if pdf_path:
        test_pdf_processor(pdf_path)
    else:
        print("⚠️  未提供PDF文件，跳过PDF测试")
    
    # 测试Word处理
    if word_path:
        test_word_processor(word_path)
    else:
        print("⚠️  未提供Word文件，跳过Word测试")
    
    # 测试OCR（可选）
    test_ocr_processor()
    
    print("\n" + "="*70)
    print("✅ Layer 1 测试完成！")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试Layer 1 - PDF和Word文档预处理")
    parser.add_argument("--pdf", type=str, help="PDF文件路径")
    parser.add_argument("--word", type=str, help="Word文件路径")
    
    args = parser.parse_args()
    
    pdf_path = None
    word_path = None
    
    try:
        if args.pdf:
            pdf_path = validate_file_exists(args.pdf)
        
        if args.word:
            word_path = validate_file_exists(args.word)
        
        if not pdf_path and not word_path:
            print("❌ 请至少提供一个PDF或Word文件进行测试")
            print("用法示例:")
            print("  python test_layer1.py --pdf path/to/file.pdf")
            print("  python test_layer1.py --word path/to/file.docx")
            print("  python test_layer1.py --pdf path/to/pdf.pdf --word path/to/word.docx")
            sys.exit(1)
        
        run_tests(pdf_path, word_path)
        
    except (FileNotFoundError, IsADirectoryError) as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)