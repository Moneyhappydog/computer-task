#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看公式OCR结果
显示OCR处理后的LaTeX、图片路径、统计信息等
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

def load_ocr_results(json_path: str) -> Dict:
    """加载OCR结果JSON文件"""
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON文件不存在: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def view_ocr_results(json_path: str, show_images: bool = False, max_results: int = 20):
    """
    查看OCR结果
    
    Args:
        json_path: JSON结果文件路径
        show_images: 是否尝试显示图片（需要PIL）
        max_results: 最多显示的结果数
    """
    print("=" * 70)
    print("公式OCR结果查看器")
    print("=" * 70)
    print(f"\nJSON文件: {json_path}\n")
    
    # 加载结果
    data = load_ocr_results(json_path)
    
    formulas = data.get('formulas', [])
    total = data.get('total_formulas', len(formulas))
    block_count = data.get('block_count', sum(1 for f in formulas if f.get('formula_type') == 'block'))
    inline_count = data.get('inline_count', sum(1 for f in formulas if f.get('formula_type') == 'inline'))
    
    # 统计信息
    print("=" * 70)
    print("统计信息")
    print("=" * 70)
    print(f"\n总公式数: {total}")
    print(f"  块级公式: {block_count}")
    print(f"  行内公式: {inline_count}")
    
    # OCR置信度统计
    formulas_with_confidence = [f for f in formulas if f.get('ocr_confidence') is not None]
    if formulas_with_confidence:
        confidences = [f['ocr_confidence'] for f in formulas_with_confidence]
        avg_confidence = sum(confidences) / len(confidences)
        print(f"\nOCR置信度:")
        print(f"  有置信度的公式: {len(formulas_with_confidence)}")
        print(f"  平均置信度: {avg_confidence:.3f}")
        print(f"  最高置信度: {max(confidences):.3f}")
        print(f"  最低置信度: {min(confidences):.3f}")
    else:
        print(f"\nOCR置信度: 无（OCR模型未返回置信度）")
    
    # 按页面分组统计
    formulas_by_page = {}
    for f in formulas:
        page = f.get('page_number', 0)
        formulas_by_page[page] = formulas_by_page.get(page, 0) + 1
    
    print(f"\n每页公式分布（前10页）:")
    for page in sorted(formulas_by_page.keys())[:10]:
        print(f"  Page {page}: {formulas_by_page[page]} 个")
    
    # 显示详细结果
    print(f"\n{'=' * 70}")
    print(f"详细结果（前{max_results}个）")
    print("=" * 70)
    
    for i, formula in enumerate(formulas[:max_results], 1):
        print(f"\n公式 {i}: {formula.get('formula_id', 'N/A')}")
        print(f"  类型: {formula.get('formula_type', 'N/A')}")
        print(f"  页码: {formula.get('page_number', 'N/A')}")
        
        if formula.get('block_index') is not None:
            print(f"  块索引: {formula.get('block_index')}")
        if formula.get('line_index') is not None:
            print(f"  行索引: {formula.get('line_index')}")
        if formula.get('span_indices'):
            print(f"  span索引: {formula.get('span_indices')}")
        
        print(f"  位置: bbox={formula.get('bbox')}")
        print(f"  图片: {Path(formula.get('image_path', '')).name}")
        
        # 显示LaTeX
        latex = formula.get('latex', '')
        if latex:
            # 限制显示长度
            latex_display = latex[:100] + "..." if len(latex) > 100 else latex
            print(f"  LaTeX: {latex_display!r}")
        else:
            print(f"  LaTeX: [空]")
        
        # 显示置信度
        if formula.get('ocr_confidence') is not None:
            print(f"  OCR置信度: {formula.get('ocr_confidence'):.3f}")
        
        if formula.get('detector_score') is not None:
            print(f"  检测得分: {formula.get('detector_score'):.3f}")
        
        # 显示原始文本（如果有）
        source_text = formula.get('source_text')
        if source_text:
            source_display = source_text[:60] + "..." if len(source_text) > 60 else source_text
            print(f"  原始文本: {source_text!r}")
        
        # 尝试显示图片路径（如果存在）
        image_path = formula.get('image_path')
        if image_path and Path(image_path).exists():
            if show_images:
                try:
                    from PIL import Image
                    img = Image.open(image_path)
                    print(f"  图片尺寸: {img.size}")
                except:
                    pass
    
    if len(formulas) > max_results:
        print(f"\n... (还有 {len(formulas) - max_results} 个公式)")
    
    # 按类型分组显示
    print(f"\n{'=' * 70}")
    print("按类型分组")
    print("=" * 70)
    
    block_formulas = [f for f in formulas if f.get('formula_type') == 'block']
    inline_formulas = [f for f in formulas if f.get('formula_type') == 'inline']
    
    if block_formulas:
        print(f"\n块级公式（前5个）:")
        for i, f in enumerate(block_formulas[:5], 1):
            print(f"  {i}. {f.get('formula_id')}: {f.get('latex', '')[:50]!r}")
    
    if inline_formulas:
        print(f"\n行内公式（前5个）:")
        for i, f in enumerate(inline_formulas[:5], 1):
            print(f"  {i}. {f.get('formula_id')}: {f.get('latex', '')[:50]!r}")
    
    print(f"\n{'=' * 70}\n")

