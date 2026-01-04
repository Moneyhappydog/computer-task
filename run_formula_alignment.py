#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行公式对齐与回写 - 测试脚本
"""
import sys
from pathlib import Path
import importlib.util

ROOT = Path(__file__).parent

# 导入formula_alignment模块
formula_alignment_path = ROOT / "src" / "layer1_preprocessing" / "formula_alignment.py"
spec = importlib.util.spec_from_file_location("formula_alignment", formula_alignment_path)
formula_alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula_alignment)

FormulaAligner = formula_alignment.FormulaAligner

# 主程序
# 默认路径
md_path = "data/output/2023CVPR-CoMFormer/layer1_markdown.txt"  # 需要根据实际情况调整
json_path = "data/output/2023CVPR-CoMFormer/formula_ocr/formula_ocr_results.json"
out_md_path = "data/output/2023CVPR-CoMFormer/layer1_markdown_with_formulas.md"

if len(sys.argv) >= 3:
    md_path = sys.argv[1]
    json_path = sys.argv[2]
    if len(sys.argv) > 3:
        out_md_path = sys.argv[3]

print("=" * 70)
print("公式对齐与回写")
print("=" * 70)
print(f"\nMarkdown文件: {md_path}")
print(f"OCR结果JSON: {json_path}")
print(f"输出文件: {out_md_path}\n")

try:
    # 检查文件是否存在
    if not Path(md_path).exists():
        print(f"⚠️ Markdown文件不存在: {md_path}")
        print("提示: 请先确保有Markdown文件，或使用其他路径")
        sys.exit(1)
    
    if not Path(json_path).exists():
        print(f"⚠️ OCR结果JSON不存在: {json_path}")
        print("提示: 请先运行公式OCR处理:")
        print("  python run_formula_ocr.py")
        sys.exit(1)
    
    # 读取markdown
    print("步骤1: 读取Markdown文件...")
    markdown_text = Path(md_path).read_text(encoding="utf-8")
    print(f"✓ 读取完成，共 {len(markdown_text)} 字符\n")
    
    # 读取OCR结果JSON
    print("步骤2: 加载OCR结果...")
    aligner = FormulaAligner.from_json(json_path)
    print(f"✓ 加载完成，共 {len(aligner.formula_results)} 个公式\n")
    
    # 对齐并回写
    print("步骤3: 对齐并回写公式...")
    new_markdown = aligner.align_markdown(markdown_text)
    print("✓ 处理完成\n")
    
    # 保存结果
    print("步骤4: 保存结果...")
    Path(out_md_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md_path).write_text(new_markdown, encoding="utf-8")
    print(f"✓ 已保存到: {out_md_path}\n")
    
    # 显示统计信息
    stats = aligner.get_replacement_stats()
    print("=" * 70)
    print("替换统计")
    print("=" * 70)
    print(f"总公式数: {stats['total']}")
    print(f"成功替换: {stats['successful']} ({stats['success_rate']:.1%})")
    print(f"失败: {stats['failed']}")
    print(f"  块级公式成功: {stats['block_success']}")
    print(f"  行内公式成功: {stats['inline_success']}")
    
    # 显示部分日志
    aligner.print_replacement_logs(max_logs=10)
    
    print(f"\n{'=' * 70}\n")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



