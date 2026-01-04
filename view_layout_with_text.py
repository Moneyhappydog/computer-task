#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看版面解析效果 - 直接从spans提取文本显示
"""
import sys
from pathlib import Path
import importlib.util

# 导入模块
formula_layout_path = Path(__file__).parent / "src" / "layer1_preprocessing" / "formula_layout.py"
spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print("=" * 70)
print("PDF 版面解析效果查看 - 直接显示文本内容")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

try:
    extractor = formula_layout.PDFLayoutExtractor(pdf_path, debug=False)
    pages = extractor.parse()
    
    # ========== 总体统计 ==========
    print("=" * 70)
    print("📊 总体统计")
    print("=" * 70)
    
    total_blocks = sum(len(page.blocks) for page in pages)
    total_lines = sum(len(block.lines) for page in pages for block in page.blocks)
    total_spans = sum(len(line.spans) for page in pages for block in page.blocks for line in block.lines)
    
    print(f"\n总页数: {len(pages)}")
    print(f"总文本块数: {total_blocks}")
    print(f"总文本行数: {total_lines}")
    print(f"总文本片段数: {total_spans}")
    print(f"\n平均每页:")
    print(f"  - 文本块: {total_blocks/len(pages):.1f} 个")
    print(f"  - 文本行: {total_lines/len(pages):.1f} 行")
    print(f"  - 文本片段: {total_spans/len(pages):.1f} 个")
    
    # ========== 文本内容预览（直接从spans提取） ==========
    print(f"\n{'=' * 70}")
    print("📝 文本内容预览（从前3页直接提取）")
    print("=" * 70)
    
    for page in pages[:3]:
        print(f"\n{'─' * 70}")
        print(f"📄 Page {page.page_number} ({page.width:.1f} x {page.height:.1f})")
        print(f"   文本块: {len(page.blocks)} 个")
        print(f"{'─' * 70}\n")
        
        for bi, block in enumerate(page.blocks[:5]):  # 只显示前5个块
            print(f"  ┌─ Block {bi} ({len(block.lines)} 行)")
            print(f"  │  位置: x={block.bbox[0]:.1f}, y={block.bbox[1]:.1f}, "
                  f"宽={block.bbox[2]-block.bbox[0]:.1f}, 高={block.bbox[3]-block.bbox[1]:.1f}")
            
            # 直接从spans提取文本
            for li, line in enumerate(block.lines[:5]):  # 每块显示前5行
                # 从spans中提取文本并拼接
                span_texts = []
                for span in line.spans:
                    if span.text and span.text.strip():
                        span_texts.append(span.text)
                
                # 拼接文本
                if span_texts:
                    # 根据spans的位置决定是否加空格
                    full_text = " ".join(span_texts)
                    text_preview = full_text[:80]
                else:
                    # 如果spans的文本都是空的，尝试显示原始text
                    text_preview = line.text[:80] if line.text else "[无法提取文本]"
                
                print(f"  │  行 {li}: {text_preview!r}")
                
                # 显示字体信息
                if line.spans:
                    fonts = set(span.font for span in line.spans[:3] if span.font)
                    sizes = [span.size for span in line.spans[:3] if span.size > 0]
                    if fonts and sizes:
                        print(f"  │       字体: {', '.join(list(fonts)[:2])}, "
                              f"大小: {min(sizes):.1f}-{max(sizes):.1f}, "
                              f"spans: {len(line.spans)}")
            
            if len(block.lines) > 5:
                print(f"  │  ... (还有 {len(block.lines) - 5} 行)")
            
            print(f"  └─")
            print()
        
        if len(page.blocks) > 5:
            print(f"  ... (还有 {len(page.blocks) - 5} 个块)")
    
    # ========== 与原PDF对比 ==========
    print(f"\n{'=' * 70}")
    print("📊 与原PDF文本提取对比")
    print("=" * 70)
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(3, len(pages))):
            page_pdf = doc[page_num]
            page_layout = pages[page_num]
            
            # PDF直接提取
            text_pdf = page_pdf.get_text("text")
            lines_pdf = len([l for l in text_pdf.split('\n') if l.strip()])
            
            # 版面解析提取（从spans）
            texts_layout = []
            for block in page_layout.blocks:
                for line in block.lines:
                    span_texts = [s.text for s in line.spans if s.text and s.text.strip()]
                    if span_texts:
                        texts_layout.append(" ".join(span_texts))
            
            lines_layout = len(texts_layout)
            
            print(f"\nPage {page_num + 1}:")
            print(f"  PDF直接提取: {lines_pdf} 行")
            print(f"  版面解析提取: {lines_layout} 行（从spans）")
            print(f"  差异: {abs(lines_layout - lines_pdf)} 行")
            
            # 显示前3行对比
            pdf_lines = [l.strip() for l in text_pdf.split('\n') if l.strip()][:3]
            print(f"\n  PDF直接提取的前3行:")
            for i, line in enumerate(pdf_lines):
                print(f"    {i+1}. {line[:70]}")
            
            print(f"\n  版面解析提取的前3行:")
            for i, line in enumerate(texts_layout[:3]):
                print(f"    {i+1}. {line[:70]}")
        
        doc.close()
        
    except Exception as e:
        print(f"\n无法对比（可能需要安装PyMuPDF）: {e}")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



