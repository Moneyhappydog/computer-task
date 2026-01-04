#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 诊断工具 - 快速检查 PDF 文本提取情况
"""
import sys
from pathlib import Path

# 直接导入 fitz，避免其他依赖
try:
    import fitz
except ImportError:
    print("错误: 未安装 PyMuPDF (fitz)")
    print("请运行: pip install PyMuPDF>=1.23.0")
    sys.exit(1)

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

pdf_path = Path(pdf_path)

if not pdf_path.exists():
    print(f"错误: PDF 文件不存在: {pdf_path}")
    sys.exit(1)

print("=" * 60)
print(f"PDF 诊断: {pdf_path.name}")
print("=" * 60)
print()

try:
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    print(f"总页数: {total_pages}\n")
    
    # 检查前3页
    for page_num in range(min(3, total_pages)):
        page = doc[page_num]
        print(f"{'='*60}")
        print(f"Page {page_num + 1}")
        print(f"{'='*60}")
        
        # 方法1: 简单文本提取
        simple_text = page.get_text("text").strip()
        print(f"\n[方法1] get_text('text'):")
        print(f"  文本长度: {len(simple_text)} 字符")
        if len(simple_text) > 0:
            print(f"  前200字符: {simple_text[:200]}")
        else:
            print("  ❌ 无法提取文本")
        
        # 方法2: rawdict 格式
        print(f"\n[方法2] get_text('rawdict'):")
        raw_dict = page.get_text("rawdict")
        blocks = raw_dict.get("blocks", [])
        print(f"  总 blocks: {len(blocks)}")
        
        text_blocks = 0
        image_blocks = 0
        total_spans = 0
        
        for block in blocks:
            block_type = block.get("type", -1)
            if block_type == 0:
                text_blocks += 1
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    total_spans += len(spans)
            elif block_type == 1:
                image_blocks += 1
        
        print(f"  文本 blocks: {text_blocks}")
        print(f"  图片 blocks: {image_blocks}")
        print(f"  总 spans: {total_spans}")
        
        # 如果找到文本，显示一些示例
        if total_spans > 0:
            print(f"\n  示例 spans (前5个):")
            count = 0
            for block in blocks:
                if block.get("type", -1) == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", [])[:5]:
                            text = span.get("text", "").strip()
                            if text:
                                print(f"    - {text[:50]!r} (font={span.get('font', '?')}, size={span.get('size', 0):.1f})")
                                count += 1
                                if count >= 5:
                                    break
                        if count >= 5:
                            break
                    if count >= 5:
                        break
        
        # 检查是否有图片
        images = page.get_images()
        print(f"\n  页面图片数量: {len(images)}")
        
        # 总结
        if len(simple_text) == 0 and total_spans == 0:
            print(f"\n  ⚠️  警告: 此页似乎没有可提取的文本")
            print(f"    可能原因:")
            print(f"      1. PDF 是扫描件（只有图片）")
            print(f"      2. 需要 OCR 处理")
            print(f"      3. 文本以特殊格式编码")
        elif total_spans > 0:
            print(f"\n  ✓ 找到文本内容: {total_spans} 个文本片段")
        print()
    
    doc.close()
    
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



