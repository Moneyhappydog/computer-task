#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行公式OCR处理 - 使用真实OCR模型（pix2tex）
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

formula_ocr_path = ROOT / "src" / "layer1_preprocessing" / "formula_ocr.py"
spec4 = importlib.util.spec_from_file_location("formula_ocr", formula_ocr_path)

sys.modules['src.layer1_preprocessing.inline_formula_detector'] = inline_formula_detector

formula_ocr = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(formula_ocr)

FormulaOCRProcessor = formula_ocr.FormulaOCRProcessor
Pix2TexOCR = formula_ocr.Pix2TexOCR
DummyFormulaOCR = formula_ocr.DummyFormulaOCR

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

output_dir = "data/output/2023CVPR-CoMFormer/formula_ocr"
if len(sys.argv) > 2:
    output_dir = sys.argv[2]

print("=" * 70)
print("公式OCR处理流程 - 使用真实OCR模型（pix2tex）")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    # 检查pix2tex是否安装
    try:
        import pix2tex
        print("✓ pix2tex已安装\n")
    except ImportError:
        print("⚠️ pix2tex未安装")
        print("正在尝试安装...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pix2tex"])
        print("✓ pix2tex安装完成\n")
    
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
    
    # 4. 公式OCR（使用真实OCR模型）
    print("步骤4: 公式OCR处理（使用pix2tex）...")
    print("  注意: 首次运行会下载模型，可能需要一些时间...\n")
    
    try:
        ocr_model = Pix2TexOCR()
        print("✓ pix2tex OCR模型初始化成功\n")
    except Exception as e:
        print(f"⚠️ pix2tex初始化失败: {e}")
        print("  回退到占位OCR模型...\n")
        ocr_model = DummyFormulaOCR()
    
    processor = FormulaOCRProcessor(
        pdf_path,
        ocr_model,
        output_dir=output_dir,
        zoom=2.0,
        padding=2
    )
    
    results = processor.run(
        block_formulas=block_formulas,
        inline_formulas=inline_formulas
    )
    
    # 5. 保存JSON结果
    json_path = Path(output_dir) / "formula_ocr_results.json"
    processor.save_results_to_json(results, str(json_path))
    
    # 6. 显示结果
    print(f"\n{'=' * 70}")
    print("OCR结果摘要")
    print("=" * 70)
    
    block_count = sum(1 for r in results if r.formula_type == 'block')
    inline_count = sum(1 for r in results if r.formula_type == 'inline')
    
    print(f"\n总公式数: {len(results)}")
    print(f"  块级公式: {block_count}")
    print(f"  行内公式: {inline_count}")
    print(f"\n图片保存目录: {output_dir}")
    print(f"JSON结果: {json_path}")
    
    # 显示有LaTeX的结果
    results_with_latex = [r for r in results if r.latex and r.latex.strip() and r.latex != r"\\mathrm{dummy\\_formula}"]
    print(f"\n成功OCR的公式: {len(results_with_latex)}/{len(results)}")
    
    print(f"\n前5个OCR结果示例:")
    for i, r in enumerate(results_with_latex[:5], 1):
        print(f"\n公式 {i} ({r.formula_id}):")
        print(f"  类型: {r.formula_type}, 页码: {r.page_number}")
        print(f"  LaTeX: {r.latex[:80]!r}...")
        print(f"  检测得分: {r.detector_score:.3f}")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



