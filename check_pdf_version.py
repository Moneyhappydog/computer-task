"""检查PDF文件和输出文件的时间戳，确认是否为旧版本"""
import os
from pathlib import Path
from datetime import datetime

pdf_path = Path('data/input/2023CVPR-CoMFormer.pdf')
md_path = Path('data/output/2023CVPR-CoMFormer/layer1/2023CVPR-CoMFormer.md')
layer2_json = Path('data/output/2023CVPR-CoMFormer/layer2/layer2_result.json')

print("="*70)
print("PDF版本检查")
print("="*70)

if pdf_path.exists():
    pdf_time = os.path.getmtime(pdf_path)
    pdf_size = os.path.getsize(pdf_path)
    print(f"\nPDF文件:")
    print(f"  路径: {pdf_path}")
    print(f"  大小: {pdf_size:,} bytes ({pdf_size/1024/1024:.2f} MB)")
    print(f"  修改时间: {datetime.fromtimestamp(pdf_time).strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print(f"\n❌ PDF文件不存在: {pdf_path}")
    exit(1)

if md_path.exists():
    md_time = os.path.getmtime(md_path)
    print(f"\nLayer1输出 (Markdown):")
    print(f"  路径: {md_path}")
    print(f"  修改时间: {datetime.fromtimestamp(md_time).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查是否包含Appendix A
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        has_appendix = '## Appendix A. Additional Quantitative Results' in content
        print(f"  包含Appendix A: {has_appendix}")
else:
    print(f"\n❌ Markdown文件不存在: {md_path}")
    md_time = 0

if layer2_json.exists():
    layer2_time = os.path.getmtime(layer2_json)
    print(f"\nLayer2输出 (JSON):")
    print(f"  路径: {layer2_json}")
    print(f"  修改时间: {datetime.fromtimestamp(layer2_time).strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print(f"\n❌ Layer2 JSON不存在: {layer2_json}")
    layer2_time = 0

print("\n" + "="*70)
print("时间对比:")
print("="*70)

if pdf_time > md_time:
    diff = pdf_time - md_time
    days = diff / (24 * 3600)
    print(f"\n[WARNING] PDF文件比Markdown文件新 {diff:.0f} 秒 ({days:.1f} 天)")
    print("   这意味着PDF已更新，但输出是旧的")
    print("\n建议操作:")
    print("   1. 删除输出目录: data/output/2023CVPR-CoMFormer")
    print("   2. 重新上传并处理PDF文件")
elif pdf_time < md_time:
    diff = md_time - pdf_time
    print(f"\n[OK] PDF文件比Markdown文件旧 {diff:.0f} 秒")
    print("   输出文件是新的，可能PDF没有更新")
else:
    print(f"\n[OK] 时间戳相同（可能同时创建）")

print("\n" + "="*70)

