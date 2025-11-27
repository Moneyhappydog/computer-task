"""
Step 3: 语法约束引擎
定义DITA语法规则并指导LLM生成符合规范的内容
"""
from typing import Dict, List, Any
import logging

from .errors import ConstraintError, DITAConversionError

logger = logging.getLogger(__name__)

class ConstraintEngine:
    """DITA语法约束引擎"""
    
    def __init__(self):
        """初始化约束引擎"""
        # 定义DITA规范约束
        self.constraints = {
            'Task': self._task_constraints(),
            'Concept': self._concept_constraints(),
            'Reference': self._reference_constraints()
        }
        
        logger.info("✅ 语法约束引擎初始化完成")
    
    def _task_constraints(self) -> Dict:
        """Task类型的约束规则"""
        return {
            'required_elements': ['title', 'taskbody'],
            'taskbody_children': {
                'prereq': {'min': 0, 'max': 1},
                'context': {'min': 0, 'max': 1},
                'steps': {'min': 1, 'max': 1},  # 必需且只能有一个
                'result': {'min': 0, 'max': 1},
                'example': {'min': 0, 'max': 1},
                'postreq': {'min': 0, 'max': 1}
            },
            'steps_constraints': {
                'min_steps': 1,
                'step_required_elements': ['cmd'],
                'step_optional_elements': ['info', 'stepxmp', 'substeps', 'stepresult']
            },
            'element_order': [
                'title',
                'shortdesc',
                'prolog',
                'taskbody'
            ],
            'taskbody_order': [
                'prereq',
                'context',
                'steps',
                'result',
                'example',
                'postreq'
            ],
            'id_pattern': r'^[a-zA-Z][a-zA-Z0-9_\-\.]*$',
            'content_rules': {
                'cmd': {
                    'description': '步骤的主要命令，必须是明确的操作指令',
                    'allowed_children': ['text', 'ph', 'uicontrol', 'codeph'],
                    'forbidden_children': ['p', 'ul', 'ol', 'section']
                },
                'info': {
                    'description': '步骤的补充信息',
                    'allowed_children': ['text', 'p', 'ul', 'ol', 'note']
                }
            }
        }
    
    def _concept_constraints(self) -> Dict:
        """Concept类型的约束规则"""
        return {
            'required_elements': ['title', 'conbody'],
            'conbody_children': {
                'p': {'min': 0, 'max': float('inf')},
                'section': {'min': 0, 'max': float('inf')},
                'example': {'min': 0, 'max': float('inf')},
                'note': {'min': 0, 'max': float('inf')}
            },
            'element_order': [
                'title',
                'shortdesc',
                'prolog',
                'conbody',
                'related-links'
            ],
            'id_pattern': r'^[a-zA-Z][a-zA-Z0-9_\-\.]*$',
            'content_rules': {
                'section': {
                    'description': '概念的子章节',
                    'required_children': [],
                    'allowed_children': ['title', 'p', 'ul', 'ol', 'note', 'example']
                },
                'p': {
                    'description': '段落',
                    'allowed_children': ['text', 'ph', 'term', 'cite', 'xref']
                }
            }
        }
    
    def _reference_constraints(self) -> Dict:
        """Reference类型的约束规则"""
        return {
            'required_elements': ['title', 'refbody'],
            'refbody_children': {
                'section': {'min': 0, 'max': float('inf')},
                'properties': {'min': 0, 'max': 1},
                'refsyn': {'min': 0, 'max': 1},
                'table': {'min': 0, 'max': float('inf')}
            },
            'element_order': [
                'title',
                'shortdesc',
                'prolog',
                'refbody',
                'related-links'
            ],
            'properties_structure': {
                'required_elements': ['prophead'],
                'property_required': ['proptype', 'propvalue', 'propdesc']
            },
            'table_structure': {
                'required_elements': ['tgroup'],
                'tgroup_required': ['thead', 'tbody'],
                'min_cols': 1
            },
            'id_pattern': r'^[a-zA-Z][a-zA-Z0-9_\-\.]*$'
        }
    
    def get_constraints(self, content_type: str) -> Dict:
        """
        获取指定类型的约束规则
        
        Args:
            content_type: 内容类型
            
        Returns:
            约束规则字典
        """
        if content_type not in self.constraints:
            raise ConstraintError(
                f"不支持的内容类型: {content_type}",
                "UNSUPPORTED_CONTENT_TYPE"
            )
        
        return self.constraints[content_type]
    
    def validate_structure(self, structured_data: Dict, content_type: str) -> Dict[str, Any]:
        """
        验证结构化数据是否符合约束
        
        Args:
            structured_data: 结构化数据
            content_type: 内容类型
            
        Returns:
            验证结果字典
        """
        logger.info(f"🔍 验证 {content_type} 结构...")
        
        constraints = self.get_constraints(content_type)
        errors = []
        warnings = []
        
        # 验证必需元素
        for required in constraints['required_elements']:
            if required not in structured_data and f"{required}_id" not in structured_data:
                errors.append(f"缺少必需元素: {required}")
        
        # 根据类型进行特定验证
        if content_type == 'Task':
            errors.extend(self._validate_task_structure(structured_data, constraints))
        elif content_type == 'Concept':
            errors.extend(self._validate_concept_structure(structured_data, constraints))
        elif content_type == 'Reference':
            errors.extend(self._validate_reference_structure(structured_data, constraints))
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"✅ 结构验证通过")
        else:
            logger.warning(f"⚠️  发现 {len(errors)} 个错误")
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_task_structure(self, data: Dict, constraints: Dict) -> List[str]:
        """验证Task特定结构"""
        errors = []
        
        # 验证steps
        steps = data.get('steps', [])
        min_steps = constraints['steps_constraints']['min_steps']
        
        if len(steps) < min_steps:
            errors.append(f"steps数量不足: 需要至少{min_steps}个，实际{len(steps)}个")
        
        # 验证每个step的结构
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"第{i+1}个step格式错误: 必须是字典")
                continue
            
            # 检查必需的cmd字段
            if 'cmd' not in step:
                errors.append(f"第{i+1}个step缺少必需字段: cmd")
        
        return errors
    
    def _validate_concept_structure(self, data: Dict, constraints: Dict) -> List[str]:
        """验证Concept特定结构"""
        errors = []
        
        # Concept必须有introduction或sections
        if not data.get('introduction') and not data.get('sections'):
            errors.append("Concept必须包含introduction或sections")
        
        # 检查sections中的ID唯一性
        sections = data.get('sections', [])
        id_set = set()
        for section in sections:
            if 'id' in section:
                if section['id'] in id_set:
                    errors.append(f"ID重复: {section['id']}")
                else:
                    id_set.add(section['id'])
        
        return errors
    
    def _validate_reference_structure(self, data: Dict, constraints: Dict) -> List[str]:
        """验证Reference特定结构"""
        errors = []
        
        # Reference应该有properties或table或sections
        has_content = any([
            data.get('properties'),
            data.get('table'),
            data.get('sections')
        ])
        
        # 放宽约束：如果没有这些结构，但有其他内容，也可以接受
        # 这是为了兼容各种Reference类型的文档
        if not has_content:
            # 检查是否有其他内容
            has_other_content = any([
                data.get('title'),
                data.get('shortdesc'),
                # 检查是否有其他字段
                any(key not in ['reference_id', 'title', 'shortdesc'] for key in data.keys())
            ])
            
            if not has_other_content:
                errors.append("Reference必须包含properties、table或sections中的至少一项")
            else:
                # 只有标题和短描述是不够的，需要有实际内容
                if list(data.keys()) == ['reference_id', 'title', 'shortdesc']:
                    errors.append("Reference必须包含properties、table或sections中的至少一项")
        
        # 验证table结构
        if 'table' in data and data['table']:
            table = data['table']
            if not isinstance(table, dict):
                errors.append("table必须是字典格式")
            elif 'columns' not in table or 'rows' not in table:
                errors.append("table必须包含columns和rows字段")
        
        return errors
    
    def generate_constraint_prompt(self, content_type: str) -> str:
        """
        生成约束提示（用于指导LLM）
        
        Args:
            content_type: 内容类型
            
        Returns:
            约束说明文本
        """
        constraints = self.get_constraints(content_type)
        
        if content_type == 'Task':
            return self._task_constraint_prompt(constraints)
        elif content_type == 'Concept':
            return self._concept_constraint_prompt(constraints)
        elif content_type == 'Reference':
            return self._reference_constraint_prompt(constraints)
    
    def _task_constraint_prompt(self, constraints: Dict) -> str:
        """生成Task约束提示"""
        return f"""
DITA Task 约束规则:

1. 必需元素: {', '.join(constraints['required_elements'])}

2. <taskbody> 结构:
   - 元素顺序: {' → '.join(constraints['taskbody_order'])}
   - <steps> 是必需的，且至少包含 {constraints['steps_constraints']['min_steps']} 个 <step>

3. <step> 结构:
   - 必需元素: <cmd> (步骤的主要操作)
   - 可选元素: <info> (补充说明), <stepxmp> (示例)
   - <cmd> 必须是明确的操作指令（如"点击按钮"、"输入命令"）

4. ID命名规范:
   - 必须以字母开头
   - 只能包含字母、数字、下划线、连字符、点号
   - 推荐格式: task_verb_noun (如 task_install_python)

示例:
<task id="task_create_account">
  <title>Creating an Account</title>
  <taskbody>
    <prereq>You need a valid email address</prereq>
    <steps>
      <step>
        <cmd>Click the Sign Up button</cmd>
        <info>Located in the top-right corner</info>
      </step>
      <step>
        <cmd>Enter your email address</cmd>
      </step>
    </steps>
    <result>Your account is created and ready to use</result>
  </taskbody>
</task>
"""
    
    def _concept_constraint_prompt(self, constraints: Dict) -> str:
        """生成Concept约束提示"""
        return f"""
DITA Concept 约束规则:

1. 必需元素: {', '.join(constraints['required_elements'])}

2. <conbody> 结构:
   - 通常以 <p> 开头提供概述
   - 可包含多个 <section> 详细说明概念的不同方面
   - 可包含 <example> 提供示例

3. 内容特点:
   - 解释性内容，回答"是什么"的问题
   - 包含定义、背景、原理等
   - 避免使用祈使句和步骤列表

4. ID命名规范:
   - 推荐格式: concept_topic_name (如 concept_object_oriented_programming)

示例:
<concept id="concept_cloud_computing">
  <title>Cloud Computing</title>
  <shortdesc>An overview of cloud computing technology</shortdesc>
  <conbody>
    <p>Cloud computing is the delivery of computing services over the internet.</p>
    <section>
      <title>Key Characteristics</title>
      <p>Cloud computing offers on-demand resources, scalability, and pay-per-use pricing.</p>
    </section>
    <section>
      <title>Service Models</title>
      <p>Common models include IaaS, PaaS, and SaaS.</p>
    </section>
  </conbody>
</concept>
"""
    
    def _reference_constraint_prompt(self, constraints: Dict) -> str:
        """生成Reference约束提示"""
        return f"""
DITA Reference 约束规则:

1. 必需元素: {', '.join(constraints['required_elements'])}

2. <refbody> 结构:
   - <properties>: 用于参数列表、配置项
   - <table>: 用于表格数据
   - <section>: 用于其他参考信息

3. <properties> 结构:
   - 必须包含 <prophead> 定义列标题
   - 每个 <property> 包含: <proptype>, <propvalue>, <propdesc>

4. <table> 结构:
   - 必须包含 <tgroup> 指定列数
   - <thead> 包含表头
   - <tbody> 包含数据行

5. ID命名规范:
   - 推荐格式: ref_topic_name (如 ref_api_parameters)

示例:
<reference id="ref_config_options">
  <title>Configuration Options</title>
  <refbody>
    <properties>
      <prophead>
        <proptypehd>Option</proptypehd>
        <propvaluehd>Default</propvaluehd>
        <propdeschd>Description</propdeschd>
      </prophead>
      <property>
        <proptype>timeout</proptype>
        <propvalue>30</propvalue>
        <propdesc>Connection timeout in seconds</propdesc>
      </property>
    </properties>
  </refbody>
</reference>
"""
    
    def get_fix_suggestions(self, errors: List[str], content_type: str) -> List[str]:
        """
        根据错误生成修复建议
        
        Args:
            errors: 错误列表
            content_type: 内容类型
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        for error in errors:
            if "缺少必需元素" in error:
                suggestions.append(f"添加缺失的元素到结构化数据中")
            elif "steps数量不足" in error:
                suggestions.append("至少添加一个步骤到steps数组")
            elif "缺少必需字段: cmd" in error:
                suggestions.append("为每个step添加cmd字段，描述具体操作")
            elif "必须包含introduction或sections" in error:
                suggestions.append("添加introduction字段或至少一个section")
            else:
                suggestions.append(f"检查并修复: {error}")
        
        return suggestions


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("constraint_engine")
    
    engine = ConstraintEngine()
    
    # 测试获取约束
    print("\n" + "="*70)
    print("Task 约束规则")
    print("="*70)
    print(engine.generate_constraint_prompt('Task'))
    
    # 测试验证
    print("\n" + "="*70)
    print("验证测试")
    print("="*70)
    
    # 正确的Task结构
    valid_task = {
        'task_id': 'task_install_software',
        'title': 'Installing Software',
        'steps': [
            {'cmd': 'Download the installer'},
            {'cmd': 'Run the setup wizard'}
        ]
    }
    
    result = engine.validate_structure(valid_task, 'Task')
    print(f"\n有效结构: {result['is_valid']}")
    if result['errors']:
        print("错误:", result['errors'])
    
    # 无效的Task结构
    invalid_task = {
        'task_id': 'task_invalid',
        'title': 'Invalid Task',
        'steps': []  # 缺少步骤
    }
    
    result = engine.validate_structure(invalid_task, 'Task')
    print(f"\n无效结构: {result['is_valid']}")
    if result['errors']:
        print("错误:", result['errors'])
        print("建议:", engine.get_fix_suggestions(result['errors'], 'Task'))