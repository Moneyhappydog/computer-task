#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试块级公式检测模块 - 独立版本（绕过 __init__.py）
"""
import sys
import importlib.util
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent

# 直接导入 formula_layout 模块文件
formula_layout_path = project_root / "src" / "layer1_preprocessing" / "formula_layout.py"
spec1 = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(formula_layout)
PDFLayoutExtractor = formula_layout.PDFLayoutExtractor

# 直接导入 block_formula_detector 模块文件
block_detector_path = project_root / "src" / "layer1_preprocessing" / "block_formula_detector.py"
spec2 = importlib.util.spec_from_file_location("block_formula_detector", block_detector_path)

# 需要在导入 block_formula_detector 之前设置 formula_layout 模块
sys.modules['src'] = type(sys)('src')
sys.modules['src.layer1_preprocessing'] = type(sys)('layer1_preprocessing')
sys.modules['src.layer1_preprocessing.formula_layout'] = formula_layout

block_formula_detector = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(block_formula_detector)

BlockFormulaDetector = block_formula_detector.BlockFormulaDetector
BlockFormulaConfig = block_formula_detector.BlockFormulaConfig

def main():
    """测试块级公式检测"""
    pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"错误: PDF文件不存在: {pdf_path}")
        return False
    
    try:
        print("=" * 70)
        print("测试块级公式检测模块")
        print("=" * 70)
        print(f"\nPDF: {pdf_path.name}\n")
        
        # 1. 版面解析
        print("步骤1: 版面解析...")
        layout_extractor = PDFLayoutExtractor(str(pdf_path))
        pages = layout_extractor.parse()
        print(f"✓ 解析完成，共 {len(pages)} 页\n")
        
        # 2. 公式检测（使用默认配置）
        print("步骤2: 检测块级公式（默认配置）...")
        detector = BlockFormulaDetector()
        formulas = detector.detect_block_formulas(pages)
        print(f"✓ 检测完成，发现 {len(formulas)} 个块级公式\n")
        
        # 3. 显示前10个结果
        print("=" * 70)
        print("检测结果（前10个）:")
        print("=" * 70)
        
        for i, formula in enumerate(formulas[:10]):
            print(f"\n公式 {i+1}:")
            print(f"  页码: {formula.page_number}")
            print(f"  块索引: {formula.block_index}")
            print(f"  行数: {len(formula.line_indices)} 行 (行索引: {formula.line_indices})")
            print(f"  得分: {formula.score:.3f}")
            print(f"  位置: x={formula.bbox[0]:.1f}, y={formula.bbox[1]:.1f}, "
                  f"宽={formula.bbox[2]-formula.bbox[0]:.1f}, 高={formula.bbox[3]-formula.bbox[1]:.1f}")
            text_preview = formula.text[:80] if formula.text else "[无文本]"
            print(f"  文本预览: {text_preview!r}")
        
        if len(formulas) > 10:
            print(f"\n... (还有 {len(formulas) - 10} 个公式)")
        
        # 4. 统计信息
        print(f"\n{'=' * 70}")
        print("统计信息:")
        print("=" * 70)
        
        formulas_by_page = {}
        for formula in formulas:
            page_num = formula.page_number
            formulas_by_page[page_num] = formulas_by_page.get(page_num, 0) + 1
        
        print(f"  总公式数: {len(formulas)}")
        print(f"  包含公式的页数: {len(formulas_by_page)}")
        if pages:
            print(f"  平均每页公式数: {len(formulas) / len(pages):.2f}")
        
        if formulas_by_page:
            print(f"\n  每页公式分布:")
            for page_num in sorted(formulas_by_page.keys()):
                count = formulas_by_page[page_num]
                print(f"    Page {page_num}: {count} 个公式")
        
        # 5. 测试自定义配置
        print(f"\n{'=' * 70}")
        print("测试自定义配置（更严格的阈值）:")
        print("=" * 70)
        
        strict_config = BlockFormulaConfig(
            min_block_score=0.7,  # 更高的阈值
            min_line_score=0.8,
            min_math_char_ratio=0.2
        )
        strict_detector = BlockFormulaDetector(config=strict_config)
        strict_formulas = strict_detector.detect_block_formulas(pages)
        print(f"严格模式检测到: {len(strict_formulas)} 个公式")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



