"""
Step 4: 最终验证循环
重复验证和修复直到通过或达到最大迭代次数
"""
from typing import Dict, List, Any
import logging

from .dita_ot_validator import DITAOTValidator
from .intelligent_repairer import IntelligentRepairer

logger = logging.getLogger(__name__)

class ValidationLoop:
    """验证-修复循环"""
    
    def __init__(
        self,
        max_iterations: int = 3,
        use_dita_ot: bool = False,
        use_ai_repair: bool = True
    ):
        """
        初始化验证循环
        
        Args:
            max_iterations: 最大迭代次数
            use_dita_ot: 是否使用DITA-OT验证
            use_ai_repair: 是否使用AI修复
        """
        self.max_iterations = max_iterations
        
        # 初始化组件
        self.validator = DITAOTValidator(use_dita_ot=use_dita_ot)
        self.repairer = IntelligentRepairer(use_ai=use_ai_repair)
        
        logger.info(f"✅ 验证循环初始化完成 (最大迭代: {max_iterations})")
    
    def run(
        self,
        dita_xml: str,
        content_type: str = None
    ) -> Dict[str, Any]:
        """
        运行验证-修复循环
        
        Args:
            dita_xml: DITA XML字符串
            content_type: 内容类型
            
        Returns:
            循环结果
        """
        logger.info("="*70)
        logger.info("🔄 开始验证-修复循环...")
        logger.info("="*70)
        
        result = {
            'success': False,
            'final_xml': dita_xml,
            'iterations': 0,
            'validation_history': [],
            'repair_history': [],
            'final_validation': None
        }
        
        current_xml = dita_xml
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"🔁 迭代 {iteration}/{self.max_iterations}")
            logger.info(f"{'='*70}")
            
            # Step 1: 验证
            logger.info(f"\n  [验证] 检查DITA标准...")
            validation_result = self.validator.validate(current_xml, content_type)
            
            result['validation_history'].append({
                'iteration': iteration,
                'result': validation_result
            })
            
            # 显示验证结果
            if validation_result['is_valid']:
                logger.info(f"  ✅ 验证通过！")
                result['success'] = True
                result['final_xml'] = current_xml
                result['iterations'] = iteration
                result['final_validation'] = validation_result
                break
            else:
                error_count = len(validation_result['errors'])
                logger.warning(f"  ⚠️  发现 {error_count} 个错误")
                
                # 显示前3个错误
                for i, error in enumerate(validation_result['errors'][:3], 1):
                    logger.warning(f"    {i}. {error.get('message', 'Unknown error')}")
                
                if error_count > 3:
                    logger.warning(f"    ... 还有 {error_count - 3} 个错误")
            
            # Step 2: 修复（如果不是最后一次迭代）
            if iteration < self.max_iterations:
                logger.info(f"\n  [修复] 尝试修复错误...")
                
                repair_result = self.repairer.repair(
                    current_xml,
                    validation_result['errors'],
                    content_type
                )
                
                result['repair_history'].append({
                    'iteration': iteration,
                    'result': repair_result
                })
                
                if repair_result['success']:
                    logger.info(f"  ✅ 所有错误已修复")
                    current_xml = repair_result['repaired_xml']
                elif repair_result['applied_fixes']:
                    fixed_count = len(repair_result['applied_fixes'])
                    remaining = len(repair_result['remaining_errors'])
                    logger.info(f"  ✓ 已修复 {fixed_count} 个错误")
                    logger.warning(f"  ⚠️  仍有 {remaining} 个错误未修复")
                    current_xml = repair_result['repaired_xml']
                else:
                    logger.warning(f"  ⚠️  无法自动修复错误")
                    # 没有修复，提前退出循环
                    break
            else:
                logger.info(f"\n  已达到最大迭代次数")
        
        # 最终状态
        result['final_xml'] = current_xml
        result['iterations'] = iteration
        
        if not result['success']:
            # 最后一次验证
            final_validation = self.validator.validate(current_xml, content_type)
            result['final_validation'] = final_validation
        
        # 汇总
        logger.info("\n" + "="*70)
        if result['success']:
            logger.info("✅ 验证-修复循环成功完成")
            logger.info(f"   迭代次数: {result['iterations']}")
        else:
            logger.warning("⚠️  验证-修复循环未能通过所有检查")
            logger.warning(f"   迭代次数: {result['iterations']}")
            if result['final_validation']:
                error_count = len(result['final_validation']['errors'])
                logger.warning(f"   剩余错误: {error_count}")
        logger.info("="*70)
        
        return result
    
    def get_summary(self, result: Dict) -> str:
        """
        生成循环摘要
        
        Args:
            result: 循环结果
            
        Returns:
            摘要文本
        """
        lines = []
        lines.append("验证-修复循环摘要")
        lines.append("="*70)
        lines.append(f"状态: {'成功 ✅' if result['success'] else '失败 ❌'}")
        lines.append(f"迭代次数: {result['iterations']}/{self.max_iterations}")
        lines.append("")
        
        # 每次迭代的情况
        lines.append("迭代历史:")
        for i, val_history in enumerate(result['validation_history'], 1):
            val_result = val_history['result']
            error_count = len(val_result['errors'])
            
            lines.append(f"\n  迭代 {i}:")
            lines.append(f"    验证: {error_count} 个错误")
            
            # 修复历史
            if i <= len(result['repair_history']):
                rep_history = result['repair_history'][i-1]
                rep_result = rep_history['result']
                fixed_count = len(rep_result['applied_fixes'])
                
                if fixed_count > 0:
                    lines.append(f"    修复: {fixed_count} 个")
        
        # 最终状态
        if result['final_validation']:
            final_errors = len(result['final_validation']['errors'])
            lines.append(f"\n最终错误数: {final_errors}")
        
        return '\n'.join(lines)


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("validation_loop")
    
    loop = ValidationLoop(
        max_iterations=3,
        use_dita_ot=False,
        use_ai_repair=True
    )
    
    # 测试1: 可修复的错误
    print("\n" + "="*70)
    print("测试1: 可修复的错误")
    print("="*70)
    
    fixable_xml = """<?xml version="1.0" encoding="UTF-8"?>
<task id="my invalid id">
  <title>Test Task</title>
  <taskbody>
    <steps>
      <step><cmd>Do something</cmd></step>
    </steps>
  </taskbody>
</task>"""
    
    result = loop.run(fixable_xml, 'Task')
    
    print("\n" + loop.get_summary(result))
    
    if result['success']:
        print(f"\n最终XML:")
        print(result['final_xml'][:500])
    
    # 测试2: 复杂错误
    print("\n" + "="*70)
    print("测试2: 需要LLM修复的错误")
    print("="*70)
    
    complex_xml = """<?xml version="1.0" encoding="UTF-8"?>
<task id="task_test">
  <title>Test Task</title>
  <taskbody>
    <steps>
      <step>
        <info>Step without cmd</info>
      </step>
    </steps>
  </taskbody>
</task>"""
    
    result2 = loop.run(complex_xml, 'Task')
    
    print("\n" + loop.get_summary(result2))