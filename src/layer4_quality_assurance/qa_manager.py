"""
Layer 4 主质量保证管理器
协调所有QA步骤，确保DITA文档完全符合标准
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .dita_ot_validator import DITAOTValidator
from .custom_rules_checker import CustomRulesChecker
from .intelligent_repairer import IntelligentRepairer
from .validation_loop import ValidationLoop
from .quality_reporter import QualityReporter

logger = logging.getLogger(__name__)

class QAManager:
    """质量保证管理器 - Layer 4 主控制器"""
    
    def __init__(
        self,
        use_dita_ot: bool = False,
        use_ai_repair: bool = True,
        max_iterations: int = 3,
        rules_config: Optional[Path] = None,
        image_dir: Optional[Path] = None
    ):
        """
        初始化质量保证管理器
        
        Args:
            use_dita_ot: 是否使用DITA-OT验证
            use_ai_repair: 是否使用AI修复
            max_iterations: 最大验证-修复迭代次数
            rules_config: 自定义规则配置文件
            image_dir: 图片目录（用于检查图片引用）
        """
        logger.info("🚀 初始化质量保证管理器...")
        
        self.use_dita_ot = use_dita_ot
        self.use_ai_repair = use_ai_repair
        self.max_iterations = max_iterations
        
        # 初始化各组件
        self.dita_ot_validator = DITAOTValidator(use_dita_ot=use_dita_ot)
        self.custom_rules_checker = CustomRulesChecker(rules_config, image_dir)
        self.intelligent_repairer = IntelligentRepairer(use_ai=use_ai_repair)
        self.validation_loop = ValidationLoop(
            max_iterations=max_iterations,
            use_dita_ot=use_dita_ot,
            use_ai_repair=use_ai_repair
        )
        self.quality_reporter = QualityReporter()
        
        logger.info("✅ 质量保证管理器初始化完成")
    
    def process(
        self,
        dita_xml: str,
        content_type: str = None,
        processing_metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        执行完整的质量保证流程
        
        Args:
            dita_xml: DITA XML字符串
            content_type: 内容类型（Task/Concept/Reference）
            processing_metadata: 前三层的处理元数据
            
        Returns:
            QA结果字典
        """
        logger.info("="*70)
        logger.info("🎯 开始质量保证流程...")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        result = {
            'success': False,
            'final_dita_xml': dita_xml,
            'content_type': content_type,
            'processing_metadata': processing_metadata or {},
            'qa_metadata': {
                'start_time': start_time.isoformat(),
                'use_dita_ot': self.use_dita_ot,
                'use_ai_repair': self.use_ai_repair,
                'max_iterations': self.max_iterations
            },
            'step_results': {},
            'quality_report': None
        }
        
        try:
            # Step 1: DITA标准验证 + 修复循环
            logger.info("\n[Step 1/5] DITA标准验证与修复...")
            loop_result = self._step1_validation_loop(dita_xml, content_type)
            
            result['step_results']['validation_loop'] = loop_result
            result['final_dita_xml'] = loop_result['final_xml']
            
            if loop_result['success']:
                logger.info("  ✅ DITA标准验证通过")
            else:
                logger.warning("  ⚠️  DITA标准验证未完全通过")
            
            # Step 2: 自定义规则检查
            logger.info("\n[Step 2/5] 自定义规则检查...")
            custom_checks_result = self._step2_custom_checks(result['final_dita_xml'])
            
            result['step_results']['custom_checks'] = custom_checks_result
            
            logger.info(f"  ✓ 检查完成: {custom_checks_result['total_issues']} 个问题")
            
            # Step 3: 最终验证（确认）
            logger.info("\n[Step 3/5] 最终验证...")
            final_validation = self._step3_final_validation(
                result['final_dita_xml'],
                content_type
            )
            
            result['step_results']['final_validation'] = final_validation
            
            if final_validation['is_valid']:
                logger.info("  ✅ 最终验证通过")
            else:
                logger.warning(f"  ⚠️  最终验证发现 {len(final_validation['errors'])} 个错误")
            
            # Step 4: 生成质量报告
            logger.info("\n[Step 4/5] 生成质量报告...")
            quality_report = self._step4_generate_report(
                result['final_dita_xml'],
                final_validation,
                custom_checks_result,
                loop_result,
                processing_metadata
            )
            
            result['quality_report'] = quality_report
            
            logger.info(f"  ✓ 质量分数: {quality_report['quality_scores']['overall_quality']:.2f}")
            
            # Step 5: 确定最终状态
            logger.info("\n[Step 5/5] 确定最终状态...")
            result['success'] = self._step5_determine_success(
                final_validation,
                custom_checks_result,
                quality_report
            )
            
            # 计算处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result['qa_metadata']['end_time'] = end_time.isoformat()
            result['qa_metadata']['processing_time'] = processing_time
            
            # 汇总
            logger.info("\n" + "="*70)
            if result['success']:
                logger.info("✅ 质量保证流程成功完成")
            else:
                logger.warning("⚠️  质量保证流程完成，但存在问题")
            
            logger.info(f"   总体状态: {quality_report['overall_status']}")
            logger.info(f"   质量分数: {quality_report['quality_scores']['overall_quality']:.2f}")
            logger.info(f"   处理时间: {processing_time:.2f}s")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ 质量保证流程出错: {e}", exc_info=True)
            result['error'] = str(e)
        
        return result
    
    def _step1_validation_loop(
        self,
        dita_xml: str,
        content_type: str
    ) -> Dict:
        """Step 1: DITA标准验证 + 修复循环"""
        return self.validation_loop.run(dita_xml, content_type)
    
    def _step2_custom_checks(self, dita_xml: str) -> Dict:
        """Step 2: 自定义规则检查"""
        return self.custom_rules_checker.check(dita_xml)
    
    def _step3_final_validation(
        self,
        dita_xml: str,
        content_type: str
    ) -> Dict:
        """Step 3: 最终验证"""
        return self.dita_ot_validator.validate(dita_xml, content_type)
    
    def _step4_generate_report(
        self,
        dita_xml: str,
        validation_result: Dict,
        custom_checks_result: Dict,
        loop_result: Dict,
        processing_metadata: Dict
    ) -> Dict:
        """Step 4: 生成质量报告"""
        return self.quality_reporter.generate_report(
            dita_xml,
            validation_result,
            custom_checks_result,
            loop_result,
            processing_metadata
        )
    
    def _step5_determine_success(
        self,
        validation_result: Dict,
        custom_checks_result: Dict,
        quality_report: Dict
    ) -> bool:
        """Step 5: 确定最终成功状态"""
        
        # 必须通过DITA标准验证
        if not validation_result['is_valid']:
            logger.warning("  ✗ DITA标准验证未通过")
            return False
        
        # 不能有自定义规则的错误级别问题
        has_custom_errors = any(
            issue.get('severity') == 'error'
            for failed_rule in custom_checks_result.get('failed', [])
            for issue in failed_rule.get('issues', [])
        )
        
        if has_custom_errors:
            logger.warning("  ✗ 存在自定义规则错误")
            return False
        
        # 质量分数必须达到最低要求
        overall_quality = quality_report['quality_scores'].get('overall_quality', 0)
        min_quality_threshold = 0.7
        
        if overall_quality < min_quality_threshold:
            logger.warning(f"  ✗ 质量分数过低: {overall_quality:.2f} < {min_quality_threshold}")
            return False
        
        logger.info("  ✅ 所有质量检查通过")
        return True
    
    def _merge_dita_documents(self, results: List[Dict]) -> Dict[str, Any]:
        """
        合并多个DITA文档为一个完整的DITA文档
        
        Args:
            results: 批量处理结果列表
            
        Returns:
            包含合并后DITA XML和验证结果的字典
        """
        logger.info("🔄 开始合并DITA文档...")
        
        # 提取所有成功的DITA XML内容
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            logger.warning("⚠️ 没有成功的DITA文档可以合并")
            return None
        
        # 合并文档内容
        merged_content = []
        document_ids = set()
        
        for i, result in enumerate(successful_results, 1):
            dita_xml = result['final_dita_xml']
            
            try:
                # 尝试从不同位置获取文档标题
                title = ""
                if 'title' in result:
                    title = result['title']
                elif 'metadata' in result and 'title' in result['metadata']:
                    title = result['metadata']['title']
                elif 'filename' in result:
                    # 从文件名提取标题
                    title = result['filename'].replace('.dita', '').split('_')[-1]
                elif 'quality_report' in result and 'title' in result['quality_report']:
                    title = result['quality_report']['title']
                
                # 如果仍然没有标题，使用默认名称
                if not title:
                    title = f"Section_{i}"
                
                # 生成唯一的文档ID
                doc_id = "".join(c if c.isalnum() else '_' for c in title)[:30]
                
                # 确保ID唯一
                counter = 1
                unique_doc_id = doc_id
                while unique_doc_id in document_ids:
                    unique_doc_id = f"{doc_id}_{counter}"
                    counter += 1
                document_ids.add(unique_doc_id)
                
                # 移除XML声明，避免重复
                if dita_xml.startswith('<?xml'):
                    xml_end = dita_xml.find('?>')
                    if xml_end != -1:
                        dita_xml = dita_xml[xml_end+2:].strip()
                
                # 提取对应类型的主体内容，避免嵌套的根元素
                import re
                body_content = ""
                
                # 检查文档类型并提取相应的主体内容
                if '<conbody>' in dita_xml:
                    # Concept类型
                    body_match = re.search(r'<conbody>(.*?)</conbody>', dita_xml, re.DOTALL)
                    if body_match:
                        body_content = body_match.group(1)
                elif '<refbody>' in dita_xml:
                    # Reference类型
                    body_match = re.search(r'<refbody>(.*?)</refbody>', dita_xml, re.DOTALL)
                    if body_match:
                        body_content = body_match.group(1)
                elif '<taskbody>' in dita_xml:
                    # Task类型
                    body_match = re.search(r'<taskbody>(.*?)</taskbody>', dita_xml, re.DOTALL)
                    if body_match:
                        body_content = body_match.group(1)
                else:
                    # 如果没有识别的主体元素，使用整个内容（移除根元素标签）
                    root_start = dita_xml.find('>')
                    root_end = dita_xml.rfind('</')
                    if root_start != -1 and root_end != -1:
                        body_content = dita_xml[root_start+1:root_end].strip()
                    else:
                        body_content = dita_xml
                
                # 将提取的内容添加到section中
                section_content = f'<section id="{unique_doc_id}"><title>{title}</title>{body_content}</section>'
                merged_content.append(section_content)
            except Exception as e:
                logger.warning(f"⚠️ 处理文档 {i} 时出错: {str(e)}")
                import traceback
                logger.debug(f"错误详情: {traceback.format_exc()}")
        
        # 创建合并后的DITA文档（使用concept类型作为主文档）
        merged_content_str = "\n    ".join(merged_content)
        merged_dita = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="merged_complete_document">
  <title>合并后的完整文档</title>
  <conbody>
    {}
  </conbody>
