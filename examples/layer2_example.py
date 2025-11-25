"""
Layer 2 使用示例
演示如何使用文档分析器
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.layer2_semantic import DocumentAnalyzer

def main():
    print("="*70)
    print("Layer 2 文档分析示例")
    print("="*70)
    
    # 示例Markdown内容
    markdown_content = """
# Python快速入门指南

## Python简介

Python is a powerful, high-level programming language.
It was created by Guido van Rossum and first released in 1991.
Python is known for its clear syntax and code readability.
The language supports multiple programming paradigms.

## 安装步骤

To get started with Python:

1. Visit python.org
2. Download the latest version
3. Run the installer
4. Check "Add Python to PATH"
5. Verify by running: python --version

## 基础语法

### 变量和数据类型

| Type | Example | Description |
|------|---------|-------------|
| int | 42 | Integer number |
| str | "hello" | String text |
| float | 3.14 | Decimal number |
| bool | True | Boolean value |

### 控制流

Python uses indentation for code blocks.
The if statement checks conditions.
Loops include for and while statements.

## 第一个程序

Follow these steps to create your first program:

1. Open a text editor
2. Type: print("Hello, World!")
3. Save as hello.py
4. Run: python hello.py
    """
    
    # 初始化分析器（不使用AI以节省成本）
    analyzer = DocumentAnalyzer(use_ai=True)
    
    # 分析文档
    print("\n🔍 开始分析...")
    results = analyzer.analyze(markdown_content)
    
    # 显示结果
    print("\n" + "="*70)
    print("📊 分析结果")
    print("="*70)
    
    print(f"\n总块数: {results['statistics']['total_chunks']}")
    print(f"类型分布: {results['statistics']['type_distribution']}")
    print(f"平均置信度: {results['statistics']['overall_avg_confidence']:.2f}")
    print(f"需要审核: {results['statistics']['needs_review']}")
    
    print("\n" + "="*70)
    print("📦 分块详情")
    print("="*70)
    
    for i, chunk in enumerate(results['chunks'], 1):
        print(f"\n[{i}] {chunk['title']}")
        print(f"    层级: H{chunk['level']}")
        print(f"    类型: {chunk['classification']['type']}")
        print(f"    置信度: {chunk['classification']['confidence']:.2f}")
        print(f"    分数: Task={chunk['classification']['scores']['Task']:.2f}, "
              f"Concept={chunk['classification']['scores']['Concept']:.2f}, "
              f"Reference={chunk['classification']['scores']['Reference']:.2f}")
        
        # 显示部分内容
        content_preview = chunk['content'][:100].replace('\n', ' ')
        print(f"    内容预览: {content_preview}...")
    
    # 保存结果
    output_path = Path("data/output/layer2_example_result.json")
    analyzer.save_results(results, output_path)
    print(f"\n💾 结果已保存到: {output_path}")
    
    print("\n" + "="*70)
    print("✅ 示例完成！")
    print("="*70)


if __name__ == "__main__":
    main()