#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行块级公式检测 - 最终简化版本
使用之前验证过的导入方式
"""
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent

# 导入 formula_layout（使用之前验证过的方式）
formula_layout_path = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec_layout = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout_module = importlib.util.module_from_spec(spec_layout)
spec_layout.loader.exec_module(formula_layout_module)

# 检查模块是否有内容
if not hasattr(formula_layout_module, 'PDFLayoutExtractor'):
    print(f"错误: formula_layout.py 文件可能不完整")
    print(f"文件路径: {formula_layout_path}")
    print(f"文件大小: {formula_layout_path.stat().st_size} 字节")
    sys.exit(1)

PDFLayoutExtractor = formula_layout_module.PDFLayoutExtractor
PageLayout = formula_layout_module.PageLayout
TextBlock = formula_layout_module.TextBlock
TextLine = formula_layout_module.TextLine
TextSpan = formula_layout_module.TextSpan

# 加载 block_formula_detector
block_detector_path = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"
with open(block_detector_path, 'r', encoding='utf-8') as f:
    detector_code = f.read()

# 创建命名空间
namespace = {
    'PageLayout': PageLayout,
    'TextBlock': TextBlock,
    'TextLine': TextLine,
    'TextSpan': TextSpan,
    '__name__': '__main__',
    '__file__': str(block_detector_path),
}

# 添加标准库
import dataclasses, typing, re
namespace.update({
    'dataclasses': dataclasses,
    'typing': typing,
    're': re,
    'List': typing.List,
    'Tuple': typing.Tuple,
    'Optional': typing.Optional,
    'field': dataclasses.field,
    'Path': Path,
})

# 移除相对导入行
lines = detector_code.split('\n')
code_lines = [line for line in lines if 'from .formula_layout import' not in line]
detector_code_fixed = '\n'.join(code_lines)

# 执行
exec(detector_code_fixed, namespace)

BlockFormulaDetector = namespace['BlockFormulaDetector']

# 运行
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("块级公式检测")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    print("正在解析PDF...")
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    print("正在检测块级公式...")
    detector = BlockFormulaDetector()
    formulas = detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(formulas)} 个块级公式\n")
    
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
    
    print(f"\n{'=' * 70}")
    print(f"统计: 总公式数={len(formulas)}, 平均每页={len(formulas)/len(pages):.2f}")
    print("=" * 70)
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()



