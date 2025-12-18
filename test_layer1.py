"""
测试Layer 1 - PDF和Word文档预处理
详细测试每一层功能，支持用户自定义输入文件
"""
import json
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
    print(f"📁 文件名(不含扩展名): {pdf_path.stem}")
    
    # 测试1: 使用marker提取（启用OCR）
    print("\n1️⃣  测试Marker提取（深度学习方案，启用OCR）...")
    
    # 尝试获取 API Key
    try:
        from response.gpt import openai_api_key
        api_key = openai_api_key
        print(f"🔑 已加载 API Key: {api_key[:8]}...")
    except ImportError:
        api_key = None
        print("⚠️ 未找到 API Key，公式提取和表格智能过滤将不可用")

    processor_marker = PDFProcessor(
        use_marker=True, 
        use_ocr=True,
        use_table=True,
        use_formula=True,
        api_key=api_key
    )
    result_marker = processor_marker.process(pdf_path)
    
    if result_marker['success']:
        print("✅ Marker提取成功!")
        print(f"   提取方法: {result_marker['metadata']['method']}")
        print(f"   总页数: {result_marker['metadata']['pages']}")
        print(f"   总字符数: {len(result_marker['markdown'])}")
        print(f"   图片数量: {result_marker['metadata'].get('image_count', 0)}")
        print(f"   图片保存目录: {result_marker['metadata'].get('image_dir', 'None')}")
        print(f"   Markdown保存位置: {result_marker['metadata'].get('output_file', 'None')}")
        print(f"   元数据: {result_marker['metadata'].get('raw_metadata', {})}")
        
        # 保存 layer1_result.json（与 test_integration.py 保持一致）
        output_file_path = Path(result_marker['metadata'].get('output_file'))
        layer1_output_dir = output_file_path.parent
        layer1_json_path = layer1_output_dir / "layer1_result.json"
        
        with open(layer1_json_path, 'w', encoding='utf-8') as f:
            json.dump(result_marker, f, ensure_ascii=False, indent=2)
        print(f"   JSON结果保存位置: {layer1_json_path}")
        
        if result_marker.get('image_mapping'):
            print(f"\n   图片映射 ({len(result_marker['image_mapping'])}张):")
            for old, new in list(result_marker['image_mapping'].items())[:5]:  # 只显示前5个
                print(f"     {old} -> {new}")
            if len(result_marker['image_mapping']) > 5:
                print(f"     ... 还有 {len(result_marker['image_mapping']) - 5} 张图片")
        
        # 显示部分提取内容
        print(f"\n📄 Marker提取内容预览 (前1000字符):")
        print("=" * 70)
        print(result_marker['markdown'][:1000])
        print("=" * 70)
    else:
        print(f"⚠️  Marker提取失败: {result_marker.get('error')}")
    
    return True
    
    # 测试2: OCR模式已经在Marker中集成，不再单独测试
    print("\n2️⃣  提示: OCR功能已集成在Marker中")
    
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
    print(f"📁 文件名(不含扩展名): {word_path.stem}")
    
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
    print(f"   图片数量: {result['metadata'].get('image_count', 0)}")
    print(f"   图片保存目录: {result['metadata'].get('image_dir', 'None')}")
    print(f"   Markdown保存位置: {result['metadata'].get('output_file', 'None')}")
    print(f"   标题统计: {result['metadata']['headings']}")
    print(f"   总字符数: {len(result['markdown'])}")
    
    # 保存 layer1_result.json（与 test_integration.py 保持一致）
    output_file_path = Path(result['metadata'].get('output_file'))
    layer1_output_dir = output_file_path.parent
    layer1_json_path = layer1_output_dir / "layer1_result.json"
    
    with open(layer1_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"   JSON结果保存位置: {layer1_json_path}")
    
    if result.get('image_mapping'):
        print(f"\n   图片映射 ({len(result['image_mapping'])}张):")
        for old, new in result['image_mapping'].items():
            print(f"     {old} -> {new}")
    
    # 显示部分提取内容
    print(f"\n📄 Word提取内容预览 (前1000字符):")
    print("=" * 70)
    print(result['markdown'][:1000])
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


