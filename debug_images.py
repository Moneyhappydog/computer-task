"""调试图片命名问题"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.layer1_preprocessing.pdf_processor import PDFProcessor

# 处理 PDF
pdf_path = Path("uploads/2023CVPR-CoMFormer.pdf")
processor = PDFProcessor(use_marker=True, use_ocr=False)

# 提取文本（会触发图片提取）
result = processor.extract_text(pdf_path)

print("\n=== 调试信息 ===")
print(f"提取方法: {result.get('method')}")
print(f"图片映射: {result.get('image_mapping')}")
print(f"图片目录: {result.get('image_dir')}")

# 检查实际保存的文件
image_dir = Path(result.get('image_dir'))
if image_dir.exists():
    print(f"\n实际保存的文件:")
    for img_file in sorted(image_dir.glob("*.png")):
        print(f"  - {img_file.name}")

# 检查 Markdown 中的引用
markdown = result.get('text', '')
import re
image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
print(f"\nMarkdown 中的图片引用（前5个）:")
for alt, path in image_refs[:5]:
    print(f"  - alt='{alt}', path='{path}'")
