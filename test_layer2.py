"""
测试Layer 2 - 语义分析功能
"""
from pathlib import Path
from src.utils.config import Config
from src.layer1_preprocessing import PDFProcessor
from src.layer2_semantic import DocumentAnalyzer

def test_document_analyzer():
    """测试文档分析器（语义分析）"""
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
    analyzer = DocumentAnalyzer(use_ai=False)  # 先不使用AI分类器

    # 分析文档
    result = analyzer.analyze(test_text)

    # 显示结果
    print(f"\n✅ 分析完成！")
    print(f"  语义块数量: {len(result['chunks'])}")
    print(f"\n📊 统计信息:")
    print(f"    总块数: {result['statistics']['total_chunks']}")
    print(f"    类型分布: {result['statistics']['type_distribution']}")
    print(f"    平均置信度: {result['statistics']['overall_avg_confidence']:.2f}")
    print(f"    需要人工审核: {result['statistics']['needs_review']} 块")

    print(f"\n📑 语义块分析结果:")
    for chunk in result['chunks']:
        indent = "  " * (chunk['level'] - 2)  # H2开始
        print(f"{indent}{'#' * chunk['level']} {chunk['title']}")
        print(f"{indent}  分类: {chunk['classification']['type']} (置信度: {chunk['classification']['confidence']:.2f})")
        print(f"{indent}  内容长度: {len(chunk['content'].strip())} 字符")

    return True

def test_pdf_integration():
    """测试PDF到语义分析的完整流程"""
    print("\n" + "="*70)
    print("🧪 测试PDF到语义分析的完整流程")
    print("="*70)

    # 读取测试PDF文件
    test_pdf = Path(r"d:\codeC\VsCodeP\dita-converter\uploads\2023CVPR-CoMFormer.pdf")

    if not test_pdf.exists():
        print("⚠️  未找到测试PDF文件，跳过测试")
        return False

    print(f"📄 测试文件: {test_pdf.name}")
    
    # Step 1: 使用Layer 1提取PDF文本为Markdown
    print("\n1️⃣  使用Layer 1提取PDF文本...")
    processor = PDFProcessor(use_marker=True, use_ocr=True)
    layer1_result = processor.process(test_pdf)
    
    if not layer1_result['success']:
        print(f"❌ Layer 1处理失败: {layer1_result.get('error')}")
        return False
    
    markdown_content = layer1_result['markdown']
    print(f"✅ 提取完成: {len(markdown_content)} 字符")
    print(f"   使用方法: {layer1_result['metadata']['method']}")
    print(f"   页数: {layer1_result['metadata']['pages']}")

    # Step 2: 使用Layer 2进行语义分析
    print("\n2️⃣  使用Layer 2进行语义分析...")
    analyzer = DocumentAnalyzer(use_ai=False)  # 先不使用AI分类器
    layer2_result = analyzer.analyze(markdown_content, layer1_result['metadata'])
    
    # 显示结果
    print(f"✅ 语义分析完成！")
    print(f"   语义块数量: {len(layer2_result['chunks'])}")
    print(f"   类型分布: {layer2_result['statistics']['type_distribution']}")
    
    # 显示前几个语义块的分析结果
    print(f"\n📑 前5个语义块分析:")
    for chunk in layer2_result['chunks'][:5]:
        print(f"\n  {'#' * chunk['level']} {chunk['title']}")
        print(f"    分类: {chunk['classification']['type']} (置信度: {chunk['classification']['confidence']:.2f})")
        print(f"    内容预览: {chunk['content'].strip()[:100]}...")

    return True

def test_with_ai_classifier():
    """测试使用AI分类器的文档分析（可选）"""
    print("\n" + "="*70)
    print("🧪 测试使用AI分类器的文档分析")
    print("="*70)

    try:
        # 准备简短的测试文本
        test_text = """## Installation Guide

Follow these steps to install the software:

1. Download the installation package from our website
2. Run the installer as administrator
3. Follow the on-screen instructions
4. Restart your computer after installation

## Troubleshooting

If you encounter any issues, try the following:
- Check if your system meets the requirements
- Ensure you have administrator privileges
- Disable antivirus software temporarily
"""
        
        print("📝 测试文本准备完成")
        
        # 创建分析器（启用AI分类器）
        analyzer = DocumentAnalyzer(use_ai=True)
        
        # 分析文档
        result = analyzer.analyze(test_text)
        
        # 显示结果
        print(f"\n✅ AI分析完成！")
        print(f"   语义块数量: {len(result['chunks'])}")
        
        for chunk in result['chunks']:
            print(f"\n  {'#' * chunk['level']} {chunk['title']}")
            print(f"    AI分类: {chunk['classification']['type']} (置信度: {chunk['classification']['confidence']:.2f})")
            print(f"    特征: {list(chunk['features'].keys())[:5]}...")
        
        print("\n✅ AI分类器测试通过！")
        return True
        
    except Exception as e:
        print(f"⚠️ AI分类器测试跳过: {e}")
        print("   这可能是因为没有配置AI API密钥或网络问题")
        return False

if __name__ == "__main__":
    print("🧪 开始测试 Layer 2 功能...\n")

    # 测试1: 文档分析器（基础功能）
    test_document_analyzer()

    # 测试2: PDF到语义分析的完整流程
    test_pdf_integration()

    # 测试3: AI分类器（可选）
    print("\n" + "="*70)
    print("⚠️  准备测试AI分类器功能")
    print("="*70)

    user_input = input("是否继续测试AI分类器？(y/n): ").strip().lower()

    if user_input == 'y':
        test_with_ai_classifier()
    else:
        print("⏭️  跳过AI分类器测试")

    print("\n" + "="*70)
    print("✅ Layer 2 测试完成！")
    print("="*70)