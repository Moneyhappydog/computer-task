#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成版面解析详细报告 - 保存到文件
"""
import sys
from pathlib import Path
from datetime import datetime
import importlib.util

# 导入模块
formula_layout_path = Path(__file__).parent / "src" / "layer1_preprocessing" / "formula_layout.py"
spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)

pdf_path = r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf"

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]

# 生成报告文件路径
pdf_name = Path(pdf_path).stem
report_dir = Path("data/output") / pdf_name / "layout_analysis"
report_dir.mkdir(parents=True, exist_ok=True)
report_file = report_dir / f"layout_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

print("=" * 70)
print("生成版面解析详细报告")
print("=" * 70)
print(f"\nPDF: {Path(pdf_path).name}")
print(f"报告将保存到: {report_file}\n")

try:
    extractor = formula_layout.PDFLayoutExtractor(pdf_path, debug=False)
    pages = extractor.parse()
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # 写入报告头部
        f.write("=" * 70 + "\n")
        f.write("PDF 版面解析详细报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"PDF 文件: {pdf_path}\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 总体统计
        total_blocks = sum(len(page.blocks) for page in pages)
        total_lines = sum(len(block.lines) for page in pages for block in page.blocks)
        total_spans = sum(len(line.spans) for page in pages for block in page.blocks for line in block.lines)
        
        f.write("=" * 70 + "\n")
        f.write("总体统计\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"总页数: {len(pages)}\n")
        f.write(f"总文本块数: {total_blocks}\n")
        f.write(f"总文本行数: {total_lines}\n")
        f.write(f"总文本片段数: {total_spans}\n\n")
        f.write(f"平均每页:\n")
        f.write(f"  - 文本块: {total_blocks/len(pages):.1f} 个\n")
        f.write(f"  - 文本行: {total_lines/len(pages):.1f} 行\n")
        f.write(f"  - 文本片段: {total_spans/len(pages):.1f} 个\n\n")
        
        # 每页统计表
        f.write("=" * 70 + "\n")
        f.write("每页详细统计\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'页码':<6} {'文本块':<10} {'文本行':<10} {'文本片段':<12} {'页面尺寸':<20}\n")
        f.write("-" * 70 + "\n")
        
        for page in pages:
            page_blocks = len(page.blocks)
            page_lines = sum(len(block.lines) for block in page.blocks)
            page_spans = sum(len(line.spans) for block in page.blocks for line in block.lines)
            size_str = f"{page.width:.1f} x {page.height:.1f}"
            f.write(f"{page.page_number:<6} {page_blocks:<10} {page_lines:<10} {page_spans:<12} {size_str:<20}\n")
        
        f.write("\n")
        
        # 详细内容（前5页）
        f.write("=" * 70 + "\n")
        f.write("详细内容预览（前5页）\n")
        f.write("=" * 70 + "\n\n")
        
        for page in pages[:5]:
            f.write(f"{'─' * 70}\n")
            f.write(f"Page {page.page_number} ({page.width:.1f} x {page.height:.1f})\n")
            f.write(f"文本块数: {len(page.blocks)}\n")
            f.write(f"{'─' * 70}\n\n")
            
            for bi, block in enumerate(page.blocks):
                f.write(f"Block {bi}:\n")
                f.write(f"  位置: x={block.bbox[0]:.1f}, y={block.bbox[1]:.1f}, "
                       f"宽={block.bbox[2]-block.bbox[0]:.1f}, 高={block.bbox[3]-block.bbox[1]:.1f}\n")
                f.write(f"  行数: {len(block.lines)}\n")
                f.write(f"  内容:\n")
                
                for li, line in enumerate(block.lines[:10]):  # 每块最多显示10行
                    text = line.text.strip()
                    if not text:
                        text = f"[空白行，{len(line.spans)} 个片段]"
                    f.write(f"    行 {li}: {text[:100]}\n")
                
                if len(block.lines) > 10:
                    f.write(f"    ... (还有 {len(block.lines) - 10} 行)\n")
                f.write("\n")
            
            f.write("\n")
        
        # 字体统计
        f.write("=" * 70 + "\n")
        f.write("字体使用统计\n")
        f.write("=" * 70 + "\n\n")
        
        font_count = {}
        font_size_range = {}
        
        for page in pages:
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
        
        sorted_fonts = sorted(font_count.items(), key=lambda x: x[1], reverse=True)
        
        f.write(f"{'字体名称':<45} {'使用次数':<12} {'字号范围':<20}\n")
        f.write("-" * 70 + "\n")
        
        for font, count in sorted_fonts:
            size_min, size_max = font_size_range[font]
            if size_min == float('inf'):
                size_str = "N/A"
            elif size_min == size_max:
                size_str = f"{size_min:.1f}"
            else:
                size_str = f"{size_min:.1f}-{size_max:.1f}"
            
            f.write(f"{font[:43]:<45} {count:<12} {size_str:<20}\n")
        
        f.write("\n")
        
        # 评估结论
        f.write("=" * 70 + "\n")
        f.write("效果评估\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("✅ 正常指标范围:\n")
        f.write("  - 每页文本块数: 通常在 3-15 个之间\n")
        f.write("  - 每页文本行数: 通常在 20-80 行之间\n")
        f.write("  - 每页文本片段: 通常在 100-500 个之间\n\n")
        
        # 检查是否有异常
        avg_blocks = total_blocks / len(pages)
        avg_lines = total_lines / len(pages)
        
        f.write("📊 当前结果:\n")
        f.write(f"  - 平均每页文本块: {avg_blocks:.1f} 个")
        if 3 <= avg_blocks <= 15:
            f.write(" ✓ 正常范围\n")
        else:
            f.write(" ⚠️ 超出正常范围\n")
        
        f.write(f"  - 平均每页文本行: {avg_lines:.1f} 行")
        if 20 <= avg_lines <= 80:
            f.write(" ✓ 正常范围\n")
        else:
            f.write(" ⚠️ 超出正常范围\n")
        
        # 识别数学字体
        math_keywords = ['math', 'cmr', 'cambriamath', 'symbol', 'timesnewroman']
        math_fonts = [f for f in font_count.keys() 
                     if any(kw in f.lower() for kw in math_keywords)]
        
        if math_fonts:
            f.write(f"\n🔢 检测到可能的数学字体 ({len(math_fonts)} 种):\n")
            for font in math_fonts[:10]:
                f.write(f"  - {font} (使用 {font_count[font]} 次)\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("报告结束\n")
        f.write("=" * 70 + "\n")
    
    print(f"✅ 报告已保存到: {report_file}")
    print(f"\n你可以用文本编辑器打开查看详细内容。")
    print(f"\n快速查看前几页内容，可以运行:")
    print(f"  python view_layout_results.py")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



