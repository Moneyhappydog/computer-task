#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成公式区域的截图
从PDF中提取检测到的公式块并保存为图片
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

# 主程序
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"
if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

pdf_path = Path(pdf_path)
pdf_name = pdf_path.stem

print("=" * 70)
print("生成块级公式截图")
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
    
    if not formulas:
        print("⚠️ 未检测到公式，无法生成截图")
        sys.exit(0)
    
    # 3. 创建输出目录
    output_dir = Path("data/output") / pdf_name / "block_formulas_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. 打开PDF并提取公式区域
    print("步骤3: 提取公式区域并保存为图片...")
    doc = fitz.open(str(pdf_path))
    
    saved_count = 0
    
    for i, formula in enumerate(formulas, 1):
        try:
            page_num = formula.page_number - 1  # PyMuPDF使用0-based索引
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            # 获取公式区域的bbox
            x0, y0, x1, y1 = formula.bbox
            
            # 添加一些边距
            margin = 5
            rect = fitz.Rect(
                max(0, x0 - margin),
                max(0, y0 - margin),
                min(page.rect.width, x1 + margin),
                min(page.rect.height, y1 + margin)
            )
            
            # 渲染该区域为图片
            mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放，提高清晰度
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # 转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # 保存图片
            filename = f"page{formula.page_number}_block{formula.block_index}_formula{i}.png"
            img_path = output_dir / filename
            img.save(img_path, 'PNG')
            
            saved_count += 1
            
            if i <= 5:  # 只打印前5个
                print(f"  ✓ 公式 {i}: Page {formula.page_number}, Block {formula.block_index} "
                      f"→ {filename}")
        
        except Exception as e:
            print(f"  ⚠️ 公式 {i} 提取失败: {e}")
            continue
    
    doc.close()
    
    print(f"\n✓ 共保存 {saved_count} 个公式图片到: {output_dir}\n")
    
    # 5. 生成索引文件
    index_file = output_dir / "index.txt"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("块级公式图片索引\n")
        f.write("=" * 70 + "\n\n")
        
        for i, formula in enumerate(formulas, 1):
            filename = f"page{formula.page_number}_block{formula.block_index}_formula{i}.png"
            f.write(f"公式 {i}: {filename}\n")
            f.write(f"  页码: {formula.page_number}\n")
            f.write(f"  块索引: {formula.block_index}\n")
            f.write(f"  行索引: {formula.line_indices}\n")
            f.write(f"  得分: {formula.score:.3f}\n")
            f.write(f"  位置: bbox={formula.bbox}\n")
            f.write("\n")
    
    print(f"✓ 索引文件已保存: {index_file}\n")
    
    print("=" * 70)
    print("完成！")
    print("=" * 70)
    print(f"\n所有公式图片保存在: {output_dir}")
    print(f"共 {saved_count} 个公式图片\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



