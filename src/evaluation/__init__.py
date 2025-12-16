"""
评估模块
提供各层级的评判标准实现
"""

from .layer1_metrics import (
    calculate_cer,
    calculate_wer,
    calculate_heading_accuracy,
    evaluate_layer1
)

from .layer1_metrics_no_gt import (
    evaluate_layer1_without_gt,
    generate_evaluation_report,
    evaluate_structure_completeness,
    evaluate_heading_hierarchy,
    detect_extraction_issues
)

__all__ = [
    'calculate_cer',
    'calculate_wer',
    'calculate_heading_accuracy',
    'evaluate_layer1',
    'evaluate_layer1_without_gt',
    'generate_evaluation_report',
    'evaluate_structure_completeness',
    'evaluate_heading_hierarchy',
    'detect_extraction_issues'
]
