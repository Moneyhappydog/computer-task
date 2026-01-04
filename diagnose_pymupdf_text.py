#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断 PyMuPDF 文本提取问题
检查实际返回的数据结构
"""
import fitz
from pathlib import Path

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

print("=" * 70)
print("PyMuPDF 文本提取诊断")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}\n")

doc = fitz.open(pdf_path)
page = doc[0]  # 第一页

print("方法1: 使用 get_text('dict')")
print("-" * 70)
d = page.get_text("dict")

span_count = 0
span_with_text = 0
span_with_empty_text = 0
span_with_none_text = 0
span_no_text_key = 0

sample_spans = []

for block in d.get("blocks", []):
    if block.get("type", 0) != 0:
        continue
    
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            span_count += 1
            
            # 检查所有可能的字段
            text = span.get("text", None)
            text_alt1 = span.get("string", None)
            text_alt2 = span.get("content", None)
            
            # 检查字段是否存在
            has_text_key = "text" in span
            has_string_key = "string" in span
            has_content_key = "content" in span
            
            if span_count <= 10:
                print(f"\nSpan {span_count}:")
                print(f"  所有键: {list(span.keys())}")
                print(f"  'text' in span: {has_text_key}, value={repr(text)}")
                print(f"  'string' in span: {has_string_key}, value={repr(text_alt1)}")
                print(f"  'content' in span: {has_content_key}, value={repr(text_alt2)}")
                print(f"  font: {span.get('font', 'N/A')}")
                print(f"  size: {span.get('size', 'N/A')}")
                print(f"  bbox: {span.get('bbox', 'N/A')}")
            
            # 统计
            if not has_text_key:
                span_no_text_key += 1
            elif text is None:
                span_with_none_text += 1
            elif text == "":
                span_with_empty_text += 1
            else:
                span_with_text += 1
                if len(sample_spans) < 5:
                    sample_spans.append({
                        'text': text,
                        'font': span.get('font', ''),
                        'size': span.get('size', 0)
                    })

print(f"\n统计 (dict格式):")
print(f"  总span数: {span_count}")
print(f"  有文本的span: {span_with_text}")
print(f"  文本为空的span: {span_with_empty_text}")
print(f"  文本为None的span: {span_with_none_text}")
print(f"  没有text键的span: {span_no_text_key}")

print(f"\n样本span (前5个有文本的):")
for i, s in enumerate(sample_spans, 1):
    print(f"  {i}. text={repr(s['text'])}, font={s['font']}, size={s['size']}")

print("\n" + "=" * 70)
print("方法2: 使用 get_text('rawdict')")
print("-" * 70)

d_raw = page.get_text("rawdict")

span_count_raw = 0
span_with_text_raw = 0
span_with_empty_text_raw = 0
span_with_none_text_raw = 0
span_no_text_key_raw = 0

sample_spans_raw = []

for block in d_raw.get("blocks", []):
    if block.get("type", 0) != 0:
        continue
    
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            span_count_raw += 1
            
            text = span.get("text", None)
            text_alt1 = span.get("string", None)
            text_alt2 = span.get("content", None)
            
            has_text_key = "text" in span
            
            if span_count_raw <= 10:
                print(f"\nSpan {span_count_raw}:")
                print(f"  所有键: {list(span.keys())}")
                print(f"  'text' in span: {has_text_key}, value={repr(text)}")
                print(f"  'string' in span: {'string' in span}, value={repr(text_alt1)}")
                print(f"  'content' in span: {'content' in span}, value={repr(text_alt2)}")
                print(f"  font: {span.get('font', 'N/A')}")
                print(f"  size: {span.get('size', 'N/A')}")
            
            if not has_text_key:
                span_no_text_key_raw += 1
            elif text is None:
                span_with_none_text_raw += 1
            elif text == "":
                span_with_empty_text_raw += 1
            else:
                span_with_text_raw += 1
                if len(sample_spans_raw) < 5:
                    sample_spans_raw.append({
                        'text': text,
                        'font': span.get('font', ''),
                        'size': span.get('size', 0)
                    })

print(f"\n统计 (rawdict格式):")
print(f"  总span数: {span_count_raw}")
print(f"  有文本的span: {span_with_text_raw}")
print(f"  文本为空的span: {span_with_empty_text_raw}")
print(f"  文本为None的span: {span_with_none_text_raw}")
print(f"  没有text键的span: {span_no_text_key_raw}")

print(f"\n样本span (前5个有文本的):")
for i, s in enumerate(sample_spans_raw, 1):
    print(f"  {i}. text={repr(s['text'])}, font={s['font']}, size={s['size']}")

print("\n" + "=" * 70)
print("方法3: 使用 get_text('text') 直接获取文本")
print("-" * 70)

text_content = page.get_text("text")
print(f"直接文本内容长度: {len(text_content)}")
print(f"前200字符: {repr(text_content[:200])}")

doc.close()

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)



