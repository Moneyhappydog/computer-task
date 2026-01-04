"""
检查Layer3输出结果中的表格、图片、公式问题
"""
from pathlib import Path
import re
from typing import List, Dict

def check_dita_file(file_path: Path) -> Dict:
    """检查单个DITA文件的问题"""
    problems = []
    warnings = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return {'file': str(file_path), 'error': f'无法读取文件: {e}', 'problems': [], 'warnings': []}
    
    # 检查XML结构
    table_open = len(re.findall(r'<table[^>]*>', content, re.IGNORECASE))
    table_close = len(re.findall(r'</table>', content, re.IGNORECASE))
    if table_open != table_close:
        problems.append(f'表格标签不匹配: <table> {table_open} 个, </table> {table_close} 个')
    
    fig_open = len(re.findall(r'<fig[^>]*>', content, re.IGNORECASE))
    fig_close = len(re.findall(r'</fig>', content, re.IGNORECASE))
    if fig_open != fig_close:
        problems.append(f'图片标签不匹配: <fig> {fig_open} 个, </fig> {fig_close} 个')
    
    # 检查表格结构
    table_matches = list(re.finditer(r'<table[^>]*>.*?</table>', content, re.DOTALL | re.IGNORECASE))
    for i, match in enumerate(table_matches):
        table_content = match.group(0)
        # 检查表格标题位置
        if '<title>' in table_content and '<tgroup>' in table_content:
            title_pos = table_content.find('<title>')
            tgroup_pos = table_content.find('<tgroup>')
            if title_pos > tgroup_pos:
                problems.append(f'表格 {i+1}: 标题在tgroup之后（应该在table内，tgroup之前）')
        
        # 检查表格是否有tgroup
        if '<tgroup' not in table_content:
            problems.append(f'表格 {i+1}: 缺少<tgroup>标签')
        
        # 检查表格列数是否匹配
        tgroup_match = re.search(r'<tgroup\s+cols="(\d+)"', table_content, re.IGNORECASE)
        if tgroup_match:
            declared_cols = int(tgroup_match.group(1))
            # 检查表头列数
            thead_match = re.search(r'<thead>.*?</thead>', table_content, re.DOTALL | re.IGNORECASE)
            if thead_match:
                entry_count = len(re.findall(r'<entry[^>]*>', thead_match.group(0), re.IGNORECASE))
                if entry_count != declared_cols:
                    warnings.append(f'表格 {i+1}: 声明列数 {declared_cols} 但表头有 {entry_count} 个entry')
    
    # 检查图片结构
    fig_matches = list(re.finditer(r'<fig[^>]*>.*?</fig>', content, re.DOTALL | re.IGNORECASE))
    for i, match in enumerate(fig_matches):
        fig_content = match.group(0)
        # 检查是否有image标签
        if '<image' not in fig_content:
            problems.append(f'图片 {i+1}: <fig>标签内缺少<image>标签')
        # 检查image标签是否自闭合或正确闭合
        image_matches = list(re.finditer(r'<image[^>]*/?>', fig_content, re.IGNORECASE))
        if not image_matches:
            problems.append(f'图片 {i+1}: 没有找到<image>标签')
    
    # 检查公式
    # 块级公式
    math_blocks = re.findall(r'<codeblock[^>]*outputclass="math"[^>]*>.*?</codeblock>', content, re.DOTALL | re.IGNORECASE)
    unclosed_math = len(re.findall(r'<codeblock[^>]*outputclass="math"[^>]*>', content, re.IGNORECASE)) - len(math_blocks)
    if unclosed_math > 0:
        problems.append(f'有 {unclosed_math} 个未闭合的数学公式块')
    
    # 检查Markdown残留（不应该有的符号）
    if '$$' in content:
        problems.append('发现Markdown公式标记 $$（应该已转换为DITA格式）')
    if re.search(r'\$[^<]+\$', content) and 'equation-inline' not in content:
        problems.append('发现行内公式标记 $...$（可能未转换）')
    
    # 检查图片Markdown语法残留
    if re.search(r'!\[.*?\]\(.*?\)', content):
        problems.append('发现Markdown图片语法 ![alt](path)（应该已转换为DITA格式）')
    
    # 检查表格Markdown语法残留
    if re.search(r'\|.*\|.*\|', content):
        # 排除已经是DITA表格的情况
        if '<table' not in content or len(re.findall(r'\|.*\|', content)) > len(re.findall(r'<table', content, re.IGNORECASE)) * 3:
            warnings.append('可能还有Markdown表格语法残留')
    
    # 检查<p>标签闭合
    p_open = len(re.findall(r'<p[^>]*>', content, re.IGNORECASE))
    p_close = len(re.findall(r'</p>', content, re.IGNORECASE))
    if p_open != p_close:
        problems.append(f'段落标签不匹配: <p> {p_open} 个, </p> {p_close} 个')
    
    # 检查标签嵌入问题（常见错误）
    # 图片嵌入段落
    if re.search(r'<p[^>]*>.*?<fig', content, re.DOTALL | re.IGNORECASE):
        problems.append('发现<fig>标签嵌入在<p>标签内（应该独立成段）')
    
    # 表格嵌入段落
    if re.search(r'<p[^>]*>.*?<table', content, re.DOTALL | re.IGNORECASE):
        problems.append('发现<table>标签嵌入在<p>标签内（应该独立成段）')
    
    # 公式嵌入段落（块级公式不应该在段落内）
    if re.search(r'<p[^>]*>.*?<codeblock[^>]*outputclass="math"', content, re.DOTALL | re.IGNORECASE):
        problems.append('发现块级公式<codeblock>嵌入在<p>标签内（应该独立成段）')
    
    return {
        'file': str(file_path.name),
        'problems': problems,
        'warnings': warnings,
        'table_count': table_open,
        'fig_count': fig_open,
        'math_block_count': len(math_blocks),
        'inline_math_count': len(re.findall(r'<equation-inline>', content, re.IGNORECASE))
    }

