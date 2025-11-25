"""
Step 3: 智能修复器
使用LLM对验证错误进行智能修复
"""
from typing import Dict, List, Any, Optional
import logging
import re
from lxml import etree

from src.utils.ai_service import AIService

logger = logging.getLogger(__name__)

class IntelligentRepairer:
    """智能修复器 - 使用LLM修复DITA错误"""
    
    def __init__(self, use_ai: bool = True):
        """
        初始化智能修复器
        
        Args:
            use_ai: 是否使用AI进行修复
        """
        self.use_ai = use_ai
        self.ai_service = AIService() if use_ai else None
        
        logger.info(f"✅ 智能修复器初始化完成 (AI: {use_ai})")
    
    def repair(
        self,
        dita_xml: str,
        errors: List[Dict],
        content_type: str = None
    ) -> Dict[str, Any]:
        """
        修复DITA XML
        
        Args:
            dita_xml: 原始DITA XML
            errors: 错误列表
            content_type: 内容类型（Task/Concept/Reference）
            
        Returns:
            修复结果
        """
        logger.info(f"🔧 开始智能修复 ({len(errors)} 个错误)...")
        
        result = {
            'success': False,
            'repaired_xml': dita_xml,
            'applied_fixes': [],
            'remaining_errors': errors.copy()
        }
        
        # 分类错误
        simple_errors, complex_errors = self._classify_errors(errors)
        
        # Step 1: 规则自动修复（简单错误）
        if simple_errors:
            logger.info(f"  [1/2] 规则修复 ({len(simple_errors)} 个简单错误)...")
            fixed_xml, applied = self._apply_rule_fixes(dita_xml, simple_errors)
            
            if applied:
                dita_xml = fixed_xml
                result['applied_fixes'].extend(applied)
                result['remaining_errors'] = [e for e in result['remaining_errors'] 
                                             if e not in simple_errors]
                logger.info(f"    ✓ 已修复 {len(applied)} 个错误")
        
        # Step 2: LLM智能修复（复杂错误）
        if complex_errors and self.use_ai:
            logger.info(f"  [2/2] LLM修复 ({len(complex_errors)} 个复杂错误)...")
            fixed_xml, applied = self._apply_llm_fixes(
                dita_xml, complex_errors, content_type
            )
            
            if applied:
                dita_xml = fixed_xml
                result['applied_fixes'].extend(applied)
                result['remaining_errors'] = [e for e in result['remaining_errors'] 
                                             if e not in complex_errors]
                logger.info(f"    ✓ 已修复 {len(applied)} 个错误")
        
        result['repaired_xml'] = dita_xml
        result['success'] = len(result['remaining_errors']) == 0
        
        if result['success']:
            logger.info(f"✅ 所有错误已修复")
        else:
            logger.warning(f"⚠️  仍有 {len(result['remaining_errors'])} 个错误未修复")
        
        return result
    
    def _classify_errors(self, errors: List[Dict]) -> tuple:
        """
        分类错误为简单/复杂
        
        Args:
            errors: 错误列表
            
        Returns:
            (simple_errors, complex_errors)
        """
        simple_errors = []
        complex_errors = []
        
        simple_types = [
            'InvalidIDFormat',
            'MissingDeclaration',
            'EmptyElement',
            'DuplicateID'
        ]
        
        for error in errors:
            error_type = error.get('type', '')
            
            if error_type in simple_types:
                simple_errors.append(error)
            else:
                complex_errors.append(error)
        
        return simple_errors, complex_errors
    
    def _apply_rule_fixes(
        self,
        dita_xml: str,
        errors: List[Dict]
    ) -> tuple:
        """
        应用规则修复
        
        Args:
            dita_xml: 原始XML
            errors: 简单错误列表
            
        Returns:
            (fixed_xml, applied_fixes)
        """
        fixed_xml = dita_xml
        applied_fixes = []
        
        for error in errors:
            error_type = error.get('type')
            
            # 修复无效ID格式
            if error_type == 'InvalidIDFormat':
                invalid_id = error.get('id')
                if invalid_id:
                    valid_id = self._fix_id_format(invalid_id)
                    fixed_xml = fixed_xml.replace(
                        f'id="{invalid_id}"',
                        f'id="{valid_id}"'
                    )
                    applied_fixes.append({
                        'type': error_type,
                        'action': f'修复ID: {invalid_id} → {valid_id}'
                    })
            
            # 添加缺失的XML声明
            elif error_type == 'MissingDeclaration':
                if not fixed_xml.strip().startswith('<?xml'):
                    fixed_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + fixed_xml
                    applied_fixes.append({
                        'type': error_type,
                        'action': '添加XML声明'
                    })
            
            # 移除空元素
            elif error_type == 'EmptyElement':
                element = error.get('element')
                if element:
                    # 使用lxml移除空元素
                    try:
                        tree = etree.fromstring(fixed_xml.encode('utf-8'))
                        for elem in tree.xpath(f'.//{element}'):
                            if not elem.text and len(elem) == 0:
                                elem.getparent().remove(elem)
                        
                        fixed_xml = etree.tostring(
                            tree,
                            encoding='unicode',
                            pretty_print=True
                        )
                        
                        # 添加XML声明
                        if not fixed_xml.startswith('<?xml'):
                            fixed_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + fixed_xml
                        
                        applied_fixes.append({
                            'type': error_type,
                            'action': f'移除空元素: {element}'
                        })
                    except Exception as e:
                        logger.warning(f"移除空元素失败: {e}")
            
            # 修复重复ID
            elif error_type == 'DuplicateID':
                duplicate_id = error.get('id')
                if duplicate_id:
                    # 为后续出现的重复ID添加后缀
                    fixed_xml = self._fix_duplicate_ids(fixed_xml, duplicate_id)
                    applied_fixes.append({
                        'type': error_type,
                        'action': f'修复重复ID: {duplicate_id}'
                    })
        
        return fixed_xml, applied_fixes
    
    def _apply_llm_fixes(
        self,
        dita_xml: str,
        errors: List[Dict],
        content_type: str
    ) -> tuple:
        """
        应用LLM修复
        
        Args:
            dita_xml: 原始XML
            errors: 复杂错误列表
            content_type: 内容类型
            
        Returns:
            (fixed_xml, applied_fixes)
        """
        # 构建修复提示词
        prompt = self._build_repair_prompt(dita_xml, errors, content_type)
        
        try:
            # 调用LLM
            response = self.ai_service.generate(prompt)
            
            # 提取修复后的XML
            fixed_xml = self._extract_xml_from_response(response)
            
            if fixed_xml and fixed_xml != dita_xml:
                applied_fixes = [{
                    'type': 'LLMRepair',
                    'action': f'LLM修复了 {len(errors)} 个错误',
                    'errors': [e.get('message', '') for e in errors]
                }]
                return fixed_xml, applied_fixes
            else:
                logger.warning("LLM修复未生成有效结果")
                return dita_xml, []
        
        except Exception as e:
            logger.error(f"❌ LLM修复失败: {e}")
            return dita_xml, []
    
    def _build_repair_prompt(
        self,
        dita_xml: str,
        errors: List[Dict],
        content_type: str
    ) -> str:
        """构建LLM修复提示词"""
        
        # 错误描述
        error_descriptions = []
        for i, error in enumerate(errors, 1):
            error_type = error.get('type', 'Unknown')
            message = error.get('message', '')
            element = error.get('element', '')
            
            error_descriptions.append(
                f"{i}. [{error_type}] {message}" +
                (f" (元素: {element})" if element else "")
            )
        
        errors_text = '\n'.join(error_descriptions)
        
        # 根据内容类型提供约束
        constraints = self._get_dita_constraints(content_type)
        
        prompt = f"""你是一个DITA XML修复专家。请修复以下DITA文档中的错误。

**原始DITA XML:**
```xml
{dita_xml}
```

**验证错误:**
{errors_text}

**DITA约束规则:**
{constraints}

**修复要求:**
- 只修复上述列出的错误
- 保持原有内容和结构不变
- 确保修复后的XML符合DITA标准
- 不要添加额外的解释，只输出修复后的完整XML

**输出格式:**
直接输出修复后的完整XML代码（包含<?xml声明），不要使用xml代码块标记。
"""
        return prompt

    def _get_dita_constraints(self, content_type: str) -> str:
        """获取DITA约束说明"""
        
        if content_type == 'Task' or content_type == 'task':
            return """
**Task类型约束:**
- 必需元素: <title>, <taskbody>
- <taskbody>必需包含: <steps>
- <steps>必需包含至少一个<step>
- 每个<step>必需包含: <cmd>
- 元素顺序: <title> → <shortdesc>? → <prolog>? → <taskbody>
- <taskbody>内顺序: <prereq>? → <context>? → <steps> → <result>? → <example>?
"""
        
        elif content_type == 'Concept' or content_type == 'concept':
            return """
**Concept类型约束:**
- 必需元素: <title>, <conbody>
- 元素顺序: <title> → <shortdesc>? → <prolog>? → <conbody>
- <conbody>可包含: <p>, <section>, <example>, <note>
"""
        
        elif content_type == 'Reference' or content_type == 'reference':
            return """
**Reference类型约束:**
- 必需元素: <title>, <refbody>
- 元素顺序: <title> → <shortdesc>? → <prolog>? → <refbody>
- <refbody>可包含: <section>, <properties>, <table>
"""
        
        else:
            return """
**通用DITA约束:**
- ID必须以字母开头，只能包含字母、数字、-_.
- ID必须唯一
- 所有元素必须正确闭合
"""

    def _extract_xml_from_response(self, response: str) -> Optional[str]:
        """从LLM响应中提取XML"""
        
        # 移除可能的markdown代码块标记
        xml = response.strip()
        xml = re.sub(r'^```xml\s*', '', xml)
        xml = re.sub(r'^```\s*', '', xml)
        xml = re.sub(r'\s*```$', '', xml)
        xml = xml.strip()
        
        # 验证是否为有效XML
        try:
            etree.fromstring(xml.encode('utf-8'))
            return xml
        except etree.XMLSyntaxError:
            logger.warning("从LLM响应中提取的XML无效")
            return None

    def _fix_id_format(self, invalid_id: str) -> str:
        """修复ID格式"""
        # 转小写
        valid_id = invalid_id.lower()
        
        # 移除特殊字符
        valid_id = re.sub(r'[^a-z0-9_\-\.]', '_', valid_id)
        
        # 移除首尾下划线
        valid_id = valid_id.strip('_')
        
        # 确保以字母开头
        if valid_id and not valid_id[0].isalpha():
            valid_id = 'id_' + valid_id
        
        return valid_id or 'unnamed'

    def _fix_duplicate_ids(self, xml: str, duplicate_id: str) -> str:
        """修复重复ID"""
        try:
            tree = etree.fromstring(xml.encode('utf-8'))
            
            # 查找所有使用该ID的元素
            elements = tree.xpath(f'//*[@id="{duplicate_id}"]')
            
            # 为后续出现的元素添加序号后缀
            for i, elem in enumerate(elements[1:], 2):
                new_id = f"{duplicate_id}_{i}"
                elem.set('id', new_id)
                logger.debug(f"重复ID修复: {duplicate_id} → {new_id}")
            
            # 转换回字符串
            fixed_xml = etree.tostring(tree, encoding='unicode', pretty_print=True)
            
            # 添加XML声明
            if not fixed_xml.startswith('<?xml'):
                fixed_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + fixed_xml
            
            return fixed_xml
        
        except Exception as e:
            logger.warning(f"修复重复ID失败: {e}")
            return xml


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("intelligent_repairer")
    
    repairer = IntelligentRepairer(use_ai=True)
    
    # 测试1: 简单错误修复
    print("\n" + "="*70)
    print("测试1: 修复简单错误（ID格式）")
    print("="*70)
    
    invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<task id="my task with spaces">
    <title>Test Task</title>
    <taskbody>
        <steps>
            <step><cmd>Do something</cmd></step>
        </steps>
    </taskbody>
