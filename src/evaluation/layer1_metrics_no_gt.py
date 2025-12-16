"""
Layer 1 无Ground Truth评估指标
适用于实际场景，无需准备参考文本
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path
import fitz  # PyMuPDF


def evaluate_structure_completeness(markdown_text: str) -> Dict[str, any]:
    """评估文档结构完整性（无需Ground Truth）
    
    检查提取的Markdown是否包含完整的文档结构元素
    
    Args:
        markdown_text: 提取的Markdown文本
        
    Returns:
        Dict: 结构完整性指标
    """
    lines = markdown_text.split('\n')
    
    # 统计各种元素
    stats = {
        'has_headings': False,
        'heading_count': 0,
        'heading_levels': set(),
        'has_paragraphs': False,
        'paragraph_count': 0,
        'has_lists': False,
        'list_item_count': 0,
        'has_code_blocks': False,
        'code_block_count': 0,
        'has_tables': False,
        'table_count': 0,
        'has_images': False,
        'image_count': 0,
        'has_formulas': False,
        'formula_count': 0,
        'empty_line_ratio': 0.0,
        'avg_paragraph_length': 0.0
    }
    
    in_code_block = False
    paragraph_lengths = []
    current_paragraph = []
    empty_lines = 0
    
    for line in lines:
        stripped = line.strip()
        
        # 空行
        if not stripped:
            empty_lines += 1
            if current_paragraph:
                paragraph_lengths.append(len(' '.join(current_paragraph)))
                current_paragraph = []
            continue
        
        # 标题
        if re.match(r'^#{1,6}\s+', stripped):
            stats['has_headings'] = True
            stats['heading_count'] += 1
            level = len(re.match(r'^(#{1,6})', stripped).group(1))
            stats['heading_levels'].add(level)
            continue
        
        # 代码块
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            if in_code_block:
                stats['has_code_blocks'] = True
                stats['code_block_count'] += 1
            continue
        
        if in_code_block:
            continue
        
        # 列表
        if re.match(r'^[-*+]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            stats['has_lists'] = True
            stats['list_item_count'] += 1
            continue
        
        # 表格
        if '|' in stripped:
            stats['has_tables'] = True
            if '---' not in stripped:  # 不计算分隔行
                stats['table_count'] += 1
            continue
        
        # 图片
        if re.search(r'!\[.*?\]\(.*?\)', stripped):
            stats['has_images'] = True
            stats['image_count'] += len(re.findall(r'!\[.*?\]\(.*?\)', stripped))
        
        # 公式
        if '$' in stripped or '$$' in stripped:
            stats['has_formulas'] = True
            stats['formula_count'] += stripped.count('$') // 2
        
        # 普通段落
        if not any([
            stripped.startswith('#'),
            stripped.startswith('-'),
            stripped.startswith('*'),
            stripped.startswith('+'),
            re.match(r'^\d+\.', stripped),
            '|' in stripped
        ]):
            stats['has_paragraphs'] = True
            stats['paragraph_count'] += 1
            current_paragraph.append(stripped)
    
    # 处理最后一段
    if current_paragraph:
        paragraph_lengths.append(len(' '.join(current_paragraph)))
    
    # 计算平均段落长度
    if paragraph_lengths:
        stats['avg_paragraph_length'] = sum(paragraph_lengths) / len(paragraph_lengths)
    
    # 空行比例
    stats['empty_line_ratio'] = empty_lines / len(lines) if lines else 0.0
    
    # 计算结构丰富度得分 (0-100)
    richness_score = 0
    if stats['has_headings']:
        richness_score += 30
        # 标题层级多样性
        richness_score += min(len(stats['heading_levels']) * 5, 20)
    if stats['has_paragraphs']:
        richness_score += 20
    if stats['has_lists']:
        richness_score += 10
    if stats['has_tables']:
        richness_score += 10
    if stats['has_images']:
        richness_score += 5
    if stats['has_code_blocks']:
        richness_score += 5
    
    stats['heading_levels'] = sorted(list(stats['heading_levels']))
    stats['structure_richness_score'] = min(richness_score, 100)
    
    return stats


def evaluate_heading_hierarchy(markdown_text: str) -> Dict[str, any]:
    """评估标题层级结构的合理性（无需Ground Truth）
    
    检查：
    1. 标题层级是否连续（不跳级）
    2. 是否有合理的标题分布
    3. H1是否唯一
    
    Args:
        markdown_text: 提取的Markdown文本
        
    Returns:
        Dict: 标题层级评估结果
    """
    from src.evaluation.layer1_metrics import extract_headings
    
    headings = extract_headings(markdown_text)
    
    if not headings:
        return {
            'valid': False,
            'issues': ['没有检测到任何标题'],
            'score': 0,
            'heading_count': 0
        }
    
    issues = []
    score = 100
    
    # 检查H1数量
    h1_count = sum(1 for h in headings if h['level'] == 1)
    if h1_count == 0:
        issues.append('缺少一级标题（H1）')
        score -= 20
    elif h1_count > 1:
        issues.append(f'有{h1_count}个一级标题，建议只有1个')
        score -= 10
    
    # 检查层级跳跃
    for i in range(1, len(headings)):
        prev_level = headings[i-1]['level']
        curr_level = headings[i]['level']
        
        # 向下跳级（如H1直接跳到H3）
        if curr_level > prev_level + 1:
            issues.append(f'标题 "{headings[i]["text"]}" 从H{prev_level}跳到H{curr_level}（跳级）')
            score -= 5
    
    # 检查标题分布
    level_dist = {}
    for h in headings:
        level_dist[h['level']] = level_dist.get(h['level'], 0) + 1
    
    # 计算标题层级连续性
    max_level = max(h['level'] for h in headings)
    min_level = min(h['level'] for h in headings)
    expected_levels = set(range(min_level, max_level + 1))
    actual_levels = set(level_dist.keys())
    missing_levels = expected_levels - actual_levels
    
    if missing_levels:
        issues.append(f'缺少中间层级: H{sorted(missing_levels)}')
        score -= 10
    
    # 检查是否有过度扁平或过度嵌套
    if max_level > 4:
        issues.append(f'标题层级过深（最深H{max_level}），可能过度嵌套')
        score -= 5
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'score': max(score, 0),
        'heading_count': len(headings),
        'h1_count': h1_count,
        'max_level': max_level,
        'level_distribution': level_dist
    }


def compare_with_pdf_pages(pdf_path: Path, markdown_text: str) -> Dict[str, any]:
    """对比PDF页数与Markdown内容量（间接验证完整性）
    
    Args:
        pdf_path: PDF文件路径
        markdown_text: 提取的Markdown文本
        
    Returns:
        Dict: 对比结果
    """
    try:
        doc = fitz.open(pdf_path)
        pdf_pages = len(doc)
        
        # 估算PDF总字符数（粗略）
        pdf_text = ""
        for page in doc:
            pdf_text += page.get_text()
        
        pdf_chars = len(pdf_text)
        doc.close()
        
        # Markdown统计
        md_chars = len(markdown_text)
        md_lines = len(markdown_text.split('\n'))
        
        # 计算比例
        char_ratio = md_chars / pdf_chars if pdf_chars > 0 else 0.0
        chars_per_page = md_chars / pdf_pages if pdf_pages > 0 else 0.0
        
        # 评估完整性（基于字符比例）
        completeness_score = 100
        if char_ratio < 0.7:
            completeness_score = char_ratio * 100
            warning = f"提取字符数仅为原文的{char_ratio:.1%}，可能有内容遗漏"
        elif char_ratio > 1.3:
            completeness_score = 90
            warning = f"提取字符数是原文的{char_ratio:.1%}，可能包含重复内容"
        else:
            warning = None
        
        return {
            'pdf_pages': pdf_pages,
            'pdf_chars': pdf_chars,
            'markdown_chars': md_chars,
            'markdown_lines': md_lines,
            'char_ratio': char_ratio,
            'chars_per_page': chars_per_page,
            'completeness_score': completeness_score,
            'warning': warning
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'completeness_score': 0
        }


def detect_extraction_issues(markdown_text: str) -> Dict[str, any]:
    """检测提取过程中的常见问题（无需Ground Truth）
    
    Args:
        markdown_text: 提取的Markdown文本
        
    Returns:
        Dict: 检测到的问题列表
    """
    issues = []
    warnings = []
    
    lines = markdown_text.split('\n')
    
    # 检测1: 过多的空行（可能是表格或布局问题）
    empty_line_count = sum(1 for line in lines if not line.strip())
    empty_ratio = empty_line_count / len(lines) if lines else 0
    if empty_ratio > 0.5:
        issues.append(f'空行比例过高({empty_ratio:.1%})，可能存在布局提取问题')
    
    # 检测2: 单行过长（可能是表格或分栏问题）
    long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 300]
    if long_lines:
        warnings.append(f'有{len(long_lines)}行内容过长(>300字符)，可能是表格或分栏未正确处理')
    
    # 检测3: 大量数字/特殊字符（可能是页眉页脚或页码）
    suspicious_lines = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and len(stripped) < 20:
            # 检测纯数字行
            if stripped.isdigit():
                suspicious_lines.append((i, stripped, '可能是页码'))
            # 检测大量特殊字符
            elif sum(1 for c in stripped if not c.isalnum() and c not in ' \t') / len(stripped) > 0.5:
                suspicious_lines.append((i, stripped, '特殊字符过多'))
    
    if len(suspicious_lines) > 5:
        warnings.append(f'检测到{len(suspicious_lines)}行可疑内容（页码、页眉页脚等）')
    
    # 检测4: 重复内容
    line_set = set()
    duplicate_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) > 20:  # 只检查有意义的行
            if stripped in line_set:
                duplicate_count += 1
            else:
                line_set.add(stripped)
    
    if duplicate_count > len(lines) * 0.1:
        issues.append(f'检测到较多重复内容({duplicate_count}行)，可能是多栏或表格重复提取')
    
    # 检测5: 标题连续性
    from src.evaluation.layer1_metrics import extract_headings
    headings = extract_headings(markdown_text)
    
    # 检测连续标题（中间没有内容）
    consecutive_headings = 0
    prev_was_heading = False
    content_between_headings = []
    last_heading_line = 0
    
    for i, line in enumerate(lines):
        is_heading = re.match(r'^#{1,6}\s+', line.strip())
        if is_heading:
            if prev_was_heading:
                consecutive_headings += 1
            if last_heading_line > 0:
                content_between_headings.append(i - last_heading_line)
            last_heading_line = i
            prev_was_heading = True
        elif line.strip():
            prev_was_heading = False
    
    if consecutive_headings > 3:
        warnings.append(f'有{consecutive_headings}处连续标题（中间无内容）')
    
    # 检测6: 标题下内容过少
    if content_between_headings:
        avg_content = sum(content_between_headings) / len(content_between_headings)
        if avg_content < 3:
            warnings.append('标题之间平均内容较少，可能存在内容遗漏')
    
    # 计算质量分数
    quality_score = 100
    quality_score -= len(issues) * 15
    quality_score -= len(warnings) * 5
    
    return {
        'issues': issues,
        'warnings': warnings,
        'quality_score': max(quality_score, 0),
        'suspicious_lines': suspicious_lines[:10],  # 只返回前10个
        'total_suspicious': len(suspicious_lines)
    }


def evaluate_layer1_without_gt(
    markdown_text: str,
    pdf_path: Path = None,
    metadata: Dict = None
) -> Dict[str, any]:
    """Layer 1完整评估（无需Ground Truth）
    
    Args:
        markdown_text: 提取的Markdown文本
        pdf_path: 原始PDF路径（可选，用于对比）
        metadata: 提取过程的元数据
        
    Returns:
        Dict: 完整的评估结果
    """
    results = {
        'evaluation_type': 'no_ground_truth',
        'timestamp': None
    }
    
    # 1. 结构完整性
    results['structure'] = evaluate_structure_completeness(markdown_text)
    
    # 2. 标题层级
    results['heading_hierarchy'] = evaluate_heading_hierarchy(markdown_text)
    
    # 3. 提取质量
    results['quality'] = detect_extraction_issues(markdown_text)
    
    # 4. PDF对比（如果提供）
    if pdf_path and pdf_path.exists():
        results['pdf_comparison'] = compare_with_pdf_pages(pdf_path, markdown_text)
    
    # 5. 元数据分析
    if metadata:
        results['metadata'] = {
            'method': metadata.get('method'),
            'pages': metadata.get('pages'),
            'image_count': metadata.get('image_count', 0),
            'processing_time': metadata.get('processing_time')
        }
    
    # 计算综合得分
    scores = []
    if 'structure' in results:
        scores.append(results['structure']['structure_richness_score'])
    if 'heading_hierarchy' in results:
        scores.append(results['heading_hierarchy']['score'])
    if 'quality' in results:
        scores.append(results['quality']['quality_score'])
    if 'pdf_comparison' in results and 'completeness_score' in results['pdf_comparison']:
        scores.append(results['pdf_comparison']['completeness_score'])
    
    results['overall_score'] = sum(scores) / len(scores) if scores else 0
    
    return results


def generate_evaluation_report(evaluation_result: Dict, output_file: Path = None) -> str:
    """生成可读的评估报告
    
    Args:
        evaluation_result: 评估结果
        output_file: 输出文件路径（可选）
        
    Returns:
        str: 报告文本
    """
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("Layer 1 评估报告（无Ground Truth）")
    report_lines.append("=" * 70)
    
    # 综合得分
    report_lines.append(f"\n🎯 综合得分: {evaluation_result['overall_score']:.2f} / 100\n")
    
    # 结构完整性
    if 'structure' in evaluation_result:
        struct = evaluation_result['structure']
        report_lines.append("\n1️⃣  文档结构完整性")
        report_lines.append(f"   结构丰富度: {struct['structure_richness_score']}/100")
        report_lines.append(f"   {'✅' if struct['has_headings'] else '❌'} 标题: {struct['heading_count']}个 (层级: {struct['heading_levels']})")
        report_lines.append(f"   {'✅' if struct['has_paragraphs'] else '❌'} 段落: {struct['paragraph_count']}个")
        report_lines.append(f"   {'✅' if struct['has_lists'] else '⚪'} 列表: {struct['list_item_count']}项")
        report_lines.append(f"   {'✅' if struct['has_tables'] else '⚪'} 表格: {struct['table_count']}个")
        report_lines.append(f"   {'✅' if struct['has_images'] else '⚪'} 图片: {struct['image_count']}张")
        report_lines.append(f"   {'✅' if struct['has_code_blocks'] else '⚪'} 代码块: {struct['code_block_count']}个")
        if struct['has_formulas']:
            report_lines.append(f"   ✅ 公式: {struct['formula_count']}个")
    
    # 标题层级
    if 'heading_hierarchy' in evaluation_result:
        heading = evaluation_result['heading_hierarchy']
        report_lines.append(f"\n2️⃣  标题层级结构")
        report_lines.append(f"   层级合理性: {heading['score']}/100")
        report_lines.append(f"   标题总数: {heading['heading_count']}")
        report_lines.append(f"   层级分布: {heading['level_distribution']}")
        
        if heading['issues']:
            report_lines.append(f"   ⚠️  发现问题:")
            for issue in heading['issues']:
                report_lines.append(f"      - {issue}")
    
    # 提取质量
    if 'quality' in evaluation_result:
        quality = evaluation_result['quality']
        report_lines.append(f"\n3️⃣  提取质量")
        report_lines.append(f"   质量分数: {quality['quality_score']}/100")
        
        if quality['issues']:
            report_lines.append(f"   ❌ 严重问题:")
            for issue in quality['issues']:
                report_lines.append(f"      - {issue}")
        
        if quality['warnings']:
            report_lines.append(f"   ⚠️  警告:")
            for warning in quality['warnings'][:5]:
                report_lines.append(f"      - {warning}")
            if len(quality['warnings']) > 5:
                report_lines.append(f"      ... 还有 {len(quality['warnings']) - 5} 个警告")
    
    # PDF对比
    if 'pdf_comparison' in evaluation_result:
        pdf = evaluation_result['pdf_comparison']
        if 'error' not in pdf:
            report_lines.append(f"\n4️⃣  PDF对比")
            report_lines.append(f"   PDF页数: {pdf['pdf_pages']}")
            report_lines.append(f"   PDF字符数: {pdf['pdf_chars']}")
            report_lines.append(f"   Markdown字符数: {pdf['markdown_chars']}")
            report_lines.append(f"   提取比例: {pdf['char_ratio']:.1%}")
            report_lines.append(f"   完整性得分: {pdf['completeness_score']:.0f}/100")
            
            if pdf['warning']:
                report_lines.append(f"   ⚠️  {pdf['warning']}")
    
    # 元数据
    if 'metadata' in evaluation_result:
        meta = evaluation_result['metadata']
        report_lines.append(f"\n5️⃣  处理信息")
        report_lines.append(f"   提取方法: {meta.get('method', 'N/A')}")
        report_lines.append(f"   页数: {meta.get('pages', 'N/A')}")
        report_lines.append(f"   图片数: {meta.get('image_count', 0)}")
    
    report_lines.append("\n" + "=" * 70)
    
    report_text = '\n'.join(report_lines)
    
    # 保存到文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    return report_text
