"""
Layer 3 主转换器
协调所有步骤，将分类后的内容转换为DITA XML
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime

from .template_selector import TemplateSelector
from .content_structurer import ContentStructurer
from .constraint_engine import ConstraintEngine
from .template_renderer import TemplateRenderer
from .xml_validator import XMLValidator
from .errors import ErrorHandler, DITAConversionError, ConverterError, StructureError, TemplateError, ConstraintError

logger = logging.getLogger(__name__)

class DITAConverter:
    """DITA转换器 - Layer 3 主控制器"""
    
    def __init__(
        self,
        use_ai: bool = True,
        templates_dir: Optional[Path] = None,
        max_fix_iterations: int = 3
    ):
        """
        初始化DITA转换器
        
        Args:
            use_ai: 是否使用AI进行内容结构化
            templates_dir: 自定义模板目录
            max_fix_iterations: 最大修复迭代次数
        """
        logger.info("🚀 初始化DITA转换器...")
        
        self.use_ai = use_ai
        self.max_fix_iterations = max_fix_iterations
        self.templates_dir = templates_dir
        
        # 初始化各组件（除了content_structurer，它会在每次转换时重新创建）
        self.template_selector = TemplateSelector(templates_dir)
        self.constraint_engine = ConstraintEngine()
        self.template_renderer = TemplateRenderer(templates_dir)
        self.xml_validator = XMLValidator()
        
        logger.info("✅ DITA转换器初始化完成")
    
    def convert(
        self,
        content: str,
        title: str,
        content_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        转换内容为DITA XML
        
        Args:
            content: 原始内容
            title: 标题
            content_type: 内容类型 (Task/Concept/Reference)
            metadata: 附加元数据
            
        Returns:
            转换结果字典
        """
        logger.info("="*70)
        logger.info("🔄 开始DITA转换...")
        logger.info(f"   类型: {content_type}")
        logger.info(f"   标题: {title}")
        logger.info("="*70)
        
        result = {
            'success': False,
            'content_type': content_type,
            'title': title,
            'dita_xml': None,
            'structured_data': None,
            'validation': None,
            'errors': [],
            'warnings': [],
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'use_ai': self.use_ai,
                'iterations': 0
            }
        }
        
        # 创建错误处理器
        error_handler = ErrorHandler()
        
        try:
            # Step 1: 模板选择
            logger.info("\n[Step 1/5] 选择模板...")
            try:
                template_info = self._step1_select_template(content_type)
                result['metadata']['template'] = template_info
                logger.info(f"   ✓ 选择: {template_info['template_file']}")
            except Exception as e:
                error_handler.add_error(ConverterError(
                    f"模板选择失败: {str(e)}",
                    "TEMPLATE_SELECTION_FAILED"
                ))
                raise
            
            # Step 2: 内容结构化
            logger.info("\n[Step 2/5] 结构化内容...")
            try:
                structured_data = self._step2_structure_content(
                    content, title, content_type, metadata
                )
                result['structured_data'] = structured_data
                logger.info(f"   ✓ 结构化完成")
            except StructureError as e:
                error_handler.add_error(e)
                logger.warning(f"   ⚠️  结构化内容失败: {e}")
                raise
            except Exception as e:
                error_handler.add_error(ConverterError(
                    f"结构化内容失败: {str(e)}",
                    "CONTENT_STRUCTURING_FAILED"
                ))
                raise
            
            # Step 3: 约束验证
            logger.info("\n[Step 3/5] 验证约束...")
            constraint_result = self._step3_validate_constraints(
                structured_data, content_type
            )
            
            if not constraint_result['is_valid']:
                logger.warning(f"   ⚠️  发现 {len(constraint_result['errors'])} 个约束错误")
                # 将约束错误转换为标准化的警告
                for err_msg in constraint_result['errors']:
                    error_handler.add_error(ConstraintError(
                        err_msg,
                        "STRUCTURE_VALIDATION_FAILED",
                        is_warning=True
                    ))
                
                # 尝试修复结构
                structured_data = self._fix_structure(
                    structured_data, constraint_result['errors'], content_type
                )
                result['structured_data'] = structured_data
                logger.info("   ✓ 已尝试修复结构")
            else:
                logger.info("   ✓ 约束验证通过")
            
            # Step 4: 模板渲染
            logger.info("\n[Step 4/5] 渲染模板...")
            try:
                dita_xml = self._step4_render_template(
                    structured_data, content_type
                )
                result['dita_xml'] = dita_xml
                logger.info(f"   ✓ 渲染完成: {len(dita_xml)} 字符")
            except TemplateError as e:
                error_handler.add_error(e)
                logger.error(f"   ❌ 模板渲染失败: {e}")
                raise
            except Exception as e:
                error_handler.add_error(ConverterError(
                    f"模板渲染失败: {str(e)}",
                    "TEMPLATE_RENDERING_FAILED"
                ))
                raise
            
            # Step 5: XML验证 + 修复循环
            logger.info("\n[Step 5/5] XML验证...")
            validation_result, final_xml = self._step5_validate_and_fix(dita_xml)
            
            result['validation'] = validation_result
            result['dita_xml'] = final_xml
            result['metadata']['iterations'] = validation_result.get('iterations', 0)
            
            if validation_result['is_valid']:
                result['success'] = True
                logger.info("   ✓ XML验证通过")
            else:
                logger.warning(f"   ⚠️  XML验证失败: {len(validation_result['errors'])} 个错误")
                # 将XML验证错误转换为标准化的错误
                for err in validation_result['errors']:
                    error_handler.add_error(DITAConversionError(
                        err if isinstance(err, str) else str(err),
                        "XML_VALIDATION_FAILED",
                        "XMLValidator"
                    ))
            
            # 汇总统计
            logger.info("\n" + "="*70)
            logger.info("✅ DITA转换完成")
            logger.info(f"   状态: {'成功' if result['success'] else '失败'}")
            logger.info(f"   迭代次数: {result['metadata']['iterations']}")
            logger.info(f"   错误数: {error_handler.get_results()['error_count']}")
            logger.info(f"   警告数: {error_handler.get_results()['warning_count']}")
            logger.info("="*70)
            
        except Exception as e:
            if not error_handler.get_results()['has_errors']:
                # 如果错误处理器中没有错误，添加一个通用错误
                logger.error(f"❌ 转换过程出错: {e}", exc_info=True)
                error_handler.add_error(ConverterError(
                    f"转换过程出错: {str(e)}",
                    "GENERAL_CONVERSION_ERROR"
                ))
            raise
        finally:
            # 收集错误和警告
            result['errors'] = [err['message'] for err in error_handler.get_results()['errors']]
            result['warnings'] = [warn['message'] for warn in error_handler.get_results()['warnings']]
        
        return result
    
    def _step1_select_template(self, content_type: str) -> Dict:
        """Step 1: 模板选择"""
        return self.template_selector.get_template_info(content_type)
    
    def _step2_structure_content(
        self,
        content: str,
        title: str,
        content_type: str,
        metadata: Optional[Dict]
    ) -> Dict:
        """Step 2: 内容结构化"""
        # 每次结构化时创建新的ContentStructurer实例，确保ID唯一性
        content_structurer = ContentStructurer(self.use_ai)
        return content_structurer.structure_content(
            content, title, content_type, metadata
        )
    
    def _step3_validate_constraints(
        self,
        structured_data: Dict,
        content_type: str
    ) -> Dict:
        """Step 3: 约束验证"""
        return self.constraint_engine.validate_structure(
            structured_data, content_type
        )
    
    def _step4_render_template(
        self,
        structured_data: Dict,
        content_type: str
    ) -> str:
        """Step 4: 模板渲染"""
        if content_type == 'Task':
            return self.template_renderer.render_task(structured_data)
        elif content_type == 'Concept':
            return self.template_renderer.render_concept(structured_data)
        elif content_type == 'Reference':
            return self.template_renderer.render_reference(structured_data)
        else:
            raise ValueError(f"不支持的内容类型: {content_type}")
    
    def _step5_validate_and_fix(self, dita_xml: str) -> tuple:
        """
        Step 5: XML验证 + 自动修复循环
        
        Returns:
            (validation_result, final_xml)
        """
        current_xml = dita_xml
        iteration = 0
        
        while iteration < self.max_fix_iterations:
            # 验证
            validation_result = self.xml_validator.validate(current_xml)
            validation_result['iterations'] = iteration
            
            if validation_result['is_valid']:
                return validation_result, current_xml
            
            # 尝试自动修复
            if iteration < self.max_fix_iterations - 1:
                logger.info(f"   ⚙️  尝试修复 (迭代 {iteration + 1})...")
                
                fixed_xml = self.xml_validator.try_fix(
                    current_xml,
                    validation_result['errors']
                )
                
                if fixed_xml and fixed_xml != current_xml:
                    current_xml = fixed_xml
                    iteration += 1
                else:
                    # 无法修复，退出循环
                    break
            else:
                break
        
        # 达到最大迭代次数或无法修复
        return validation_result, current_xml
    
    def _fix_structure(
        self,
        structured_data: Dict,
        errors: List[str],
        content_type: str
    ) -> Dict:
        """
        修复结构化数据
        
        Args:
            structured_data: 原始结构化数据
            errors: 错误列表
            content_type: 内容类型
            
        Returns:
            修复后的结构化数据
        """
        fixed_data = structured_data.copy()
        
        # 根据错误类型进行修复
        for error in errors:
            error_msg = error if isinstance(error, str) else error.get('message', '')
            
            # 修复缺失的必需字段
            if "缺少必需元素" in error_msg or "缺少必需字段" in error_msg:
                if content_type == 'Task':
                    # 确保有steps
                    if 'steps' not in fixed_data or not fixed_data['steps']:
                        fixed_data['steps'] = [{'cmd': 'Complete the task'}]
                    
                    # 确保每个step有cmd
                    for step in fixed_data.get('steps', []):
                        if 'cmd' not in step:
                            step['cmd'] = 'Perform action'
                
                elif content_type == 'Concept':
                    # 确保有introduction或sections
                    if not fixed_data.get('introduction') and not fixed_data.get('sections'):
                        fixed_data['introduction'] = 'This is a concept description.'
                
                elif content_type == 'Reference':
                    # 确保有内容
                    if not any([fixed_data.get('properties'), fixed_data.get('table'), fixed_data.get('sections')]):
                        fixed_data['sections'] = [{'content': 'Reference information'}]
            
            # 修复steps数量不足
            elif "steps数量不足" in error_msg:
                if content_type == 'Task' and len(fixed_data.get('steps', [])) == 0:
                    fixed_data['steps'] = [{'command': 'Complete the task'}]
        
        return fixed_data
    
    def convert_batch(
        self,
        chunks: List[Dict],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        批量转换
        
        Args:
            chunks: 分块列表，每个包含 content, title, type
            output_dir: 输出目录（可选）
            
        Returns:
            批量转换结果
        """
        logger.info("="*70)
        logger.info(f"🔄 批量转换: {len(chunks)} 个块")
        logger.info("="*70)
        
        results = []
        success_count = 0
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"\n[{i}/{len(chunks)}] 处理: {chunk.get('title', 'Untitled')}")
            
            result = self.convert(
                content=chunk['content'],
                title=chunk['title'],
                content_type=chunk['type'],
                metadata=chunk.get('metadata')
            )
            
            results.append(result)
            
            if result['success']:
                success_count += 1
                
                # 保存到文件
                if output_dir:
                    self._save_dita_file(result, output_dir, i)
        
        # 生成批量报告
        batch_result = {
            'total': len(chunks),
            'success': success_count,
            'failed': len(chunks) - success_count,
            'success_rate': success_count / len(chunks) if chunks else 0,
            'results': results
        }
        
        logger.info("\n" + "="*70)
        logger.info("✅ 批量转换完成")
        logger.info(f"   总数: {batch_result['total']}")
        logger.info(f"   成功: {batch_result['success']}")
        logger.info(f"   失败: {batch_result['failed']}")
        logger.info(f"   成功率: {batch_result['success_rate']:.1%}")
        logger.info("="*70)
        
        return batch_result
    
    def _save_dita_file(
        self,
        result: Dict,
        output_dir: Path,
        index: int
    ):
        """保存DITA文件"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        title = result['title']
        content_type = result['content_type'].lower()
        safe_title = "".join(c if c.isalnum() else '_' for c in title)[:50]
        
        filename = f"{index:03d}_{content_type}_{safe_title}.dita"
        filepath = output_dir / filename
        
        # 保存XML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result['dita_xml'])
        
        logger.info(f"   💾 已保存: {filepath.name}")
    
    def save_conversion_report(
        self,
        result: Dict,
        output_path: Path
    ):
        """
        保存转换报告
        
        Args:
            result: 转换结果
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 准备报告数据（移除XML内容以减小文件大小）
        report = result.copy()
        if 'dita_xml' in report:
            report['dita_xml_length'] = len(report['dita_xml'])
            report['dita_xml_preview'] = report['dita_xml'][:500] + '...'
            del report['dita_xml']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 转换报告已保存: {output_path}")


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("dita_converter")
    
    converter = DITAConverter(use_ai=True)
    
    # 测试单个转换
    print("\n" + "="*70)
    print("测试单个转换 - Task")
    print("="*70)
    
    task_content = """
    Before you begin, ensure you have:
    - Python 3.8 or higher
    - Administrator privileges
    - 20MB free disk space
    
    Follow these steps to install the package:
    
    1. Download the installer from the official website
    2. Run the installer with administrator rights
    3. Follow the on-screen instructions
    4. Verify the installation by running: program --version
    
    After successful installation, you should see the version number displayed.
    """
    
    result = converter.convert(
        content=task_content,
        title="Installing the Software Package",
        content_type="Task"
    )
    
    print(f"\n转换结果:")
    print(f"  成功: {result['success']}")
    print(f"  迭代次数: {result['metadata']['iterations']}")
    print(f"  错误数: {len(result['errors'])}")
    
    if result['success']:
        print(f"\n生成的DITA XML:")
        print(result['dita_xml'][:500] + "...")
        
        # 保存
        output_file = Path("data/output/layer3/test_task.dita")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['dita_xml'])
        print(f"\n✅ 已保存到: {output_file}")
        
        # 保存报告
        report_file = Path("data/output/layer3/test_task_report.json")
        converter.save_conversion_report(result, report_file)
    else:
        print(f"\n错误:")
        for error in result['errors']:
            print(f"  - {error}")
    
    # 测试批量转换
    print("\n" + "="*70)
    print("测试批量转换")
    print("="*70)
    
    chunks = [
        {
            'content': task_content,
            'title': 'Installing Software',
            'type': 'Task'
        },
        {
            'content': 'Python is a high-level programming language. It emphasizes code readability.',
            'title': 'What is Python',
            'type': 'Concept'
        },
        {
            'content': '| Parameter | Type | Description |\n|-----------|------|-------------|\n| timeout | int | Connection timeout |',
            'title': 'API Parameters',
            'type': 'Reference'
        }
    ]
    
    batch_result = converter.convert_batch(
        chunks,
        output_dir=Path("data/output/layer3/batch")
    )
    
    print(f"\n批量转换汇总:")
    print(f"  总数: {batch_result['total']}")
    print(f"  成功: {batch_result['success']}")
    print(f"  失败: {batch_result['failed']}")
    print(f"  成功率: {batch_result['success_rate']:.1%}")