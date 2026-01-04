#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的版面解析模块
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 直接导入模块文件，避免触发 __init__.py
import importlib.util
formula_layout_path = Path(__file__).parent / "src" / "layer1_preprocessing" / "formula_layout.py"
spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

print("=" * 60)
print("测试修复后的版面解析模块")
print("=" * 60)
print()

try:
    print(f"正在解析 PDF: {pdf_path}")
    print()
    
    # 启用调试模式
    extractor = formula_layout.PDFLayoutExtractor(pdf_path, debug=True)
    pages = extractor.parse()
    
    print(f"\n{'='*60}")
    print(f"解析完成！共 {len(pages)} 页")
    print(f"{'='*60}\n")
    
    # 统计信息
    total_blocks = sum(len(page.blocks) for page in pages)
    total_lines = sum(len(block.lines) for page in pages for block in page.blocks)
    total_spans = sum(len(line.spans) for page in pages for block in page.blocks for line in block.lines)
    
    print(f"统计信息:")
    print(f"  总页数: {len(pages)}")
    print(f"  总文本块数: {total_blocks}")
    print(f"  总文本行数: {total_lines}")
    print(f"  总文本片段数: {total_spans}")
    print()
    
    # 显示前两页的详细信息
    for page in pages[:2]:
        print(f"{'='*60}")
        print(f"Page {page.page_number} ({page.width:.1f} x {page.height:.1f})")
        print(f"{'='*60}")
        print(f"文本块数量: {len(page.blocks)}\n")
        
        if page.blocks:
            for bi, block in enumerate(page.blocks[:3]):
                print(f"  Block {bi}: {len(block.lines)} 行, bbox={block.bbox}")
                
                if block.lines:
                    line = block.lines[0]
                    print(f"    第一行: {line.text[:60]!r}")
                    print(f"      包含 {len(line.spans)} 个文本片段")
                
                print()
            
            if len(page.blocks) > 3:
                print(f"  ... (还有 {len(page.blocks) - 3} 个块)")
        else:
            print("  ⚠️ 未找到文本块")
        
        print()
    
    if total_blocks > 0:
        print("✅ 版面解析成功！")
    else:
        print("❌ 未提取到任何文本块，可能需要进一步调试")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()



