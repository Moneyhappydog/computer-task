#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速运行块级公式检测 - 最简单版本
"""
import sys
from pathlib import Path

# 添加路径
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# 直接导入模块文件，避免包导入
import importlib.util

# 1. 导入 formula_layout
formula_layout_file = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec1 = importlib.util.spec_from_file_location("formula_layout", formula_layout_file)
formula_layout = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(formula_layout)

# 2. 导入 block_formula_detector，替换其导入
block_detector_file = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"

# 读取源代码并修改导入
with open(block_detector_file, 'r', encoding='utf-8') as f:
    code = f.read()

# 替换相对导入
code = code.replace(
    'from .formula_layout import PageLayout, TextBlock, TextLine, TextSpan',
    '# 使用已加载的模块\nPageLayout = formula_layout.PageLayout\nTextBlock = formula_layout.TextBlock\nTextLine = formula_layout.TextLine\nTextSpan = formula_layout.TextSpan'
)

# 执行代码
namespace = {
    'formula_layout': formula_layout,
    'PageLayout': formula_layout.PageLayout,
    'TextBlock': formula_layout.TextBlock,
    'TextLine': formula_layout.TextLine,
    'TextSpan': formula_layout.TextSpan,
    '__name__': 'block_formula_detector',
    '__file__': str(block_detector_file),
    'dataclasses': __import__('dataclasses'),
    'typing': __import__('typing'),
    're': __import__('re'),
    'Path': Path,
}

# 添加 dataclass 相关
import dataclasses
namespace['field'] = dataclasses.field
namespace['List'] = __import__('typing').List
namespace['Tuple'] = __import__('typing').Tuple
namespace['Optional'] = __import__('typing').Optional

exec(code, namespace)

# 获取类
BlockFormulaDetector = namespace['BlockFormulaDetector']
PDFLayoutExtractor = formula_layout.PDFLayoutExtractor

# 主程序
if __name__ == "__main__":
    pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    print("=" * 70)
    print("块级公式检测")
    print("=" * 70)
    print(f"\nPDF: {Path(pdf_path).name}\n")
    
    try:
        # 版面解析
        print("正在解析PDF...")
        extractor = PDFLayoutExtractor(pdf_path)
        pages = extractor.parse()
        print(f"✓ 解析完成，共 {len(pages)} 页\n")
        
        # 公式检测
        print("正在检测块级公式...")
        detector = BlockFormulaDetector()
        formulas = detector.detect_block_formulas(pages)
        print(f"✓ 检测完成，发现 {len(formulas)} 个块级公式\n")
        
        # 显示结果
        print("=" * 70)
        print("检测结果（前10个）:")
        print("=" * 70)
        
        for i, f in enumerate(formulas[:10]):
            print(f"\n公式 {i+1}:")
            print(f"  页码: {f.page_number}, 块: {f.block_index}")
            print(f"  行索引: {f.line_indices}, 得分: {f.score:.3f}")
            print(f"  位置: bbox={f.bbox}")
        
        if len(formulas) > 10:
            print(f"\n... (还有 {len(formulas) - 10} 个公式)")
        
        # 统计
        print(f"\n{'=' * 70}")
        print("统计:")
        print(f"  总公式数: {len(formulas)}")
        print(f"  平均每页: {len(formulas)/len(pages):.2f} 个")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()



