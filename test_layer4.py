"""
测试 Layer 4 - 质量保证功能
支持：
1. 手动创建的测试DITA XML
2. 从第三层输出目录读取DITA文件
"""
import sys
import json
from pathlib import Path
from src.layer4_quality_assurance.qa_manager import QAManager


def test_qa_manager_initialization():
    """测试QA管理器初始化"""
    print("\n" + "="*70)
    print("🧪 测试1: QA管理器初始化")
    print("="*70)
    
    try:
        qa_manager = QAManager(
            use_dita_ot=False,  # 暂时不使用DITA-OT
            use_ai_repair=True,
            max_iterations=3
        )
        
        print("✅ QA管理器初始化成功")
        print(f"   DITA-OT验证: {'启用' if qa_manager.use_dita_ot else '禁用'}")
        print(f"   AI修复: {'启用' if qa_manager.use_ai_repair else '禁用'}")
        print(f"   最大迭代: {qa_manager.max_iterations}")
        
        return True
    except Exception as e:
        print(f"❌ QA管理器初始化失败: {e}")
        return False


def test_task_quality_assurance():
    """测试Task类型文档的质量保证"""
    print("\n" + "="*70)
    print("🧪 测试2: Task类型文档质量保证")
    print("="*70)
    
    # 创建测试DITA XML
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="task_install_software">
  <title>安装软件</title>
  <shortdesc>学习如何安装软件包</shortdesc>
  <taskbody>
    <prereq>
      <p>在开始之前，请确保您拥有管理员权限。</p>
    </prereq>
    <steps>
      <step>
        <cmd>从官方网站下载安装程序</cmd>
        <info>选择与您的操作系统匹配的版本</info>
      </step>
      <step>
        <cmd>运行安装程序</cmd>
        <info>按照屏幕上的说明进行操作</info>
      </step>
      <step>
        <cmd>验证安装</cmd>
        <info>运行命令：software --version</info>
      </step>
    </steps>
    <result>
      <p>软件现已安装并准备使用。</p>
    </result>
  </taskbody>
</task>"""
    
    try:
        qa_manager = QAManager(use_dita_ot=False, use_ai_repair=True)
        
        print("📝 执行质量保证流程...")
        result = qa_manager.process(
            dita_xml=test_xml,
            content_type='Task',
            processing_metadata={
                'layer1_confidence': 0.92,
                'layer2_confidence': 0.87,
                'layer3_iterations': 1
            }
        )
        
        print("\n📊 质量报告摘要:")
        print(f"  处理结果: {'成功' if result['success'] else '失败'}")
        print(f"  总体状态: {result['quality_report']['overall_status']}")
        
        scores = result['quality_report']['quality_scores']
        print(f"  质量分数: {scores['overall_quality']:.2f}")
        print(f"  DITA合规性: {scores['dita_compliance']:.2f}")
        print(f"  结构质量: {scores['structure_quality']:.2f}")
        print(f"  内容完整性: {scores['content_completeness']:.2f}")
        
        validation_summary = result['quality_report']['validation_summary']
        print(f"\n🔍 验证摘要:")
        print(f"  错误数: {validation_summary['errors']}")
        print(f"  警告数: {validation_summary['warnings']}")
        print(f"  迭代次数: {validation_summary['iterations_required']}")
        
        custom_checks = result['quality_report']['custom_checks_summary']
        print(f"\n📏 自定义规则检查:")
        print(f"  规则总数: {custom_checks['total_rules']}")
        print(f"  失败规则: {custom_checks['failed_rules']}")
        print(f"  问题总数: {custom_checks['total_issues']}")
        
        # 保存结果
        output_dir = Path("data/output/layer4/task_test")
        qa_manager.save_results(result, output_dir)
        print(f"\n💾 结果已保存到: {output_dir}")
        
        return result['success']
    except Exception as e:
        print(f"❌ 质量保证测试失败: {e}")
        return False


def test_concept_quality_assurance():
    """测试Concept类型文档的质量保证"""
    print("\n" + "="*70)
    print("🧪 测试3: Concept类型文档质量保证")
    print("="*70)
    
    # 创建测试DITA XML
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="concept_software_architecture">
  <title>软件架构概念</title>
  <shortdesc>了解软件架构的基本概念</shortdesc>
  <conbody>
    <p>软件架构是软件系统的骨架和蓝图，定义了系统的组织结构、组件关系和交互方式。</p>
    <section>
      <title>架构风格</title>
      <p>常见的软件架构风格包括：</p>
      <ul>
        <li>分层架构</li>
        <li>微服务架构</li>
        <li>事件驱动架构</li>
        <li>面向服务架构</li>
      </ul>
    </section>
    <section>
      <title>核心原则</title>
      <p>好的软件架构应遵循以下原则：</p>
      <ul>
        <li>模块化设计</li>
        <li>高内聚低耦合</li>
        <li>可扩展性</li>
        <li>可维护性</li>
      </ul>
    </section>
  </conbody>
</concept>"""
    
    try:
        qa_manager = QAManager(use_dita_ot=False, use_ai_repair=True)
        
        print("📝 执行质量保证流程...")
        result = qa_manager.process(
            dita_xml=test_xml,
            content_type='Concept',
            processing_metadata={}
        )
        
        print("\n📊 质量报告摘要:")
        print(f"  处理结果: {'成功' if result['success'] else '失败'}")
        print(f"  总体状态: {result['quality_report']['overall_status']}")
        print(f"  质量分数: {result['quality_report']['quality_scores']['overall_quality']:.2f}")
        
        return result['success']
    except Exception as e:
        print(f"❌ Concept质量保证测试失败: {e}")
        return False


