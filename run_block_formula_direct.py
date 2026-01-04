#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接运行块级公式检测 - 最简单方式
"""
import sys
import importlib.util
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent

# 加载 formula_layout 模块（之前验证过可以工作）
formula_layout_path = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)

PDFLayoutExtractor = formula_layout.PDFLayoutExtractor
PageLayout = formula_layout.PageLayout
TextBlock = formula_layout.TextBlock
TextLine = formula_layout.TextLine
TextSpan = formula_layout.TextSpan

# 加载 block_formula_detector 并修复导入
block_detector_path = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"

# 读取并修改源代码
with open(block_detector_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 创建命名空间
namespace = {
    'PageLayout': PageLayout,
    'TextBlock': TextBlock,
    'TextLine': TextLine,
    'TextSpan': TextSpan,
    '__name__': '__main__',
    '__file__': str(block_detector_path),
}

# 添加需要的标准库
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
lines = code.split('\n')
code_lines = []
skip_next = False
for line in lines:
    if 'from .formula_layout import' in line:
        # 跳过这一行，但添加注释
        code_lines.append('# 已通过命名空间注入依赖')
        continue
    code_lines.append(line)

code_fixed = '\n'.join(code_lines)

# 执行代码
exec(code_fixed, namespace)

# 获取类
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
        if f.text:
            print(f"  文本: {f.text[:60]!r}...")
    
    if len(formulas) > 10:
        print(f"\n... (还有 {len(formulas) - 10} 个公式)")
    
    print(f"\n{'=' * 70}")
    print(f"统计: 总公式数={len(formulas)}, 平均每页={len(formulas)/len(pages):.2f}")
    print("=" * 70)
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()



