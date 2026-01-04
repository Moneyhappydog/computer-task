#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整公式处理流程：检测 → OCR → 对齐
使用真实OCR模型（pix2tex）
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

formula_alignment_path = ROOT / "src" / "layer1_preprocessing" / "formula_alignment.py"
spec5 = importlib.util.spec_from_file_location("formula_alignment", formula_alignment_path)

sys.modules['src.layer1_preprocessing.formula_ocr'] = formula_ocr

formula_alignment = importlib.util.module_from_spec(spec5)
spec5.loader.exec_module(formula_alignment)

FormulaAligner = formula_alignment.FormulaAligner

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
md_path = r"E:\1study\3\sw\computer-task\data\output\integration_test\2023CVPR-CoMFormer\layer1\layer1_markdown.txt"

if len(sys.argv) >= 2:
    pdf_path = sys.argv[1]
if len(sys.argv) >= 3:
    md_path = sys.argv[2]

output_dir = "data/output/2023CVPR-CoMFormer/formula_ocr"
out_md_path = "data/output/integration_test/2023CVPR-CoMFormer/layer1/layer1_markdown_with_formulas_real.md"

print("=" * 70)
print("完整公式处理流程 - 使用真实OCR（pix2tex）")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}")
print(f"Markdown: {Path(md_path).name}\n")

try:
    # 检查pix2tex
    try:
        import pix2tex
        print("✓ pix2tex已安装\n")
    except ImportError:
        print("⚠️ pix2tex未安装")
        print("正在尝试安装...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pix2tex"])
        print("✓ pix2tex安装完成\n")
    
    # 步骤1: 版面解析
    print("=" * 70)
    print("步骤1: 版面解析")
    print("=" * 70)
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    # 步骤2: 块级公式检测
    print("=" * 70)
    print("步骤2: 检测块级公式")
    print("=" * 70)
    block_detector = BlockFormulaDetector()
    block_formulas = block_detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(block_formulas)} 个块级公式\n")
    
    # 步骤3: 行内公式检测
    print("=" * 70)
    print("步骤3: 检测行内公式")
    print("=" * 70)
    inline_detector = InlineFormulaDetector()
    inline_formulas = inline_detector.detect_inline_formulas(pages, block_formulas)
    print(f"✓ 检测完成，发现 {len(inline_formulas)} 个行内公式\n")
    
    # 步骤4: 公式OCR（使用真实OCR）
    print("=" * 70)
    print("步骤4: 公式OCR处理（使用pix2tex）")
    print("=" * 70)
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
    
    # 保存JSON结果
    json_path = Path(output_dir) / "formula_ocr_results.json"
    processor.save_results_to_json(results, str(json_path))
    print(f"✓ OCR结果已保存: {json_path}\n")
    
    # 步骤5: 公式对齐与回写
    print("=" * 70)
    print("步骤5: 公式对齐与回写")
    print("=" * 70)
    
    if not Path(md_path).exists():
        print(f"⚠️ Markdown文件不存在: {md_path}")
        print("  跳过对齐步骤\n")
    else:
        # 读取Markdown
        markdown_text = Path(md_path).read_text(encoding="utf-8")
        print(f"✓ 读取Markdown文件，共 {len(markdown_text)} 字符\n")
        
        # 对齐公式
        aligner = FormulaAligner.from_json(str(json_path))
        new_markdown = aligner.align_markdown(markdown_text)
        
        # 保存结果
        Path(out_md_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_md_path).write_text(new_markdown, encoding="utf-8")
        print(f"✓ 对齐完成，已保存到: {out_md_path}\n")
        
        # 显示统计
        stats = aligner.get_replacement_stats()
        print("替换统计:")
        print(f"  总公式数: {stats['total']}")
        print(f"  成功替换: {stats['successful']} ({stats['success_rate']:.1%})")
        print(f"  失败: {stats['failed']}")
        print(f"    块级公式成功: {stats['block_success']}")
        print(f"    行内公式成功: {stats['inline_success']}\n")
    
    # 最终统计
    print("=" * 70)
    print("流程完成总结")
    print("=" * 70)
    
    results_with_latex = [r for r in results if r.latex and r.latex.strip() and r.latex != r"\\mathrm{dummy\\_formula}"]
    
    print(f"\nOCR结果:")
    print(f"  总公式数: {len(results)}")
    print(f"  成功OCR: {len(results_with_latex)} ({len(results_with_latex)/len(results)*100:.1f}%)")
    print(f"  使用占位符: {len(results) - len(results_with_latex)}")
    
    if Path(md_path).exists():
        print(f"\n对齐结果:")
        print(f"  输出文件: {out_md_path}")
        print(f"  可以查看对齐后的Markdown文件")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