</concept>'''.format(merged_content_str)
        
        logger.info(f"✅ 成功合并 {len(merged_content)} 个文档")
        
        # 对合并后的文档进行质量检查
        logger.info("🔍 对合并后的文档进行质量检查...")
        merged_result = self.process(
            dita_xml=merged_dita,
            content_type='Concept',
            processing_metadata={'source': 'merged_document'}
        )
        
        return merged_result

    def process_batch(
        self,
        dita_documents: List[Dict],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        批量处理DITA文档
        
        Args:
            dita_documents: DITA文档列表，每个包含 xml, type, metadata
            output_dir: 输出目录
            
        Returns:
            批量处理结果
        """
        logger.info("="*70)
        logger.info(f"🔄 批量质量保证: {len(dita_documents)} 个文档")
        logger.info("="*70)
        
        results = []
        success_count = 0
        
        for i, doc in enumerate(dita_documents, 1):
            logger.info(f"\n[{i}/{len(dita_documents)}] 处理文档...")
            
            result = self.process(
                dita_xml=doc['xml'],
                content_type=doc.get('type'),
                processing_metadata=doc.get('metadata')
            )
            
            results.append(result)
            
            if result['success']:
                success_count += 1
                
                # 保存文档和报告
                if output_dir:
                    self._save_batch_output(result, output_dir, i)
        
        # 生成批量报告
        batch_result = {
            'total': len(dita_documents),
            'success': success_count,
            'failed': len(dita_documents) - success_count,
            'success_rate': success_count / len(dita_documents) if dita_documents else 0,
            'results': results,
            'summary': self._generate_batch_summary(results)
        }
        
        # 生成并保存合成版完整文档
        if output_dir and success_count > 0:
            merged_result = self._merge_dita_documents(results)
            if merged_result:
                # 保存合并后的文档
                merged_file = output_dir / "merged_complete_document.dita"
                with open(merged_file, 'w', encoding='utf-8') as f:
                    f.write(merged_result['final_dita_xml'])
                logger.info(f"💾 合成版完整文档已保存: {merged_file}")
                
                # 保存合并文档的质量报告
                doc_id = merged_result['quality_report']['document_id']
                
                # 保存JSON报告
                json_file = output_dir / f"merged_complete_report.json"
                self.quality_reporter.save_report(
                    merged_result['quality_report'],
                    json_file,
                    include_xml=True,
                    dita_xml=merged_result['final_dita_xml']
                )
                
                # 保存HTML报告
                html_file = output_dir / f"merged_complete_report.html"
                self.quality_reporter.save_html_report(
                    merged_result['quality_report'],
                    html_file
                )
                
                logger.info("📊 合成版文档的质量报告已生成")
                batch_result['merged_document_path'] = str(merged_file)
                batch_result['merged_document_result'] = merged_result
        
        logger.info("\n" + "="*70)
        logger.info("✅ 批量质量保证完成")
        logger.info(f"   总数: {batch_result['total']}")
        logger.info(f"   成功: {batch_result['success']}")
        logger.info(f"   失败: {batch_result['failed']}")
        logger.info(f"   成功率: {batch_result['success_rate']:.1%}")
        logger.info("="*70)
        
        return batch_result
    
    def _save_batch_output(
        self,
        result: Dict,
        output_dir: Path,
        index: int
    ):
        """保存批量处理的输出"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        content_type = result.get('content_type', 'unknown').lower()
        doc_id = result['quality_report']['document_id']
        
        # 保存DITA XML
        dita_file = output_dir / f"{index:03d}_{content_type}_{doc_id}.dita"
        with open(dita_file, 'w', encoding='utf-8') as f:
            f.write(result['final_dita_xml'])
        
        logger.info(f"  💾 已保存DITA: {dita_file.name}")
        
        # 保存JSON报告
        json_report = output_dir / f"{index:03d}_{content_type}_{doc_id}_report.json"
        self.quality_reporter.save_report(
            result['quality_report'],
            json_report,
            include_xml=False
        )
        
        # 保存HTML报告
        html_report = output_dir / f"{index:03d}_{content_type}_{doc_id}_report.html"
        self.quality_reporter.save_html_report(
            result['quality_report'],
            html_report
        )
    
    def _generate_batch_summary(self, results: List[Dict]) -> Dict:
        """生成批量处理摘要"""
        
        summary = {
            'quality_scores': {
                'avg_overall_quality': 0,
                'avg_dita_compliance': 0,
                'avg_structure_quality': 0,
                'avg_content_completeness': 0
            },
            'validation_stats': {
                'total_errors': 0,
                'total_warnings': 0,
                'avg_iterations': 0
            },
            'custom_checks_stats': {
                'total_issues': 0,
                'avg_issues_per_doc': 0
            }
        }
        
        if not results:
            return summary
        
        # 计算平均质量分数
        for result in results:
            if result.get('quality_report'):
                scores = result['quality_report']['quality_scores']
                summary['quality_scores']['avg_overall_quality'] += scores.get('overall_quality', 0)
                summary['quality_scores']['avg_dita_compliance'] += scores.get('dita_compliance', 0)
                summary['quality_scores']['avg_structure_quality'] += scores.get('structure_quality', 0)
                summary['quality_scores']['avg_content_completeness'] += scores.get('content_completeness', 0)
                
                # 验证统计
                val_summary = result['quality_report']['validation_summary']
                summary['validation_stats']['total_errors'] += val_summary.get('errors', 0)
                summary['validation_stats']['total_warnings'] += val_summary.get('warnings', 0)
                summary['validation_stats']['avg_iterations'] += val_summary.get('iterations_required', 0)
                
                # 自定义检查统计
                custom_summary = result['quality_report']['custom_checks_summary']
                summary['custom_checks_stats']['total_issues'] += custom_summary.get('total_issues', 0)
        
        count = len(results)
        summary['quality_scores']['avg_overall_quality'] /= count
        summary['quality_scores']['avg_dita_compliance'] /= count
        summary['quality_scores']['avg_structure_quality'] /= count
        summary['quality_scores']['avg_content_completeness'] /= count
        summary['validation_stats']['avg_iterations'] /= count
        summary['custom_checks_stats']['avg_issues_per_doc'] = \
            summary['custom_checks_stats']['total_issues'] / count
        
        return summary
    
    def save_results(
        self,
        result: Dict,
        output_dir: Path,
        save_formats: List[str] = ['json', 'html', 'dita']
    ):
        """
        保存QA结果
        
        Args:
            result: QA结果
            output_dir: 输出目录
            save_formats: 保存格式列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        doc_id = result['quality_report']['document_id']
        
        # 保存DITA XML
        if 'dita' in save_formats:
            dita_file = output_dir / f"{doc_id}.dita"
            with open(dita_file, 'w', encoding='utf-8') as f:
                f.write(result['final_dita_xml'])
            logger.info(f"💾 DITA已保存: {dita_file}")
        
        # 保存JSON报告
        if 'json' in save_formats:
            json_file = output_dir / f"{doc_id}_report.json"
            self.quality_reporter.save_report(
                result['quality_report'],
                json_file,
                include_xml=True,
                dita_xml=result['final_dita_xml']
            )
        
        # 保存HTML报告
        if 'html' in save_formats:
            html_file = output_dir / f"{doc_id}_report.html"
            self.quality_reporter.save_html_report(
                result['quality_report'],
                html_file
            )


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("qa_manager")
    
    qa_manager = QAManager(
        use_dita_ot=False,
        use_ai_repair=True,
        max_iterations=3
    )
    
    # 测试单个文档
    print("\n" + "="*70)
    print("测试单个文档质量保证")
    print("="*70)
    
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="task_install_software">
  <title>Installing Software</title>
  <shortdesc>Learn how to install the software package</shortdesc>
  <taskbody>
    <prereq>
      <p>Before you begin, ensure you have administrator privileges.</p>
    </prereq>
    <steps>
      <step>
        <cmd>Download the installer from the official website</cmd>
        <info>Choose the version matching your operating system</info>
      </step>
      <step>
        <cmd>Run the installer</cmd>
        <info>Follow the on-screen instructions</info>
      </step>
      <step>
        <cmd>Verify the installation</cmd>
        <info>Run the command: software --version</info>
      </step>
    </steps>
    <result>
      <p>The software is now installed and ready to use.</p>
    </result>
  </taskbody>
</task>"""
    
    result = qa_manager.process(
        dita_xml=test_xml,
        content_type='Task',
        processing_metadata={
            'layer1_confidence': 0.92,
            'layer2_confidence': 0.87,
            'layer3_iterations': 1
        }
    )
    
    print(f"\n处理结果:")
    print(f"  成功: {result['success']}")
    print(f"  总体状态: {result['quality_report']['overall_status']}")
    print(f"  质量分数: {result['quality_report']['quality_scores']['overall_quality']:.2f}")
    print(f"  处理时间: {result['qa_metadata']['processing_time']:.2f}s")
    
    # 保存结果
    output_dir = Path("data/output/layer4/single_test")
    qa_manager.save_results(result, output_dir)
    
    print(f"\n✅ 结果已保存到: {output_dir}")
    
    # 测试批量处理
    print("\n" + "="*70)
    print("测试批量处理")
    print("="*70)
    
    batch_docs = [
        {
            'xml': test_xml,
            'type': 'Task',
            'metadata': {'source': 'test1'}
        },
        {
            'xml': test_xml.replace('task_install_software', 'task_configure_software')
                          .replace('Installing Software', 'Configuring Software'),
            'type': 'Task',
            'metadata': {'source': 'test2'}
        }
    ]
    
    batch_result = qa_manager.process_batch(
        batch_docs,
        output_dir=Path("data/output/layer4/batch_test")
    )
    
    print(f"\n批量处理汇总:")
    print(f"  总数: {batch_result['total']}")
    print(f"  成功: {batch_result['success']}")
    print(f"  失败: {batch_result['failed']}")
    print(f"  成功率: {batch_result['success_rate']:.1%}")
    print(f"  平均质量分数: {batch_result['summary']['quality_scores']['avg_overall_quality']:.2f}")