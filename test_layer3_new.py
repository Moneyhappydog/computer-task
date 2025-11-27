"""
测试Layer 3 - DITA转换功能
测试当前架构的DITAConverter组件
"""
from pathlib import Path
from src.utils.config import Config
from src.layer3_dita_conversion import DITAConverter

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
    
    # 运行测试
    success = test_dita_converter()
    
    print("\n" + "="*70)
    if success:
        print("✅ Layer 3 DITA转换器测试成功！")
    else:
        print("❌ Layer 3 DITA转换器测试失败！")
    print("="*70)