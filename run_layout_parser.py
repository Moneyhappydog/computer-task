#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接运行版面解析器 - 独立脚本
"""
import sys
import importlib.util
from pathlib import Path

# 直接加载 formula_layout.py 模块，避免触发 __init__.py
formula_layout_path = Path(__file__).parent / "src" / "layer1_preprocessing" / "formula_layout.py"

spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)

# 使用用户指定的 PDF 路径
pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

try:
    print(f"正在解析 PDF: {pdf_path}")
    print("=" * 60)
    
    extractor = formula_layout.PDFLayoutExtractor(pdf_path)
    pages = extractor.parse()
    
    print(f"\n解析完成！共 {len(pages)} 页\n")
    
    # 简单打印前两页的结构
    for page in pages[:2]:
        print(f"\n{'='*60}")
        print(f"=== Page {page.page_number} ({page.width:.1f} x {page.height:.1f}) ===")
        print(f"{'='*60}")
        print(f"共 {len(page.blocks)} 个文本块\n")
        
        for bi, block in enumerate(page.blocks[:5]):
            print(f"[Block {bi}] bbox={block.bbox}")
            print(f"  包含 {len(block.lines)} 行")
            
            for li, line in enumerate(block.lines[:3]):
                print(f"\n    (Line {li}) bbox={line.bbox}")
                print(f"      text: {line.text[:80]!r}")
                print(f"      spans: {len(line.spans)} 个")
                
                # 显示第一个span的详细信息作为示例
                if line.spans and li == 0:
                    span = line.spans[0]
                    print(f"        示例Span: {span.text[:40]!r}")
                    print(f"          font={span.font}, size={span.size:.1f}")
            
            print()
        
        if len(page.blocks) > 5:
            print(f"... (还有 {len(page.blocks) - 5} 个块)")
    
    if len(pages) > 2:
        print(f"\n{'='*60}")
        print(f"... (还有 {len(pages) - 2} 页)")
    
    # 统计信息
    print(f"\n{'='*60}")
    print("统计信息:")
    total_blocks = sum(len(page.blocks) for page in pages)
    total_lines = sum(len(block.lines) for page in pages for block in page.blocks)
    total_spans = sum(len(line.spans) for page in pages for block in page.blocks for line in block.lines)
    
    print(f"  总页数: {len(pages)}")
    print(f"  总文本块数: {total_blocks}")
    print(f"  总文本行数: {total_lines}")
    print(f"  总文本片段数: {total_spans}")
    print(f"{'='*60}\n")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



