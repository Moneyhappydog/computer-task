"""
Step 1: DITA-OT标准验证器
使用DITA Open Toolkit进行官方标准验证
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import subprocess
import json
import tempfile
import re
from lxml import etree

logger = logging.getLogger(__name__)

class DITAOTValidator:
    """DITA-OT标准验证器"""
    
    def __init__(
        self,
        dita_ot_dir: Optional[Path] = None,
        use_dita_ot: bool = False  # 默认关闭，因为需要安装DITA-OT
    ):
        """
        初始化DITA-OT验证器
        
        Args:
            dita_ot_dir: DITA-OT安装目录
            use_dita_ot: 是否使用真实的DITA-OT（需要预先安装）
        """
        self.use_dita_ot = use_dita_ot
        self.dita_ot_dir = dita_ot_dir
        
        if use_dita_ot:
            if not dita_ot_dir or not dita_ot_dir.exists():
                logger.warning("⚠️  DITA-OT目录未配置或不存在，将使用内置验证")
                self.use_dita_ot = False
            else:
                self.dita_cmd = dita_ot_dir / "bin" / "dita.bat"
                if not self.dita_cmd.exists():
                    logger.warning("⚠️  DITA命令未找到，将使用内置验证")
                    self.use_dita_ot = False
        
        logger.info(f"✅ DITA-OT验证器初始化完成 (使用DITA-OT: {self.use_dita_ot})")
    
    def validate(self, dita_xml: str, content_type: str = None) -> Dict[str, Any]:
        """
        验证DITA XML
        
        Args:
            dita_xml: DITA XML字符串
            content_type: 内容类型（Task/Concept/Reference）
            
        Returns:
            验证结果字典
        """
        logger.info("🔍 开始DITA标准验证...")
        
        if self.use_dita_ot:
            return self._validate_with_dita_ot(dita_xml)
        else:
            return self._validate_builtin(dita_xml, content_type)
    
    def _validate_with_dita_ot(self, dita_xml: str) -> Dict[str, Any]:
        """使用真实的DITA-OT进行验证"""
        logger.info("🔧 使用DITA-OT进行验证...")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.dita',
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(dita_xml)
            tmp_path = Path(tmp_file.name)
        
        try:
            # 调用DITA-OT验证命令
            cmd = [
                str(self.dita_cmd),
                '--input', str(tmp_path),
                '--format', 'html5',  # 需要指定输出格式
                '--output', str(tmp_path.parent / 'output'),
                '--debug'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 解析输出
            errors = self._parse_dita_ot_output(result.stderr)
            
            return {
                'is_valid': result.returncode == 0,
                'errors': errors,
                'warnings': [],
                'validator': 'DITA-OT',
                'raw_output': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            logger.error("❌ DITA-OT验证超时")
            return {
                'is_valid': False,
                'errors': [{'type': 'Timeout', 'message': 'DITA-OT validation timeout'}],
                'warnings': [],
                'validator': 'DITA-OT'
            }
        
        except Exception as e:
            logger.error(f"❌ DITA-OT验证失败: {e}")
            return {
                'is_valid': False,
                'errors': [{'type': 'Error', 'message': str(e)}],
                'warnings': [],
                'validator': 'DITA-OT'
            }
        
        finally:
            # 清理临时文件
            if tmp_path.exists():
                tmp_path.unlink()
    
    def _parse_dita_ot_output(self, output: str) -> List[Dict]:
        """解析DITA-OT输出的错误信息"""
        errors = []
        
        # DITA-OT错误格式通常为：
        # [ERROR] file.dita:15:8: Element 'step' is missing required child 'cmd'
        error_pattern = r'\[ERROR\]\s+(.+?):(\d+):(\d+):\s+(.+)'
        
        for match in re.finditer(error_pattern, output):
            errors.append({
                'type': 'ValidationError',
                'file': match.group(1),
                'line': int(match.group(2)),
                'column': int(match.group(3)),
                'message': match.group(4)
            })
        
        return errors
    
    def _validate_builtin(self, dita_xml: str, content_type: str) -> Dict[str, Any]:
        """使用内置规则进行验证（不依赖DITA-OT）"""
        logger.info("🔧 使用内置规则进行验证...")
        
        errors = []
        warnings = []
        
        try:
            # 解析XML
            tree = etree.fromstring(dita_xml.encode('utf-8'))
            root_tag = tree.tag
            
            # 检测内容类型
            if content_type is None:
                if root_tag in ['task', 'concept', 'reference']:
                    content_type = root_tag.capitalize()
                else:
                    errors.append({
                        'type': 'InvalidRootElement',
                        'message': f'根元素必须是task/concept/reference之一，实际为: {root_tag}'
                    })
                    content_type = 'Unknown'
            
            # 根据类型进行验证
            if content_type == 'Task' or root_tag == 'task':
                task_errors = self._validate_task_structure(tree)
                errors.extend(task_errors)
            
            elif content_type == 'Concept' or root_tag == 'concept':
                concept_errors = self._validate_concept_structure(tree)
                errors.extend(concept_errors)
            
            elif content_type == 'Reference' or root_tag == 'reference':
                reference_errors = self._validate_reference_structure(tree)
                errors.extend(reference_errors)
            
            # 通用验证
            common_errors, common_warnings = self._validate_common_rules(tree)
            errors.extend(common_errors)
            warnings.extend(common_warnings)
            
        except etree.XMLSyntaxError as e:
            errors.append({
                'type': 'XMLSyntaxError',
                'message': str(e),
                'line': e.lineno if hasattr(e, 'lineno') else None
            })
        
        except Exception as e:
            errors.append({
                'type': 'UnknownError',
                'message': str(e)
            })
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("✅ DITA标准验证通过")
        else:
            logger.warning(f"⚠️  发现 {len(errors)} 个错误")
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'validator': 'Builtin'
        }
    
    def _validate_task_structure(self, tree: etree._Element) -> List[Dict]:
        """验证Task结构"""
        errors = []
        
        # 检查必需元素：title
        if tree.find('title') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<task> 必须包含 <title> 元素',
                'element': 'title'
            })
        
        # 检查必需元素：taskbody
        taskbody = tree.find('taskbody')
        if taskbody is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<task> 必须包含 <taskbody> 元素',
                'element': 'taskbody'
            })
        else:
            # 检查taskbody内的元素顺序
            order_errors = self._check_element_order(
                taskbody,
                ['prereq', 'context', 'steps', 'result', 'example', 'postreq']
            )
            errors.extend(order_errors)
            
            # 检查必需元素：steps
            steps = taskbody.find('steps')
            if steps is None:
                errors.append({
                    'type': 'MissingRequiredElement',
                    'message': '<taskbody> 必须包含 <steps> 元素',
                    'element': 'steps'
                })
            else:
                # 检查steps至少包含一个step
                step_list = steps.findall('step')
                if len(step_list) == 0:
                    errors.append({
                        'type': 'EmptyElement',
                        'message': '<steps> 必须至少包含一个 <step>',
                        'element': 'steps'
                    })
                
                # 检查每个step必须包含cmd
                for i, step in enumerate(step_list, 1):
                    if step.find('cmd') is None:
                        errors.append({
                            'type': 'MissingRequiredElement',
                            'message': f'第 {i} 个 <step> 缺少必需的 <cmd> 元素',
                            'element': f'step[{i}]/cmd'
                        })
        
        # 检查元素顺序：title → shortdesc? → prolog? → taskbody
        root_order_errors = self._check_element_order(
            tree,
            ['title', 'shortdesc', 'prolog', 'taskbody', 'related-links']
        )
        errors.extend(root_order_errors)
        
        return errors
    
    def _validate_concept_structure(self, tree: etree._Element) -> List[Dict]:
        """验证Concept结构"""
        errors = []
        
        # 检查必需元素
        if tree.find('title') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<concept> 必须包含 <title> 元素',
                'element': 'title'
            })
        
        if tree.find('conbody') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<concept> 必须包含 <conbody> 元素',
                'element': 'conbody'
            })
        
        # 检查元素顺序
        root_order_errors = self._check_element_order(
            tree,
            ['title', 'shortdesc', 'prolog', 'conbody', 'related-links']
        )
        errors.extend(root_order_errors)
        
        return errors
    
    def _validate_reference_structure(self, tree: etree._Element) -> List[Dict]:
        """验证Reference结构"""
        errors = []
        
        # 检查必需元素
        if tree.find('title') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<reference> 必须包含 <title> 元素',
                'element': 'title'
            })
        
        if tree.find('refbody') is None:
            errors.append({
                'type': 'MissingRequiredElement',
                'message': '<reference> 必须包含 <refbody> 元素',
                'element': 'refbody'
            })
        
        # 检查元素顺序
        root_order_errors = self._check_element_order(
            tree,
            ['title', 'shortdesc', 'prolog', 'refbody', 'related-links']
        )
        errors.extend(root_order_errors)
        
        return errors
    
    def _validate_common_rules(self, tree: etree._Element) -> tuple:
        """验证通用规则"""
        errors = []
        warnings = []
        
        # 检查ID唯一性
        id_map = {}
        for elem in tree.xpath('//*[@id]'):
            elem_id = elem.get('id')
            if elem_id in id_map:
                errors.append({
                    'type': 'DuplicateID',
                    'message': f'ID "{elem_id}" 重复使用',
                    'id': elem_id
                })
            else:
                id_map[elem_id] = elem
        
        # 检查ID格式（必须以字母开头）
        id_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_\-\.]*$')
        for elem in tree.xpath('//*[@id]'):
            elem_id = elem.get('id')
            if not id_pattern.match(elem_id):
                errors.append({
                    'type': 'InvalidIDFormat',
                    'message': f'ID "{elem_id}" 格式无效（必须以字母开头，只能包含字母、数字、-_. ）',
                    'id': elem_id
                })
        
        # 检查空元素
        for elem in tree.iter():
            # 跳过允许为空的元素
            if elem.tag in ['shortdesc', 'note', 'info', 'stepresult']:
                continue
            
            # 检查是否完全为空
            if not elem.text and len(elem) == 0:
                warnings.append({
                    'type': 'EmptyElement',
                    'message': f'元素 <{elem.tag}> 为空',
                    'element': elem.tag
                })
        
        # 检查DOCTYPE声明
        # 注意：lxml解析后会丢失DOCTYPE，这里只是示例
        
        return errors, warnings
    
    def _check_element_order(
        self,
        parent: etree._Element,
        expected_order: List[str]
    ) -> List[Dict]:
        """
        检查子元素顺序
        
        Args:
            parent: 父元素
            expected_order: 期望的子元素顺序
            
        Returns:
            错误列表
        """
        errors = []
        
        # 获取实际出现的元素及其位置
        actual_elements = [(child.tag, i) for i, child in enumerate(parent)]
        
        # 检查顺序
        last_index = -1
        for tag in expected_order:
            # 跳过可选元素标记（如 'prereq?'）
            tag_clean = tag.rstrip('?')
            
            # 查找该标签的位置
            positions = [i for t, i in actual_elements if t == tag_clean]
            
            if positions:
                first_pos = positions[0]
                if first_pos < last_index:
                    errors.append({
                        'type': 'ElementOrderError',
                        'message': f'元素 <{tag_clean}> 的顺序不正确',
                        'element': tag_clean,
                        'expected_order': expected_order
                    })
                last_index = first_pos
        
        return errors


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("dita_ot_validator")
    
    validator = DITAOTValidator(use_dita_ot=False)
    
    # 测试1: 有效的Task
    print("\n" + "="*70)
    print("测试1: 有效的Task XML")
    print("="*70)
    
    valid_task = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="task_example">
  <title>Example Task</title>
  <taskbody>
    <prereq>Prerequisites here</prereq>
    <steps>
      <step>
        <cmd>Do something</cmd>
        <info>Additional information</info>
      </step>
    </steps>
    <result>Expected result</result>
  </taskbody>
</task>"""
    
    result = validator.validate(valid_task, 'Task')
    print(f"有效: {result['is_valid']}")
    print(f"错误数: {len(result['errors'])}")
    print(f"警告数: {len(result['warnings'])}")
    
    # 测试2: 无效的Task（缺少cmd）
    print("\n" + "="*70)
    print("测试2: 无效的Task XML")
    print("="*70)
    
    invalid_task = """<?xml version="1.0" encoding="UTF-8"?>
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
    
    result = validator.validate(invalid_task, 'Task')
    print(f"有效: {result['is_valid']}")
    print(f"错误数: {len(result['errors'])}")
    if result['errors']:
        print("\n错误列表:")
        for error in result['errors']:
            print(f"  - {error['type']}: {error['message']}")