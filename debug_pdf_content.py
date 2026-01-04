#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 PDF 内容 - 查看 PyMuPDF 能提取到什么
"""
import sys
from pathlib import Path
import fitz  # PyMuPDF

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

print(f"正在分析 PDF: {pdf_path}")
print("=" * 60)

try:
    doc = fitz.open(pdf_path)
    print(f"PDF 总页数: {len(doc)}\n")
    
    # 检查前3页
    for page_num in range(min(3, len(doc))):
        page = doc[page_num]
        print(f"\n{'='*60}")
        print(f"=== Page {page_num + 1} ===")
        print(f"{'='*60}")
        
        # 方法1: 获取原始字典结构
        print("\n[方法1] get_text('rawdict'):")
        raw_dict = page.get_text("rawdict")
        print(f"  blocks 数量: {len(raw_dict.get('blocks', []))}")
        
        total_spans = 0
        for block in raw_dict.get("blocks", []):
            if "lines" in block:
                for line in block.get("lines", []):
                    total_spans += len(line.get("spans", []))
        print(f"  总 spans 数量: {total_spans}")
        
        # 方法2: 获取普通文本
        print("\n[方法2] get_text('text'):")
        text_content = page.get_text("text")
        text_len = len(text_content.strip())
        print(f"  文本长度: {text_len} 字符")
        if text_len > 0:
            print(f"  前100字符: {text_content[:100]!r}")
        
        # 方法3: 获取字典格式
        print("\n[方法3] get_text('dict'):")
        dict_text = page.get_text("dict")
        dict_blocks = len(dict_text.get("blocks", []))
        print(f"  blocks 数量: {dict_blocks}")
        
        # 方法4: 查看页面是否有图片
        image_list = page.get_images()
        print(f"\n  图片数量: {len(image_list)}")
        
        # 详细查看第一个 block（如果有）
        if raw_dict.get("blocks"):
            first_block = raw_dict["blocks"][0]
            print(f"\n  第一个 block 类型: {first_block.get('type', 'unknown')}")
            if "lines" in first_block:
                print(f"  第一个 block 包含 {len(first_block['lines'])} 行")
                if first_block["lines"]:
                    first_line = first_block["lines"][0]
                    if "spans" in first_line:
                        print(f"  第一行包含 {len(first_line['spans'])} 个 spans")
                        if first_line["spans"]:
                            first_span = first_line["spans"][0]
                            print(f"  第一个 span 内容: {first_span.get('text', '')[:50]!r}")
        
        # 检查是否有文本层
        if text_len == 0:
            print("\n  ⚠️ 警告: 此页似乎没有可提取的文本内容")
            print("  可能原因:")
            print("    1. PDF 是扫描件（只有图片）")
            print("    2. 文本被编码为特殊格式")
            print("    3. 需要 OCR 处理")
    
    doc.close()
    
    print(f"\n{'='*60}")
    print("分析完成")
    print(f"{'='*60}")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()



