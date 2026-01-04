#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断文本提取问题 - 查看spans的实际内容
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
print("诊断文本提取问题")
print("=" * 70)
print()

try:
    extractor = formula_layout.PDFLayoutExtractor(pdf_path, debug=False)
    pages = extractor.parse()
    
    # 检查第一页的第一个块的第一行的spans
    page = pages[0]
    
    print(f"Page {page.page_number} 详细诊断:\n")
    print(f"文本块数量: {len(page.blocks)}\n")
    
    # 检查前3个块
    for bi, block in enumerate(page.blocks[:3]):
        print(f"{'─' * 70}")
        print(f"Block {bi}: {len(block.lines)} 行\n")
        
        if block.lines:
            line = block.lines[0]  # 检查第一行
            print(f"第一行信息:")
            print(f"  line.text (拼接后的文本): {repr(line.text)}")
            print(f"  line.text 长度: {len(line.text)}")
            print(f"  spans 数量: {len(line.spans)}\n")
            
            print(f"Spans 详细内容 (前10个):")
            for si, span in enumerate(line.spans[:10]):
                text_repr = repr(span.text)
                text_len = len(span.text)
                
                # 检查是否包含可打印字符
                printable = any(c.isprintable() for c in span.text) if span.text else False
                
                print(f"  Span {si}:")
                print(f"    文本: {text_repr[:60]}")
                print(f"    长度: {text_len}")
                print(f"    字体: {span.font}")
                print(f"    大小: {span.size:.1f}")
                print(f"    可打印: {printable}")
                if span.text:
                    # 显示字符编码信息
                    try:
                        # 尝试显示前几个字符的Unicode编码
                        chars_info = []
                        for i, char in enumerate(span.text[:5]):
                            chars_info.append(f"U+{ord(char):04X}")
                        print(f"    字符编码: {', '.join(chars_info)}")
                    except:
                        pass
                print()
            
            # 尝试手动拼接文本
            manual_text = ""
            for span in line.spans:
                if span.text:
                    manual_text += span.text
            
            print(f"手动拼接结果:")
            print(f"  长度: {len(manual_text)}")
            print(f"  内容: {repr(manual_text[:100])}")
            print()
        
        print()
    
    # 统计有多少spans有文本
    total_spans = 0
    spans_with_text = 0
    spans_with_printable = 0
    
    for block in page.blocks:
        for line in block.lines:
            for span in line.spans:
                total_spans += 1
                if span.text:
                    spans_with_text += 1
                    if any(c.isprintable() for c in span.text):
                        spans_with_printable += 1
    
    print(f"{'─' * 70}")
    print(f"Page {page.page_number} 统计:")
    print(f"  总spans: {total_spans}")
    print(f"  有文本的spans: {spans_with_text} ({spans_with_text/total_spans*100:.1f}%)")
    print(f"  有可打印字符的spans: {spans_with_printable} ({spans_with_printable/total_spans*100:.1f}%)")
    print()
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



