"""
Layer 3: DITA转换层
将分类后的内容转换为符合DITA规范的XML

组件:
- DITAConverter: 主转换器（协调所有步骤）
- TemplateSelector: 模板选择器
- ContentStructurer: 内容结构化器
- ConstraintEngine: 语法约束引擎
- TemplateRenderer: 模板渲染器
- XMLValidator: XML验证器
"""
from .converter import DITAConverter
from .template_selector import TemplateSelector
from .content_structurer import ContentStructurer
from .constraint_engine import ConstraintEngine
from .template_renderer import TemplateRenderer
from .xml_validator import XMLValidator

__all__ = [
    'DITAConverter',
    'TemplateSelector',
    'ContentStructurer',
    'ConstraintEngine',
    'TemplateRenderer',
    'XMLValidator'
]

__version__ = '1.0.0'