#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 详细诊断工具 - 查看原始 spans 的详细信息
"""
import sys
from pathlib import Path
import fitz

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

pdf_path = Path(pdf_path)

print("=" * 60)
print(f"详细诊断 PDF: {pdf_path.name}")
print("=" * 60)
print()

try:
    doc = fitz.open(str(pdf_path))
    page = doc[0]  # 只看第一页
    
    print(f"Page 1 详细分析\n")
    
    raw_dict = page.get_text("rawdict")
    blocks = raw_dict.get("blocks", [])
    
    print(f"总 blocks: {len(blocks)}\n")
    
    # 详细分析每个文本 block
    text_block_count = 0
    span_count = 0
    filtered_count = 0
    
    for bi, block in enumerate(blocks):
        block_type = block.get("type", -1)
        
        if block_type == 0:  # 文本块
            text_block_count += 1
            lines = block.get("lines", [])
            
            print(f"Block {bi} (文本块): {len(lines)} 行")
            
            for li, line in enumerate(lines):
                spans = line.get("spans", [])
                
                if li < 3:  # 只显示前3行
                    print(f"  Line {li}: {len(spans)} spans")
                
                for si, span in enumerate(spans):
                    span_count += 1
                    
                    if span_count <= 10:  # 只详细显示前10个
                        text = span.get("text", "")
                        bbox = span.get("bbox", [])
                        font = span.get("font", "?")
                        size = span.get("size", 0)
                        flags = span.get("flags", 0)
                        
                        # 检查各种过滤条件
                        text_empty = not text or not text.strip()
                        bbox_valid = len(bbox) >= 4 and bbox[2] > bbox[0] and bbox[3] > bbox[1]
                        size_valid = size > 0
                        
                        status = "✓" if (not text_empty and bbox_valid and size_valid) else "✗"
                        
                        print(f"    Span {si}: {status} text={text[:30]!r} "
                              f"font={font} size={size:.1f} "
                              f"bbox={bbox[:4] if len(bbox) >= 4 else 'invalid'}")
                        
                        if not bbox_valid:
                            print(f"      ⚠️ bbox 无效: {bbox}")
                        if not size_valid:
                            print(f"      ⚠️ 字体大小为 0")
                        if text_empty:
                            print(f"      ⚠️ 文本为空")
                    
                    # 检查是否会被过滤
                    text = span.get("text", "")
                    if not text or not text.strip():
                        filtered_count += 1
                        continue
                    
                    bbox = span.get("bbox", [])
                    if len(bbox) >= 4:
                        x0, y0, x1, y1 = bbox[0], bbox[1], bbox[2], bbox[3]
                        if x1 <= x0 or y1 <= y0:
                            filtered_count += 1
                            continue
                    
                    size = span.get("size", 0)
                    if size <= 0:
                        filtered_count += 1
                        continue
            
            if text_block_count >= 3:
                print(f"\n... (只显示前 3 个文本块)")
                break
    
    print(f"\n{'='*60}")
    print(f"统计:")
    print(f"  文本块数量: {text_block_count}")
    print(f"  总 spans: {span_count}")
    print(f"  会被过滤的 spans: {filtered_count}")
    print(f"  有效 spans: {span_count - filtered_count}")
    print(f"{'='*60}")
    
    doc.close()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()



