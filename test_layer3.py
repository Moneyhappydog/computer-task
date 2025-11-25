"""
测试Layer 3 - DITA转换功能
"""
from pathlib import Path
from src.utils.config import Config
from src.layer1_preprocessing import PDFProcessor
from src.layer3_dita import DITATemplates, DITAMap, DITAConverter

def test_dita_templates():
    """测试DITA模板生成"""
    print("\n" + "="*70)
    print("🧪 测试DITA模板")
    print("="*70)
    
    templates = DITATemplates()
    
    # 测试1: Concept模板
    print("\n📝 测试1: Concept主题")
    concept_xml = templates.create_concept(
        title="什么是DITA",
        content="""DITA（Darwin Information Typing Architecture）是一种基于XML的信息架构标准。

它将文档分为三种主要类型：概念（Concept）、任务（Task）和参考（Reference）。

DITA的核心优势在于内容重用和多渠道发布。""",
        id="concept_what_is_dita",
        metadata={
            "author": "测试作者",
            "keywords": ["DITA", "XML", "技术写作"],
            "summary": "介绍DITA信息架构标准的基本概念"
        }
    )
    
    print("✅ Concept XML生成成功")
    print(f"预览:\n{concept_xml[:500]}...\n")
    
    # 测试2: Task模板
    print("📝 测试2: Task主题")
    task_xml = templates.create_task(
        title="安装Python环境",
        steps=[
            {"cmd": "访问Python官网下载安装包"},
            {"cmd": "运行安装程序", "info": "确保勾选'Add Python to PATH'选项"},
            {"cmd": "验证安装", "example": "python --version"}
        ],
        id="task_install_python",
        prereq="需要管理员权限",
        context="本任务指导您在Windows系统上安装Python 3.8+"
    )
    
    print("✅ Task XML生成成功")
    print(f"预览:\n{task_xml[:500]}...\n")
    
    # 测试3: Reference模板
    print("📝 测试3: Reference主题")
    reference_xml = templates.create_reference(
        title="API参数说明",
        sections=[
            {
                "title": "请求参数",
                "list": ["api_key: API密钥（必需）", "format: 响应格式（可选，默认json）"]
            },
            {
                "title": "响应格式",
                "content": "API返回JSON格式的数据"
            }
        ],
        id="ref_api_parameters"
    )
    
    print("✅ Reference XML生成成功")
    print(f"预览:\n{reference_xml[:500]}...\n")
    
    # 保存示例文件
    output_dir = Config.OUTPUT_DIR / "test_templates"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    (output_dir / "concept_example.dita").write_text(concept_xml, encoding='utf-8')
    (output_dir / "task_example.dita").write_text(task_xml, encoding='utf-8')
    (output_dir / "reference_example.dita").write_text(reference_xml, encoding='utf-8')
    
    print(f"✅ 示例文件已保存到: {output_dir}")
    
    return True

def test_dita_map():
    """测试DITA Map生成"""
    print("\n" + "="*70)
    print("🧪 测试DITA Map")
    print("="*70)
    
    # 创建DITA Map
    dita_map = DITAMap(title="Python入门指南", map_id="python_guide")
    
    # 添加topics（模拟层级结构）
    dita_map.add_topic("introduction.dita", "简介", "concept", level=1)
    dita_map.add_topic("what_is_python.dita", "什么是Python", "concept", level=2)
    dita_map.add_topic("why_python.dita", "为什么选择Python", "concept", level=2)
    
    dita_map.add_topic("installation.dita", "安装", "task", level=1)
    dita_map.add_topic("install_windows.dita", "Windows安装", "task", level=2)
    dita_map.add_topic("install_mac.dita", "Mac安装", "task", level=2)
    
    dita_map.add_topic("api_reference.dita", "API参考", "reference", level=1)
    
    # 生成Map XML
    map_xml = dita_map.generate()
    
    print("✅ DITA Map生成成功")
    print(f"预览:\n{map_xml[:600]}...\n")
    
    # 保存Map文件
    output_dir = Config.OUTPUT_DIR / "test_templates"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    map_file = output_dir / "python_guide.ditamap"
    map_file.write_text(map_xml, encoding='utf-8')
    
    print(f"✅ Map文件已保存: {map_file}")
    
    return True

def test_content_converter():
    """测试内容转换器"""
    print("\n" + "="*70)
    print("🧪 测试内容转换器")
    print("="*70)
    
    from src.layer3_dita import ContentConverter
    
    # 创建转换器（不使用AI，避免消耗额度）
    converter = ContentConverter(use_ai=False)
    
    # 测试文本
    test_text = """# 安装Git

Git是一个分布式版本控制系统。

## 安装步骤

1. 访问 https://git-scm.com 下载安装包
2. 运行安装程序，保持默认设置
3. 打开终端，验证安装

验证命令：
git --version

## 配置Git

安装完成后，需要配置用户信息：

1. 设置用户名：git config --global user.name "Your Name"
2. 设置邮箱：git config --global user.email "email@example.com"
"""
    
    # 测试1: 转换为Task
    print("\n📝 测试1: 转换为Task主题")
    task_xml = converter.convert_to_task(
        text=test_text,
        title="安装Git",
        topic_id="task_install_git"
    )
    
    print("✅ Task转换成功")
    print(f"提取的步骤数: {task_xml.count('<step>')}")
    
    # 测试2: 转换为Concept
    concept_text = """# 什么是版本控制

版本控制是一种记录文件变化的系统，以便将来查阅特定版本。

## 版本控制的优势

使用版本控制系统可以：
- 追踪每个文件的修改历史
- 在不同版本之间切换
- 多人协作开发
"""
    
    print("\n📝 测试2: 转换为Concept主题")
    concept_xml = converter.convert_to_concept(
        text=concept_text,
        title="什么是版本控制",
        topic_id="concept_version_control"
    )
    
    print("✅ Concept转换成功")
    
    # 保存示例
    output_dir = Config.OUTPUT_DIR / "test_converter"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    (output_dir / "task_install_git.dita").write_text(task_xml, encoding='utf-8')
    (output_dir / "concept_version_control.dita").write_text(concept_xml, encoding='utf-8')
    
    print(f"\n✅ 转换文件已保存到: {output_dir}")
    
    return True

