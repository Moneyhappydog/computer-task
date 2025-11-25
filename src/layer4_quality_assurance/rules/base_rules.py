"""
基础自定义规则
定义可重用的检查规则
"""
from typing import Dict, List, Any, Callable
from lxml import etree
import re

class BaseRule:
    """规则基类"""
    
    def __init__(self, name: str, description: str, severity: str = 'error'):
        """
        初始化规则
        
        Args:
            name: 规则名称
            description: 规则描述
            severity: 严重程度 (error/warning/info)
        """
        self.name = name
        self.description = description
        self.severity = severity
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        """
        执行检查
        
        Args:
            tree: XML树
            context: 上下文信息
            
        Returns:
            问题列表
        """
        raise NotImplementedError


class TitleLengthRule(BaseRule):
    """标题长度检查"""
    
    def __init__(self, max_length: int = 100, min_length: int = 5):
        super().__init__(
            name='title_length',
            description=f'标题长度应在 {min_length}-{max_length} 字符之间',
            severity='warning'
        )
        self.max_length = max_length
        self.min_length = min_length
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        title_elem = tree.find('title')
        if title_elem is not None and title_elem.text:
            length = len(title_elem.text)
            
            if length > self.max_length:
                issues.append({
                    'rule': self.name,
                    'severity': self.severity,
                    'message': f'标题过长: {length} 字符（最大 {self.max_length}）',
                    'element': 'title',
                    'suggestion': '考虑缩短标题或使用shortdesc补充说明'
                })
            
            elif length < self.min_length:
                issues.append({
                    'rule': self.name,
                    'severity': self.severity,
                    'message': f'标题过短: {length} 字符（最小 {self.min_length}）',
                    'element': 'title',
                    'suggestion': '提供更具描述性的标题'
                })
        
        return issues


class NestingDepthRule(BaseRule):
    """嵌套深度检查"""
    
    def __init__(self, max_depth: int = 5):
        super().__init__(
            name='nesting_depth',
            description=f'元素嵌套深度不应超过 {max_depth} 层',
            severity='warning'
        )
        self.max_depth = max_depth
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        def get_depth(elem, current_depth=0):
            if len(elem) == 0:
                return current_depth
            return max(get_depth(child, current_depth + 1) for child in elem)
        
        depth = get_depth(tree)
        
        if depth > self.max_depth:
            issues.append({
                'rule': self.name,
                'severity': self.severity,
                'message': f'嵌套深度过深: {depth} 层（最大 {self.max_depth}）',
                'suggestion': '考虑简化文档结构或拆分为多个主题'
            })
        
        return issues


class ShortdescLengthRule(BaseRule):
    """简短描述长度检查"""
    
    def __init__(self, max_length: int = 150):
        super().__init__(
            name='shortdesc_length',
            description=f'shortdesc长度不应超过 {max_length} 字符',
            severity='warning'
        )
        self.max_length = max_length
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        shortdesc = tree.find('shortdesc')
        if shortdesc is not None and shortdesc.text:
            length = len(shortdesc.text)
            
            if length > self.max_length:
                issues.append({
                    'rule': self.name,
                    'severity': self.severity,
                    'message': f'shortdesc过长: {length} 字符（最大 {self.max_length}）',
                    'element': 'shortdesc',
                    'suggestion': 'shortdesc应简洁概括，详细内容放在正文中'
                })
        
        return issues


