"""
测试Layer 3 - DITA转换功能
测试当前架构的DITAConverter组件
支持从Layer 2的输出读取数据
"""
import json
import argparse
from pathlib import Path
from src.utils.config import Config
from src.layer3_dita_conversion import DITAConverter

def test_from_layer2_output(layer2_output_dir: Path, use_ai: bool = False):
    """从Layer 2的输出读取数据并进行DITA转换
    
    Args:
        layer2_output_dir: Layer 2的输出目录
        use_ai: 是否使用AI功能
        
    Returns:
        bool: 测试是否通过
    """
    print("\n" + "="*70)
    print("🧪 从Layer 2输出进行DITA转换")
    print("="*70)
    
    # 读取Layer 2的结果文件
    layer2_result_file = layer2_output_dir / "layer2_result.json"
    if not layer2_result_file.exists():
        print(f"❌ 未找到Layer 2结果文件: {layer2_result_file}")
        return False
    
    print(f"📄 读取Layer 2结果: {layer2_result_file}")
    
    with open(layer2_result_file, 'r', encoding='utf-8') as f:
        layer2_result = json.load(f)
    
    chunks = layer2_result.get('chunks', [])
    if not chunks:
        print(f"❌ Layer 2结果中没有语义块")
        return False
    
    print(f"✅ 读取成功: {len(chunks)} 个语义块")
    print(f"   类型分布: {layer2_result['statistics']['type_distribution']}")
    print(f"   平均置信度: {layer2_result['statistics']['overall_avg_confidence']:.2f}")
    
    # 创建Layer 3输出目录
    output_dir = layer2_output_dir.parent / "layer3"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 确保每个chunk都有type字段
    type_dist = layer2_result['statistics']['type_distribution']
    primary_type = max(type_dist.items(), key=lambda x: x[1])[0] if type_dist else "Concept"
    
    for chunk in chunks:
        if 'type' not in chunk and 'classification' in chunk:
            chunk['type'] = chunk['classification']['type']
        elif 'type' not in chunk:
            chunk['type'] = primary_type
    
    # 使用Layer 3进行DITA转换
    print(f"\n3️⃣  使用Layer 3进行DITA批量转换...")
    converter = DITAConverter(use_ai=use_ai, max_fix_iterations=3)
    layer3_result = converter.convert_batch(chunks, output_dir=output_dir)
    
    # 保存Layer 3结果
    layer3_result_file = output_dir / "layer3_result.json"
    with open(layer3_result_file, 'w', encoding='utf-8') as f:
        json.dump(layer3_result, f, ensure_ascii=False, indent=2)
    
    # 显示结果
    if layer3_result['failed'] > 0:
        print(f"⚠️  DITA转换部分失败: {layer3_result['failed']} 个块失败")
    else:
        print(f"✅ DITA批量转换成功！")
    
    print(f"   总数: {layer3_result['total']}")
    print(f"   成功: {layer3_result['success']}")
    print(f"   失败: {layer3_result['failed']}")
    print(f"   成功率: {layer3_result['success_rate']:.1%}")
    print(f"   输出已保存到: {output_dir}")
    
    # 显示成功转换的前几个DITA文件
    print(f"\n📄 成功转换的DITA文件:")
    success_count = 0
    for result in layer3_result['results']:
        if result['success']:
            print(f"   ✅ {result['title']} ({result['content_type']})")
            success_count += 1
            if success_count >= 5:
                if layer3_result['success'] > 5:
                    print(f"   ... 还有 {layer3_result['success'] - 5} 个成功转换的文件")
                break
    
    return True


