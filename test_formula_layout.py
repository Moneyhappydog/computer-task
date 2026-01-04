#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试公式版面解析模块
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

from src.layer1_preprocessing.formula_layout import PDFLayoutExtractor


def test_formula_layout():
    """测试版面解析功能"""
    # 使用项目中的 PDF 文件
    pdf_path = Path("data/input/2023CVPR-CoMFormer.pdf")
    
    if not pdf_path.exists():
        print(f"错误: PDF 文件不存在: {pdf_path}")
        print("\n可用的 PDF 文件:")
        for pdf in Path(".").rglob("*.pdf"):
            if "dita-ot" not in str(pdf):  # 排除 dita-ot 目录
                print(f"  - {pdf}")
        return False
    
    try:
        print(f"正在解析 PDF: {pdf_path}")
        print("=" * 60)
        
        extractor = PDFLayoutExtractor(str(pdf_path))
        pages = extractor.parse()
        
        print(f"\n✅ 解析完成！共 {len(pages)} 页\n")
        
        # 详细打印前两页的结构
        for page in pages[:2]:
            print(f"\n{'='*60}")
            print(f"=== Page {page.page_number} "
                  f"({page.width:.1f} x {page.height:.1f}) ===")
            print(f"{'='*60}")
            print(f"共 {len(page.blocks)} 个文本块\n")
            
            for bi, block in enumerate(page.blocks[:5]):
                print(f"[Block {bi}] bbox={block.bbox}")
                print(f"  包含 {len(block.lines)} 行")
                
                for li, line in enumerate(block.lines[:3]):
                    print(f"\n    (Line {li}) bbox={line.bbox}")
                    print(f"      text: {line.text[:100]!r}")
                    print(f"      spans: {len(line.spans)} 个")
                    
                    # 显示前几个 span 的详细信息
                    if line.spans:
                        for si, span in enumerate(line.spans[:3]):
                            print(f"        Span {si}: {span.text[:40]!r}")
                            print(f"          font={span.font}, size={span.size:.1f}, "
                                  f"bbox={span.bbox}")
                
                if len(block.lines) > 3:
                    print(f"\n    ... (还有 {len(block.lines) - 3} 行)")
                print()
            
            if len(page.blocks) > 5:
                print(f"... (还有 {len(page.blocks) - 5} 个块)")
        
        if len(pages) > 2:
            print(f"\n{'='*60}")
            print(f"... (还有 {len(pages) - 2} 页)")
        
        # 统计信息
        print(f"\n{'='*60}")
        print("统计信息:")
        total_blocks = sum(len(page.blocks) for page in pages)
        total_lines = sum(
            len(block.lines) for page in pages for block in page.blocks
        )
        total_spans = sum(
            len(line.spans) for page in pages 
            for block in page.blocks 
            for line in block.lines
        )
        
        print(f"  总页数: {len(pages)}")
        print(f"  总文本块数: {total_blocks}")
        print(f"  总文本行数: {total_lines}")
        print(f"  总文本片段数: {total_spans}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_formula_layout()
    sys.exit(0 if success else 1)

