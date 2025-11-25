"""
测试Layer 2 - 语义分析功能
"""
from pathlib import Path
from src.utils.config import Config
from src.layer1_preprocessing import PDFProcessor
from src.layer2_semantic import AIClient, DocumentAnalyzer, ContentSplitter

def test_document_analyzer():
    """测试文档分析器（规则提取）"""
    print("\n" + "="*70)
    print("🧪 测试文档分析器")
    print("="*70)
    
    # 准备测试文本（Markdown格式）
    test_text = """# Introduction

This is the introduction section.

## Background

Some background information here.

### Prerequisites

- Python 3.8+
- pip installed
- Basic knowledge of APIs

## Installation

Follow these steps:

1. Install the package
2. Configure the API key
3. Run the application

### Code Example

```python
import requests
response = requests.get("https://api.example.com")
print(response.json())
```

## Conclusion

This is the conclusion.
"""
    # 创建分析器
    analyzer = DocumentAnalyzer()

    # 分析文档
    result = analyzer.analyze(test_text)

    # 显示结果
    print(f"\n✅ 分析完成！")
    print(f"  结构类型: {result['structure_type']}")
    print(f"  章节数量: {len(result['sections'])}")
    print(f"  元素数量: {len(result['elements'])}")
    print(f"\n📊 统计信息:")
    for key, value in result['statistics'].items():
        print(f"    {key}: {value}")

    print(f"\n📑 章节结构:")
    for section in result['sections']:
        indent = "  " * (section['level'] - 1)
        print(f"{indent}{'#' * section['level']} {section['title']}")

    print(f"\n📝 识别的元素类型:")
    element_types = {}
    for elem in result['elements']:
        elem_type = elem['type']
        element_types[elem_type] = element_types.get(elem_type, 0) + 1

    for elem_type, count in element_types.items():
        print(f"  {elem_type}: {count}")

    return True

def test_content_splitter():
    """测试内容分割器"""
    print("\n" + "="*70)
    print("🧪 测试内容分割器")
    print("="*70)

    # 读取之前处理的PDF文本
    test_pdf = Config.INPUT_DIR / "test.pdf"

    if not test_pdf.exists():
        print("⚠️  未找到test.pdf，跳过测试")
        return False

    # 提取文本
    processor = PDFProcessor(use_marker=False)
    result = processor.extract_text(test_pdf)
    text = result['text']

    print(f"✅ PDF文本: {len(text)} 字符")

    # 创建分割器
    splitter = ContentSplitter(chunk_size=2000)

    # 按固定大小分割
    chunks = splitter.split_by_fixed_size(text)

    print(f"\n✅ 分割完成: {len(chunks)} 个块")
    print(f"\n前3个块的信息:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n  块 {i + 1}:")
        print(f"    字符数: {chunk['metadata']['char_count']}")
        print(f"    预览: {chunk['content'][:100]}...")

    return True

def test_ai_client():
    """测试AI客户端（调用千问API）"""
    print("\n" + "="*70)
    print("🧪 测试AI客户端")
    print("="*70)

    try:
        # 创建AI客户端
        client = AIClient(provider="qwen")
        
        print("✅ AI客户端初始化成功")
        
        # 测试1: 简单对话
        print("\n📝 测试1: 简单对话")
        messages = [
            {"role": "system", "content": "你是一个简洁的助手，只用一句话回答。"},
            {"role": "user", "content": "什么是DITA？"}
        ]
        
        response = client.chat(messages, temperature=0.3, max_tokens=100)
        print(f"  回答: {response}")
        
        # 测试2: JSON模式
        print("\n📝 测试2: JSON模式")
        messages = [
            {"role": "system", "content": "你是JSON数据生成器。"},
            {"role": "user", "content": '生成一个包含name和age字段的JSON对象，name是"Alice"，age是25'}
        ]
        
        response = client.chat(messages, temperature=0.1, max_tokens=100, json_mode=True)
        print(f"  JSON: {response}")
        
        # 测试3: 文档分析
        print("\n📝 测试3: 提取元数据")
        test_text = """
Python API Authentication Guide
Author: John Doe
Version: 2.0

This guide explains how to implement OAuth 2.0 authentication in Python applications.
We'll cover the basic concepts, implementation steps, and best practices.
"""

        metadata = client.extract_metadata(test_text)
        print(f"  标题: {metadata['title']}")
        print(f"  关键词: {', '.join(metadata['keywords'][:5])}")
        print(f"  摘要: {metadata['summary'][:100]}...")
        
        print("\n✅ 所有AI测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ AI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试 Layer 2 功能...\n")

    # 测试1: 文档分析器
    test_document_analyzer()

    # 测试2: 内容分割器
    test_content_splitter()

    # 测试3: AI客户端（需要API Key）
    print("\n" + "="*70)
    print("⚠️  准备测试AI功能，这将消耗API额度")
    print("="*70)

    user_input = input("是否继续测试AI客户端？(y/n): ").strip().lower()

    if user_input == 'y':
        test_ai_client()
    else:
        print("⏭️  跳过AI测试")

    print("\n" + "="*70)
    print("✅ Layer 2 测试完成！")
    print("="*70)