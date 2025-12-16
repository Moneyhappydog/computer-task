"""
Layer 1 评估指标
- 字符错误率 (CER)
- 词错误率 (WER)
- 标题层级准确率
"""

import re
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
import Levenshtein


def calculate_cer(reference: str, hypothesis: str) -> float:
    """计算字符错误率 (Character Error Rate)
    
    CER = (插入 + 删除 + 替换) / 参考文本字符数
    
    Args:
        reference: 参考文本（Ground Truth）
        hypothesis: 待评估文本（系统输出）
        
    Returns:
        float: 字符错误率 (0-1之间，越小越好)
    """
    if not reference:
        return 1.0 if hypothesis else 0.0
    
    # 计算Levenshtein距离（编辑距离）
    distance = Levenshtein.distance(reference, hypothesis)
    
    # CER = 编辑距离 / 参考文本长度
    cer = distance / len(reference)
    
    return cer


def calculate_wer(reference: str, hypothesis: str) -> float:
    """计算词错误率 (Word Error Rate)
    
    WER = (插入 + 删除 + 替换) / 参考文本词数
    
    Args:
        reference: 参考文本（Ground Truth）
        hypothesis: 待评估文本（系统输出）
        
    Returns:
        float: 词错误率 (0-1之间，越小越好)
    """
    # 分词（支持中英文）
    ref_words = tokenize_text(reference)
    hyp_words = tokenize_text(hypothesis)
    
    if not ref_words:
        return 1.0 if hyp_words else 0.0
    
    # 计算词级别的编辑距离
    distance = Levenshtein.distance(' '.join(ref_words), ' '.join(hyp_words))
    
    # WER = 编辑距离 / 参考文本词数
    wer = distance / len(ref_words)
    
    return wer


def tokenize_text(text: str) -> List[str]:
    """文本分词（支持中英文混合）
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 词列表
    """
    # 先按空格分割（处理英文）
    words = []
    
    # 正则表达式：匹配英文单词、数字、中文字符
    pattern = r'[a-zA-Z]+|\d+|[\u4e00-\u9fff]'
    words = re.findall(pattern, text)
    
    return words


def extract_headings(markdown_text: str) -> List[Dict[str, any]]:
    """从Markdown文本中提取标题信息
    
    Args:
        markdown_text: Markdown格式的文本
        
    Returns:
        List[Dict]: 标题列表，每个标题包含 level, text, line_number
    """
    headings = []
    lines = markdown_text.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # 匹配 ATX 风格标题：# Title, ## Title, etc.
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))  # 计算#的数量
            text = match.group(2).strip()
            headings.append({
                'level': level,
                'text': text,
                'line_number': line_num
            })
    
    return headings


