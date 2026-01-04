#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行块级公式检测 - 调试版本（显示每个块的得分）
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
BlockFormulaConfig = block_formula_detector.BlockFormulaConfig

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("块级公式检测 - 调试模式")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    # 版面解析
    print("正在解析PDF...")
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    # 创建检测器（使用更宽松的配置）
    config = BlockFormulaConfig(
        min_block_score=0.3,  # 降低阈值
        min_line_score=0.4,
        weight_font=0.5,  # 增加字体权重（因为文本可能为空）
        weight_math_char_ratio=0.2,  # 降低文本特征权重
    )
    detector = BlockFormulaDetector(config=config)
    
    # 调试：显示前3页每个块的得分
    print("=" * 70)
    print("调试信息：前3页每个块的得分")
    print("=" * 70)
    
    for page in pages[:3]:
        print(f"\nPage {page.page_number}:")
        avg_line_gap = detector._estimate_average_line_gap(page)
        
        for block_idx, block in enumerate(page.blocks[:10]):  # 只显示前10个块
            score = detector._score_block_as_formula(block, page, avg_line_gap)
            
            # 获取特征
            block_text = detector._get_block_text(block)
            text_features = detector._extract_text_features(block_text)
            font_features = detector._extract_font_features(block)
            
            print(f"  Block {block_idx}: score={score:.3f}")
            print(f"    文本特征: math_char_ratio={text_features['math_char_ratio']:.3f}, "
                  f"has_math_keywords={text_features['has_math_keywords']}")
            print(f"    字体特征: math_font_score={font_features['math_font_score']:.3f}")
            print(f"    行数: {len(block.lines)}")
            
            if score >= config.min_block_score:
                print(f"    ✓ 检测为公式！")
    
    # 正式检测
    print(f"\n{'=' * 70}")
    print("正式检测结果:")
    print("=" * 70)
    
    formulas = detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(formulas)} 个块级公式\n")
    
    if formulas:
        print("检测结果（前10个）:")
        for i, f in enumerate(formulas[:10]):
            print(f"\n公式 {i+1}:")
            print(f"  页码: {f.page_number}, 块: {f.block_index}")
            print(f"  行索引: {f.line_indices}, 得分: {f.score:.3f}")
            print(f"  位置: bbox={f.bbox}")
    else:
        print("⚠️ 未检测到公式，可能原因：")
        print("  1. 阈值设置过高")
        print("  2. 文本内容为空，导致文本特征得分低")
        print("  3. 建议：更依赖字体特征进行检测")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()



