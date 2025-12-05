"""
测试Layer 2 - 语义分析功能
支持从Layer 1的输出读取数据
"""
import json
import argparse
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

def test_from_layer1_output(layer1_output_dir: Path, use_ai: bool = False):
    """从Layer 1的输出读取数据并进行语义分析
    
    Args:
        layer1_output_dir: Layer 1的输出目录
        use_ai: 是否使用AI分类器
        
    Returns:
        bool: 测试是否通过
    """
    print("\n" + "="*70)
    print("🧪 从Layer 1输出进行语义分析")
    print("="*70)
    
    # 优先尝试读取JSON文件（包含完整的metadata）
    layer1_result_file = layer1_output_dir / "layer1_result.json"
    metadata = {}
    markdown_content = None
    
    if layer1_result_file.exists():
        print(f"📄 读取Layer 1结果文件: {layer1_result_file.name}")
        with open(layer1_result_file, 'r', encoding='utf-8') as f:
            layer1_result = json.load(f)
        
        if not layer1_result.get('success', False):
            print(f"❌ Layer 1处理失败: {layer1_result.get('error')}")
            return False
        
        markdown_content = layer1_result.get('markdown')
        metadata = layer1_result.get('metadata', {})
        print(f"✅ 从JSON读取成功: {len(markdown_content)} 字符")
        print(f"   使用方法: {metadata.get('method', 'N/A')}")
        print(f"   页数: {metadata.get('pages', 'N/A')}")
    else:
        # 如果没有JSON，尝试读取Markdown文件
        md_files = list(layer1_output_dir.glob("*.md"))
        if not md_files:
            print(f"❌ 未找到Layer 1的输出文件（JSON或Markdown）: {layer1_output_dir}")
            return False
        
        markdown_file = md_files[0]
        print(f"📄 读取Layer 1的Markdown文件: {markdown_file.name}")
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        print(f"✅ 从Markdown读取成功: {len(markdown_content)} 字符")
        print(f"   提示: 未找到metadata信息（JSON文件不存在）")
    
    # 创建Layer 2输出目录
    output_dir = layer1_output_dir.parent / "layer2"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用Layer 2进行语义分析
    print(f"\n2️⃣  使用Layer 2进行语义分析...")
    analyzer = DocumentAnalyzer(use_ai=use_ai)
    layer2_result = analyzer.analyze(markdown_content, metadata)
    
    # 保存Layer 2结果
    layer2_result_file = output_dir / "layer2_result.json"
    with open(layer2_result_file, 'w', encoding='utf-8') as f:
        json.dump(layer2_result, f, ensure_ascii=False, indent=2)
    
    # 保存语义块文本
    chunks_file = output_dir / "layer2_chunks.txt"
    with open(chunks_file, 'w', encoding='utf-8') as f:
        for chunk in layer2_result['chunks']:
            f.write(f"\n\n{'='*70}\n")
            f.write(f"{'#' * chunk['level']} {chunk['title']}\n")
            f.write(f"类型: {chunk['classification']['type']} (置信度: {chunk['classification']['confidence']:.2f})\n")
            f.write(f"{'='*70}\n\n")
            f.write(chunk['content'])
    
    # 显示结果
    print(f"✅ 语义分析完成！")
    print(f"   语义块数量: {len(layer2_result['chunks'])}")
    print(f"   类型分布: {layer2_result['statistics']['type_distribution']}")
    print(f"   平均置信度: {layer2_result['statistics']['overall_avg_confidence']:.2f}")
    print(f"   需要人工审核: {layer2_result['statistics']['needs_review']} 块")
    print(f"   输出已保存到: {output_dir}")
    
    # 显示前几个语义块的分析结果
    print(f"\n📑 前5个语义块分析:")
    for chunk in layer2_result['chunks'][:5]:
        print(f"\n  {'#' * chunk['level']} {chunk['title']}")
        print(f"    分类: {chunk['classification']['type']} (置信度: {chunk['classification']['confidence']:.2f})")
        print(f"    内容预览: {chunk['content'].strip()[:100]}...")
    
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
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试Layer 2 - 语义分析功能')
    parser.add_argument('--layer1-output', type=str, help='Layer 1的输出目录路径')
    parser.add_argument('--use-ai', action='store_true', help='是否使用AI分类器')
    parser.add_argument('--full-test', action='store_true', help='运行完整测试（包括PDF处理）')
    
    args = parser.parse_args()
    
    success = True
    
    # 如果指定了Layer 1输出目录，从该目录读取数据
    if args.layer1_output:
        layer1_output_dir = Path(args.layer1_output)
        if not layer1_output_dir.exists():
            print(f"❌ Layer 1输出目录不存在: {layer1_output_dir}")
            success = False
        else:
            success = test_from_layer1_output(layer1_output_dir, use_ai=args.use_ai)
    
    # 否则运行标准测试
    elif args.full_test:
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
    else:
        print("使用方法:")
        print("  从Layer 1输出读取: python test_layer2.py --layer1-output <layer1输出目录>")
        print("  运行完整测试:      python test_layer2.py --full-test")
        print("  使用AI分类器:      添加 --use-ai 参数")
        print("\n示例:")
        print("  python test_layer2.py --layer1-output data/output/2023CVPR-CoMFormer/layer1")
        print("  python test_layer2.py --layer1-output data/output/2023CVPR-CoMFormer/layer1 --use-ai")
        success = False

    print("\n" + "="*70)
    if success:
        print("✅ Layer 2 测试完成！")
    else:
        print("❌ Layer 2 测试失败或未运行！")
    print("="*70)