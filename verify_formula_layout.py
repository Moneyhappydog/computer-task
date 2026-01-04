"""快速验证 formula_layout 模块"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "layer1_preprocessing"))

try:
    from formula_layout import PDFLayoutExtractor, PageLayout, TextBlock, TextLine, TextSpan
    print("✅ formula_layout 模块导入成功！")
    print(f"   - PDFLayoutExtractor: {PDFLayoutExtractor}")
    print(f"   - PageLayout: {PageLayout}")
    print(f"   - TextBlock: {TextBlock}")
    print(f"   - TextLine: {TextLine}")
    print(f"   - TextSpan: {TextSpan}")
    print("\n✅ 所有类都可用，模块结构正确！")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



