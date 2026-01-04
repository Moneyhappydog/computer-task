#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化行内公式检测结果
生成报告和JSON文件
"""
import sys
import importlib.util
from pathlib import Path
import json
from datetime import datetime

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

pdf_path = Path(pdf_path)
pdf_name = pdf_path.stem

print("=" * 70)
print("行内公式检测结果可视化")
print("=" * 70)
print(f"\nPDF: {pdf_path.name}\n")

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
    
    # 3. 行内公式检测
    print("步骤3: 检测行内公式...")
    inline_detector = InlineFormulaDetector()
    inline_formulas = inline_detector.detect_inline_formulas(pages, block_formulas)
    print(f"✓ 检测完成，发现 {len(inline_formulas)} 个行内公式\n")
    
    # 4. 创建输出目录
    output_dir = Path("data/output") / pdf_name / "inline_formulas"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. 生成详细报告
    report_file = output_dir / f"inline_formulas_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("行内公式检测详细报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"PDF文件: {pdf_path}\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"总行内公式数: {len(inline_formulas)}\n")
        f.write(f"总页数: {len(pages)}\n")
        f.write(f"块级公式数: {len(block_formulas)}\n\n")
        
        if inline_formulas:
            f.write("=" * 70 + "\n")
            f.write("检测到的行内公式列表\n")
            f.write("=" * 70 + "\n\n")
            
            for i, formula in enumerate(inline_formulas, 1):
                f.write(f"行内公式 {i}:\n")
                f.write(f"  页码: {formula.page_number}\n")
                f.write(f"  块索引: {formula.block_index}\n")
                f.write(f"  行索引: {formula.line_index}\n")
                f.write(f"  span索引: {formula.span_indices}\n")
                f.write(f"  得分: {formula.score:.3f}\n")
                f.write(f"  边界框: x={formula.bbox[0]:.1f}, y={formula.bbox[1]:.1f}, "
                        f"宽={formula.bbox[2]-formula.bbox[0]:.1f}, 高={formula.bbox[3]-formula.bbox[1]:.1f}\n")
                f.write(f"  文本内容: {formula.text!r}\n")
                f.write("\n")
        else:
            f.write("未检测到任何行内公式。\n")
    
    print(f"✓ 详细报告已保存: {report_file}\n")
    
    # 6. 生成JSON文件
    json_file = output_dir / f"inline_formulas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    formulas_data = []
    for formula in inline_formulas:
        formulas_data.append({
            'page_number': formula.page_number,
            'block_index': formula.block_index,
            'line_index': formula.line_index,
            'span_indices': formula.span_indices,
            'bbox': list(formula.bbox),
            'text': formula.text,
            'score': formula.score
        })
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pdf_path': str(pdf_path),
            'total_inline_formulas': len(inline_formulas),
            'total_pages': len(pages),
            'total_block_formulas': len(block_formulas),
            'formulas': formulas_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JSON数据已保存: {json_file}\n")
    
    # 7. 生成按页面分组的摘要
    summary_file = output_dir / f"inline_formulas_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("行内公式检测摘要（按页面分组）\n")
        f.write("=" * 70 + "\n\n")
        
        formulas_by_page = {}
        for formula in inline_formulas:
            page_num = formula.page_number
            if page_num not in formulas_by_page:
                formulas_by_page[page_num] = []
            formulas_by_page[page_num].append(formula)
        
        for page_num in sorted(formulas_by_page.keys()):
            page_formulas = formulas_by_page[page_num]
            f.write(f"Page {page_num}: {len(page_formulas)} 个行内公式\n")
            f.write("-" * 70 + "\n")
            
            for i, formula in enumerate(page_formulas, 1):
                f.write(f"  公式 {i}:\n")
                f.write(f"    块索引: {formula.block_index}, 行索引: {formula.line_index}\n")
                f.write(f"    得分: {formula.score:.3f}\n")
                f.write(f"    位置: ({formula.bbox[0]:.1f}, {formula.bbox[1]:.1f}) "
                        f"宽={formula.bbox[2]-formula.bbox[0]:.1f}, 高={formula.bbox[3]-formula.bbox[1]:.1f}\n")
                f.write(f"    文本: {formula.text!r}\n")
                f.write("\n")
    
    print(f"✓ 摘要报告已保存: {summary_file}\n")
    
    # 8. 控制台输出
    print("=" * 70)
    print("检测结果摘要")
    print("=" * 70)
    
    if inline_formulas:
        formulas_by_page = {}
        for formula in inline_formulas:
            page_num = formula.page_number
            formulas_by_page[page_num] = formulas_by_page.get(page_num, 0) + 1
        
        print(f"\n总行内公式数: {len(inline_formulas)}")
        print(f"包含行内公式的页数: {len(formulas_by_page)}")
        print(f"\n每页行内公式分布（前10页）:")
        for page_num in sorted(formulas_by_page.keys())[:10]:
            print(f"  Page {page_num}: {formulas_by_page[page_num]} 个")
        
        print(f"\n前5个行内公式示例:")
        for i, formula in enumerate(inline_formulas[:5], 1):
            print(f"\n公式 {i}:")
            print(f"  页码: {formula.page_number}, 块: {formula.block_index}, 行: {formula.line_index}")
            print(f"  得分: {formula.score:.3f}")
            print(f"  文本: {formula.text!r}")
    else:
        print("\n⚠️ 未检测到任何行内公式")
    
    print(f"\n{'=' * 70}")
    print(f"所有报告文件已保存到: {output_dir}")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



