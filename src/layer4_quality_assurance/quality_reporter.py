"""
Step 5: 质量报告生成器
生成完整的质量评估报告
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class QualityReporter:
    """质量报告生成器"""
    
    def __init__(self):
        """初始化质量报告生成器"""
        logger.info("✅ 质量报告生成器初始化完成")
    
    def generate_report(
        self,
        dita_xml: str,
        validation_result: Dict,
        custom_checks_result: Dict,
        loop_result: Dict,
        processing_metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        生成质量报告
        
        Args:
            dita_xml: 最终的DITA XML
            validation_result: DITA标准验证结果
            custom_checks_result: 自定义规则检查结果
            loop_result: 验证循环结果
            processing_metadata: 处理元数据（来自前三层）
            
        Returns:
            完整质量报告
        """
        logger.info("📊 生成质量报告...")
        
        report = {
            'document_id': self._generate_document_id(),
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'quality_scores': {},
            'validation_summary': {},
            'custom_checks_summary': {},
            'processing_metadata': processing_metadata or {},
            'recommendations': [],
            'statistics': {}
        }
        
        # 1. 计算质量分数
        report['quality_scores'] = self._calculate_quality_scores(
            validation_result,
            custom_checks_result,
            loop_result
        )
        
        # 2. 验证摘要
        report['validation_summary'] = self._create_validation_summary(
            validation_result,
            loop_result
        )
        
        # 3. 自定义检查摘要
        report['custom_checks_summary'] = self._create_custom_checks_summary(
            custom_checks_result
        )
        
        # 4. 统计信息
        report['statistics'] = self._calculate_statistics(dita_xml)
        
        # 5. 生成建议
        report['recommendations'] = self._generate_recommendations(
            validation_result,
            custom_checks_result,
            loop_result
        )
        
        # 6. 确定总体状态
        report['overall_status'] = self._determine_overall_status(
            validation_result,
            custom_checks_result
        )
        
        logger.info(f"✅ 质量报告生成完成 (状态: {report['overall_status']})")
        
        return report
    
    def _generate_document_id(self) -> str:
        """生成文档ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"dita_doc_{timestamp}"
    
    def _calculate_quality_scores(
        self,
        validation_result: Dict,
        custom_checks_result: Dict,
        loop_result: Dict
    ) -> Dict[str, float]:
        """计算质量分数"""
        
        scores = {}
        
        # 1. DITA合规性分数
        if validation_result['is_valid']:
            scores['dita_compliance'] = 1.0
        else:
            error_count = len(validation_result.get('errors', []))
            # 每个错误扣0.1分，最低0分
            scores['dita_compliance'] = max(0.0, 1.0 - error_count * 0.1)
        
        # 2. 结构质量分数
        # 基于验证循环的迭代次数
        iterations = loop_result.get('iterations', 0)
        max_iterations = 3  # 假设最大迭代次数为3
        
        if loop_result.get('success'):
            # 成功的情况：迭代次数越少分数越高
            scores['structure_quality'] = 1.0 - (iterations - 1) * 0.1
        else:
            # 失败的情况
            scores['structure_quality'] = 0.5
        
        # 3. 内容完整性分数
        # 基于自定义规则检查
        total_issues = custom_checks_result.get('total_issues', 0)
        
        if total_issues == 0:
            scores['content_completeness'] = 1.0
        else:
            # 根据问题严重程度计算
            severity_weights = {'error': 0.2, 'warning': 0.1, 'info': 0.05}
            
            deduction = 0
            for severity, count in custom_checks_result.get('issues_by_severity', {}).items():
                weight = severity_weights.get(severity, 0.1)
                deduction += count * weight
            
            scores['content_completeness'] = max(0.0, 1.0 - deduction)
        
        # 4. 总体质量分数（加权平均）
        weights = {
            'dita_compliance': 0.4,
            'structure_quality': 0.3,
            'content_completeness': 0.3
        }
        
        scores['overall_quality'] = sum(
            scores[key] * weights[key]
            for key in weights.keys()
        )
        
        return scores
    
    def _create_validation_summary(
        self,
        validation_result: Dict,
        loop_result: Dict
    ) -> Dict:
        """创建验证摘要"""
        
        summary = {
            'is_valid': validation_result['is_valid'],
            'validator': validation_result.get('validator', 'Unknown'),
            'total_checks': 1,  # 简化
            'passed': 1 if validation_result['is_valid'] else 0,
            'errors': len(validation_result.get('errors', [])),
            'warnings': len(validation_result.get('warnings', [])),
            'iterations_required': loop_result.get('iterations', 0),
            'repairs_applied': sum(
                len(h['result'].get('applied_fixes', []))
                for h in loop_result.get('repair_history', [])
            )
        }
        
        # 错误详情（前5个）
        summary['error_details'] = [
            {
                'type': e.get('type', 'Unknown'),
                'message': e.get('message', ''),
                'element': e.get('element', '')
            }
            for e in validation_result.get('errors', [])[:5]
        ]
        
        return summary
    
    def _create_custom_checks_summary(
        self,
        custom_checks_result: Dict
    ) -> Dict:
        """创建自定义检查摘要"""
        
        summary = {
            'total_rules': len(custom_checks_result.get('passed', [])) + 
                          len(custom_checks_result.get('failed', [])),
            'passed_rules': len(custom_checks_result.get('passed', [])),
            'failed_rules': len(custom_checks_result.get('failed', [])),
            'total_issues': custom_checks_result.get('total_issues', 0),
            'issues_by_severity': custom_checks_result.get('issues_by_severity', {})
        }
        
        # 失败规则详情
        summary['failed_rule_details'] = [
            {
                'rule': f['rule'],
                'description': f.get('description', ''),
                'issue_count': len(f.get('issues', []))
            }
            for f in custom_checks_result.get('failed', [])
        ]
        
        return summary
    
    def _calculate_statistics(self, dita_xml: str) -> Dict:
        """计算文档统计信息"""
        
        from lxml import etree
        
        stats = {
            'xml_size': len(dita_xml),
            'line_count': dita_xml.count('\n'),
            'element_count': 0,
            'text_content_length': 0
        }
        
        try:
            tree = etree.fromstring(dita_xml.encode('utf-8'))
            
            # 元素数量
            stats['element_count'] = len(tree.xpath('//*'))
            
            # 文本内容长度
            text_content = ' '.join(tree.itertext())
            stats['text_content_length'] = len(text_content)
            stats['word_count'] = len(text_content.split())
            
            # 特定元素统计
            stats['elements'] = {
                'steps': len(tree.xpath('.//step')),
                'sections': len(tree.xpath('.//section')),
                'paragraphs': len(tree.xpath('.//p')),
                'lists': len(tree.xpath('.//ul | .//ol')),
                'tables': len(tree.xpath('.//table')),
                'images': len(tree.xpath('.//image')),
                'notes': len(tree.xpath('.//note')),
                'codeblocks': len(tree.xpath('.//codeblock'))
            }
            
        except Exception as e:
            logger.warning(f"统计计算失败: {e}")
        
        return stats
    
    def _generate_recommendations(
        self,
        validation_result: Dict,
        custom_checks_result: Dict,
        loop_result: Dict
    ) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        # 基于验证错误
        if validation_result.get('errors'):
            error_types = set(e.get('type') for e in validation_result['errors'])
            
            if 'MissingRequiredElement' in error_types:
                recommendations.append(
                    "文档缺少某些必需元素，请确保所有DITA必需元素都已包含"
                )
            
            if 'ElementOrderError' in error_types:
                recommendations.append(
                    "元素顺序不符合DITA规范，请调整元素的排列顺序"
                )
            
            if 'InvalidIDFormat' in error_types:
                recommendations.append(
                    "某些ID格式不正确，ID应以字母开头，仅包含字母、数字、-_."
                )
        
        # 基于自定义检查
        for failed_rule in custom_checks_result.get('failed', []):
            rule_name = failed_rule['rule']
            issues = failed_rule.get('issues', [])
            
            if rule_name == 'title_length' and issues:
                recommendations.append(
                    f"标题长度需要调整：{issues[0].get('suggestion', '')}"
                )
            
            if rule_name == 'step_count' and issues:
                recommendations.append(
                    "步骤数量较多，考虑拆分为多个子任务以提高可读性"
                )
            
            if rule_name == 'nesting_depth' and issues:
                recommendations.append(
                    "文档嵌套层次过深，建议简化结构或拆分主题"
                )
        
        # 基于循环结果
        if loop_result.get('iterations', 0) > 1:
            recommendations.append(
                "文档需要多次修复才能通过验证，建议在初始生成时加强质量控制"
            )
        
        # 如果没有特定建议，添加通用建议
        if not recommendations:
            recommendations.append(
                "文档质量良好，继续保持当前的编写标准"
            )
        
        return recommendations
    
    def _determine_overall_status(
        self,
        validation_result: Dict,
        custom_checks_result: Dict
    ) -> str:
        """确定总体状态"""
        
        # 检查是否有错误级别的问题
        has_validation_errors = not validation_result['is_valid']
        
        has_custom_errors = any(
            issue.get('severity') == 'error'
            for failed_rule in custom_checks_result.get('failed', [])
            for issue in failed_rule.get('issues', [])
        )
        
        if has_validation_errors or has_custom_errors:
            return 'failed'
        
        # 检查是否有警告
        has_warnings = (
            len(validation_result.get('warnings', [])) > 0 or
            custom_checks_result.get('issues_by_severity', {}).get('warning', 0) > 0
        )
        
        if has_warnings:
            return 'passed_with_warnings'
        
        return 'passed'
    
    def save_report(
        self,
        report: Dict,
        output_path: Path,
        include_xml: bool = False,
        dita_xml: str = None
    ):
        """
        保存报告到文件
        
        Args:
            report: 报告数据
            output_path: 输出路径
            include_xml: 是否包含完整XML
            dita_xml: DITA XML内容
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 准备保存的数据
        save_data = report.copy()
        
        if include_xml and dita_xml:
            save_data['final_dita_xml'] = dita_xml
        
        # 保存JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 质量报告已保存: {output_path}")
    
    def generate_html_report(self, report: Dict) -> str:
        """生成HTML格式的报告"""
        
        status_color = {
            'passed': '#28a745',
            'passed_with_warnings': '#ffc107',
            'failed': '#dc3545'
        }
        
        color = status_color.get(report['overall_status'], '#6c757d')
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DITA质量报告 - {report['document_id']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header .meta {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            background-color: {color};
            color: white;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .score-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        .score-card .label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 8px;
        }}
        .score-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }}
        .stat-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
        }}
        .stat-item .label {{
            font-size: 0.85em;
            color: #6c757d;
        }}
        .stat-item .value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
        .recommendations {{
            list-style: none;
            padding: 0;
        }}
        .recommendations li {{
            background: #fff3cd;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
        }}
        .error-list {{
            list-style: none;
            padding: 0;
        }}
        .error-list li {{
            background: #f8d7da;
            padding: 10px;
            margin-bottom: 8px;
            border-left: 4px solid #dc3545;
            border-radius: 4px;
        }}
        .warning-list li {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .info-list li {{
            background: #d1ecf1;
            border-left-color: #17a2b8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 DITA质量报告</h1>
        <div class="meta">
            <div>文档ID: {report['document_id']}</div>
            <div>生成时间: {report['timestamp']}</div>
        </div>
        <div class="status">{self._get_status_text(report['overall_status'])}</div>
    </div>
    
    <div class="section">
        <h2>质量分数</h2>
        <div class="score-grid">
            {self._generate_score_cards(report['quality_scores'])}
        </div>
    </div>
    
    <div class="section">
        <h2>验证摘要</h2>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="label">验证器</div>
                <div class="value">{report['validation_summary'].get('validator', 'N/A')}</div>
            </div>
            <div class="stat-item">
                <div class="label">错误数</div>
                <div class="value" style="color: #dc3545;">{report['validation_summary'].get('errors', 0)}</div>
            </div>
            <div class="stat-item">
                <div class="label">警告数</div>
                <div class="value" style="color: #ffc107;">{report['validation_summary'].get('warnings', 0)}</div>
            </div>
            <div class="stat-item">
                <div class="label">修复次数</div>
                <div class="value">{report['validation_summary'].get('repairs_applied', 0)}</div>
            </div>
        </div>
        
        {self._generate_error_details(report['validation_summary'])}
    </div>
    
    <div class="section">
        <h2>自定义规则检查</h2>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="label">总规则数</div>
                <div class="value">{report['custom_checks_summary'].get('total_rules', 0)}</div>
            </div>
            <div class="stat-item">
                <div class="label">通过规则</div>
                <div class="value" style="color: #28a745;">{report['custom_checks_summary'].get('passed_rules', 0)}</div>
            </div>
            <div class="stat-item">
                <div class="label">失败规则</div>
                <div class="value" style="color: #dc3545;">{report['custom_checks_summary'].get('failed_rules', 0)}</div>
            </div>
            <div class="stat-item">
                <div class="label">问题总数</div>
                <div class="value">{report['custom_checks_summary'].get('total_issues', 0)}</div>
            </div>
        </div>
        
        {self._generate_failed_rules_table(report['custom_checks_summary'])}
    </div>
    
    <div class="section">
        <h2>文档统计</h2>
        <div class="stats-grid">
            {self._generate_statistics(report['statistics'])}
        </div>
    </div>
    
    <div class="section">
        <h2>改进建议</h2>
        <ul class="recommendations">
            {self._generate_recommendations_html(report['recommendations'])}
        </ul>
    </div>
    
    <div class="footer">
        生成于 DITA Converter Quality Assurance Layer
    </div>
</body>
</html>"""
        
        return html
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            'passed': '✅ 通过',
            'passed_with_warnings': '⚠️ 通过（有警告）',
            'failed': '❌ 失败'
        }
        return status_map.get(status, status)
    
    def _generate_score_cards(self, scores: Dict) -> str:
        """生成分数卡片HTML"""
        cards = []
        
        score_labels = {
            'dita_compliance': 'DITA合规性',
            'structure_quality': '结构质量',
            'content_completeness': '内容完整性',
            'overall_quality': '总体质量'
        }
        
        for key, label in score_labels.items():
            if key in scores:
                value = scores[key]
                cards.append(f"""
                <div class="score-card">
                    <div class="label">{label}</div>
                    <div class="value">{value:.2f}</div>
                </div>
                """)
        
        return '\n'.join(cards)
    
    def _generate_error_details(self, validation_summary: Dict) -> str:
        """生成错误详情HTML"""
        error_details = validation_summary.get('error_details', [])
        
        if not error_details:
            return '<p style="color: #28a745;">✅ 没有验证错误</p>'
        
        items = []
        for error in error_details:
            items.append(f"""
            <li>
                <strong>[{error.get('type', 'Unknown')}]</strong> {error.get('message', '')}
                {f"<br><small>元素: {error['element']}</small>" if error.get('element') else ''}
            </li>
            """)
        
        return f'<ul class="error-list">{"".join(items)}</ul>'
    
    def _generate_failed_rules_table(self, custom_checks_summary: Dict) -> str:
        """生成失败规则表格HTML"""
        failed_rules = custom_checks_summary.get('failed_rule_details', [])
        
        if not failed_rules:
            return '<p style="color: #28a745;">✅ 所有自定义规则检查通过</p>'
        
        rows = []
        for rule in failed_rules:
            rows.append(f"""
            <tr>
                <td>{rule.get('rule', '')}</td>
                <td>{rule.get('description', '')}</td>
                <td style="text-align: center;">{rule.get('issue_count', 0)}</td>
            </tr>
            """)
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>规则名称</th>
                    <th>描述</th>
                    <th style="text-align: center;">问题数</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """
    
    def _generate_statistics(self, statistics: Dict) -> str:
        """生成统计信息HTML"""
        items = []
        
        stat_labels = {
            'xml_size': ('XML大小', 'bytes'),
            'element_count': ('元素总数', '个'),
            'word_count': ('字数', '个'),
            'line_count': ('行数', '行')
        }
        
        for key, (label, unit) in stat_labels.items():
            if key in statistics:
                value = statistics[key]
                items.append(f"""
                <div class="stat-item">
                    <div class="label">{label}</div>
                    <div class="value">{value:,} {unit}</div>
                </div>
                """)
        
        return '\n'.join(items)
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """生成建议列表HTML"""
        if not recommendations:
            return '<li>暂无建议</li>'
        
        return '\n'.join(f'<li>{rec}</li>' for rec in recommendations)
    
    def save_html_report(self, report: Dict, output_path: Path):
        """保存HTML格式的报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        html = self.generate_html_report(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"📄 HTML报告已保存: {output_path}")


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("quality_reporter")
    
    reporter = QualityReporter()
    
    # 模拟数据
    test_dita_xml = """<?xml version="1.0" encoding="UTF-8"?>
<task id="test_task">
  <title>Test Task</title>
  <taskbody>
    <steps>
      <step><cmd>Do something</cmd></step>
    </steps>
  </taskbody>
</task>"""
    
    test_validation = {
        'is_valid': True,
        'validator': 'Builtin',
        'errors': [],
        'warnings': []
    }
    
    test_custom_checks = {
        'passed': [
            {'rule': 'title_length', 'description': '标题长度检查'}
        ],
        'failed': [],
        'total_issues': 0,
        'issues_by_severity': {'error': 0, 'warning': 0, 'info': 0}
    }
    
    test_loop = {
        'success': True,
        'iterations': 1,
        'repair_history': []
    }
    
    # 生成报告
    report = reporter.generate_report(
        dita_xml=test_dita_xml,
        validation_result=test_validation,
        custom_checks_result=test_custom_checks,
        loop_result=test_loop
    )
    
    print("\n" + "="*70)
    print("质量报告:")
    print("="*70)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 保存报告
    output_dir = Path("data/output/layer4/reports")
    
    reporter.save_report(
        report,
        output_dir / "test_report.json",
        include_xml=True,
        dita_xml=test_dita_xml
    )
    
    reporter.save_html_report(
        report,
        output_dir / "test_report.html"
    )
    
    print(f"\n✅ 报告已保存到: {output_dir}")