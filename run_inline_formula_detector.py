#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行行内公式检测 - 测试脚本
"""
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent

# 导入模块
formula_layout_path = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec1 = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(formula_layout)

PDFLayoutExtractor = formula_layout.PDFLayoutExtractor

block_detector_path = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"
spec2 = importlib.util.spec_from_file_location("block_formula_detector", block_detector_path)

sys.modules['src'] = type(sys)('src')
sys.modules['src.layer1_preprocessing'] = type(sys)('layer1_preprocessing')
sys.modules['src.layer1_preprocessing.formula_layout'] = formula_layout

block_formula_detector = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(block_formula_detector)

BlockFormulaDetector = block_formula_detector.BlockFormulaDetector

# 导入行内公式检测器
inline_detector_path = ROOT / "src" / "layer1_preprocessing" / "inline_formula_detector.py"
spec3 = importlib.util.spec_from_file_location("inline_formula_detector", inline_detector_path)

sys.modules['src.layer1_preprocessing.block_formula_detector'] = block_formula_detector

inline_formula_detector = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(inline_formula_detector)

InlineFormulaDetector = inline_formula_detector.InlineFormulaDetector

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("行内公式检测模块测试")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    # 1. 版面解析
    print("步骤1: 版面解析...")
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    # 2. 块级公式检测（可选，用于避免重复）
    print("步骤2: 检测块级公式（用于排除）...")
    block_detector = BlockFormulaDetector()
    block_formulas = block_detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(block_formulas)} 个块级公式\n")
    
    # 3. 行内公式检测
    print("步骤3: 检测行内公式...")
    inline_detector = InlineFormulaDetector()
    inline_formulas = inline_detector.detect_inline_formulas(pages, block_formulas)
    print(f"✓ 检测完成，发现 {len(inline_formulas)} 个行内公式\n")
    
    # 4. 显示结果
    print("=" * 70)
    print("检测结果（前20个）:")
    print("=" * 70)
    
    for i, f in enumerate(inline_formulas[:20], 1):
        print(f"\n行内公式 {i}:")
        print(f"  页码: {f.page_number}, 块: {f.block_index}, 行: {f.line_index}")
        print(f"  得分: {f.score:.3f}")
        print(f"  位置: bbox=({f.bbox[0]:.1f}, {f.bbox[1]:.1f}, {f.bbox[2]:.1f}, {f.bbox[3]:.1f})")
        print(f"  span索引: {f.span_indices}")
        print(f"  文本: {f.text!r}")
    
    if len(inline_formulas) > 20:
        print(f"\n... (还有 {len(inline_formulas) - 20} 个行内公式)")
    
    # 5. 统计
    print(f"\n{'=' * 70}")
    print("统计信息:")
    print("=" * 70)
    
    formulas_by_page = {}
    for f in inline_formulas:
        page_num = f.page_number
        formulas_by_page[page_num] = formulas_by_page.get(page_num, 0) + 1
    
    print(f"  总行内公式数: {len(inline_formulas)}")
    print(f"  包含行内公式的页数: {len(formulas_by_page)}")
    if pages:
        print(f"  平均每页行内公式数: {len(inline_formulas) / len(pages):.2f}")
    
    if formulas_by_page:
        print(f"\n  每页行内公式分布（前10页）:")
        for page_num in sorted(formulas_by_page.keys())[:10]:
            print(f"    Page {page_num}: {formulas_by_page[page_num]} 个")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



