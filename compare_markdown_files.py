#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较原始Markdown和公式对齐后的Markdown
显示差异和替换情况
"""
import sys
from pathlib import Path
from difflib import unified_diff, SequenceMatcher

def compare_markdown_files(original_path: str, aligned_path: str, max_diff_lines: int = 50):
    """
    比较两个Markdown文件
    
    Args:
        original_path: 原始Markdown文件路径
        aligned_path: 对齐后的Markdown文件路径
        max_diff_lines: 最多显示的差异行数
    """
    original_path = Path(original_path)
    aligned_path = Path(aligned_path)
    
    if not original_path.exists():
        print(f"错误: 原始文件不存在: {original_path}")
        return
    
    if not aligned_path.exists():
        print(f"错误: 对齐文件不存在: {aligned_path}")
        return
    
    print("=" * 70)
    print("Markdown文件比较")
    print("=" * 70)
    print(f"\n原始文件: {original_path}")
    print(f"对齐文件: {aligned_path}\n")
    
    # 读取文件
    original_text = original_path.read_text(encoding='utf-8')
    aligned_text = aligned_path.read_text(encoding='utf-8')
    
    original_lines = original_text.splitlines(keepends=True)
    aligned_lines = aligned_text.splitlines(keepends=True)
    
    print(f"原始文件: {len(original_lines)} 行, {len(original_text)} 字符")
    print(f"对齐文件: {len(aligned_lines)} 行, {len(aligned_text)} 字符")
    print(f"差异: {len(aligned_lines) - len(original_lines)} 行, {len(aligned_text) - len(original_text)} 字符\n")
    
    # 计算相似度
    similarity = SequenceMatcher(None, original_text, aligned_text).ratio()
    print(f"整体相似度: {similarity:.2%}\n")
    
    # 查找公式标记
    original_formulas = count_formulas(original_text)
    aligned_formulas = count_formulas(aligned_text)
    
    print("=" * 70)
    print("公式标记统计")
    print("=" * 70)
    print(f"\n原始文件:")
    print(f"  $$块级公式: {original_formulas['block']} 个")
    print(f"  $行内公式: {original_formulas['inline']} 个")
    print(f"\n对齐文件:")
    print(f"  $$块级公式: {aligned_formulas['block']} 个")
    print(f"  $行内公式: {aligned_formulas['inline']} 个")
    print(f"\n新增:")
    print(f"  块级公式: {aligned_formulas['block'] - original_formulas['block']} 个")
    print(f"  行内公式: {aligned_formulas['inline'] - original_formulas['inline']} 个")
    
    # 使用unified_diff显示差异
    print(f"\n{'=' * 70}")
    print("差异对比（前50处）")
    print("=" * 70)
    print("\n格式说明:")
    print("  - 行以 '-' 开头：原始文件中的内容")
    print("  + 行以 '+' 开头：对齐文件中的内容")
    print("  ' ' 行：上下文（未改变）\n")
    
    diff = list(unified_diff(
        original_lines,
        aligned_lines,
        fromfile=str(original_path.name),
        tofile=str(aligned_path.name),
        lineterm='',
        n=3  # 上下文行数
    ))
    
    shown_count = 0
    for line in diff:
        if shown_count >= max_diff_lines:
            print(f"\n... (还有更多差异，共 {len(diff)} 行差异)")
            break
        
        # 跳过文件头信息
        if line.startswith('---') or line.startswith('+++'):
            continue
        
        print(line, end='')
        shown_count += 1
    
    # 查找具体的公式替换
    print(f"\n{'=' * 70}")
    print("公式替换示例（查找$$和$标记）")
    print("=" * 70)
    
    # 在原始文件中查找可能的公式位置
    original_lines_list = original_text.splitlines()
    aligned_lines_list = aligned_text.splitlines()
    
    # 查找对齐文件中新增的公式
    formula_examples = []
    for i, line in enumerate(aligned_lines_list):
        if '$$' in line or (line.strip().startswith('$') and line.strip().endswith('$') and len(line.strip()) > 2):
            # 检查是否在原始文件中存在
            found_in_original = False
            for orig_line in original_lines_list:
                if line.strip() in orig_line or orig_line.strip() in line.strip():
                    found_in_original = True
                    break
            
            if not found_in_original:
                formula_examples.append((i+1, line))
                if len(formula_examples) >= 10:
                    break
    
    if formula_examples:
        print(f"\n对齐文件中新增的公式（前10个）:")
        for line_num, formula_line in formula_examples:
            print(f"\n行 {line_num}:")
            print(f"  {formula_line[:100]!r}...")
    else:
        print("\n未找到明显的新增公式标记")
    
    print(f"\n{'=' * 70}\n")

def count_formulas(text: str) -> dict:
    """统计公式标记数量"""
    # 块级公式：$$...$$
    block_pattern = r'\$\$[^$]+\$\$'
    block_count = len(re.findall(block_pattern, text, re.DOTALL))
    
    # 行内公式：$...$（但不在$$中）
    # 先移除块级公式
    text_no_block = re.sub(r'\$\$[^$]+\$\$', '', text, flags=re.DOTALL)
    inline_pattern = r'\$[^$\n]+\$'
    inline_count = len(re.findall(inline_pattern, text_no_block))
    
    return {
        'block': block_count,
        'inline': inline_count
    }

# 主程序
if __name__ == "__main__":
    import re
    
    original_path = r"E:\1study\3\sw\computer-task\data\output\integration_test\2023CVPR-CoMFormer\layer1\layer1_markdown.txt"
    aligned_path = r"E:\1study\3\sw\computer-task\data\output\integration_test\2023CVPR-CoMFormer\layer1\layer1_markdown_with_formulas.md"
    
    if len(sys.argv) >= 3:
        original_path = sys.argv[1]
        aligned_path = sys.argv[2]
    
    compare_markdown_files(original_path, aligned_path)