def test_omnidocbench(omnidocbench_dir: Path, batch_size: int = 100) -> bool:
    """测试OmniDocBench数据集处理
    
    Args:
        omnidocbench_dir: OmniDocBench数据集根目录
        batch_size: 处理的文件数量
        
    Returns:
        bool: 测试是否通过
    """
    print("\n" + "="*70)
    print("🧪 测试OmniDocBench数据集处理")
    print("="*70)
    
    json_path = omnidocbench_dir / "OmniDocBench.json"
    pdfs_dir = omnidocbench_dir / "pdfs"
    images_dir = omnidocbench_dir / "images"
    
    if not json_path.exists():
        print(f"❌ 找不到标注文件: {json_path}")
        return False
    
    # 检查是否有PDF目录（优先使用PDF）
    use_pdf = pdfs_dir.exists()
    use_images = images_dir.exists()
    
    if not use_pdf and not use_images:
        print(f"❌ 找不到PDF目录或图片目录")
        print(f"   请确保数据集包含以下目录之一:")
        print(f"   - {pdfs_dir} (推荐，用于测试PDF转Markdown)")
        print(f"   - {images_dir} (备选，用于OCR测试)")
        return False
        
    print(f"📂 数据集目录: {omnidocbench_dir}")
    print(f"📄 标注文件: {json_path.name}")
    
    if use_pdf:
        print(f"📑 PDF目录: {pdfs_dir.name} ✅")
        print(f"🖼️ 图片目录: {images_dir.name if use_images else '(未找到)'}")
    else:
        print(f"📑 PDF目录: (未找到)")
        print(f"🖼️ 图片目录: {images_dir.name} ✅")
        
    print(f"🔢 处理数量: {batch_size}")
    
    # 读取标注文件
    print("\n1️⃣  读取标注文件...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 读取成功，共 {len(data)} 条数据")
    except Exception as e:
        print(f"❌ 读取标注文件失败: {e}")
        return False
    
    # 根据可用数据初始化相应的处理器
    if use_pdf:
        print("\n2️⃣  初始化PDF处理器（Marker + OCR模式，用于PDF转Markdown）...")
        try:
            processor = PDFProcessor(use_marker=True, use_ocr=True)
            print("✅ PDF处理器初始化成功!")
            processing_mode = "PDF"
        except Exception as e:
            print(f"❌ PDF处理器初始化失败: {e}")
            return False
    else:
        print("\n2️⃣  初始化OCR处理器（用于单页图片识别）...")
        try:
            processor = OCRProcessor()
            print("✅ OCR处理器初始化成功!")
            processing_mode = "IMAGE"
        except Exception as e:
            print(f"❌ OCR处理器初始化失败: {e}")
            print("   提示: 如果不需要OCR可以忽略此错误")
            return False
        
    # 处理数据
    print(f"\n3️⃣  开始处理前 {batch_size} 个文件（使用{processing_mode}模式）...")
    if use_pdf:
        print(f"   ⏱️  预计时间: {batch_size * 8 / 60:.1f} 分钟 (每个文件约8秒)")
    
    success_count = 0
    processed_count = 0
    failed_files = []
    skipped_count = 0
    
    # 创建输出目录
    output_base_dir = Path("data/output/OmniDocBench")
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    import time
    start_time = time.time()
    
    for item in data[:batch_size]:
        processed_count += 1
        
        # 获取文件路径
        try:
            image_filename = item['page_info']['image_path']
            file_stem = Path(image_filename).stem
            
            if use_pdf:
                # 使用PDF文件（推荐，测试PDF转Markdown能力）
                pdf_filename = file_stem + ".pdf"
                file_path = pdfs_dir / pdf_filename
                file_display_name = pdf_filename
            else:
                # 使用图片文件（备选）
                file_path = images_dir / image_filename
                file_display_name = image_filename
            
            if not file_path.exists():
                print(f"⚠️  文件不存在 (跳过): {file_display_name}")
                failed_files.append(file_display_name)
                continue
            
            # 检查是否已经处理过（避免重复处理）
            expected_output_dir = output_base_dir / file_stem / "layer1"
            expected_json = expected_output_dir / "layer1_result.json"
            expected_md = expected_output_dir / f"{file_stem}.md"
            
            if expected_json.exists() and expected_md.exists():
                print(f"   ⏩ [{processed_count}/{batch_size}] 跳过: {file_display_name} (已处理)")
                success_count += 1
                skipped_count += 1
                continue
                
            print(f"\n   处理 [{processed_count}/{batch_size}]: {file_display_name}")
            
            # 处理文件
            result = processor.process(file_path)
            
            if result['success']:
                print(f"   ✅ 处理成功!")
                print(f"      提取方法: {result['metadata']['method']}")
                if use_pdf:
                    print(f"      总页数: {result['metadata'].get('pages', 1)}")
                    print(f"      图片数量: {result['metadata'].get('image_count', 0)}")
                print(f"      总字符数: {len(result['markdown'])}")
                
                # 添加Ground Truth信息以便对比
                result['ground_truth'] = item
                
                # 保存结果（与test_pdf_processor保持一致的结构）
                output_file_path = Path(result['metadata'].get('output_file'))
                layer1_output_dir = output_file_path.parent
                
                # 保存layer1_result.json
                layer1_json_path = layer1_output_dir / "layer1_result.json"
                with open(layer1_json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"      Markdown: {output_file_path}")
                print(f"      JSON结果: {layer1_json_path}")
                
                success_count += 1
            else:
                print(f"   ❌ 处理失败: {result.get('error')}")
                failed_files.append(file_display_name)
                
        except KeyError as e:
            print(f"⚠️  数据格式错误 (缺少字段 {e})")
            failed_files.append(f"unknown_{processed_count}")
            continue
        except Exception as e:
            print(f"❌ 处理异常: {e}")
            import traceback
            traceback.print_exc()
            failed_files.append(file_display_name if 'file_display_name' in locals() else f"unknown_{processed_count}")
            continue
            
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*70)
    print(f"✅ 批量处理完成!")
    print(f"   处理模式: {processing_mode}")
    print(f"   总计扫描: {processed_count}")
    print(f"   成功处理: {success_count - skipped_count}")
    print(f"   跳过已有: {skipped_count}")
    print(f"   失败数量: {len(failed_files)}")
    print(f"   成功率: {success_count/processed_count*100:.1f}%")
    print(f"   总耗时: {elapsed_time/60:.1f} 分钟")
    if success_count - skipped_count > 0:
        print(f"   平均速度: {elapsed_time/(success_count - skipped_count):.1f} 秒/文件")
    print(f"   输出目录: {output_base_dir}")
    
    if failed_files:
        print(f"\n⚠️  失败文件列表:")
        for failed_file in failed_files[:10]:  # 只显示前10个
            print(f"      {failed_file}")
        if len(failed_files) > 10:
            print(f"      ... 还有 {len(failed_files) - 10} 个失败文件")
    
    # 如果没有PDF，提示用户如何下载
    if not use_pdf:
        print("\n💡 提示: 当前使用图片模式进行OCR识别")
        print("   如需测试PDF转Markdown能力，请下载包含PDF的完整数据集:")
        print("   - Hugging Face: https://huggingface.co/datasets/opendatalab/OmniDocBench")
        print("   - OpenDataLab: https://opendatalab.com/OpenDataLab/OmniDocBench")
        print(f"   下载后将pdfs目录放到: {omnidocbench_dir}")
    
    print("="*70)
    
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


