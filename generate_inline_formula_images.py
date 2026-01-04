#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成行内公式区域的截图
从PDF中提取检测到的行内公式并保存为图片
"""
import sys
import importlib.util
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

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
print("生成行内公式截图")
print("=" * 70)
print(f"\nPDF: {pdf_path.name}\n")

try:
    # 1. 版面解析
    print("步骤1: 版面解析...")
    extractor = PDFLayoutExtractor(str(pdf_path))
    pages = extractor.parse()
    print(f"✓ 解析完成，共 {len(pages)} 页\n")
    
    # 2. 块级公式检测（用于排除）
    print("步骤2: 检测块级公式...")
    block_detector = BlockFormulaDetector()
    block_formulas = block_detector.detect_block_formulas(pages)
    print(f"✓ 检测完成，发现 {len(block_formulas)} 个块级公式\n")
    
    # 3. 行内公式检测
    print("步骤3: 检测行内公式...")
    inline_detector = InlineFormulaDetector()
    inline_formulas = inline_detector.detect_inline_formulas(pages, block_formulas)
    print(f"✓ 检测完成，发现 {len(inline_formulas)} 个行内公式\n")
    
    if not inline_formulas:
        print("⚠️ 未检测到行内公式，无法生成截图")
        sys.exit(0)
    
    # 4. 创建输出目录
    output_dir = Path("data/output") / pdf_name / "inline_formulas_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. 打开PDF并提取行内公式区域
    print("步骤4: 提取行内公式区域并保存为图片...")
    doc = fitz.open(str(pdf_path))
    
    saved_count = 0
    
    for i, formula in enumerate(inline_formulas, 1):
        try:
            page_num = formula.page_number - 1  # PyMuPDF使用0-based索引
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            # 获取行内公式区域的bbox
            x0, y0, x1, y1 = formula.bbox
            
            # 添加一些边距（行内公式通常较小，边距可以小一点）
            margin = 3
            rect = fitz.Rect(
                max(0, x0 - margin),
                max(0, y0 - margin),
                min(page.rect.width, x1 + margin),
                min(page.rect.height, y1 + margin)
            )
            
            # 渲染该区域为图片（行内公式通常较小，使用更高倍率）
            mat = fitz.Matrix(3.0, 3.0)  # 3倍缩放，提高清晰度
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # 转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # 保存图片
            filename = f"page{formula.page_number}_block{formula.block_index}_line{formula.line_index}_formula{i}.png"
            img_path = output_dir / filename
            img.save(img_path, 'PNG')
            
            saved_count += 1
            
            if i <= 10:  # 只打印前10个
                print(f"  ✓ 行内公式 {i}: Page {formula.page_number}, Block {formula.block_index}, "
                      f"Line {formula.line_index} → {filename}")
                print(f"    文本: {formula.text!r}, 得分: {formula.score:.3f}")
        
        except Exception as e:
            print(f"  ⚠️ 行内公式 {i} 提取失败: {e}")
            continue
    
    doc.close()
    
    print(f"\n✓ 共保存 {saved_count} 个行内公式图片到: {output_dir}\n")
    
    # 6. 生成索引文件
    index_file = output_dir / "index.txt"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("行内公式图片索引\n")
        f.write("=" * 70 + "\n\n")
        
        for i, formula in enumerate(inline_formulas, 1):
            filename = f"page{formula.page_number}_block{formula.block_index}_line{formula.line_index}_formula{i}.png"
            f.write(f"行内公式 {i}: {filename}\n")
            f.write(f"  页码: {formula.page_number}\n")
            f.write(f"  块索引: {formula.block_index}\n")
            f.write(f"  行索引: {formula.line_index}\n")
            f.write(f"  span索引: {formula.span_indices}\n")
            f.write(f"  得分: {formula.score:.3f}\n")
            f.write(f"  位置: bbox={formula.bbox}\n")
            f.write(f"  文本: {formula.text!r}\n")
            f.write("\n")
    
    print(f"✓ 索引文件已保存: {index_file}\n")
    
    # 7. 生成HTML查看器（可选，方便浏览）
    html_file = output_dir / "viewer.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>行内公式图片查看器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .formula-item {
            background: white;
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .formula-info {
            margin-bottom: 10px;
            color: #666;
            font-size: 14px;
        }
        .formula-image {
            max-width: 100%;
            border: 1px solid #ddd;
            margin-top: 10px;
        }
        .formula-text {
            font-family: monospace;
            background: #f0f0f0;
            padding: 5px;
            border-radius: 3px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>行内公式图片查看器</h1>
    <p>共 <strong>""" + str(len(inline_formulas)) + """</strong> 个行内公式</p>
    <hr>
""")
        
        for i, formula in enumerate(inline_formulas, 1):
            filename = f"page{formula.page_number}_block{formula.block_index}_line{formula.line_index}_formula{i}.png"
            f.write(f"""
    <div class="formula-item">
        <div class="formula-info">
            <strong>行内公式 {i}</strong><br>
            页码: {formula.page_number}, 块: {formula.block_index}, 行: {formula.line_index}<br>
            得分: {formula.score:.3f}, span索引: {formula.span_indices}
        </div>
        <div class="formula-text">文本: {formula.text!r}</div>
        <img src="{filename}" alt="行内公式 {i}" class="formula-image">
    </div>
""")
        
        f.write("""
</body>
</html>
""")
    
    print(f"✓ HTML查看器已保存: {html_file}\n")
    
    print("=" * 70)
    print("完成！")
    print("=" * 70)
    print(f"\n所有行内公式图片保存在: {output_dir}")
    print(f"共 {saved_count} 个行内公式图片")
    print(f"\n查看方式:")
    print(f"  1. 直接查看PNG图片文件")
    print(f"  2. 打开 {html_file} 在浏览器中查看")
    print(f"  3. 查看 {index_file} 了解详细信息")
    print()
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



