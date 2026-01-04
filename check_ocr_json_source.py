#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查OCR JSON文件是否使用真实OCR生成
"""
import json
from pathlib import Path
import sys

json_path = r"E:\1study\3\sw\computer-task\data\output\2023CVPR-CoMFormer\formula_ocr\formula_ocr_results.json"

if len(sys.argv) > 1:
    json_path = sys.argv[1]

print("=" * 70)
print("检查OCR JSON文件来源")
print("=" * 70)
print(f"\nJSON文件: {json_path}\n")

if not Path(json_path).exists():
    print(f"❌ JSON文件不存在: {json_path}")
    sys.exit(1)

# 读取JSON
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

formulas = data.get('formulas', [])
if isinstance(data, list):
    formulas = data

print(f"总公式数: {len(formulas)}\n")

# 检查LaTeX内容
dummy_count = 0
real_latex_count = 0
empty_latex_count = 0

dummy_pattern = r"\\mathrm\{dummy\\_formula\}"
import re

for formula in formulas:
    latex = formula.get('latex', '')
    if not latex or not latex.strip():
        empty_latex_count += 1
    elif re.search(dummy_pattern, latex):
        dummy_count += 1
    else:
        real_latex_count += 1

print("=" * 70)
print("LaTeX内容分析")
print("=" * 70)
print(f"\n使用占位符（dummy）: {dummy_count} 个")
print(f"真实LaTeX: {real_latex_count} 个")
print(f"空LaTeX: {empty_latex_count} 个")

if dummy_count > 0 and real_latex_count == 0:
    print(f"\n⚠️ 当前JSON使用的是占位OCR（DummyFormulaOCR）")
    print(f"   需要运行真实OCR重新生成JSON")
    print(f"\n   运行命令:")
    print(f"   python run_formula_ocr_real.py")
elif real_latex_count > 0:
    print(f"\n✓ 当前JSON使用的是真实OCR（pix2tex）")
    print(f"   对齐代码会使用真实的LaTeX")
else:
    print(f"\n⚠️ 无法确定OCR来源，建议重新运行OCR")

# 显示示例
print(f"\n{'=' * 70}")
print("LaTeX示例（前5个）")
print("=" * 70)

shown = 0
for formula in formulas:
    if shown >= 5:
        break
    
    latex = formula.get('latex', '')
    if latex:
        is_dummy = bool(re.search(dummy_pattern, latex))
        print(f"\n公式 {formula.get('formula_id', 'N/A')}:")
        print(f"  LaTeX: {latex[:80]!r}...")
        print(f"  类型: {'占位符' if is_dummy else '真实LaTeX'}")
        shown += 1

print(f"\n{'=' * 70}\n")