def run_tests(pdf_path: Path = None, word_path: Path = None, omnidocbench_dir: Path = None, batch_size: int = 100) -> None:
    """运行所有测试
    
    Args:
        pdf_path: PDF文件路径（可选）
        word_path: Word文件路径（可选）
        omnidocbench_dir: OmniDocBench数据集路径（可选）
        batch_size: 批处理大小
    """
    print("🧪 开始测试 Layer 1 功能...\n")
    
    # 先测试配置
    from test_config import test_config
    if not test_config():
        print("\n❌ 配置测试失败，请先修复配置问题")
        sys.exit(1)
    
    # 测试OmniDocBench
    if omnidocbench_dir:
        test_omnidocbench(omnidocbench_dir, batch_size)
        return  # 如果指定了数据集测试，则只运行数据集测试

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
    print("\n📁 输出文件结构:")
    print("data/output/")
    print("  └── {文件名}/")
    print("      ├── layer1/")
    print("      │   └── {文件名}.md     # Markdown输出")
    print("      └── images/              # 提取的图片")
    print("          ├── 0_image_0.png")
    print("          └── ...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试Layer 1 - PDF和Word文档预处理")
    parser.add_argument("--pdf", type=str, help="PDF文件路径")
    parser.add_argument("--word", type=str, help="Word文件路径")
    parser.add_argument("--omnidocbench", type=str, help="OmniDocBench数据集根目录 (包含OmniDocBench.json和images目录)")
    parser.add_argument("--batch_size", type=int, default=100, help="OmniDocBench处理数量 (默认: 100)")
    
    args = parser.parse_args()
    
    pdf_path = None
    word_path = None
    omnidocbench_dir = None
    
    try:
        if args.pdf:
            pdf_path = validate_file_exists(args.pdf)
        
        if args.word:
            word_path = validate_file_exists(args.word)
            
        if args.omnidocbench:
            omnidocbench_dir = Path(args.omnidocbench)
            if not omnidocbench_dir.exists():
                raise FileNotFoundError(f"数据集目录不存在: {omnidocbench_dir}")
        
        if not pdf_path and not word_path and not omnidocbench_dir:
            print("❌ 请至少提供一个PDF/Word文件或数据集目录进行测试")
            print("用法示例:")
            print("  python test_layer1.py --pdf path/to/file.pdf")
            print("  python test_layer1.py --word path/to/file.docx")
            print("  python test_layer1.py --omnidocbench data/input/OmniDocBench --batch_size 100")
            sys.exit(1)
        
        run_tests(pdf_path, word_path, omnidocbench_dir, args.batch_size)
        
    except (FileNotFoundError, IsADirectoryError) as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)