</task>"""
    
    errors = [
        {
            'type': 'InvalidIDFormat',
            'message': 'ID "my task with spaces" 格式无效',
            'id': 'my task with spaces'
        }
    ]
    
    result = repairer.repair(invalid_xml, errors, 'Task')
    
    print(f"修复成功: {result['success']}")
    print(f"应用的修复: {len(result['applied_fixes'])}")
    
    for fix in result['applied_fixes']:
        print(f"  - {fix['action']}")
    
    if result['success']:
        print(f"\n修复后的XML:")
        print(result['repaired_xml'][:300] + "...")
    
    # 测试2: 复杂错误修复（需要LLM）
    print("\n" + "="*70)
    print("测试2: 修复复杂错误（缺少cmd）")
    print("="*70)
    
    invalid_xml2 = """<?xml version="1.0" encoding="UTF-8"?>
<task id="task_test">
    <title>Test Task</title>
    <taskbody>
        <steps>
            <step>
                <info>Missing cmd element</info>
            </step>
        </steps>
    </taskbody>
</task>"""
    
    errors2 = [
        {
            'type': 'MissingRequiredElement',
            'message': '第1个<step>缺少必需的<cmd>元素',
            'element': 'cmd'
        }
    ]
    
    result2 = repairer.repair(invalid_xml2, errors2, 'Task')
    
    print(f"修复成功: {result2['success']}")
    print(f"应用的修复: {len(result2['applied_fixes'])}")
    
    for fix in result2['applied_fixes']:
        print(f"  - {fix['action']}")
    
    if result2['applied_fixes']:
        print(f"\n修复后的XML:")
        print(result2['repaired_xml'])