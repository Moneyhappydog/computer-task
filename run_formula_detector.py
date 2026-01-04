#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行块级公式检测 - 简化版本
"""
import sys
import importlib.util
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent

# 直接加载 formula_layout.py
formula_layout_file = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec_layout = importlib.util.spec_from_file_location("formula_layout_mod", formula_layout_file)
layout_mod = importlib.util.module_from_spec(spec_layout)
spec_layout.loader.exec_module(layout_mod)

PDFLayoutExtractor = layout_mod.PDFLayoutExtractor
PageLayout = layout_mod.PageLayout
TextBlock = layout_mod.TextBlock
TextLine = layout_mod.TextLine
TextSpan = layout_mod.TextSpan

# 直接加载 block_formula_detector.py，但需要修改导入
block_detector_file = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"

# 读取文件内容
with open(block_detector_file, 'r', encoding='utf-8') as f:
    detector_code = f.read()

# 替换相对导入为直接导入
detector_code = detector_code.replace(
    'from .formula_layout import PageLayout, TextBlock, TextLine, TextSpan',
    '''# 直接使用已加载的模块
PageLayout = PageLayout
TextBlock = TextBlock
TextLine = TextLine
TextSpan = TextSpan'''
)

# 创建模块命名空间
detector_namespace = {
    'PageLayout': PageLayout,
    'TextBlock': TextBlock,
    'TextLine': TextLine,
    'TextSpan': TextSpan,
    '__name__': 'block_formula_detector',
    '__file__': str(block_detector_file),
    'Path': Path,
    'dataclasses': __import__('dataclasses'),
    'typing': __import__('typing'),
    're': __import__('re'),
    'field': __import__('dataclasses').field,
}

# 执行代码
exec(detector_code, detector_namespace)

BlockFormulaDetector = detector_namespace['BlockFormulaDetector']
BlockFormulaConfig = detector_namespace['BlockFormulaConfig']
BlockFormula = detector_namespace['BlockFormula']

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
        print("正在解析PDF版面...")
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
        print(f"检测结果（前10个）:")
        print("=" * 70)
        
        for i, f in enumerate(formulas[:10]):
            print(f"\n公式 {i+1}:")
            print(f"  页码: {f.page_number}, 块索引: {f.block_index}")
            print(f"  行数: {len(f.line_indices)}, 得分: {f.score:.3f}")
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
        sys.exit(1)



