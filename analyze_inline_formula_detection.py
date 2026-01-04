#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析行内公式检测失败的原因
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
print("行内公式检测失败原因分析")
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
    
    # 3. 分析块级公式覆盖的行
    print("=" * 70)
    print("分析1: 块级公式覆盖情况")
    print("=" * 70)
    
    block_formula_lines = set()
    for bf in block_formulas:
        for line_idx in bf.line_indices:
            block_formula_lines.add((bf.page_number, bf.block_index, line_idx))
    
    print(f"块级公式覆盖的总行数: {len(block_formula_lines)}")
    
    # 统计每页被覆盖的行数
    lines_by_page = {}
    for page_num, block_idx, line_idx in block_formula_lines:
        if page_num not in lines_by_page:
            lines_by_page[page_num] = 0
        lines_by_page[page_num] += 1
    
    print(f"\n每页被块级公式覆盖的行数:")
    for page_num in sorted(lines_by_page.keys()):
        print(f"  Page {page_num}: {lines_by_page[page_num]} 行")
    
    # 统计总行数
    total_lines = 0
    for page in pages:
        for block in page.blocks:
            total_lines += len(block.lines)
    
    print(f"\n总行数: {total_lines}")
    print(f"被块级公式覆盖的行数: {len(block_formula_lines)}")
    print(f"可用于行内公式检测的行数: {total_lines - len(block_formula_lines)}")
    print(f"覆盖率: {len(block_formula_lines) / total_lines * 100:.1f}%")
    
    # 4. 分析前3页的文本行，看看是否有行内公式特征
    print(f"\n{'=' * 70}")
    print("分析2: 检查前3页的文本行（排除块级公式行）")
    print("=" * 70)
    
    inline_detector = InlineFormulaDetector()
    
    sample_lines_checked = 0
    sample_lines_with_math = 0
    sample_spans_checked = 0
    sample_spans_with_math = 0
    
    for page in pages[:3]:
        print(f"\nPage {page.page_number}:")
        
        for block_idx, block in enumerate(page.blocks):
            for line_idx, line in enumerate(block.lines):
                # 检查是否被块级公式覆盖
                line_key = (page.page_number, block_idx, line_idx)
                if line_key in block_formula_lines:
                    continue  # 跳过块级公式行
                
                sample_lines_checked += 1
                
                if not line.spans:
                    continue
                
                # 计算行统计信息
                line_stats = inline_detector._compute_line_stats(line)
                
                # 检查每个span
                has_math_in_line = False
                for span_idx, span in enumerate(line.spans):
                    sample_spans_checked += 1
                    
                    if not span.text:
                        continue
                    
                    # 检查是否包含数学符号
                    math_chars = [c for c in span.text if c in inline_detector.config.math_symbols]
                    if math_chars:
                        sample_spans_with_math += 1
                        has_math_in_line = True
                    
                    # 计算得分
                    score = inline_detector._score_span_as_formula(span, line, line_stats)
                    
                    # 显示前几个有数学符号的span
                    if math_chars and sample_spans_with_math <= 10:
                        print(f"  Block {block_idx}, Line {line_idx}, Span {span_idx}:")
                        print(f"    文本: {span.text!r}")
                        print(f"    数学符号: {math_chars}")
                        print(f"    字体: {span.font}")
                        print(f"    字号: {span.size}")
                        print(f"    得分: {score:.3f}")
                        print(f"    阈值: {inline_detector.config.min_span_score}")
                        print(f"    是否通过: {'✓' if score >= inline_detector.config.min_span_score else '✗'}")
                        print()
                
                if has_math_in_line:
                    sample_lines_with_math += 1
    
    print(f"\n统计:")
    print(f"  检查的行数: {sample_lines_checked}")
    print(f"  包含数学符号的行数: {sample_lines_with_math}")
    print(f"  检查的span数: {sample_spans_checked}")
    print(f"  包含数学符号的span数: {sample_spans_with_math}")
    
    # 5. 分析配置参数
    print(f"\n{'=' * 70}")
    print("分析3: 配置参数检查")
    print("=" * 70)
    
    config = inline_detector.config
    print(f"min_span_score: {config.min_span_score}")
    print(f"min_group_score: {config.min_group_score}")
    print(f"max_horizontal_gap_factor: {config.max_horizontal_gap_factor}")
    print(f"\n数学符号数量: {len(config.math_symbols)}")
    print(f"数学字体关键词: {config.math_font_keywords}")
    print(f"正则模式数量: {len(config.inline_regex_patterns)}")
    
    # 6. 检查一些具体的文本行
    print(f"\n{'=' * 70}")
    print("分析4: 检查一些具体的文本行内容")
    print("=" * 70)
    
    checked_count = 0
    for page in pages[:3]:
        for block_idx, block in enumerate(page.blocks):
            for line_idx, line in enumerate(block.lines):
                line_key = (page.page_number, block_idx, line_idx)
                if line_key in block_formula_lines:
                    continue
                
                if not line.text or len(line.text.strip()) < 5:
                    continue
                
                checked_count += 1
                if checked_count <= 5:
                    print(f"\nPage {page.page_number}, Block {block_idx}, Line {line_idx}:")
                    print(f"  文本: {line.text[:100]!r}")
                    print(f"  spans数: {len(line.spans)}")
                    
                    # 检查字体
                    fonts = {}
                    for span in line.spans:
                        if span.font:
                            fonts[span.font] = fonts.get(span.font, 0) + 1
                    if fonts:
                        print(f"  字体分布: {dict(list(fonts.items())[:3])}")
                    
                    # 检查是否有数学符号
                    math_count = sum(1 for c in line.text if c in config.math_symbols)
                    print(f"  数学符号数: {math_count}")
    
    # 7. 总结可能的原因
    print(f"\n{'=' * 70}")
    print("可能的原因分析")
    print("=" * 70)
    
    print("\n1. 块级公式覆盖情况:")
    if len(block_formula_lines) / total_lines > 0.5:
        print(f"   ⚠️ 块级公式覆盖了 {len(block_formula_lines) / total_lines * 100:.1f}% 的行")
        print(f"   这可能导致很多包含行内公式的行被跳过")
    else:
        print(f"   ✓ 块级公式覆盖了 {len(block_formula_lines) / total_lines * 100:.1f}% 的行，覆盖率正常")
    
    print("\n2. 文本内容检查:")
    if sample_spans_with_math == 0:
        print(f"   ⚠️ 在前3页的 {sample_spans_checked} 个span中，没有发现包含数学符号的span")
        print(f"   可能原因：文本内容为空，或者数学符号不在定义的集合中")
    else:
        print(f"   ✓ 发现了 {sample_spans_with_math} 个包含数学符号的span")
        print(f"   但可能得分不够高，未达到阈值 {config.min_span_score}")
    
    print("\n3. 阈值设置:")
    print(f"   min_span_score = {config.min_span_score}")
    print(f"   min_group_score = {config.min_group_score}")
    print(f"   如果得分普遍较低，可能需要降低阈值")
    
    print("\n4. 建议:")
    print(f"   - 检查块级公式是否过于宽松，把行内公式也包含了")
    print(f"   - 检查文本内容是否为空（可能导致文本特征得分低）")
    print(f"   - 检查字体特征是否被正确识别")
    print(f"   - 考虑降低阈值或调整权重")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