def calculate_heading_accuracy(
    reference_headings: List[Dict[str, any]],
    extracted_headings: List[Dict[str, any]],
    level_tolerance: int = 0
) -> Dict[str, float]:
    """计算标题层级准确率
    
    比较参考标题和提取标题的层级是否一致
    
    Args:
        reference_headings: 参考标题列表（Ground Truth）
        extracted_headings: 提取的标题列表（系统输出）
        level_tolerance: 层级容差（允许的层级偏差）
        
    Returns:
        Dict: 包含多个准确率指标
            - exact_match: 完全匹配的准确率（文本+层级都对）
            - level_match: 层级匹配准确率（只看层级）
            - text_match: 文本匹配准确率（只看文本）
            - recall: 召回率（检测到的标题 / 实际标题数）
            - precision: 精确率（正确的标题 / 检测到的标题数）
    """
    if not reference_headings:
        return {
            'exact_match': 1.0 if not extracted_headings else 0.0,
            'level_match': 1.0,
            'text_match': 1.0,
            'recall': 1.0,
            'precision': 1.0 if not extracted_headings else 0.0,
            'total_reference': 0,
            'total_extracted': len(extracted_headings),
            'matched': 0
        }
    
    # 使用文本相似度进行匹配
    exact_matches = 0
    level_matches = 0
    text_matches = 0
    
    matched_indices = set()
    
    for ref_heading in reference_headings:
        best_match_score = 0
        best_match_idx = -1
        
        for idx, ext_heading in enumerate(extracted_headings):
            if idx in matched_indices:
                continue
            
            # 计算文本相似度
            similarity = SequenceMatcher(
                None,
                ref_heading['text'].lower(),
                ext_heading['text'].lower()
            ).ratio()
            
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_idx = idx
        
        # 如果文本相似度大于0.8，认为是同一个标题
        if best_match_score > 0.8 and best_match_idx >= 0:
            matched_indices.add(best_match_idx)
            ext_heading = extracted_headings[best_match_idx]
            
            # 检查层级是否匹配
            level_diff = abs(ref_heading['level'] - ext_heading['level'])
            if level_diff <= level_tolerance:
                level_matches += 1
                
                # 完全匹配（文本高度相似 + 层级正确）
                if best_match_score > 0.95:
                    exact_matches += 1
            
            text_matches += 1
    
    total_ref = len(reference_headings)
    total_ext = len(extracted_headings)
    
    # 计算各项指标
    recall = text_matches / total_ref if total_ref > 0 else 0.0
    precision = text_matches / total_ext if total_ext > 0 else 0.0
    exact_match_rate = exact_matches / total_ref if total_ref > 0 else 0.0
    level_match_rate = level_matches / total_ref if total_ref > 0 else 0.0
    text_match_rate = text_matches / total_ref if total_ref > 0 else 0.0
    
    return {
        'exact_match': exact_match_rate,
        'level_match': level_match_rate,
        'text_match': text_match_rate,
        'recall': recall,
        'precision': precision,
        'f1_score': 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0,
        'total_reference': total_ref,
        'total_extracted': total_ext,
        'matched': text_matches,
        'exact_matched': exact_matches,
        'level_matched': level_matches
    }


def evaluate_layer1(
    reference_text: str,
    extracted_text: str,
    reference_headings: List[Dict[str, any]] = None,
    extracted_headings: List[Dict[str, any]] = None
) -> Dict[str, any]:
    """Layer 1 完整评估
    
    Args:
        reference_text: 参考文本（Ground Truth）
        extracted_text: 提取的文本（系统输出）
        reference_headings: 参考标题列表（可选，如果为None则自动提取）
        extracted_headings: 提取的标题列表（可选，如果为None则自动提取）
        
    Returns:
        Dict: 完整的评估结果
    """
    # 文本提取精度
    cer = calculate_cer(reference_text, extracted_text)
    wer = calculate_wer(reference_text, extracted_text)
    
    # 标题层级准确率
    if reference_headings is None:
        reference_headings = extract_headings(reference_text)
    
    if extracted_headings is None:
        extracted_headings = extract_headings(extracted_text)
    
    heading_metrics = calculate_heading_accuracy(reference_headings, extracted_headings)
    
    # 文本长度统计
    ref_chars = len(reference_text)
    ext_chars = len(extracted_text)
    length_ratio = ext_chars / ref_chars if ref_chars > 0 else 0.0
    
    return {
        'text_extraction': {
            'cer': cer,
            'wer': wer,
            'reference_chars': ref_chars,
            'extracted_chars': ext_chars,
            'length_ratio': length_ratio
        },
        'heading_accuracy': heading_metrics,
        'overall_score': calculate_overall_score(cer, wer, heading_metrics)
    }


def calculate_overall_score(cer: float, wer: float, heading_metrics: Dict) -> float:
    """计算综合得分
    
    Args:
        cer: 字符错误率
        wer: 词错误率
        heading_metrics: 标题准确率指标
        
    Returns:
        float: 综合得分 (0-100)
    """
    # 文本提取得分（CER和WER的平均，越小越好，需要转换为得分）
    text_score = (1 - min(cer, 1.0)) * 50 + (1 - min(wer, 1.0)) * 50
    
    # 标题准确率得分（F1 score）
    heading_score = heading_metrics.get('f1_score', 0.0) * 100
    
    # 综合得分（文本70%，标题30%）
    overall = text_score * 0.7 + heading_score * 0.3
    
    return round(overall, 2)
