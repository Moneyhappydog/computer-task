#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看版面解析效果 - 详细展示提取结果
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
print("PDF 版面解析效果查看工具")
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
    
    # ========== 每页详细统计 ==========
    print(f"\n{'=' * 70}")
    print("📄 每页详细统计")
    print("=" * 70)
    print(f"\n{'页码':<6} {'文本块':<8} {'文本行':<8} {'文本片段':<10} {'页面尺寸':<15}")
    print("-" * 70)
    
    for page in pages:
        page_blocks = len(page.blocks)
        page_lines = sum(len(block.lines) for block in page.blocks)
        page_spans = sum(len(line.spans) for block in page.blocks for line in block.lines)
        size_str = f"{page.width:.0f}x{page.height:.0f}"
        
        print(f"{page.page_number:<6} {page_blocks:<8} {page_lines:<8} {page_spans:<10} {size_str:<15}")
    
    # ========== 前3页文本内容预览 ==========
    print(f"\n{'=' * 70}")
    print("📝 文本内容预览（前3页）")
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
            
            # 显示前3行文本
            for li, line in enumerate(block.lines[:3]):
                text_preview = line.text.strip()[:60]
                if not text_preview:
                    text_preview = f"[空白或特殊字符，{len(line.spans)} 个片段]"
                
                print(f"  │  行 {li}: {text_preview!r}")
                
                # 显示字体信息（如果有）
                if line.spans:
                    fonts = set(span.font for span in line.spans[:3])
                    sizes = [span.size for span in line.spans[:3]]
                    if fonts:
                        print(f"  │       字体: {', '.join(list(fonts)[:2])}, "
                              f"大小: {min(sizes):.1f}-{max(sizes):.1f}")
            
            if len(block.lines) > 3:
                print(f"  │  ... (还有 {len(block.lines) - 3} 行)")
            
            print(f"  └─")
            print()
        
        if len(page.blocks) > 5:
            print(f"  ... (还有 {len(page.blocks) - 5} 个块)")
    
    # ========== 字体统计 ==========
    print(f"\n{'=' * 70}")
    print("🔤 字体使用统计（前10页）")
    print("=" * 70)
    
    font_count = {}
    font_size_range = {}
    
    for page in pages[:10]:
        for block in page.blocks:
            for line in block.lines:
                for span in line.spans:
                    font = span.font
                    size = span.size
                    
                    if font not in font_count:
                        font_count[font] = 0
                        font_size_range[font] = [float('inf'), float('-inf')]
                    
                    font_count[font] += 1
                    if size < font_size_range[font][0]:
                        font_size_range[font][0] = size
                    if size > font_size_range[font][1]:
                        font_size_range[font][1] = size
    
    # 按使用频率排序
    sorted_fonts = sorted(font_count.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'字体名称':<40} {'使用次数':<12} {'字号范围':<20}")
    print("-" * 70)
    
    for font, count in sorted_fonts[:15]:  # 显示前15种字体
        size_min, size_max = font_size_range[font]
        if size_min == float('inf'):
            size_str = "N/A"
        elif size_min == size_max:
            size_str = f"{size_min:.1f}"
        else:
            size_str = f"{size_min:.1f}-{size_max:.1f}"
        
        font_display = font[:38] + ".." if len(font) > 40 else font
        print(f"{font_display:<40} {count:<12} {size_str:<20}")
    
    # ========== 评估建议 ==========
    print(f"\n{'=' * 70}")
    print("💡 效果评估")
    print("=" * 70)
    
    print("\n✅ 正常指标:")
    print(f"  - 每页文本块数: 通常在 3-15 个之间 ✓")
    print(f"  - 每页文本行数: 通常在 20-80 行之间 ✓")
    print(f"  - 每页文本片段: 通常在 100-500 个之间 ✓")
    
    print("\n📋 查看建议:")
    print("  1. 检查文本块数量是否合理（不应过多或过少）")
    print("  2. 查看文本内容预览，确认提取的文本是否准确")
    print("  3. 查看字体统计，识别数学字体（用于公式检测）")
    print("  4. 对比原PDF，确认版面结构是否正确")
    
    # 识别可能的数学字体
    math_fonts = [f for f in font_count.keys() if any(keyword in f.lower() 
                 for keyword in ['math', 'cmr', 'cambriamath', 'symbol'])]
    
    if math_fonts:
        print(f"\n🔢 检测到可能的数学字体 ({len(math_fonts)} 种):")
        for font in math_fonts[:5]:
            print(f"  - {font} (使用 {font_count[font]} 次)")
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



