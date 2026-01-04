#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化块级公式检测结果
生成报告和可视化图片
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
BlockFormulaConfig = block_formula_detector.BlockFormulaConfig

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

pdf_path = Path(pdf_path)
pdf_name = pdf_path.stem

print("=" * 70)
print("块级公式检测结果可视化")
print("=" * 70)
print(f"\nPDF: {pdf_path.name}\n")

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
    
    # 3. 创建输出目录
    output_dir = Path("data/output") / pdf_name / "block_formulas"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. 生成详细报告
    report_file = output_dir / f"block_formulas_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("块级公式检测详细报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"PDF文件: {pdf_path}\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"总公式数: {len(formulas)}\n")
        f.write(f"总页数: {len(pages)}\n\n")
        
        if formulas:
            f.write("=" * 70 + "\n")
            f.write("检测到的块级公式列表\n")
            f.write("=" * 70 + "\n\n")
            
            for i, formula in enumerate(formulas, 1):
                f.write(f"公式 {i}:\n")
                f.write(f"  页码: {formula.page_number}\n")
                f.write(f"  块索引: {formula.block_index}\n")
                f.write(f"  行索引: {formula.line_indices} (共 {len(formula.line_indices)} 行)\n")
                f.write(f"  得分: {formula.score:.3f}\n")
                f.write(f"  边界框: x={formula.bbox[0]:.1f}, y={formula.bbox[1]:.1f}, "
                        f"宽={formula.bbox[2]-formula.bbox[0]:.1f}, 高={formula.bbox[3]-formula.bbox[1]:.1f}\n")
                
                # 获取对应的块和行信息
                page = pages[formula.page_number - 1]
                if formula.block_index < len(page.blocks):
                    block = page.blocks[formula.block_index]
                    f.write(f"  块信息: {len(block.lines)} 行\n")
                    
                    # 显示涉及的行的信息
                    f.write(f"  涉及的文本行:\n")
                    for line_idx in formula.line_indices:
                        if line_idx < len(block.lines):
                            line = block.lines[line_idx]
                            f.write(f"    行 {line_idx}: bbox={line.bbox}, spans={len(line.spans)}\n")
                            
                            # 显示字体信息
                            if line.spans:
                                fonts = {}
                                for span in line.spans:
                                    fonts[span.font] = fonts.get(span.font, 0) + 1
                                font_str = ", ".join([f"{k}({v})" for k, v in sorted(fonts.items(), key=lambda x: x[1], reverse=True)[:3]])
                                f.write(f"      字体: {font_str}\n")
                
                f.write(f"  文本内容: {formula.text[:200] if formula.text else '[无文本]'}\n")
                f.write("\n")
        else:
            f.write("未检测到任何块级公式。\n")
            f.write("\n可能原因：\n")
            f.write("  1. 阈值设置过高\n")
            f.write("  2. 文本内容为空，导致文本特征得分低\n")
            f.write("  3. 字体特征不够明显\n")
    
    print(f"✓ 详细报告已保存: {report_file}\n")
    
    # 5. 生成JSON文件（便于程序处理）
    json_file = output_dir / f"block_formulas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    formulas_data = []
    for formula in formulas:
        formulas_data.append({
            'page_number': formula.page_number,
            'block_index': formula.block_index,
            'line_indices': formula.line_indices,
            'bbox': list(formula.bbox),
            'text': formula.text,
            'score': formula.score
        })
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pdf_path': str(pdf_path),
            'total_formulas': len(formulas),
            'total_pages': len(pages),
            'formulas': formulas_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JSON数据已保存: {json_file}\n")
    
    # 6. 生成按页面分组的摘要
    summary_file = output_dir / f"block_formulas_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("块级公式检测摘要（按页面分组）\n")
        f.write("=" * 70 + "\n\n")
        
        formulas_by_page = {}
        for formula in formulas:
            page_num = formula.page_number
            if page_num not in formulas_by_page:
                formulas_by_page[page_num] = []
            formulas_by_page[page_num].append(formula)
        
        for page_num in sorted(formulas_by_page.keys()):
            page_formulas = formulas_by_page[page_num]
            f.write(f"Page {page_num}: {len(page_formulas)} 个公式\n")
            f.write("-" * 70 + "\n")
            
            for i, formula in enumerate(page_formulas, 1):
                f.write(f"  公式 {i}:\n")
                f.write(f"    块索引: {formula.block_index}, 行索引: {formula.line_indices}\n")
                f.write(f"    得分: {formula.score:.3f}\n")
                f.write(f"    位置: ({formula.bbox[0]:.1f}, {formula.bbox[1]:.1f}) "
                        f"宽={formula.bbox[2]-formula.bbox[0]:.1f}, 高={formula.bbox[3]-formula.bbox[1]:.1f}\n")
                f.write("\n")
    
    print(f"✓ 摘要报告已保存: {summary_file}\n")
    
    # 7. 控制台输出
    print("=" * 70)
    print("检测结果摘要")
    print("=" * 70)
    
    if formulas:
        formulas_by_page = {}
        for formula in formulas:
            page_num = formula.page_number
            formulas_by_page[page_num] = formulas_by_page.get(page_num, 0) + 1
        
        print(f"\n总公式数: {len(formulas)}")
        print(f"包含公式的页数: {len(formulas_by_page)}")
        print(f"\n每页公式分布:")
        for page_num in sorted(formulas_by_page.keys()):
            print(f"  Page {page_num}: {formulas_by_page[page_num]} 个公式")
        
        print(f"\n前5个公式详情:")
        for i, formula in enumerate(formulas[:5], 1):
            print(f"\n公式 {i}:")
            print(f"  页码: {formula.page_number}, 块索引: {formula.block_index}")
            print(f"  行索引: {formula.line_indices}, 得分: {formula.score:.3f}")
            print(f"  位置: bbox=({formula.bbox[0]:.1f}, {formula.bbox[1]:.1f}, "
                  f"{formula.bbox[2]:.1f}, {formula.bbox[3]:.1f})")
    else:
        print("\n⚠️ 未检测到任何块级公式")
        print("\n建议:")
        print("  1. 运行调试版本查看每个块的得分: python run_block_formula_debug.py")
        print("  2. 调整配置参数，降低阈值")
        print("  3. 检查字体特征是否被正确识别")
    
    print(f"\n{'=' * 70}")
    print(f"所有报告文件已保存到: {output_dir}")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



