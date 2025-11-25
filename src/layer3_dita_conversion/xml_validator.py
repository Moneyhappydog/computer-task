"""
Step 5: XML验证器
使用lxml进行XML良构性验证和基础检查
"""
from typing import Dict, List, Any, Optional
import logging
from lxml import etree
import re

logger = logging.getLogger(__name__)

class XMLValidator:
    """XML验证器 - 基于lxml的快速验证"""
    
    def __init__(self):
        """初始化XML验证器"""
        self.parser = etree.XMLParser(
            remove_blank_text=True,
            resolve_entities=False,
            no_network=True
        )
        
        logger.info("✅ XML验证器初始化完成")
    
    def validate(self, xml_content: str) -> Dict[str, Any]:
        """
        验证XML
        
        Args:
            xml_content: XML字符串
            
        Returns:
            验证结果字典
        """
        logger.info("🔍 开始XML验证...")
        
        result = {
            'is_wellformed': False,
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        # Step 1: 检查基本格式
        basic_check = self._check_basic_format(xml_content)
        result['warnings'].extend(basic_check['warnings'])
        
        # Step 2: 解析XML
        try:
            tree = etree.fromstring(xml_content.encode('utf-8'), self.parser)
            result['is_wellformed'] = True
            result['info']['root_element'] = tree.tag
            result['info']['element_count'] = len(tree.xpath('//*'))
            
            logger.info("✓ XML格式良好")
            
        except etree.XMLSyntaxError as e:
            result['errors'].append({
                'type': 'XMLSyntaxError',
                'message': str(e),
                'line': e.lineno if hasattr(e, 'lineno') else None,
                'column': e.offset if hasattr(e, 'offset') else None
            })
            logger.error(f"❌ XML语法错误: {e}")
            return result
        
        except Exception as e:
            result['errors'].append({
                'type': 'UnknownError',
                'message': str(e)
            })
            logger.error(f"❌ 未知错误: {e}")
            return result
        
        # Step 3: 内容验证
        content_check = self._check_content(tree)
        result['errors'].extend(content_check['errors'])
        result['warnings'].extend(content_check['warnings'])
        
        # Step 4: DITA特定检查
        dita_check = self._check_dita_specifics(tree)
        result['errors'].extend(dita_check['errors'])
        result['warnings'].extend(dita_check['warnings'])
        
        # 判断是否有效
        result['is_valid'] = result['is_wellformed'] and len(result['errors']) == 0
        
        if result['is_valid']:
            logger.info("✅ XML验证通过")
        else:
            logger.warning(f"⚠️  发现 {len(result['errors'])} 个错误")
        
        return result
    
    def _check_basic_format(self, xml_content: str) -> Dict:
        """检查基本格式"""
        warnings = []
        
        # 检查XML声明
        if not xml_content.strip().startswith('<?xml'):
            warnings.append({
                'type': 'MissingDeclaration',
                'message': '缺少XML声明',
                'suggestion': '添加: <?xml version="1.0" encoding="UTF-8"?>'
            })
        
        # 检查编码声明
        if '<?xml' in xml_content and 'encoding' not in xml_content.split('\n')[0]:
            warnings.append({
                'type': 'MissingEncoding',
                'message': 'XML声明缺少encoding属性',
                'suggestion': '添加: encoding="UTF-8"'
            })
        
        # 检查DOCTYPE
        if '<!DOCTYPE' not in xml_content:
            warnings.append({
                'type': 'MissingDoctype',
                'message': '缺少DOCTYPE声明',
                'suggestion': 'DITA文档应包含DOCTYPE声明'
            })
        
        return {'warnings': warnings}
    
    def _check_content(self, tree: etree._Element) -> Dict:
        """检查内容规范"""
        errors = []
        warnings = []
        
        # 检查空元素
        for elem in tree.iter():
            # 跳过允许为空的元素
            if elem.tag in ['shortdesc', 'note', 'info']:
                continue
            
            # 检查是否完全为空（无文本、无子元素、无尾部文本）
            if (not elem.text or not elem.text.strip()) and \
               len(elem) == 0 and \
               (not elem.tail or not elem.tail.strip()):
                
                # 某些元素允许为空
                if elem.tag not in ['br', 'hr', 'img']:
                    warnings.append({
                        'type': 'EmptyElement',
                        'message': f'元素 <{elem.tag}> 为空',
                        'element': elem.tag
                    })
        
        # 检查ID唯一性
        id_counts = {}
        for elem in tree.xpath('//*[@id]'):
            elem_id = elem.get('id')
            id_counts[elem_id] = id_counts.get(elem_id, 0) + 1
        
        for elem_id, count in id_counts.items():
            if count > 1:
                errors.append({
                    'type': 'DuplicateID',
                    'message': f'ID "{elem_id}" 重复出现 {count} 次',
                    'id': elem_id
                })
        
        # 检查ID格式
        id_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_\-\.]*$')
        for elem in tree.xpath('//*[@id]'):
            elem_id = elem.get('id')
            if not id_pattern.match(elem_id):
                errors.append({
                    'type': 'InvalidIDFormat',
                    'message': f'ID "{elem_id}" 格式不符合规范',
                    'id': elem_id,
                    'suggestion': 'ID必须以字母开头，只能包含字母、数字、下划线、连字符、点号'
                })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_dita_specifics(self, tree: etree._Element) -> Dict:
        """检查DITA特定规则"""
        errors = []
        warnings = []
        
        root_tag = tree.tag
        
        # Task特定检查
        if root_tag == 'task':
            task_check = self._check_task_structure(tree)
            errors.extend(task_check['errors'])
            warnings.extend(task_check['warnings'])
        
        # Concept特定检查
        elif root_tag == 'concept':
            concept_check = self._check_concept_structure(tree)
            errors.extend(concept_check['errors'])
            warnings.extend(concept_check['warnings'])
        
        # Reference特定检查
        elif root_tag == 'reference':
            reference_check = self._check_reference_structure(tree)
            errors.extend(reference_check['errors'])
            warnings.extend(reference_check['warnings'])
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_task_structure(self, tree: etree._Element) -> Dict:
        """检查Task结构"""
        errors = []
        warnings = []
        
        # 检查必需元素
        if tree.find('title') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<task> 缺少必需的 <title> 元素'
            })
        
        taskbody = tree.find('taskbody')
        if taskbody is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<task> 缺少必需的 <taskbody> 元素'
            })
        else:
            # 检查steps
            steps = taskbody.find('steps')
            if steps is None:
                errors.append({
                    'type': 'MissingRequiredElement',
                    'message': '<taskbody> 缺少必需的 <steps> 元素'
                })
            else:
                step_list = steps.findall('step')
                if len(step_list) == 0:
                    errors.append({
                        'type': 'EmptySteps',
                        'message': '<steps> 必须至少包含一个 <step>'
                    })
                
                # 检查每个step的cmd
                for i, step in enumerate(step_list, 1):
                    if step.find('cmd') is None:
                        errors.append({
                            'type': 'MissingRequiredElement',
                            'message': f'第 {i} 个 <step> 缺少必需的 <cmd> 元素'
                        })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_concept_structure(self, tree: etree._Element) -> Dict:
        """检查Concept结构"""
        errors = []
        warnings = []
        
        # 检查必需元素
        if tree.find('title') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<concept> 缺少必需的 <title> 元素'
            })
        
        if tree.find('conbody') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<concept> 缺少必需的 <conbody> 元素'
            })
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_reference_structure(self, tree: etree._Element) -> Dict:
        """检查Reference结构"""
        errors = []
        warnings = []
        
        # 检查必需元素
        if tree.find('title') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<reference> 缺少必需的 <title> 元素'
            })
        
        if tree.find('refbody') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<reference> 缺少必需的 <refbody> 元素'
            })
        
        return {'errors': errors, 'warnings': warnings}
    
    def try_fix(self, xml_content: str, errors: List[Dict]) -> Optional[str]:
        """
        尝试自动修复简单错误
        
        Args:
            xml_content: 原始XML
            errors: 错误列表
            
        Returns:
            修复后的XML，如果无法修复则返回None
        """
        logger.info("🔧 尝试自动修复...")
        
        fixed_xml = xml_content
        fix_count = 0
        
        for error in errors:
            error_type = error.get('type')
            
            # 修复缺失XML声明
            if error_type == 'MissingDeclaration':
                if not fixed_xml.strip().startswith('<?xml'):
                    fixed_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + fixed_xml
                    fix_count += 1
                    logger.info("✓ 已添加XML声明")
            
            # 修复ID格式
            elif error_type == 'InvalidIDFormat':
                invalid_id = error.get('id')
                # 生成有效ID
                valid_id = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', invalid_id)
                if valid_id and not valid_id[0].isalpha():
                    valid_id = 'id_' + valid_id
                
                fixed_xml = fixed_xml.replace(f'id="{invalid_id}"', f'id="{valid_id}"')
                fix_count += 1
                logger.info(f"✓ 已修复ID: {invalid_id} → {valid_id}")
        
        if fix_count > 0:
            logger.info(f"✅ 自动修复了 {fix_count} 个错误")
            return fixed_xml
        else:
            logger.info("ℹ️  没有可自动修复的错误")
            return None


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    import json
    
    setup_logger("xml_validator")
    
    validator = XMLValidator()
    
    # 测试1: 有效的XML
    print("\n" + "="*70)
    print("测试1: 有效的Task XML")
    print("="*70)
    
    valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="task_example">
  <title>Example Task</title>
  <taskbody>
    <steps>
      <step>
        <cmd>Do something</cmd>
      </step>
    </steps>
  </taskbody>
</task>"""
    
    result = validator.validate(valid_xml)
    print(f"是否良构: {result['is_wellformed']}")
    print(f"是否有效: {result['is_valid']}")
    print(f"错误数: {len(result['errors'])}")
    print(f"警告数: {len(result['warnings'])}")
    
    # 测试2: 无效的XML
    print("\n" + "="*70)
    print("测试2: 无效的Task XML (缺少cmd)")
    print("="*70)
    
    invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<task id="task_invalid">
  <title>Invalid Task</title>
  <taskbody>
    <steps>
      <step>
        <info>Missing cmd element</info>
      </step>
    </steps>
  </taskbody>
</task>"""
    
    result = validator.validate(invalid_xml)
    print(f"是否良构: {result['is_wellformed']}")
    print(f"是否有效: {result['is_valid']}")
    if result['errors']:
        print("\n错误:")
        for error in result['errors']:
            print(f"  - {error['type']}: {error['message']}")