def test_reference_quality_assurance():
    """测试Reference类型文档的质量保证"""
    print("\n" + "="*70)
    print("🧪 测试4: Reference类型文档质量保证")
    print("="*70)
    
    # 创建测试DITA XML
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="reference_api_function">
  <title>API函数参考</title>
  <shortdesc>常用API函数的详细说明</shortdesc>
  <refbody>
    <section>
      <title>get_user_info()</title>
      <prolog>
        <metadata>
          <keywords>
            <keyword>API</keyword>
            <keyword>用户</keyword>
            <keyword>信息</keyword>
          </keywords>
        </metadata>
      </prolog>
      <refsyn>
        <codeblock language="python">
def get_user_info(user_id):
    pass</codeblock>
      </refsyn>
      <section>
        <title>参数</title>
        <dl>
          <dlentry>
            <dt>user_id</dt>
            <dd>
              <p>用户的唯一标识符</p>
              <p><b>类型:</b> string</p>
            </dd>
          </dlentry>
        </dl>
      </section>
      <section>
        <title>返回值</title>
        <p>包含用户信息的字典，包括：</p>
        <ul>
          <li><b>id</b>: 用户ID</li>
          <li><b>name</b>: 用户名</li>
          <li><b>email</b>: 邮箱地址</li>
          <li><b>created_at</b>: 创建时间</li>
        </ul>
      </section>
    </section>
  </refbody>
</reference>"""
    
    try:
        qa_manager = QAManager(use_dita_ot=False, use_ai_repair=True)
        
        print("📝 执行质量保证流程...")
        result = qa_manager.process(
            dita_xml=test_xml,
            content_type='Reference',
            processing_metadata={}
        )
        
        print("\n📊 质量报告摘要:")
        print(f"  处理结果: {'成功' if result['success'] else '失败'}")
        print(f"  总体状态: {result['quality_report']['overall_status']}")
        print(f"  质量分数: {result['quality_report']['quality_scores']['overall_quality']:.2f}")
        
        return result['success']
    except Exception as e:
        print(f"❌ Reference质量保证测试失败: {e}")
        return False


def test_batch_processing():
    """测试批量文档质量保证"""
    print("\n" + "="*70)
    print("🧪 测试5: 批量文档质量保证")
    print("="*70)
    
    # 创建测试文档列表
    test_docs = [
        {
            'xml': """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="task_test1">
  <title>测试任务1</title>
  <taskbody>
    <steps>
      <step>
        <cmd>执行步骤1</cmd>
      </step>
      <step>
        <cmd>执行步骤2</cmd>
      </step>
    </steps>
  </taskbody>
</task>""",
            'type': 'Task',
            'metadata': {'source': 'batch_test1'}
        },
        {
            'xml': """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="concept_test1">
  <title>测试概念1</title>
  <conbody>
    <p>这是一个测试概念文档。</p>
  </conbody>
</concept>""",
            'type': 'Concept',
            'metadata': {'source': 'batch_test2'}
        },
        {
            'xml': """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="reference_test1">
  <title>测试参考1</title>
  <refbody>
    <section>
      <title>测试部分</title>
      <p>这是一个测试参考文档。</p>
    </section>
  </refbody>
