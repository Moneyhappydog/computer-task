"""
Step 2: 自定义规则检查器
应用项目特定的质量规则
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
from lxml import etree

from .rules.base_rules import (
    BaseRule,
    DEFAULT_RULES,
    TitleLengthRule,
    NestingDepthRule,
    ShortdescLengthRule,
    StepCountRule,
    ImageReferenceRule,
    TerminologyConsistencyRule,
    CodeBlockFormatRule
)

logger = logging.getLogger(__name__)

class CustomRulesChecker:
    """自定义规则检查器"""
    
    def __init__(
        self,
        rules_config: Optional[Path] = None,
        image_dir: Optional[Path] = None
    ):
        """
        初始化自定义规则检查器
        
        Args:
            rules_config: 自定义规则配置文件路径
            image_dir: 图片目录（用于检查图片引用）
        """
        self.rules: List[BaseRule] = []
        self.config = {}
        self.image_dir = image_dir
        
        # 加载配置
        if rules_config and rules_config.exists():
            with open(rules_config, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"✓ 已加载自定义规则配置: {rules_config}")
        else:
            # 使用默认配置
            default_config = Path(__file__).parent / "rules" / "custom_rules.json"
            if default_config.exists():
                with open(default_config, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"✓ 已加载默认规则配置")
        
        # 初始化规则
        self._init_rules()
        
        logger.info(f"✅ 自定义规则检查器初始化完成 ({len(self.rules)} 条规则)")
    
    def _init_rules(self):
        """初始化规则集"""
        style_guide = self.config.get('style_guide', {})
        
        # 添加基础规则（使用配置中的参数）
        self.rules.append(TitleLengthRule(
            max_length=style_guide.get('title_max_length', 100)
        ))
        
        self.rules.append(NestingDepthRule(
            max_depth=style_guide.get('max_nesting_depth', 5)
        ))
        
        self.rules.append(ShortdescLengthRule(
            max_length=style_guide.get('shortdesc_max_length', 150)
        ))
        
        self.rules.append(StepCountRule(
            max_steps=style_guide.get('max_steps', 15)
        ))
        
        self.rules.append(CodeBlockFormatRule())
        
        # 添加术语一致性规则
        terminology = self.config.get('terminology', {})
        if terminology.get('replacements'):
            self.rules.append(TerminologyConsistencyRule(
                glossary=terminology['replacements']
            ))
        
        # 添加图片引用检查
        if self.image_dir:
            self.rules.append(ImageReferenceRule(
                image_dir=str(self.image_dir)
            ))
        
        logger.info(f"✓ 已初始化 {len(self.rules)} 条基础规则")
    
    def check(self, dita_xml: str, context: Dict = None) -> Dict[str, Any]:
        """
        执行自定义规则检查
        
        Args:
            dita_xml: DITA XML字符串
            context: 上下文信息
            
        Returns:
            检查结果
        """
        logger.info("🔍 开始自定义规则检查...")
        
        result = {
            'passed': [],
            'failed': [],
            'total_issues': 0,
            'issues_by_severity': {
                'error': 0,
                'warning': 0,
                'info': 0
            }
        }
        
        try:
            # 解析XML
            tree = etree.fromstring(dita_xml.encode('utf-8'))
            
            # 执行每条规则
            for rule in self.rules:
                logger.debug(f"  检查规则: {rule.name}")
                
                issues = rule.check(tree, context)
                
                if issues:
                    result['failed'].append({
                        'rule': rule.name,
                        'description': rule.description,
                        'issues': issues
                    })
                    
                    # 统计严重程度
                    for issue in issues:
                        severity = issue.get('severity', rule.severity)
                        result['issues_by_severity'][severity] = \
                            result['issues_by_severity'].get(severity, 0) + 1
                    
                    result['total_issues'] += len(issues)
                    logger.debug(f"    ✗ 发现 {len(issues)} 个问题")
                else:
                    result['passed'].append({
                        'rule': rule.name,
                        'description': rule.description
                    })
                    logger.debug(f"    ✓ 通过")
            
            # 汇总
            logger.info(f"✅ 自定义规则检查完成")
            logger.info(f"   通过: {len(result['passed'])} 条")
            logger.info(f"   失败: {len(result['failed'])} 条")
            logger.info(f"   问题总数: {result['total_issues']}")
            
            if result['total_issues'] > 0:
                logger.info(f"   错误: {result['issues_by_severity']['error']}")
                logger.info(f"   警告: {result['issues_by_severity']['warning']}")
                logger.info(f"   提示: {result['issues_by_severity']['info']}")
            
        except etree.XMLSyntaxError as e:
            logger.error(f"❌ XML解析失败: {e}")
            result['failed'].append({
                'rule': 'xml_parse',
                'description': 'XML解析',
                'issues': [{
                    'severity': 'error',
                    'message': str(e)
                }]
            })
        
        except Exception as e:
            logger.error(f"❌ 规则检查失败: {e}")
            result['failed'].append({
                'rule': 'unknown_error',
                'description': '未知错误',
                'issues': [{
                    'severity': 'error',
                    'message': str(e)
                }]
            })
        
        return result
    
    def add_rule(self, rule: BaseRule):
        """添加自定义规则"""
        self.rules.append(rule)
        logger.info(f"✓ 已添加规则: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"✓ 已移除规则: {rule_name}")
    
    def get_rule(self, rule_name: str) -> Optional[BaseRule]:
        """获取指定规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def list_rules(self) -> List[Dict]:
        """列出所有规则"""
        return [
            {
                'name': rule.name,
                'description': rule.description,
                'severity': rule.severity
            }
            for rule in self.rules
        ]


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("custom_rules_checker")
    
    checker = CustomRulesChecker()
    
    # 显示规则列表
    print("\n" + "="*70)
    print("已加载的规则:")
    print("="*70)
    
    for rule_info in checker.list_rules():
        print(f"\n{rule_info['name']}")
        print(f"  描述: {rule_info['description']}")
        print(f"  严重程度: {rule_info['severity']}")
    
    # 测试检查
    print("\n" + "="*70)
    print("测试检查:")
    print("="*70)
    
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<task id="test">
  <title>This is a very very very very very very very very very very very very very very very very long title that exceeds the limit</title>
  <taskbody>
    <steps>
      <step><cmd>Step 1</cmd></step>
      <step><cmd>Step 2</cmd></step>
      <step><cmd>Step 3</cmd></step>
      <step><cmd>Step 4</cmd></step>
      <step><cmd>Step 5</cmd></step>
      <step><cmd>Step 6</cmd></step>
      <step><cmd>Step 7</cmd></step>
      <step><cmd>Step 8</cmd></step>
      <step><cmd>Step 9</cmd></step>
      <step><cmd>Step 10</cmd></step>
      <step><cmd>Step 11</cmd></step>
      <step><cmd>Step 12</cmd></step>
      <step><cmd>Step 13</cmd></step>
      <step><cmd>Step 14</cmd></step>
      <step><cmd>Step 15</cmd></step>
      <step><cmd>Step 16</cmd></step>
    </steps>
  </taskbody>
</task>"""
    
    result = checker.check(test_xml)
    
    print(f"\n检查结果:")
    print(f"  通过规则: {len(result['passed'])}")
    print(f"  失败规则: {len(result['failed'])}")
    print(f"  问题总数: {result['total_issues']}")
    
    if result['failed']:
        print(f"\n失败的规则:")
        for failed_rule in result['failed']:
            print(f"\n  {failed_rule['rule']}:")
            for issue in failed_rule['issues']:
                print(f"    - [{issue['severity']}] {issue['message']}")
                if 'suggestion' in issue:
                    print(f"      建议: {issue['suggestion']}")