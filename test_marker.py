from src.layer1_preprocessing.pdf_processor import PDFProcessor
from pathlib import Path

# 测试Marker提取功能
processor = PDFProcessor(use_marker=True)
result = processor.extract_text(Path('uploads/5b946750-56f2-4e6e-82ac-5e02cfec5a72_First.pdf'))

print('✓ Marker提取功能测试结果:')
print(f'提取方法: {result["method"]}')
print(f'字符数: {len(result["text"])}')
print(f'页数: {len(result["pages"])}')
print(f'元数据: {result["metadata"]}')

# 如果使用了Marker方法，打印成功信息
if result["method"] == "marker":
    print('\n🎉 Marker提取功能成功!')
else:
    print('\n⚠️  Marker提取功能未使用，回退到其他方法')