#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试文件 - 测试完整的DITA转换流程
从第一层输入PDF和Word文件，然后保存每一层的输出
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入各层模块
from src.layer1_preprocessing import PDFProcessor, WordProcessor
from src.layer2_semantic import DocumentAnalyzer
from src.layer3_dita_conversion import DITAConverter
from src.layer4_quality_assurance import QAManager
from src.utils.logger import setup_logger


def ensure_output_dir(output_dir: Path):
    """确保输出目录存在并返回目录路径"""
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_layer_output(output_dir: Path, filename: str, content: str):
    """保存层输出到文件"""
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return output_path


def save_layer_result(output_dir: Path, filename: str, result: dict):
    """保存层结果（JSON格式）到文件"""
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return output_path


def process_file(file_path: Path, output_root: Path, use_ai: bool = True):
    """处理单个文件的完整DITA转换流程"""
    print(f"\n" + "="*100)
    print(f"🔍 开始处理文件: {file_path.name}")
    print(f"📁 文件路径: {file_path}")
    print(f"📅 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    # 为每个文件创建独立的输出目录
    file_output_dir = output_root / file_path.stem
    ensure_output_dir(file_output_dir)

    # ========== 第一层: 预处理 ==========
    print("\n" + "="*70)
    print("🧪 第一层: 文档预处理")
    print("="*70)

    layer1_output_dir = file_output_dir / "layer1"
    ensure_output_dir(layer1_output_dir)

    layer1_result = None
    file_extension = file_path.suffix.lower()

    if file_extension == '.pdf':
        # 处理PDF文件
        print(f"📄 正在处理PDF文件...")
        processor = PDFProcessor(use_marker=True, use_ocr=True)
        layer1_result = processor.process(file_path)
    elif file_extension in ['.docx', '.doc']:
        # 处理Word文件
        print(f"📄 正在处理Word文件...")
        processor = WordProcessor()
        layer1_result = processor.process(file_path)
    else:
        print(f"❌ 不支持的文件格式: {file_extension}")
        return False

    if not layer1_result['success']:
        print(f"❌ 第一层预处理失败: {layer1_result.get('error')}")
        return False

    # 保存第一层输出
    save_layer_result(layer1_output_dir, f"layer1_result.json", layer1_result)
    save_layer_output(layer1_output_dir, f"layer1_markdown.txt", layer1_result['markdown'])

    print(f"✅ 第一层预处理成功!")
    # 处理不同处理器可能没有'method'键的情况
    method = layer1_result['metadata'].get('method', 'unknown')
    print(f"   提取方法: {method}")
    print(f"   输出已保存到: {layer1_output_dir}")

    # ========== 第二层: 语义分析 ==========
    print("\n" + "="*70)
    print("🧪 第二层: 语义分析")
    print("="*70)

    layer2_output_dir = file_output_dir / "layer2"
    ensure_output_dir(layer2_output_dir)

    analyzer = DocumentAnalyzer(use_ai=use_ai)
    layer2_result = analyzer.analyze(layer1_result['markdown'])

    # 保存第二层输出
    save_layer_result(layer2_output_dir, f"layer2_result.json", layer2_result)
    save_layer_output(layer2_output_dir, f"layer2_chunks.txt", 
                     "\n\n---\n\n".join([chunk['title'] + "\n" + chunk['content'] for chunk in layer2_result['chunks']]))

    print(f"✅ 第二层语义分析成功!")
    print(f"   总块数: {layer2_result['statistics']['total_chunks']}")
    print(f"   类型分布: {layer2_result['statistics']['type_distribution']}")
    print(f"   输出已保存到: {layer2_output_dir}")

    # ========== 第三层: DITA转换 ==========
    print("\n" + "="*70)
    print("🧪 第三层: DITA转换")
    print("="*70)

    layer3_output_dir = file_output_dir / "layer3"
    ensure_output_dir(layer3_output_dir)

    converter = DITAConverter(use_ai=use_ai, max_fix_iterations=3)

    # 确定文档类型（使用最主要的类型）
    type_dist = layer2_result['statistics']['type_distribution']
    if type_dist:
        primary_type = max(type_dist.items(), key=lambda x: x[1])[0]
    else:
        primary_type = "Concept"  # 默认类型

    print(f"📋 确定文档类型: {primary_type}")

    # 准备批次转换 - 从层2获取chunks
    chunks = layer2_result.get('chunks', [])
    
    # 如果没有chunks，使用原始内容作为单个chunk
    if not chunks:
        chunks = [{
            'id': 'single_chunk',
            'content': layer1_result['markdown'],
            'title': layer2_result.get('title', 'Untitled Document'),
            'type': primary_type
        }]
    else:
        # 确保每个chunk都有type字段
        for chunk in chunks:
            if 'type' not in chunk and 'classification' in chunk:
                chunk['type'] = chunk['classification']['type']
            elif 'type' not in chunk:
                chunk['type'] = primary_type

    print(f"📋 准备转换 {len(chunks)} 个块")

    # 批量转换为DITA
    layer3_result = converter.convert_batch(chunks, output_dir=layer3_output_dir)

    if layer3_result['failed'] > 0:
        print(f"⚠️  第三层DITA转换部分失败: {layer3_result['failed']} 个块失败")
    else:
        print(f"✅ 第三层DITA批量转换成功!")

    print(f"   总数: {layer3_result['total']}")
    print(f"   成功: {layer3_result['success']}")
    print(f"   失败: {layer3_result['failed']}")
    print(f"   成功率: {layer3_result['success_rate']:.1%}")
    print(f"   输出已保存到: {layer3_output_dir}")

    # 保存第三层输出
    save_layer_result(layer3_output_dir, f"layer3_result.json", layer3_result)

    # ========== 第四层: 质量保证 ==========  
    print("\n" + "="*70)
    print("第四层: 质量保证")
    layer4_output_dir = ensure_output_dir(file_output_dir / "layer4")

    qa_manager = QAManager(
        use_dita_ot=False,        # 不使用DITA-OT（需要单独安装）
        use_ai_repair=use_ai,     # 使用AI修复
        max_iterations=3          # 最大迭代3次
    )

    # 准备批量处理的DITA文档列表
    dita_documents = []
    for i, result in enumerate(layer3_result['results'], 1):
        if not result['success']:
            continue
        
        # 获取文档路径
        content_type = result['content_type']
        title = result['title']
        safe_title = "".join(c if c.isalnum() else '_' for c in title)[:50]
        filename = f"{i:03d}_{content_type.lower()}_{safe_title}.dita"
        dita_file_path = layer3_output_dir / filename
        
        # 读取DITA文件
        try:
            with open(dita_file_path, 'r', encoding='utf-8') as f:
                dita_xml = f.read()
        except Exception as e:
            print(f"❌ 读取DITA文件失败: {e}")
            continue
        
        dita_documents.append({
            'xml': dita_xml,
            'type': content_type,
            'metadata': {
                'layer1_confidence': layer1_result.get('confidence', 0.0),
                'layer2_confidence': layer2_result['statistics']['overall_avg_confidence'],
                'layer3_iterations': result['metadata']['iterations'],
                'title': title,
                'filename': filename
            }
        })

    # 使用批量处理方法处理文档
    if dita_documents:
        layer4_result = qa_manager.process_batch(dita_documents, output_dir=layer4_output_dir)
        
        print(f"\n✅ 第四层质量保证完成!")
        print(f"   处理文档数: {layer4_result['total']}")
        print(f"   成功数: {layer4_result['success']}")
        print(f"   失败数: {layer4_result['failed']}")
        print(f"   成功率: {layer4_result['success_rate']:.1%}")
        print(f"   输出已保存到: {layer4_output_dir}")
        
        # 保存总体质量保证报告
        save_layer_result(layer4_output_dir, f"layer4_overall_result.json", layer4_result)
        
        # 如果生成了合并文档，记录信息
        if 'merged_document_path' in layer4_result:
            print(f"\n📚 已生成合并后的完整文档:")
            print(f"   文件路径: {layer4_result['merged_document_path']}")
            print(f"   质量状态: {layer4_result['merged_document_result']['quality_report']['overall_status']}")
    else:
        print(f"\n⚠️ 没有可处理的DITA文档")

    print(f"\n" + "="*100)
    print(f"🎉 文件处理完成: {file_path.name}")
    print(f"💾 所有输出已保存到: {file_output_dir}")
    print("="*100)
    return True


def main():
    """主函数"""
    # 设置日志
    setup_logger("integration_test")

    print("\n" + "="*100)
    print("🎯 DITA转换器集成测试")
    print("="*100)
    print("此测试将处理PDF和Word文件，并保存每一层的输出")
    print("支持的文件格式: .pdf, .docx, .doc")
    print("="*100)

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("\n❌ 用法: python test_integration.py <文件1> [<文件2> ...]")
        print("示例: python test_integration.py data/input/sample.pdf data/input/sample.docx")
        sys.exit(1)

    # 获取输入文件列表
    input_files = []
    for path_str in sys.argv[1:]:
        path = Path(path_str)
        if not path.exists():
            print(f"\n❌ 文件不存在: {path_str}")
            continue
        if not path.is_file():
            print(f"\n❌ 不是文件: {path_str}")
            continue
        input_files.append(path)

    if not input_files:
        print("\n❌ 没有有效的输入文件")
        sys.exit(1)

    # 创建输出根目录
    output_root = project_root / "data" / "output" / "integration_test"
    ensure_output_dir(output_root)
    print(f"\n📁 输出根目录: {output_root}")

    # 询问是否使用AI功能
    use_ai = True
    if len(input_files) > 1:
        response = input("\n💡 是否使用AI功能？(y/n，默认y): ").lower().strip()
        if response == 'n':
            use_ai = False

    # 处理所有输入文件
    print(f"\n🔄 使用AI功能: {'是' if use_ai else '否'}")
    print(f"📋 待处理文件数: {len(input_files)}")
    print("\n" + "="*70)

    success_count = 0
    for i, file_path in enumerate(input_files, 1):
        print(f"\n{'-'*70}")
        print(f"📄 文件 {i}/{len(input_files)}: {file_path.name}")
        print(f"{'-'*70}")
        
        if process_file(file_path, output_root, use_ai):
            success_count += 1

    # 显示处理结果
    print(f"\n" + "="*100)
    print(f"📊 处理结果统计")
    print("="*100)
    print(f"总文件数: {len(input_files)}")
    print(f"成功处理: {success_count}")
    print(f"失败处理: {len(input_files) - success_count}")
    print(f"成功率: {success_count / len(input_files) * 100:.1f}%")
    print(f"所有输出已保存到: {output_root}")
    print("="*100)

    if success_count == len(input_files):
        print("🎉 所有文件处理成功!")
        return True
    else:
        print("⚠️  部分文件处理失败，请查看日志")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
