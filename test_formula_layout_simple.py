#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试公式版面解析模块 - 使用指定的PDF文件
"""
import sys
from pathlib import Path

# 直接导入文件，避免触发 __init__.py 中的其他导入
formula_layout_path = Path(__file__).parent / "src" / "layer1_preprocessing" / "formula_layout.py"
sys.path.insert(0, str(formula_layout_path.parent.parent.parent))

# 直接导入模块文件
import importlib.util
spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
formula_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_layout)
PDFLayoutExtractor = formula_layout.PDFLayoutExtractor

def main():
    """测试版面解析功能"""
    # 使用用户指定的 PDF 文件
    pdf_path = Path(r"E:\1study\3\sw\computer-task\data\input\2023CVPR-CoMFormer.pdf")
    
    if not pdf_path.exists():
        print(f"错误: PDF 文件不存在: {pdf_path}")
        return False
    
    try:
        print(f"正在解析 PDF: {pdf_path}")
        print("=" * 60)
        
        extractor = PDFLayoutExtractor(str(pdf_path))
        pages = extractor.parse()
        
        print(f"\n解析完成！共 {len(pages)} 页\n")
        
        # 简单打印前两页的结构
        for page in pages[:2]:
            print(f"\n{'='*60}")
            print(f"=== Page {page.page_number} "
                  f"({page.width:.1f} x {page.height:.1f}) ===")
            print(f"{'='*60}")
            print(f"共 {len(page.blocks)} 个文本块\n")
            
            for bi, block in enumerate(page.blocks[:3]):
                print(f"[Block {bi}] bbox={block.bbox}")
                print(f"  包含 {len(block.lines)} 行")
                
                for li, line in enumerate(block.lines[:2]):
                    print(f"\n    (Line {li}) bbox={line.bbox}")
                    print(f"      text: {line.text[:80]!r}")
                    print(f"      spans: {len(line.spans)} 个")
                
                print()
            
            if len(page.blocks) > 3:
                print(f"... (还有 {len(page.blocks) - 3} 个块)")
        
        # 统计信息
        print(f"\n{'='*60}")
        print("统计信息:")
        total_blocks = sum(len(page.blocks) for page in pages)
        total_lines = sum(
            len(block.lines) for page in pages for block in page.blocks
        )
        
        print(f"  总页数: {len(pages)}")
        print(f"  总文本块数: {total_blocks}")
        print(f"  总文本行数: {total_lines}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