</reference>""",
            'type': 'Reference',
            'metadata': {'source': 'batch_test3'}
        }
    ]
    
    try:
        qa_manager = QAManager(use_dita_ot=False, use_ai_repair=True)
        
        print(f"📝 批量处理 {len(test_docs)} 个文档...")
        output_dir = Path("data/output/layer4/batch_test")
        
        batch_result = qa_manager.process_batch(
            dita_documents=test_docs,
            output_dir=output_dir
        )
        
        print("\n📊 批量处理结果:")
        print(f"  总数: {batch_result['total']}")
        print(f"  成功: {batch_result['success']}")
        print(f"  失败: {batch_result['failed']}")
        print(f"  成功率: {batch_result['success_rate']:.1%}")
        
        # 显示摘要统计
        summary = batch_result['summary']
        print(f"\n📊 质量摘要:")
        print(f"  平均质量分数: {summary['quality_scores']['avg_overall_quality']:.2f}")
        print(f"  平均DITA合规性: {summary['quality_scores']['avg_dita_compliance']:.2f}")
        print(f"  平均结构质量: {summary['quality_scores']['avg_structure_quality']:.2f}")
        print(f"  平均内容完整性: {summary['quality_scores']['avg_content_completeness']:.2f}")
        
        print(f"\n💾 结果已保存到: {output_dir}")
        
        return batch_result['success_rate'] > 0
    except Exception as e:
        print(f"❌ 批量处理测试失败: {e}")
        return False


def test_custom_rules_check():
    """测试自定义规则检查"""
    print("\n" + "="*70)
    print("🧪 测试6: 自定义规则检查")
    print("="*70)
    
    # 创建一个可能违反某些规则的DITA XML
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="test_task_with_issues">
  <!-- 缺少title元素 -->
  <taskbody>
    <steps>
      <step>
        <cmd>执行步骤1，这是一个非常非常非常长的命令，可能会违反长度限制规则</cmd>
      </step>
    </steps>
  </taskbody>
</task>"""
    
    try:
        qa_manager = QAManager(use_dita_ot=False, use_ai_repair=False)
        
        print("📝 执行自定义规则检查...")
        
        # 直接调用自定义规则检查
        custom_checks = qa_manager.custom_rules_checker.check(test_xml)
        
        print(f"\n📊 自定义规则检查结果:")
        print(f"  规则总数: {len(custom_checks['passed']) + len(custom_checks['failed'])}")
        print(f"  通过规则数: {len(custom_checks['passed'])}")
        print(f"  失败规则数: {len(custom_checks['failed'])}")
        print(f"  通过规则: {[r['rule'] for r in custom_checks['passed']]}")
        print(f"  失败规则: {[r['rule'] for r in custom_checks['failed']]}")
        print(f"  问题总数: {custom_checks['total_issues']}")
        
        if custom_checks['failed']:
            print("\n⚠️  发现的问题:")
            for failed_rule in custom_checks['failed']:
                print(f"\n  📋 规则: {failed_rule['rule']}")
                print(f"     描述: {failed_rule['description']}")
                print(f"     问题数: {len(failed_rule['issues'])}")
                
                for i, issue in enumerate(failed_rule['issues'], 1):
                    print(f"     {i}. {issue}")
        
        return True
    except Exception as e:
        print(f"❌ 自定义规则检查测试失败: {e}")
        return False