def main():
    layer3_dir = Path('data/output/2023CVPR-CoMFormer/layer3')
    
    if not layer3_dir.exists():
        print(f"❌ Layer3目录不存在: {layer3_dir}")
        return
    
    dita_files = list(layer3_dir.glob('*.dita'))
    
    if not dita_files:
        print(f"❌ 没有找到DITA文件在: {layer3_dir}")
        return
    
    print(f"🔍 检查 {len(dita_files)} 个DITA文件...\n")
    print("="*80)
    
    all_problems = []
    all_warnings = []
    
    for dita_file in sorted(dita_files):
        result = check_dita_file(dita_file)
        
        if result.get('error'):
            print(f"\n❌ {result['file']}")
            print(f"   错误: {result['error']}")
            continue
        
        if result['problems'] or result['warnings']:
            print(f"\n📄 {result['file']}")
            print(f"   统计: 表格 {result['table_count']}, 图片 {result['fig_count']}, 块级公式 {result['math_block_count']}, 行内公式 {result['inline_math_count']}")
            
            if result['problems']:
                print(f"   ❌ 问题 ({len(result['problems'])} 个):")
                for problem in result['problems']:
                    print(f"      - {problem}")
                all_problems.extend([(result['file'], problem) for problem in result['problems']])
            
            if result['warnings']:
                print(f"   ⚠️  警告 ({len(result['warnings'])} 个):")
                for warning in result['warnings']:
                    print(f"      - {warning}")
                all_warnings.extend([(result['file'], warning) for warning in result['warnings']])
    
    print("\n" + "="*80)
    print(f"\n📊 总结:")
    print(f"   检查文件数: {len(dita_files)}")
    print(f"   总问题数: {len(all_problems)}")
    print(f"   总警告数: {len(all_warnings)}")
    
    if all_problems:
        print(f"\n❌ 主要问题类型:")
        problem_types = {}
        for file, problem in all_problems:
            problem_type = problem.split(':')[0] if ':' in problem else problem.split(' ')[0]
            problem_types[problem_type] = problem_types.get(problem_type, 0) + 1
        for ptype, count in sorted(problem_types.items(), key=lambda x: -x[1]):
            print(f"   - {ptype}: {count} 次")
    
    if all_problems or all_warnings:
        print(f"\n💡 建议检查以下文件的问题:")
        problem_files = set([file for file, _ in all_problems])
        for file in sorted(problem_files)[:10]:
            print(f"   - {file}")

if __name__ == '__main__':
    main()