def test_full_conversion():
    """测试完整文档转换"""
    print("\n" + "="*70)
    print("🧪 测试完整DITA转换")
    print("="*70)
    
    # 检查是否有PDF文件
    test_pdf = Config.INPUT_DIR / "test.pdf"
    
    if not test_pdf.exists():
        print("⚠️  未找到test.pdf，使用示例文本")
        
        # 使用示例Markdown文档
        test_text = """# Python编程入门

本文档介绍Python编程的基础知识。

## 什么是Python

Python是一种解释型、面向对象的高级编程语言。

### Python的特点

- 语法简洁清晰
- 强大的标准库
- 跨平台支持

## 安装Python

### Windows安装

1. 访问 python.org 下载安装包
2. 运行安装程序
3. 勾选"Add Python to PATH"
4. 点击"Install Now"

### 验证安装

打开命令提示符，输入：
python --version

## Python基础语法

### 变量和数据类型

Python支持多种数据类型：
- 整数（int）
- 浮点数（float）
- 字符串（str）
- 列表（list）

### 示例代码

```python
# 变量定义
name = "Alice"
age = 25
print(f"Hello, {name}!")
```

## API参考

### print()函数

参数：

*objects: 要打印的对象
sep: 分隔符（默认空格）
end: 结束符（默认换行）

返回值：无
"""
    else:
        # 从PDF提取文本
        print(f"📄 从PDF提取文本: {test_pdf.name}")
        processor = PDFProcessor(use_marker=False)
        result = processor.extract_text(test_pdf)
        test_text = result['text']
        print(f"✅ 提取完成: {len(test_text)} 字符")
    
    # 创建DITA转换器
    converter = DITAConverter(use_ai=False)  # 不使用AI，避免消耗额度

    # 执行转换
    output_dir = Config.OUTPUT_DIR / "test_full_conversion"

    result = converter.convert_document(
        text=test_text,
        output_dir=output_dir,
        doc_title="Python编程入门"
    )

    # 显示结果
    print("\n📊 转换结果:")
    print(f"  Map文件: {Path(result['map_file']).name}")
    print(f"  Topics数量: {len(result['topics'])}")
    print(f"\n📈 统计信息:")
    for key, value in result['statistics'].items():
        print(f"    {key}: {value}")

    print(f"\n📁 输出目录: {output_dir}")
    print("\n生成的文件:")
    for file in sorted(output_dir.glob("*.dita*")):
        print(f"  - {file.name}")

    return True

def test_with_ai():
    """测试AI辅助转换（可选）"""
    print("\n" + "="*70)
    print("🧪 测试AI辅助转换")
    print("="*70)

    from src.layer3_dita import ContentConverter

    # 创建AI转换器
    converter = ContentConverter(use_ai=True)

    test_text = """
安装Docker的详细步骤

首先，更新系统包索引。然后添加Docker官方GPG密钥。
接下来，设置稳定版仓库。最后，安装Docker Engine。

安装完成后，运行hello-world镜像验证安装是否成功。
如果看到欢迎信息，说明Docker已正确安装。
"""

    print("\n📝 使用AI提取步骤...")
    task_xml = converter.convert_to_task(
        text=test_text,
        title="安装Docker",
        topic_id="task_install_docker"
    )

    print("✅ AI辅助转换完成")
    print(f"提取的步骤数: {task_xml.count('<step>')}")

    # 保存结果
    output_dir = Config.OUTPUT_DIR / "test_ai_conversion"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "task_install_docker.dita"
    output_file.write_text(task_xml, encoding='utf-8')

    print(f"\n✅ 文件已保存: {output_file}")

    # 显示生成的XML
    print("\n生成的DITA XML:")
    print("=" * 70)
    print(task_xml)

    return True

if __name__ == "__main__":
    print("🧪 开始测试 Layer 3 - DITA转换功能...\n")

    # 测试1: DITA模板
    test_dita_templates()

    # 测试2: DITA Map
    test_dita_map()

    # 测试3: 内容转换器（规则模式）
    test_content_converter()

    # 测试4: 完整文档转换
    test_full_conversion()

    # 测试5: AI辅助转换（可选）
    print("\n" + "="*70)
    print("⚠️  准备测试AI辅助转换，这将消耗API额度")
    print("="*70)

    user_input = input("是否继续测试AI辅助转换？(y/n): ").strip().lower()

    if user_input == 'y':
        test_with_ai()
    else:
        print("⏭️  跳过AI测试")

    print("\n" + "="*70)
    print("✅ Layer 3 测试完成！")
    print("="*70)

    # 显示输出目录
    print(f"\n📁 查看生成的DITA文件:")
    print(f"  {Config.OUTPUT_DIR}")