def test_dita_converter():
    """测试DITAConverter组件"""
    print("\n" + "="*70)
    print("🧪 测试DITA转换器")
    print("="*70)
    
    # 创建DITA转换器
    converter = DITAConverter(use_ai=False)  # 不使用AI，避免消耗额度
    
    # 测试1: Task类型转换
    print("\n📝 测试1: Task主题转换")
    task_content = """
    安装Git步骤：
    1. 访问Git官网下载安装包
    2. 运行安装程序，保持默认设置
    3. 打开终端验证安装：git --version
    """
    
    task_result = converter.convert(
        content=task_content,
        title="安装Git",
        content_type="Task"
    )
    
    print(f"✅ Task转换状态: {'成功' if task_result['success'] else '失败'}")
    if task_result['success']:
        print(f"📄 XML预览: {task_result['dita_xml'][:300]}...")
    
    # 测试2: Concept类型转换
    print("\n📝 测试2: Concept主题转换")
    concept_content = """
    DITA（Darwin Information Typing Architecture）是一种基于XML的信息架构标准。
    它将文档分为三种主要类型：概念（Concept）、任务（Task）和参考（Reference）。
    DITA的核心优势在于内容重用和多渠道发布。
    """
    
    concept_result = converter.convert(
        content=concept_content,
        title="什么是DITA",
        content_type="Concept"
    )
    
    print(f"✅ Concept转换状态: {'成功' if concept_result['success'] else '失败'}")
    if concept_result['success']:
        print(f"📄 XML预览: {concept_result['dita_xml'][:300]}...")
    
    # 测试3: Reference类型转换
    print("\n📝 测试3: Reference主题转换")
    reference_content = """
    print()函数参数：
    objects: 要打印的对象
    sep: 分隔符（默认空格）
    end: 结束符（默认换行）
    返回值：无
    """
    
    reference_result = converter.convert(
        content=reference_content,
        title="print()函数参考",
        content_type="Reference"
    )
    
    print(f"✅ Reference转换状态: {'成功' if reference_result['success'] else '失败'}")
    if reference_result['success']:
        print(f"📄 XML预览: {reference_result['dita_xml'][:300]}...")
    
    # 保存测试结果
    output_dir = Config.OUTPUT_DIR / "test_new"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存Task结果
    if task_result['success']:
        with open(output_dir / "test_task.dita", "w", encoding="utf-8") as f:
            f.write(task_result['dita_xml'])
    
    # 保存Concept结果
    if concept_result['success']:
        with open(output_dir / "test_concept.dita", "w", encoding="utf-8") as f:
            f.write(concept_result['dita_xml'])
    
    # 保存Reference结果
    if reference_result['success']:
        with open(output_dir / "test_reference.dita", "w", encoding="utf-8") as f:
            f.write(reference_result['dita_xml'])
    
    print(f"\n📁 测试结果保存到: {output_dir}")
    
    return task_result['success'] and concept_result['success'] and reference_result['success']

if __name__ == "__main__":
    print("🧪 开始测试 Layer 3 - DITA转换功能...\n")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试Layer 3 - DITA转换功能')
    parser.add_argument('--layer2-output', type=str, help='Layer 2的输出目录路径')
    parser.add_argument('--use-ai', action='store_true', help='是否使用AI功能')
    parser.add_argument('--basic-test', action='store_true', help='运行基础测试（不需要Layer 2输出）')
    
    args = parser.parse_args()
    
    success = True
    
    # 如果指定了Layer 2输出目录，从该目录读取数据
    if args.layer2_output:
        layer2_output_dir = Path(args.layer2_output)
        if not layer2_output_dir.exists():
            print(f"❌ Layer 2输出目录不存在: {layer2_output_dir}")
            success = False
        else:
            success = test_from_layer2_output(layer2_output_dir, use_ai=args.use_ai)
    
    # 运行基础测试
    elif args.basic_test:
        success = test_dita_converter()
    
    else:
        print("使用方法:")
        print("  从Layer 2输出读取: python test_layer3_new.py --layer2-output <layer2输出目录>")
        print("  运行基础测试:      python test_layer3_new.py --basic-test")
        print("  使用AI功能:        添加 --use-ai 参数")
        print("\n示例:")
        print("  python test_layer3_new.py --layer2-output data/output/2023CVPR-CoMFormer/layer2")
        print("  python test_layer3_new.py --layer2-output data/output/2023CVPR-CoMFormer/layer2 --use-ai")
        print("  python test_layer3_new.py --basic-test")
        success = False
    
    print("\n" + "="*70)
    if success:
        print("✅ Layer 3 DITA转换器测试成功！")
    else:
        print("❌ Layer 3 DITA转换器测试失败或未运行！")
    print("="*70)