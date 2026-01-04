#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行块级公式检测 - 最终版本
直接导入模块，使用之前已验证的方式
"""
import sys
import importlib.util
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent

# 直接加载 formula_layout.py 文件
formula_layout_path = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec1 = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(formula_layout)

# 获取类
PDFLayoutExtractor = formula_layout.PDFLayoutExtractor
PageLayout = formula_layout.PageLayout
TextBlock = formula_layout.TextBlock
TextLine = formula_layout.TextLine
TextSpan = formula_layout.TextSpan

# 加载 block_formula_detector，但需要修复相对导入
block_detector_path = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"

# 读取源代码
with open(block_detector_path, 'r', encoding='utf-8') as f:
    detector_source = f.read()

# 替换相对导入
detector_source = detector_source.replace(
    'from .formula_layout import PageLayout, TextBlock, TextLine, TextSpan',
    f'''# 使用已加载的模块
PageLayout = {PageLayout.__module__}.PageLayout if hasattr({PageLayout.__module__}, 'PageLayout') else PageLayout
TextBlock = TextBlock
TextLine = TextLine
TextSpan = TextSpan'''
)

# 更简单的方式：直接注入到命名空间
detector_globals = {
    '__name__': 'block_formula_detector',
    '__file__': str(block_detector_path),
    'PageLayout': PageLayout,
    'TextBlock': TextBlock,
    'TextLine': TextLine,
    'TextSpan': TextSpan,
}

# 添加标准库
import dataclasses
import typing
import re
detector_globals.update({
    'dataclasses': dataclasses,
    'typing': typing,
    're': re,
    'List': typing.List,
    'Tuple': typing.Tuple,
    'Optional': typing.Optional,
    'field': dataclasses.field,
    'Path': Path,
})

# 移除相对导入行后再执行
lines = detector_source.split('\n')
filtered_lines = [line for line in lines if not line.strip().startswith('from .formula_layout')]
detector_source_fixed = '\n'.join(filtered_lines)

# 执行
exec(detector_source_fixed, detector_globals)

BlockFormulaDetector = detector_globals['BlockFormulaDetector']
BlockFormulaConfig = detector_globals.get('BlockFormulaConfig', None)

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("块级公式检测模块测试")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    # 1. 版面解析
    print("步骤1: 版面解析...")
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    # 2. 公式检测
    print("步骤2: 检测块级公式...")
    detector = BlockFormulaDetector()
    formulas = detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(formulas)} 个块级公式\n")
    
    # 3. 显示结果
    print("=" * 70)
    print("检测结果（前10个）:")
    print("=" * 70)
    
    for i, f in enumerate(formulas[:10]):
        print(f"\n公式 {i+1}:")
        print(f"  页码: {f.page_number}, 块索引: {f.block_index}")
        print(f"  行数: {len(f.line_indices)} 行, 行索引: {f.line_indices}")
        print(f"  得分: {f.score:.3f}")
        print(f"  位置: x={f.bbox[0]:.1f}, y={f.bbox[1]:.1f}, "
              f"宽={f.bbox[2]-f.bbox[0]:.1f}, 高={f.bbox[3]-f.bbox[1]:.1f}")
        text_preview = f.text[:80] if f.text else "[无文本]"
        print(f"  文本预览: {text_preview!r}")
    
    if len(formulas) > 10:
        print(f"\n... (还有 {len(formulas) - 10} 个公式)")
    
    # 4. 统计
    print(f"\n{'=' * 70}")
    print("统计信息:")
    print("=" * 70)
    
    formulas_by_page = {}
    for f in formulas:
        page_num = f.page_number
        formulas_by_page[page_num] = formulas_by_page.get(page_num, 0) + 1
    
    print(f"  总公式数: {len(formulas)}")
    print(f"  包含公式的页数: {len(formulas_by_page)}")
    if pages:
        print(f"  平均每页公式数: {len(formulas) / len(pages):.2f}")
    
    if formulas_by_page:
        print(f"\n  每页公式分布:")
        for page_num in sorted(formulas_by_page.keys()):
            print(f"    Page {page_num}: {formulas_by_page[page_num]} 个")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



