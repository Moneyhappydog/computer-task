"""
Layer 4: 质量保证层
确保生成的DITA文档完全符合DITA标准和自定义规范

组件:
- QAManager: 主质量保证管理器（协调所有步骤）
- DITAOTValidator: DITA-OT标准验证器
- CustomRulesChecker: 自定义规则检查器
- IntelligentRepairer: 智能修复器（使用LLM）
- ValidationLoop: 验证-修复循环
- QualityReporter: 质量报告生成器
"""
from .qa_manager import QAManager
from .dita_ot_validator import DITAOTValidator
from .custom_rules_checker import CustomRulesChecker
from .intelligent_repairer import IntelligentRepairer
from .validation_loop import ValidationLoop
from .quality_reporter import QualityReporter

__all__ = [
    'QAManager',
    'DITAOTValidator',
    'CustomRulesChecker',
    'IntelligentRepairer',
    'ValidationLoop',
    'QualityReporter'
]

__version__ = '1.0.0'