#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证图片转换情况"""

import json
import re
from pathlib import Path

# Layer2统计
layer2_file = Path("data/output/2023CVPR-CoMFormer/layer2/layer2_result.json")
with open(layer2_file, 'r', encoding='utf-8') as f:
    layer2_data = json.load(f)

chunks = layer2_data.get('chunks', [])
total_images = 0
chunks_with_images = []
image_refs = []

for i, chunk in enumerate(chunks):
    features = chunk.get('features', {})
    if features.get('has_images', False):
        count = features.get('image_count', 0)
        total_images += count
        chunks_with_images.append({
            'chunk_id': chunk.get('id', f'chunk_{i}'),
            'title': chunk.get('title', ''),
            'image_count': count
        })
        # 提取图片引用
        content = chunk.get('content', '')
        matches = re.findall(r'!\[([^\]]*)\]\(([^)]+\.png)\)', content)
        for alt, path in matches:
            image_refs.append({
                'chunk_id': chunk.get('id', f'chunk_{i}'),
                'alt': alt,
                'path': path
            })

print("=" * 70)
print("Layer2 图片统计")
print("=" * 70)
print(f"总图片数: {total_images}")
print(f"包含图片的chunks数: {len(chunks_with_images)}")
print(f"\n包含图片的chunks:")
for item in chunks_with_images:
    print(f"  - {item['chunk_id']}: {item['title']} ({item['image_count']}张)")

print(f"\n图片引用详情 ({len(image_refs)}个):")
for ref in image_refs:
    print(f"  - {ref['path']} (alt: {ref['alt']}) in {ref['chunk_id']}")

# Layer3统计
layer3_file = Path("data/output/2023CVPR-CoMFormer/layer3/layer3_result.json")
with open(layer3_file, 'r', encoding='utf-8') as f:
    layer3_data = json.load(f)

results = layer3_data.get('results', [])
layer3_images = []
for result in results:
    structured_data = result.get('structured_data', {})
    title = result.get('title', '')
    
    # 在sections中查找图片
    sections = structured_data.get('sections', [])
    for section in sections:
        content = section.get('content', '')
        if '<fig>' in content or '<image href' in content:
            matches = re.findall(r'<image href="([^"]+)"', content)
            for path in matches:
                layer3_images.append({
                    'title': title,
                    'section_title': section.get('title', ''),
                    'path': path
                })
    
    # 在introduction中查找
    introduction = structured_data.get('introduction', '')
    if '<fig>' in introduction or '<image href' in introduction:
        matches = re.findall(r'<image href="([^"]+)"', introduction)
        for path in matches:
            layer3_images.append({
                'title': title,
                'section_title': 'introduction',
                'path': path
            })

print("\n" + "=" * 70)
print("Layer3 图片转换统计")
print("=" * 70)
print(f"转换的图片数: {len(layer3_images)}")
print(f"\n转换的图片详情:")
for img in layer3_images:
    print(f"  - {img['path']} in {img['title']} / {img['section_title']}")

# 对比分析
print("\n" + "=" * 70)
print("对比分析")
print("=" * 70)
print(f"Layer2图片总数: {total_images}")
print(f"Layer3转换数量: {len(layer3_images)}")
print(f"转换率: {len(layer3_images)/total_images*100:.1f}%" if total_images > 0 else "N/A")

if len(layer3_images) < total_images:
    print(f"\n⚠️  警告: 有 {total_images - len(layer3_images)} 张图片未被转换")
    # 找出未转换的图片
    layer2_paths = {ref['path'] for ref in image_refs}
    layer3_paths = {img['path'] for img in layer3_images}
    missing = layer2_paths - layer3_paths
    if missing:
        print(f"\n未转换的图片路径:")
        for path in missing:
            print(f"  - {path}")
else:
    print("\n✅ 所有图片都已转换")








