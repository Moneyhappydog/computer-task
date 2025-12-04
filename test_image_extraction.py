"""
测试图片提取功能
"""
from pathlib import Path
from src.layer1_preprocessing import PDFProcessor, WordProcessor
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_pdf_image_extraction():
    """测试PDF图片提取"""
    print("\n" + "="*70)
    print("测试 PDF 图片提取")
    print("="*70)
    
    # 初始化处理器
    processor = PDFProcessor(use_marker=True, use_ocr=True)
    
    # 测试文件路径
    test_file = Path("uploads/2023CVPR-CoMFormer.pdf")
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("请将包含图片的PDF文件放到 uploads/2023CVPR-CoMFormer.pdf")
        return
    
    print(f"文件名: {test_file.stem}")
    
    # 处理PDF
    result = processor.process(test_file)
    
    if result['success']:
        print(f"\n✅ PDF处理成功")
        print(f"提取方法: {result['metadata']['method']}")
        print(f"页数: {result['metadata']['pages']}")
        print(f"图片数量: {result['metadata'].get('image_count', 0)}")
        print(f"图片保存目录: {result['metadata'].get('image_dir', 'None')}")
        print(f"Markdown保存位置: {result['metadata'].get('output_file', 'None')}")
        
        if result.get('image_mapping'):
            print("\n图片映射:")
            for old, new in result['image_mapping'].items():
                print(f"  {old} -> {new}")
        
        print(f"\nMarkdown内容预览 (前500字符):")
        print("-" * 70)
        print(result['markdown'][:500])
    else:
        print(f"❌ PDF处理失败: {result.get('error')}")


def test_word_image_extraction():
    """测试Word图片提取"""
    print("\n" + "="*70)
    print("测试 Word 图片提取")
    print("="*70)
    
    # 初始化处理器
    processor = WordProcessor()
    
    # 测试文件路径
    test_file = Path("data/input/test.docx")
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("请将包含图片的Word文件放到 data/input/test.docx")
        return
    
    print(f"文件名: {test_file.stem}")
    
    # 处理Word
    result = processor.process(test_file)
    
    if result['success']:
        print(f"\n✅ Word处理成功")
        print(f"段落数: {result['metadata']['paragraphs']}")
        print(f"表格数: {result['metadata']['tables']}")
        print(f"图片数量: {result['metadata'].get('image_count', 0)}")
        print(f"图片保存目录: {result['metadata'].get('image_dir', 'None')}")
        print(f"Markdown保存位置: {result['metadata'].get('output_file', 'None')}")
        
        if result.get('image_mapping'):
            print("\n图片映射:")
            for old, new in result['image_mapping'].items():
                print(f"  {old} -> {new}")
        
        print(f"\nMarkdown内容预览 (前500字符):")
        print("-" * 70)
        print(result['markdown'][:500])
    else:
        print(f"❌ Word处理失败: {result.get('error')}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("图片提取功能测试")
    print("="*70)
    
    # 测试PDF
    test_pdf_image_extraction()
    
    # 测试Word
    test_word_image_extraction()
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
    print("\n提示:")
    print("1. 图片保存在: data/output/{文件名}/images/")
    print("2. Markdown保存在: data/output/{文件名}/layer1/{文件名}.md")
    print("3. 图片命名格式: {页码}_image_{索引}.png")
    print("4. Markdown中的图片引用：![Figure](../images/{页码}_image_{索引}.png)")
    print("5. Markdown中的图片路径已自动修正")
