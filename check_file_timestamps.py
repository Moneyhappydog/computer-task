#!/usr/bin/env python3
"""检查PDF和输出文件的时间戳，判断是否需要重新处理"""
from pathlib import Path
import time

pdf_path = Path('data/input/2023CVPR-CoMFormer.pdf')
md_path = Path('data/output/2023CVPR-CoMFormer/layer1/2023CVPR-CoMFormer.md')
layer1_json = Path('data/output/2023CVPR-CoMFormer/layer1/layer1_result.json')

print("=" * 60)
print("文件时间戳检查")
print("=" * 60)

if pdf_path.exists():
    pdf_time = pdf_path.stat().st_mtime
    pdf_size = pdf_path.stat().st_size / 1024 / 1024
    print(f"\nPDF文件: {pdf_path}")
    print(f"  存在: ✓")
    print(f"  大小: {pdf_size:.2f} MB")
    print(f"  修改时间: {time.ctime(pdf_time)}")
else:
    print(f"\nPDF文件: {pdf_path}")
    print(f"  存在: ✗ (文件不存在!)")
    pdf_time = None

if md_path.exists():
    md_time = md_path.stat().st_mtime
    print(f"\nMarkdown文件: {md_path}")
    print(f"  存在: ✓")
    print(f"  修改时间: {time.ctime(md_time)}")
    
    if pdf_time:
        if pdf_time > md_time:
            diff = pdf_time - md_time
            print(f"\n⚠️ PDF文件比Markdown新!")
            print(f"  时间差: {diff/3600:.2f} 小时")
            print(f"  建议: 删除输出目录并重新处理PDF")
        elif md_time > pdf_time:
            diff = md_time - pdf_time
            print(f"\n✓ Markdown比PDF新")
            print(f"  时间差: {diff/3600:.2f} 小时")
        else:
            print(f"\n✓ 时间戳相同")
else:
    print(f"\nMarkdown文件: {md_path}")
    print(f"  存在: ✗ (需要处理PDF)")

if layer1_json.exists():
    json_time = layer1_json.stat().st_mtime
    print(f"\nLayer1 JSON: {layer1_json}")
    print(f"  存在: ✓")
    print(f"  修改时间: {time.ctime(json_time)}")
else:
    print(f"\nLayer1 JSON: {layer1_json}")
    print(f"  存在: ✗")

print("\n" + "=" * 60)
if pdf_time and md_path.exists() and pdf_time > md_path.stat().st_mtime:
    print("建议操作:")
    print("1. 删除输出目录: data/output/2023CVPR-CoMFormer")
    print("2. 通过Web界面重新上传并处理PDF文件")
    print("3. 或者直接重新上传PDF，系统会重新处理")
print("=" * 60)

