"""
Layer 3 完整示例
演示DITA转换的完整流程
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.layer3_dita_conversion import DITAConverter
from src.utils.logger import setup_logger
import json

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          Layer 3 DITA转换示例                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # 初始化日志
    setup_logger("layer3_example")
    
    # 初始化转换器
    converter = DITAConverter(use_ai=True, max_fix_iterations=3)
    
    # ========== 示例1: Task转换 ==========
    print("\n" + "="*70)
    print("示例1: 转换 Task 类型内容")
    print("="*70)
    
    task_content = """
    Prerequisites:
    - Python 3.8 or higher installed
    - pip package manager available
    - Administrator/root privileges
    
    Installation Steps:
    
    1. Open a terminal or command prompt
    2. Download the package using pip:
       pip install dita-converter
    3. Verify the installation:
       dita-converter --version
    4. Configure the tool:
       Edit the config file at ~/.dita-converter/config.yaml
    
    Expected Result:
    You should see the version number displayed, indicating successful installation.
    
    Example Output:
    dita-converter version 1.0.0
    """
    
    task_result = converter.convert(
        content=task_content,
        title="Installing DITA Converter",
        content_type="Task"
    )
    
    print(f"\n✓ 转换状态: {'成功' if task_result['success'] else '失败'}")
    print(f"✓ 迭代次数: {task_result['metadata']['iterations']}")
    
    if task_result['success']:
        # 保存文件
        output_file = Path("data/output/layer3/example_task.dita")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(task_result['dita_xml'])
        print(f"✓ DITA文件已保存: {output_file}")
        
        # 显示预览
        print(f"\nDITA XML预览:")
        print("-" * 70)
        print(task_result['dita_xml'][:800] + "\n...")
    else:
        print(f"\n错误:")
        for error in task_result['errors']:
            print(f"  - {error}")
    
    # ========== 示例2: Concept转换 ==========
    print("\n" + "="*70)
    print("示例2: 转换 Concept 类型内容")
    print("="*70)
    
    concept_content = """
    DITA (Darwin Information Typing Architecture) is an XML-based architecture 
    for authoring, producing, and delivering technical information.
    
    Definition:
    DITA is an open standard that defines a set of document types for authoring 
    and organizing topic-oriented information, as well as a set of mechanisms 
    for combining, extending, and constraining document types.
    
    Key Characteristics:
    
    Topic-Based Authoring:
    DITA content is organized into topics, which are discrete units of information.
    Each topic covers a single subject and can be reused across multiple documents.
    
    Separation of Content and Format:
    DITA separates content from presentation, allowing the same content to be 
    published in multiple formats (PDF, HTML, mobile apps, etc.).
    
    Content Reuse:
    Through features like conref (content reference) and keyrefs, DITA enables 
    extensive content reuse, reducing redundancy and maintenance costs.
    
    Specialization:
    Organizations can extend DITA to meet specific needs while maintaining 
    compatibility with standard DITA tools and processes.
    
    Note: DITA was originally developed by IBM and is now maintained by OASIS.
    """
    
    concept_result = converter.convert(
        content=concept_content,
        title="Understanding DITA",
        content_type="Concept"
    )
    
    print(f"\n✓ 转换状态: {'成功' if concept_result['success'] else '失败'}")
    
    if concept_result['success']:
        output_file = Path("data/output/layer3/example_concept.dita")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(concept_result['dita_xml'])
        print(f"✓ DITA文件已保存: {output_file}")
    
    # ========== 示例3: Reference转换 ==========
    print("\n" + "="*70)
    print("示例3: 转换 Reference 类型内容")
    print("="*70)
    
    reference_content = """
    Command-Line Options for DITA Converter
    
    The following table lists the available command-line options:
    
    | Option | Type | Default | Description |
    |--------|------|---------|-------------|
    | --input | string | - | Input file path (required) |
    | --output | string | ./output | Output directory |
    | --format | string | dita | Output format (dita, html, pdf) |
    | --validate | boolean | true | Enable validation |
    | --log-level | string | info | Logging level (debug, info, warn, error) |
    | --max-threads | integer | 4 | Maximum number of threads |
    | --timeout | integer | 300 | Operation timeout in seconds |
    
    Configuration Parameters:
    
    AI Service:
    - api_key: Your API key for the AI service
    - model: Model name (qwen-flash, qwen-plus, qwen-max)
    - temperature: Controls randomness (0.0 - 1.0)
    
    Processing:
    - chunk_size: Maximum chunk size in characters (default: 2000)
    - min_confidence: Minimum classification confidence (default: 0.6)
    
    Output:
    - pretty_print: Format XML with indentation (default: true)
    - include_metadata: Include processing metadata (default: true)
    """
    
    reference_result = converter.convert(
        content=reference_content,
        title="Command-Line Reference",
        content_type="Reference"
    )
    
    print(f"\n✓ 转换状态: {'成功' if reference_result['success'] else '失败'}")
    
    if reference_result['success']:
        output_file = Path("data/output/layer3/example_reference.dita")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(reference_result['dita_xml'])
        print(f"✓ DITA文件已保存: {output_file}")
    
    # ========== 批量转换示例 ==========
    print("\n" + "="*70)
    print("示例4: 批量转换")
    print("="*70)
    
    chunks = [
        {
            'content': task_content,
            'title': 'Installing DITA Converter',
            'type': 'Task'
        },
        {
            'content': concept_content,
            'title': 'Understanding DITA',
            'type': 'Concept'
        },
        {
            'content': reference_content,
            'title': 'Command-Line Reference',
            'type': 'Reference'
        }
    ]
    
    batch_result = converter.convert_batch(
        chunks,
        output_dir=Path("data/output/layer3/batch_example")
    )
    
    print(f"\n批量转换汇总:")
    print(f"  总数: {batch_result['total']}")
    print(f"  成功: {batch_result['success']}")
    print(f"  失败: {batch_result['failed']}")
    print(f"  成功率: {batch_result['success_rate']:.1%}")
    
    # 保存批量报告
    report_file = Path("data/output/layer3/batch_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 移除XML内容以减小报告大小
    slim_results = []
    for r in batch_result['results']:
        slim_r = r.copy()
        if 'dita_xml' in slim_r:
            slim_r['dita_xml_length'] = len(slim_r['dita_xml'])
            del slim_r['dita_xml']
        slim_results.append(slim_r)
    
    batch_result['results'] = slim_results
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(batch_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 批量报告已保存: {report_file}")
    
    print("\n" + "="*70)
    print("✅ Layer 3 示例完成！")
    print("="*70)
    print(f"\n生成的文件:")
    print(f"  - data/output/layer3/example_task.dita")
    print(f"  - data/output/layer3/example_concept.dita")
    print(f"  - data/output/layer3/example_reference.dita")
    print(f"  - data/output/layer3/batch_example/*.dita")
    print(f"  - data/output/layer3/batch_report.json")

if __name__ == "__main__":
    main()