def generate_html_viewer(json_path: str, output_html: str = None):
    """生成HTML查看器"""
    data = load_ocr_results(json_path)
    formulas = data.get('formulas', [])
    
    if output_html is None:
        output_html = Path(json_path).parent / "ocr_results_viewer.html"
    else:
        output_html = Path(output_html)
    
    # 获取图片基础路径（相对于HTML文件）
    json_dir = Path(json_path).parent
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>公式OCR结果查看器</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        .stats {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .formula-item {{
            background: white;
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .formula-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .formula-id {{
            font-weight: bold;
            color: #333;
        }}
        .formula-type {{
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        .formula-type.block {{
            background: #4CAF50;
            color: white;
        }}
        .formula-type.inline {{
            background: #2196F3;
            color: white;
        }}
        .formula-info {{
            color: #666;
            font-size: 14px;
            margin: 5px 0;
        }}
        .formula-image {{
            max-width: 100%;
            border: 1px solid #ddd;
            margin: 10px 0;
        }}
        .formula-latex {{
            font-family: 'Courier New', monospace;
            background: #f0f0f0;
            padding: 10px;
            border-radius: 3px;
            margin: 10px 0;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .formula-source {{
            font-family: 'Courier New', monospace;
            background: #fff3cd;
            padding: 5px;
            border-radius: 3px;
            margin-top: 5px;
            font-size: 12px;
        }}
        .scores {{
            display: flex;
            gap: 15px;
            margin-top: 10px;
        }}
        .score-item {{
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>公式OCR结果查看器</h1>
    
    <div class="stats">
        <h2>统计信息</h2>
        <p>总公式数: <strong>{len(formulas)}</strong></p>
        <p>块级公式: <strong>{sum(1 for f in formulas if f.get('formula_type') == 'block')}</strong></p>
        <p>行内公式: <strong>{sum(1 for f in formulas if f.get('formula_type') == 'inline')}</strong></p>
    </div>
    
    <hr>
"""
    
    for formula in formulas:
        formula_id = formula.get('formula_id', 'N/A')
        formula_type = formula.get('formula_type', 'unknown')
        page_number = formula.get('page_number', 'N/A')
        image_path = formula.get('image_path', '')
        latex = formula.get('latex', '')
        source_text = formula.get('source_text', '')
        ocr_confidence = formula.get('ocr_confidence')
        detector_score = formula.get('detector_score')
        
        # 计算图片相对路径
        if image_path:
            try:
                img_path = Path(image_path)
                if img_path.is_absolute():
                    # 如果是绝对路径，尝试计算相对路径
                    try:
                        rel_path = img_path.relative_to(json_dir)
                        image_url = str(rel_path).replace('\\', '/')
                    except:
                        image_url = image_path
                else:
                    image_url = image_path.replace('\\', '/')
            except:
                image_url = image_path
        else:
            image_url = ''
        
        html_content += f"""
    <div class="formula-item">
        <div class="formula-header">
            <span class="formula-id">{formula_id}</span>
            <span class="formula-type {formula_type}">{formula_type.upper()}</span>
        </div>
        <div class="formula-info">
            页码: {page_number}
            {f", 块索引: {formula.get('block_index')}" if formula.get('block_index') is not None else ""}
            {f", 行索引: {formula.get('line_index')}" if formula.get('line_index') is not None else ""}
        </div>
        {f'<img src="{image_url}" alt="{formula_id}" class="formula-image" onerror="this.style.display=\'none\'">' if image_url else ''}
        <div class="formula-latex">LaTeX: {latex}</div>
        {f'<div class="formula-source">原始文本: {source_text}</div>' if source_text else ''}
        <div class="scores">
            {f'<span class="score-item">检测得分: {detector_score:.3f}</span>' if detector_score is not None else ''}
            {f'<span class="score-item">OCR置信度: {ocr_confidence:.3f}</span>' if ocr_confidence is not None else ''}
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML查看器已生成: {output_html}")

# 主程序
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='查看公式OCR结果')
    parser.add_argument('json_path', nargs='?', 
                       default='data/output/2023CVPR-CoMFormer/formula_ocr/formula_ocr_results.json',
                       help='OCR结果JSON文件路径')
    parser.add_argument('--max', type=int, default=20,
                       help='最多显示的结果数（默认20）')
    parser.add_argument('--html', action='store_true',
                       help='生成HTML查看器')
    parser.add_argument('--show-images', action='store_true',
                       help='显示图片信息（需要PIL）')
    
    args = parser.parse_args()
    
    json_path = args.json_path
    
    if not Path(json_path).exists():
        print(f"错误: JSON文件不存在: {json_path}")
        print("\n提示: 请先运行公式OCR处理:")
        print("  python run_formula_ocr.py")
        sys.exit(1)
    
    # 查看结果
    view_ocr_results(json_path, show_images=args.show_images, max_results=args.max)
    
    # 生成HTML查看器
    if args.html:
        generate_html_viewer(json_path)