class StepCountRule(BaseRule):
    """步骤数量检查（仅Task）"""
    
    def __init__(self, max_steps: int = 15, min_steps: int = 1):
        super().__init__(
            name='step_count',
            description=f'步骤数量应在 {min_steps}-{max_steps} 之间',
            severity='warning'
        )
        self.max_steps = max_steps
        self.min_steps = min_steps
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        # 仅对Task类型检查
        if tree.tag != 'task':
            return issues
        
        steps = tree.find('.//steps')
        if steps is not None:
            step_list = steps.findall('step')
            count = len(step_list)
            
            if count > self.max_steps:
                issues.append({
                    'rule': self.name,
                    'severity': self.severity,
                    'message': f'步骤过多: {count} 个（最大 {self.max_steps}）',
                    'element': 'steps',
                    'suggestion': '考虑拆分为多个子任务或简化流程'
                })
            
            elif count < self.min_steps:
                issues.append({
                    'rule': self.name,
                    'severity': 'error',
                    'message': f'步骤过少: {count} 个（最少 {self.min_steps}）',
                    'element': 'steps'
                })
        
        return issues


class ImageReferenceRule(BaseRule):
    """图片引用检查"""
    
    def __init__(self, image_dir: str = None):
        super().__init__(
            name='image_references',
            description='检查图片引用是否有效',
            severity='warning'
        )
        self.image_dir = image_dir
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        # 查找所有image元素
        images = tree.xpath('.//image[@href]')
        
        for img in images:
            href = img.get('href')
            
            # 检查是否为空
            if not href:
                issues.append({
                    'rule': self.name,
                    'severity': 'error',
                    'message': 'image元素缺少href属性',
                    'element': 'image'
                })
                continue
            
            # 检查是否为外部URL
            if href.startswith(('http://', 'https://', 'ftp://')):
                # 外部URL，跳过文件检查
                continue
            
            # 如果提供了image_dir，检查文件是否存在
            if self.image_dir:
                from pathlib import Path
                image_path = Path(self.image_dir) / href
                
                if not image_path.exists():
                    issues.append({
                        'rule': self.name,
                        'severity': self.severity,
                        'message': f'图片文件不存在: {href}',
                        'element': 'image',
                        'href': href
                    })
        
        return issues


class TerminologyConsistencyRule(BaseRule):
    """术语一致性检查"""
    
    def __init__(self, glossary: Dict[str, str] = None):
        super().__init__(
            name='terminology_consistency',
            description='检查术语使用是否一致',
            severity='info'
        )
        self.glossary = glossary or {}
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        if not self.glossary:
            return issues
        
        # 获取所有文本内容
        text_content = ' '.join(tree.itertext())
        
        # 检查每个术语
        for incorrect, correct in self.glossary.items():
            if incorrect.lower() in text_content.lower():
                issues.append({
                    'rule': self.name,
                    'severity': self.severity,
                    'message': f'发现非标准术语: "{incorrect}"',
                    'suggestion': f'建议使用: "{correct}"',
                    'incorrect_term': incorrect,
                    'correct_term': correct
                })
        
        return issues


class CodeBlockFormatRule(BaseRule):
    """代码块格式检查"""
    
    def __init__(self):
        super().__init__(
            name='code_block_format',
            description='检查代码块是否正确使用codeblock元素',
            severity='warning'
        )
    
    def check(self, tree: etree._Element, context: Dict = None) -> List[Dict]:
        issues = []
        
        # 查找所有p元素
        paragraphs = tree.xpath('.//p')
        
        for p in paragraphs:
            if p.text:
                # 检测可能是代码的模式
                code_patterns = [
                    r'^\s*(def|class|import|from)\s+',  # Python
                    r'^\s*(function|const|let|var)\s+',  # JavaScript
                    r'^\s*(public|private|class)\s+',   # Java
                    r'^\s*\$\s+',  # Shell命令
                ]
                
                for pattern in code_patterns:
                    if re.search(pattern, p.text):
                        issues.append({
                            'rule': self.name,
                            'severity': self.severity,
                            'message': '疑似代码内容未使用codeblock元素',
                            'element': 'p',
                            'suggestion': '使用 <codeblock> 而非 <p> 来标记代码'
                        })
                        break
        
        return issues


# 默认规则集
DEFAULT_RULES = [
    TitleLengthRule(),
    NestingDepthRule(),
    ShortdescLengthRule(),
    StepCountRule(),
    CodeBlockFormatRule()
]