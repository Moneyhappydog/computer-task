import sys
from pathlib import Path
from src.layer1_preprocessing.table_extractor import TableExtractor

def main():
    pdf_path = Path('data/input/2023CVPR-CoMFormer.pdf')
    output_dir = Path('data/output/2023CVPR-CoMFormer_test_tables')
    
    # 模式 1: 使用 Surya (默认)
    # print("Testing Surya Mode...")
    # extractor = TableExtractor(use_surya=True, use_pdfplumber=True)
    
    # 模式 2: 仅使用 pdfplumber (针对数字 PDF 效果更好)
    print("Testing pdfplumber Mode (Better for digital PDFs)...")
    extractor = TableExtractor(use_surya=False, use_pdfplumber=True)
    
    # 增加 DPI 到 300 以获得更清晰的截图
    image_paths = extractor.extract(pdf_path, output_dir, dpi=300, padding=20)
    print(f"共提取 {len(image_paths)} 张表格图片：")
    for p in image_paths:
        print(p)         

if __name__ == '__main__':
    main()
