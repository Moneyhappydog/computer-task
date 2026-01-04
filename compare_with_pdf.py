#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比版面解析结果与原PDF - 查看提取效果
"""
import sys
from pathlib import Path
import importlib.util
import fitz

# 导入模块
formula_layout_path = Path(__file__).parent / "src" / "layer1_preprocessing" / "formula_layout.py"
spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("对比版面解析结果与原PDF")
print("=" * 70)
print()

try:
    # 方法1: 使用 PyMuPDF 直接提取文本（作为参考）
    doc = fitz.open(pdf_path)
    
    print("📄 原PDF文本提取（参考）:")
    print("-" * 70)
    
    for page_num in range(min(3, len(doc))):
        page = doc[page_num]
        text = page.get_text("text").strip()
        text_lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print(f"\nPage {page_num + 1}:")
        print(f"  文本行数: {len(text_lines)} 行")
        print(f"  文本长度: {len(text)} 字符")
        print(f"  前5行示例:")
        for i, line in enumerate(text_lines[:5]):
            print(f"    {i+1}. {line[:70]}")
    
    doc.close()
    
    print(f"\n{'=' * 70}")
    print("📐 版面解析结果:")
    print("=" * 70)
    
    # 方法2: 使用我们的版面解析
    extractor = formula_layout.PDFLayoutExtractor(pdf_path, debug=False)
    pages = extractor.parse()
    
    for page in pages[:3]:
        print(f"\nPage {page.page_number}:")
        
        # 统计所有行的文本
        all_text_lines = []
        for block in page.blocks:
            for line in block.lines:
                text = line.text.strip()
                if text:
                    all_text_lines.append(text)
        
        print(f"  文本块数: {len(page.blocks)} 个")
        print(f"  文本行数: {len(all_text_lines)} 行")
        print(f"  前5行示例:")
        for i, line in enumerate(all_text_lines[:5]):
            print(f"    {i+1}. {line[:70]}")
    
    # 对比分析
    print(f"\n{'=' * 70}")
    print("📊 对比分析")
    print("=" * 70)
    
    doc = fitz.open(pdf_path)
    for page_num in range(min(3, len(doc))):
        page_pdf = doc[page_num]
        page_layout = pages[page_num]
        
        # PDF 直接提取
        text_pdf = page_pdf.get_text("text").strip()
        lines_pdf = len([l for l in text_pdf.split('\n') if l.strip()])
        
        # 版面解析提取
        lines_layout = sum(len(block.lines) for block in page_layout.blocks)
        
        print(f"\nPage {page_num + 1}:")
        print(f"  PDF直接提取: {lines_pdf} 行文本")
        print(f"  版面解析: {lines_layout} 行结构")
        print(f"  差异: {abs(lines_layout - lines_pdf)} 行")
        
        if abs(lines_layout - lines_pdf) < lines_pdf * 0.3:  # 差异小于30%认为合理
            print(f"  ✅ 差异在合理范围内")
        else:
            print(f"  ⚠️  差异较大，可能需要调整")
    
    doc.close()
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



