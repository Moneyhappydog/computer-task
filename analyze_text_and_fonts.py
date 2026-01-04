#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析文本内容和字体信息
"""
import sys
import importlib.util
from pathlib import Path
from collections import Counter

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

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("文本内容和字体信息详细分析")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    # 1. 版面解析
    print("步骤1: 版面解析...")
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    # 2. 块级公式检测
    print("步骤2: 检测块级公式...")
    block_detector = BlockFormulaDetector()
    block_formulas = block_detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(block_formulas)} 个块级公式\n")
    
    # 构建块级公式覆盖的行集合
    block_formula_lines = set()
    for bf in block_formulas:
        for line_idx in bf.line_indices:
            block_formula_lines.add((bf.page_number, bf.block_index, line_idx))
    
    # 3. 详细分析前3页的文本和字体
    print("=" * 70)
    print("详细分析：前3页的文本内容和字体信息")
    print("=" * 70)
    
    total_spans = 0
    spans_with_text = 0
    spans_with_empty_text = 0
    spans_with_math_font = 0
    font_counter = Counter()
    size_counter = Counter()
    
    sample_spans = []
    
    for page in pages[:3]:
        print(f"\nPage {page.page_number}:")
        
        for block_idx, block in enumerate(page.blocks):
            for line_idx, line in enumerate(block.lines):
                # 跳过块级公式行
                line_key = (page.page_number, block_idx, line_idx)
                if line_key in block_formula_lines:
                    continue
                
                if not line.spans:
                    continue
                
                for span_idx, span in enumerate(line.spans):
                    total_spans += 1
                    
                    # 检查文本
                    has_text = span.text and len(span.text.strip()) > 0
                    if has_text:
                        spans_with_text += 1
                    else:
                        spans_with_empty_text += 1
                    
                    # 检查字体
                    font = span.font or "None"
                    font_counter[font] += 1
                    
                    # 检查是否是数学字体
                    font_lower = font.lower()
                    is_math_font = any(kw in font_lower for kw in ['math', 'cmr', 'cmsy', 'cmmi', 'cmex', 'symbol', 'cambriamath'])
                    if is_math_font:
                        spans_with_math_font += 1
                    
                    # 记录字号
                    if span.size > 0:
                        size_counter[round(span.size, 1)] += 1
                    
                    # 保存前20个有文本的span作为样本
                    if has_text and len(sample_spans) < 20:
                        sample_spans.append({
                            'page': page.page_number,
                            'block': block_idx,
                            'line': line_idx,
                            'span': span_idx,
                            'text': span.text,
                            'font': font,
                            'size': span.size,
                            'is_math_font': is_math_font
                        })
    
    # 4. 输出统计信息
    print(f"\n{'=' * 70}")
    print("统计信息")
    print("=" * 70)
    
    print(f"\n总span数: {total_spans}")
    print(f"有文本的span数: {spans_with_text} ({spans_with_text/total_spans*100:.1f}%)")
    print(f"文本为空的span数: {spans_with_empty_text} ({spans_with_empty_text/total_spans*100:.1f}%)")
    print(f"数学字体的span数: {spans_with_math_font} ({spans_with_math_font/total_spans*100:.1f}%)")
    
    # 5. 字体分布
    print(f"\n{'=' * 70}")
    print("字体分布（前10个）")
    print("=" * 70)
    
    for font, count in font_counter.most_common(10):
        is_math = any(kw in font.lower() for kw in ['math', 'cmr', 'cmsy', 'cmmi', 'cmex', 'symbol', 'cambriamath'])
        print(f"  {font}: {count} 次 {'[数学字体]' if is_math else ''}")
    
    # 6. 字号分布
    print(f"\n{'=' * 70}")
    print("字号分布（前10个）")
    print("=" * 70)
    
    for size, count in size_counter.most_common(10):
        print(f"  {size}: {count} 次")
    
    # 7. 显示样本span
    print(f"\n{'=' * 70}")
    print("样本span（前20个有文本的span）")
    print("=" * 70)
    
    for i, sample in enumerate(sample_spans, 1):
        print(f"\n样本 {i}:")
        print(f"  Page {sample['page']}, Block {sample['block']}, Line {sample['line']}, Span {sample['span']}")
        print(f"  文本: {sample['text']!r}")
        print(f"  字体: {sample['font']}")
        print(f"  字号: {sample['size']}")
        print(f"  是否数学字体: {sample['is_math_font']}")
        
        # 检查是否包含数学符号
        if sample['text']:
            math_chars = [c for c in sample['text'] if c in 'αβγδεζηθικλμνξοπρστυφχψω∈∉⊂⊃∪∩∅∀∃≤≥≠≈±×÷∞√∑∏∫^_²³']
            if math_chars:
                print(f"  数学符号: {math_chars}")
    
    # 8. 分析结论
    print(f"\n{'=' * 70}")
    print("分析结论")
    print("=" * 70)
    
    print(f"\n1. 文本内容情况:")
    if spans_with_text / total_spans < 0.1:
        print(f"   ⚠️ 只有 {spans_with_text/total_spans*100:.1f}% 的span有文本内容")
        print(f"   这是主要问题！文本内容为空导致无法通过文本特征检测行内公式")
    else:
        print(f"   ✓ {spans_with_text/total_spans*100:.1f}% 的span有文本内容")
    
    print(f"\n2. 字体特征情况:")
    if spans_with_math_font / total_spans > 0.1:
        print(f"   ✓ {spans_with_math_font/total_spans*100:.1f}% 的span使用数学字体")
        print(f"   可以基于字体特征来检测行内公式")
    else:
        print(f"   ⚠️ 只有 {spans_with_math_font/total_spans*100:.1f}% 的span使用数学字体")
        print(f"   字体特征可能不够明显")
    
    print(f"\n3. 建议:")
    if spans_with_text / total_spans < 0.1:
        print(f"   - 主要依赖字体特征来检测行内公式")
        print(f"   - 提高字体特征的权重")
        print(f"   - 降低阈值，因为文本特征得分会很低")
    else:
        print(f"   - 可以同时使用文本特征和字体特征")
        print(f"   - 检查数学符号集合是否完整")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



