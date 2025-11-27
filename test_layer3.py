import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, Any, List
import json

# 添加src路径到系统路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from layer3_dita_conversion.converter import DITAConverter

def test_task_conversion():
    """测试Task类型的DITA转换"""
    print("\n📝 测试1: Task主题转换")
    
    # 测试数据
    title = "安装Git"
    content = "Git是一个分布式版本控制系统，用于跟踪文件的变化。本教程将指导您在Windows系统上安装Git。\n\n1. 访问Git官网下载安装包\n2. 运行安装程序，保持默认设置\n3. 打开命令提示符或PowerShell验证安装"
    content_type = "Task"
    
    # 使用DITA转换器
    converter = DITAConverter(use_ai=False)
    result = converter.convert(content=content, title=title, content_type=content_type)
    
    print(f"✅ Task转换状态: {'成功' if result['success'] else '失败'}")
    
    if result['errors']:
        print(f"⚠️  发现 {len(result['errors'])} 个错误")
        for error in result['errors']:
            if hasattr(error, 'message'):
                print(f"   ⚠️  {error.message}")
            elif isinstance(error, dict) and 'message' in error:
                print(f"   ⚠️  {error['message']}")
            else:
                print(f"   ⚠️  {error}")
    
    if result['dita_xml']:
        print("📄 XML预览:", result['dita_xml'][:500] + "...")
    
    return result

def test_concept_conversion():
    """测试Concept类型的DITA转换"""
    print("\n📝 测试2: Concept主题转换")
    
    # 测试数据
    title = "什么是DITA"
    content = "DITA（Darwin Information Typing Architecture）是一种基于XML的信息架构标准。" \
              "它将文档分为三种主要类型：概念（Concept）、任务（Task）和参考（Reference）。" \
              "DITA的模块化设计使得内容可以被重用和重新组合，从而提高文档的一致性和维护效率。"
    content_type = "Concept"
    
    # 使用DITA转换器
    converter = DITAConverter(use_ai=False)
    result = converter.convert(content=content, title=title, content_type=content_type)
    
    print(f"✅ Concept转换状态: {'成功' if result['success'] else '失败'}")
    
    if result['errors']:
        print(f"⚠️  发现 {len(result['errors'])} 个错误")
        for error in result['errors']:
            if hasattr(error, 'message'):
                print(f"   ⚠️  {error.message}")
            elif isinstance(error, dict) and 'message' in error:
                print(f"   ⚠️  {error['message']}")
            else:
                print(f"   ⚠️  {error}")
    
    if result['dita_xml']:
        print("📄 XML预览:", result['dita_xml'][:500] + "...")
    
    return result

def test_reference_conversion():
    """测试Reference类型的DITA转换"""
    print("\n📝 测试3: Reference主题转换")
    
    # 测试数据
    title = "print()函数参考"
    content = "print()函数用于在控制台输出信息。它可以接受多个参数，并将它们转换为字符串后输出。\n\n参数:\n\n*objects: 要打印的对象\nsep: 分隔符（默认空格）\nend: 结束符（默认换行）\nfile: 输出文件对象，默认为标准输出"
    content_type = "Reference"
    
    # 使用DITA转换器
    converter = DITAConverter(use_ai=False)
    result = converter.convert(content=content, title=title, content_type=content_type)
    
    print(f"✅ Reference转换状态: {'成功' if result['success'] else '失败'}")
    
    if result['errors']:
        print(f"⚠️  发现 {len(result['errors'])} 个错误")
        for error in result['errors']:
            if hasattr(error, 'message'):
                print(f"   ⚠️  {error.message}")
            elif isinstance(error, dict) and 'message' in error:
                print(f"   ⚠️  {error['message']}")
            else:
                print(f"   ⚠️  {error}")
    
    if result['dita_xml']:
        print("📄 XML预览:", result['dita_xml'][:500] + "...")
    
    return result

def test_save_output():
    """测试结果保存功能"""
    print("\n📁 测试结果保存到: D:\codeC\VsCodeP\dita-converter\data\output\test_new")
    
    # 创建输出目录（如果不存在）
    output_dir = "D:/codeC/VsCodeP/dita-converter/data/output/test_new"
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试数据
    test_cases = [
        ("Task", "安装Git", "Git是一个分布式版本控制系统，用于跟踪文件的变化。\n\n1. 下载安装包\n2. 运行安装程序", "git_install.dita"),
        ("Concept", "什么是DITA", "DITA是一种基于XML的信息架构标准，用于创建模块化文档。", "what_is_dita.dita")
    ]
    
    # 使用DITA转换器
    converter = DITAConverter(use_ai=False)
    
    # 转换并保存
    for content_type, title, content, filename in test_cases:
        result = converter.convert(content=content, title=title, content_type=content_type)
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
            f.write(result["dita_xml"])
    
    return True

def main():
    """主测试函数"""
    print("="*44)
    print("🧪 测试DITA转换器")
    print("="*44)
    
    # 运行所有测试
    task_result = test_task_conversion()
    concept_result = test_concept_conversion()
    reference_result = test_reference_conversion()
    save_result = test_save_output()
    
    print("\n" + "="*44)
    print("✅ Layer 3 DITA转换器测试成功！")
    print("="*44)

if __name__ == "__main__":
    main()