def test_layer3_output_directory():
    """测试处理第三层输出目录中的所有DITA文件"""
    print("\n" + "="*70)
    print("🧪 测试7: 处理第三层输出目录")
    print("="*70)
    
    # 默认第三层输出目录
    default_layer3_dir = Path("data/output/2023CVPR-CoMFormer/layer3")
    
    # 允许从命令行参数指定目录
    if len(sys.argv) > 1:
        layer3_dir = Path(sys.argv[1])
    else:
        layer3_dir = default_layer3_dir
    
    if not layer3_dir.exists():
        print(f"❌ 第三层输出目录不存在: {layer3_dir}")
        return False
    
    print(f"📁 第三层输出目录: {layer3_dir}")
    
    # 读取所有DITA文件
    dita_files = list(layer3_dir.glob("*.dita"))
    
    if not dita_files:
        print(f"❌ 目录中没有找到DITA文件")
        return False
    
    print(f"📄 找到 {len(dita_files)} 个DITA文件")
    
    # 读取layer3_result.json获取元数据
    layer3_result_file = layer3_dir / "layer3_result.json"
    layer3_metadata = {}
    
    if layer3_result_file.exists():
        with open(layer3_result_file, 'r', encoding='utf-8') as f:
            layer3_result = json.load(f)
            print(f"✓ 读取第三层结果: {layer3_result['success']}/{layer3_result['total']} 成功")
            
            # 构建文件名到元数据的映射
            for result in layer3_result.get('results', []):
                if result['success']:
                    # 从title生成文件名（与layer3保存时的逻辑一致）
                    content_type = result['content_type']
                    title = result['title']
                    safe_title = "".join(c if c.isalnum() else '_' for c in title)[:50]
                    
                    # 查找匹配的文件
                    for dita_file in dita_files:
                        if content_type.lower() in dita_file.name.lower() and safe_title in dita_file.name:
                            layer3_metadata[dita_file.name] = {
                                'content_type': content_type,
                                'title': title,
                                'layer3_iterations': result['validation'].get('iterations', 0)
                            }
                            break
    
    # 准备批量处理的文档
    dita_documents = []
    
    for dita_file in sorted(dita_files):
        try:
            with open(dita_file, 'r', encoding='utf-8') as f:
                dita_xml = f.read()
            
            # 从文件名推断内容类型
            filename = dita_file.name
            if 'concept' in filename.lower():
                content_type = 'Concept'
            elif 'task' in filename.lower():
                content_type = 'Task'
            elif 'reference' in filename.lower():
                content_type = 'Reference'
            else:
                content_type = 'Concept'  # 默认
            
            # 获取元数据
            metadata = layer3_metadata.get(filename, {})
            if not metadata:
                metadata = {
                    'content_type': content_type,
                    'title': filename,
                    'layer3_iterations': 0
                }
            
            dita_documents.append({
                'xml': dita_xml,
                'type': metadata.get('content_type', content_type),
                'metadata': {
                    'filename': filename,
                    'title': metadata.get('title', filename),
                    'layer3_iterations': metadata.get('layer3_iterations', 0),
                    'source': 'layer3_output'
                }
            })
            
            print(f"  ✓ 加载: {filename} ({metadata.get('content_type', content_type)})")
            
        except Exception as e:
            print(f"  ✗ 加载失败 {filename}: {e}")
    
    if not dita_documents:
        print("❌ 没有成功加载任何DITA文档")
        return False
    
    print(f"\n✅ 成功加载 {len(dita_documents)} 个DITA文档")
    
    # 创建输出目录
    output_dir = layer3_dir.parent / "layer4"
    output_dir.mkdir(exist_ok=True)
    print(f"📁 输出目录: {output_dir}")
    
    # 批量处理
    try:
        qa_manager = QAManager(use_dita_ot=False, use_ai_repair=True, max_iterations=3)
        
        print(f"\n📝 开始批量质量保证处理...")
        batch_result = qa_manager.process_batch(
            dita_documents=dita_documents,
            output_dir=output_dir
        )
        
        print("\n📊 批量处理结果:")
        print(f"  总数: {batch_result['total']}")
        print(f"  成功: {batch_result['success']}")
        print(f"  失败: {batch_result['failed']}")
        print(f"  成功率: {batch_result['success_rate']:.1%}")
        
        # 显示摘要统计
        summary = batch_result['summary']
        print(f"\n📊 质量摘要:")
        print(f"  平均质量分数: {summary['quality_scores']['avg_overall_quality']:.2f}")
        print(f"  平均DITA合规性: {summary['quality_scores']['avg_dita_compliance']:.2f}")
        print(f"  平均结构质量: {summary['quality_scores']['avg_structure_quality']:.2f}")
        print(f"  平均内容完整性: {summary['quality_scores']['avg_content_completeness']:.2f}")
        
        print(f"\n💾 结果已保存到: {output_dir}")
        
        return batch_result['success_rate'] > 0
        
    except Exception as e:
        print(f"❌ 批量处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 开始测试 Layer 4 - 质量保证功能...\n")
    print("="*70)
    print("💡 使用说明:")
    print("  1. 不带参数运行: 执行所有内置测试")
    print("  2. 带参数运行: python test_layer4.py <layer3_output_dir>")
    print("     例如: python test_layer4.py data/output/2023CVPR-CoMFormer/layer3")
    print("="*70)
    
    # 如果提供了命令行参数，只运行第三层输出测试
    if len(sys.argv) > 1:
        print("\n🎯 模式: 处理第三层输出目录")
        if test_layer3_output_directory():
            print("\n✅ 第三层输出处理成功！")
            sys.exit(0)
        else:
            print("\n❌ 第三层输出处理失败！")
            sys.exit(1)
    
    # 否则运行所有测试
    print("\n🎯 模式: 运行所有内置测试")
    
    tests = [
        ("QA管理器初始化", test_qa_manager_initialization),
        ("Task类型质量保证", test_task_quality_assurance),
        ("Concept类型质量保证", test_concept_quality_assurance),
        ("Reference类型质量保证", test_reference_quality_assurance),
        ("批量文档处理", test_batch_processing),
        ("自定义规则检查", test_custom_rules_check),
        ("处理第三层输出", test_layer3_output_directory)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} - 通过")
            else:
                print(f"\n❌ {test_name} - 失败")
        except Exception as e:
            print(f"\n❌ {test_name} - 异常: {e}")
    
    print("\n" + "="*70)
    print("📊 测试结果总结")
    print("="*70)
    print(f"总测试数: {total}")
    print(f"通过测试数: {passed}")
    print(f"失败测试数: {total - passed}")
    print(f"通过率: {passed / total * 100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        print("✅ Layer 4 质量保证功能测试成功！")
    else:
        print("\n⚠️  部分测试失败，请检查并修复问题。")
