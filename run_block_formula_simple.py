#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行块级公式检测 - 最简单版本
直接导入模块文件，避免 __init__.py 的依赖问题
"""
import sys
from pathlib import Path

# 添加项目路径
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# 直接导入模块文件（通过修改导入路径）
import importlib.util

# 导入 formula_layout
formula_layout_path = ROOT / "src" / "layer1_preprocessing" / "formula_layout.py"
spec1 = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(formula_layout)

PDFLayoutExtractor = formula_layout.PDFLayoutExtractor
PageLayout = formula_layout.PageLayout
TextBlock = formula_layout.TextBlock
TextLine = formula_layout.TextLine
TextSpan = formula_layout.TextSpan

# 修改 block_formula_detector 的导入方式
# 先读取文件内容
block_detector_path = ROOT / "src" / "layer1_preprocessing" / "block_formula_detector.py"
with open(block_detector_path, 'r', encoding='utf-8') as f:
    detector_source = f.read()

# 创建模块命名空间，注入依赖
detector_globals = {
    '__name__': 'block_formula_detector',
    '__file__': str(block_detector_path),
    'PageLayout': PageLayout,
    'TextBlock': TextBlock,
    'TextLine': TextLine,
    'TextSpan': TextSpan,
}

# 添加其他需要的模块
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

# 修改源代码中的相对导入
detector_source_modified = detector_source.replace(
    'from .formula_layout import PageLayout, TextBlock, TextLine, TextSpan',
    '# 已通过命名空间注入'
)

# 执行修改后的代码
exec(detector_source_modified, detector_globals)

BlockFormulaDetector = detector_globals['BlockFormulaDetector']
BlockFormulaConfig = detector_globals['BlockFormulaConfig']

# 主程序
def main():
    pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"错误: PDF文件不存在: {pdf_path}")
        return False
    
    try:
        print("=" * 70)
        print("块级公式检测模块测试")
        print("=" * 70)
        print(f"\nPDF: {pdf_path.name}\n")
        
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
            print(f"  行数: {len(f.line_indices)}, 行索引: {f.line_indices}")
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
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



