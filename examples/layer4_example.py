"""
Layer 4 完整示例
演示质量保证的完整流程
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.layer4_quality_assurance import QAManager
from src.utils.logger import setup_logger
import json

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          Layer 4 质量保证示例                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # 初始化日志
    setup_logger("layer4_example")
    
    # 初始化QA管理器
    qa_manager = QAManager(
        use_dita_ot=False,        # 不使用DITA-OT（需要单独安装）
        use_ai_repair=True,       # 使用AI修复
        max_iterations=3          # 最大迭代3次
    )
    
    # ========== 示例1: 高质量文档 ==========
    print("\n" + "="*70)
    print("示例1: 高质量Task文档")
    print("="*70)
    
    good_task = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="task_backup_database">
  <title>Backing Up the Database</title>
  <shortdesc>Learn how to create a backup of your database</shortdesc>
  <taskbody>
    <prereq>
      <p>Before you begin:</p>
      <ul>
        <li>Ensure you have administrator privileges</li>
        <li>Verify sufficient disk space is available</li>
        <li>Stop all database connections</li>
      </ul>
    </prereq>
    <context>
      <p>Regular database backups are essential for data recovery and disaster prevention.</p>
    </context>
    <steps>
      <step>
        <cmd>Open the database management console</cmd>
        <info>Navigate to Tools > Backup Manager</info>
      </step>
      <step>
        <cmd>Select the databases to backup</cmd>
        <info>You can select multiple databases by holding Ctrl</info>
      </step>
      <step>
        <cmd>Choose the backup destination</cmd>
        <info>Recommended: Use a separate physical drive</info>
      </step>
      <step>
        <cmd>Click Start Backup</cmd>
        <stepresult>The backup process begins and shows progress</stepresult>
      </step>
    </steps>
    <result>
      <p>The database backup is created successfully. Verify the backup file exists in the destination folder.</p>
    </result>
    <example>
      <title>Backup File Example</title>
      <p>The backup file will be named: database_backup_20231215.bak</p>
    </example>
  </taskbody>
</task>"""
    
    result1 = qa_manager.process(
        dita_xml=good_task,
        content_type='Task',
        processing_metadata={
            'layer1_confidence': 0.95,
            'layer2_confidence': 0.92,
            'layer3_iterations': 1
        }
    )
    
    print(f"\n✓ 处理状态: {'成功' if result1['success'] else '失败'}")
    print(f"✓ 总体状态: {result1['quality_report']['overall_status']}")
    print(f"✓ 质量分数:")
    for key, value in result1['quality_report']['quality_scores'].items():
        print(f"    {key}: {value:.2f}")
    
    # 保存结果
    output_dir = Path("data/output/layer4/example1")
    qa_manager.save_results(result1, output_dir)
    print(f"\n💾 结果已保存: {output_dir}")
    
    # ========== 示例2: 需要修复的文档 ==========
    print("\n" + "="*70)
    print("示例2: 需要修复的Task文档")
    print("="*70)
    
    needs_repair = """<?xml version="1.0" encoding="UTF-8"?>
<task id="bad task id">
  <title>This is an extremely long title that definitely exceeds the recommended maximum length and should trigger a warning</title>
  <taskbody>
    <steps>
      <step>
        <info>This step is missing the required cmd element</info>
      </step>
      <step>
        <cmd>Do something</cmd>
      </step>
    </steps>
  </taskbody>
</task>"""
    
    result2 = qa_manager.process(
        dita_xml=needs_repair,
        content_type='Task'
    )
    
    print(f"\n✓ 处理状态: {'成功' if result2['success'] else '失败'}")
    print(f"✓ 总体状态: {result2['quality_report']['overall_status']}")
    print(f"✓ 迭代次数: {result2['step_results']['validation_loop']['iterations']}")
    print(f"✓ 修复次数: {result2['quality_report']['validation_summary']['repairs_applied']}")
    
    if result2['quality_report']['recommendations']:
        print(f"\n建议:")
        for i, rec in enumerate(result2['quality_report']['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # 保存结果
    output_dir2 = Path("data/output/layer4/example2")
    qa_manager.save_results(result2, output_dir2)
    print(f"\n💾 结果已保存: {output_dir2}")
    
    # ========== 示例3: Concept文档 ==========
    print("\n" + "="*70)
    print("示例3: Concept文档")
    print("="*70)
    
    concept_doc = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="concept_microservices">
  <title>Microservices Architecture</title>
  <shortdesc>Understanding the microservices architectural pattern</shortdesc>
  <conbody>
    <p>Microservices architecture is an approach to developing a single application as a suite of small, independently deployable services.</p>
    
    <section id="definition">
      <title>Definition</title>
      <p>Each microservice runs in its own process and communicates with lightweight mechanisms, often an HTTP-based API. These services are built around business capabilities and are independently deployable by fully automated deployment machinery.</p>
    </section>
    
    <section id="characteristics">
      <title>Key Characteristics</title>
      <p>Microservices exhibit several important characteristics:</p>
      <ul>
        <li>Componentization via Services</li>
        <li>Organized around Business Capabilities</li>
        <li>Products not Projects</li>
        <li>Smart endpoints and dumb pipes</li>
        <li>Decentralized Governance</li>
        <li>Decentralized Data Management</li>
      </ul>
    </section>
    
    <section id="benefits">
      <title>Benefits</title>
      <p>The microservices approach offers several advantages over monolithic architectures:</p>
      <p>Independent deployment allows teams to update services without affecting the entire application. Technology diversity enables using the best tool for each service. Improved fault isolation means that if one service fails, others continue to function.</p>
    </section>
    
    <section id="challenges">
      <title>Challenges</title>
      <p>Despite its benefits, microservices architecture introduces complexity in distributed system coordination, data consistency, and operational overhead.</p>
    </section>
    
    <note type="note">Microservices are not a silver bullet and may not be suitable for all applications, especially small projects with limited team size.</note>
  </conbody>
</concept>"""
    
    result3 = qa_manager.process(
        dita_xml=concept_doc,
        content_type='Concept'
    )
    
    print(f"\n✓ 处理状态: {'成功' if result3['success'] else '失败'}")
    print(f"✓ 质量分数: {result3['quality_report']['quality_scores']['overall_quality']:.2f}")
    
    # 保存结果
    output_dir3 = Path("data/output/layer4/example3")
    qa_manager.save_results(result3, output_dir3)
    print(f"\n💾 结果已保存: {output_dir3}")
    
    # ========== 示例4: 批量处理 ==========
    print("\n" + "="*70)
    print("示例4: 批量处理")
    print("="*70)
    
    batch_docs = [
        {
            'xml': good_task,
            'type': 'Task',
            'metadata': {'source': 'example1', 'layer2_confidence': 0.92}
        },
        {
            'xml': concept_doc,
            'type': 'Concept',
            'metadata': {'source': 'example3', 'layer2_confidence': 0.88}
        }
    ]
    
    batch_result = qa_manager.process_batch(
        batch_docs,
        output_dir=Path("data/output/layer4/batch_example")
    )
    
    print(f"\n批量处理汇总:")
    print(f"  总数: {batch_result['total']}")
    print(f"  成功: {batch_result['success']}")
    print(f"  失败: {batch_result['failed']}")
    print(f"  成功率: {batch_result['success_rate']:.1%}")
    print(f"\n平均质量分数:")
    for key, value in batch_result['summary']['quality_scores'].items():
        print(f"  {key}: {value:.2f}")
    
    # ========== 总结 ==========
    print("\n" + "="*70)
    print("✅ Layer 4 示例完成！")
    print("="*70)
    print(f"\n生成的文件:")
    print(f"  - data/output/layer4/example1/ (高质量Task)")
    print(f"  - data/output/layer4/example2/ (需要修复的Task)")
    print(f"  - data/output/layer4/example3/ (Concept)")
    print(f"  - data/output/layer4/batch_example/ (批量处理)")
    print(f"\n每个目录包含:")
    print(f"  • .dita - DITA XML文件")
    print(f"  • _report.json - JSON格式报告")
    print(f"  • _report.html - HTML格式报告（在浏览器中打开查看）")

if __name__ == "__main__":
    main()