"""
测试Layer 1评估指标
演示如何使用CER、WER和标题层级准确率
"""

import json
from pathlib import Path
import argparse
from src.evaluation.layer1_metrics import (
    calculate_cer,
    calculate_wer,
    extract_headings,
    calculate_heading_accuracy,
    evaluate_layer1
)


def demo_text_metrics():
    """演示文本提取精度评估"""
    print("\n" + "="*70)
    print("📊 演示：文本提取精度评估 (CER & WER)")
    print("="*70)
    
    # 示例1：完全匹配
    print("\n示例1：完全匹配")
    ref1 = "The quick brown fox jumps over the lazy dog."
    hyp1 = "The quick brown fox jumps over the lazy dog."
    cer1 = calculate_cer(ref1, hyp1)
    wer1 = calculate_wer(ref1, hyp1)
    print(f"参考文本: {ref1}")
    print(f"提取文本: {hyp1}")
    print(f"✅ CER: {cer1:.4f} (0表示完美)")
    print(f"✅ WER: {wer1:.4f} (0表示完美)")
    
    # 示例2：有错误
    print("\n示例2：有字符错误")
    ref2 = "The quick brown fox jumps over the lazy dog."
    hyp2 = "The qick brown foxs jump over the lzy dog."  # 缺少u，多了s，少了a
    cer2 = calculate_cer(ref2, hyp2)
    wer2 = calculate_wer(ref2, hyp2)
    print(f"参考文本: {ref2}")
    print(f"提取文本: {hyp2}")
    print(f"⚠️  CER: {cer2:.4f} (编辑距离: {int(cer2 * len(ref2))} 个字符)")
    print(f"⚠️  WER: {wer2:.4f}")
    
    # 示例3：中文测试
    print("\n示例3：中文文本")
    ref3 = "深度学习是机器学习的一个分支，它使用多层神经网络来学习数据的表示。"
    hyp3 = "深度学习是机器学习的一个分支它使用多层神经网络来学习数据的表示"  # 缺少标点
    cer3 = calculate_cer(ref3, hyp3)
    wer3 = calculate_wer(ref3, hyp3)
    print(f"参考文本: {ref3}")
    print(f"提取文本: {hyp3}")
    print(f"⚠️  CER: {cer3:.4f}")
    print(f"⚠️  WER: {wer3:.4f}")


def demo_heading_metrics():
    """演示标题层级准确率评估"""
    print("\n" + "="*70)
    print("📊 演示：标题层级准确率评估")
    print("="*70)
    
    # 参考Markdown（Ground Truth）
    reference_md = """# Introduction to DITA

DITA is an XML-based architecture for authoring and publishing.

## What is DITA?

DITA stands for Darwin Information Typing Architecture.

### History

DITA was originally developed by IBM in the 1990s.

### Benefits

The main benefits include content reuse and multi-channel publishing.

## DITA Topic Types

There are three main topic types in DITA.

### Concept

Concept topics explain ideas and background information.

### Task

Task topics provide step-by-step instructions.

### Reference

Reference topics contain lookup information.
"""
    
    # 提取的Markdown（系统输出）
    extracted_md = """# Introduction to DITA

DITA is an XML-based architecture for authoring and publishing.

## What is DITA

DITA stands for Darwin Information Typing Architecture.

## History

DITA was originally developed by IBM in the 1990s.

### Benefits

The main benefits include content reuse and multi-channel publishing.

## DITA Topic Types

There are three main topic types in DITA.

### Concept

Concept topics explain ideas and background information.

### Task

Task topics provide step-by-step instructions.

### Reference

Reference topics contain lookup information.
"""
    
    # 提取标题
    ref_headings = extract_headings(reference_md)
    ext_headings = extract_headings(extracted_md)
    
    print("\n📑 参考标题（Ground Truth）:")
    for h in ref_headings:
        indent = "  " * (h['level'] - 1)
        print(f"{indent}{'#' * h['level']} {h['text']}")
    
    print("\n📑 提取的标题（系统输出）:")
    for h in ext_headings:
        indent = "  " * (h['level'] - 1)
        print(f"{indent}{'#' * h['level']} {h['text']}")
    
    # 计算准确率
    metrics = calculate_heading_accuracy(ref_headings, ext_headings)
    
    print(f"\n📊 评估结果:")
    print(f"  总参考标题数: {metrics['total_reference']}")
    print(f"  总提取标题数: {metrics['total_extracted']}")
    print(f"  文本匹配数: {metrics['matched']}")
    print(f"  层级匹配数: {metrics['level_matched']}")
    print(f"  完全匹配数: {metrics['exact_matched']}")
    print(f"\n  📈 准确率指标:")
    print(f"    召回率 (Recall):    {metrics['recall']:.2%}")
    print(f"    精确率 (Precision): {metrics['precision']:.2%}")
    print(f"    F1分数:             {metrics['f1_score']:.2%}")
    print(f"    层级准确率:         {metrics['level_match']:.2%}")
    print(f"    完全匹配率:         {metrics['exact_match']:.2%}")


def evaluate_from_layer1_output(layer1_output_dir: Path, ground_truth_file: Path = None):
    """从Layer 1输出评估
    
    Args:
        layer1_output_dir: Layer 1的输出目录
        ground_truth_file: Ground Truth文件路径（可选）
    """
    print("\n" + "="*70)
    print("📊 从Layer 1输出进行评估")
    print("="*70)
    
    # 读取Layer 1的结果
    layer1_result_file = layer1_output_dir / "layer1_result.json"
    if not layer1_result_file.exists():
        print(f"❌ 未找到Layer 1结果文件: {layer1_result_file}")
        return
    
    with open(layer1_result_file, 'r', encoding='utf-8') as f:
        layer1_result = json.load(f)
    
    extracted_text = layer1_result.get('markdown', '')
    
    print(f"✅ 读取Layer 1输出: {len(extracted_text)} 字符")
    
    # 如果没有Ground Truth，只能进行标题提取展示
    if not ground_truth_file or not ground_truth_file.exists():
        print("\n⚠️  未提供Ground Truth文件，仅展示提取结果:")
        
        extracted_headings = extract_headings(extracted_text)
        print(f"\n📑 提取的标题 ({len(extracted_headings)}个):")
        for h in extracted_headings:
            indent = "  " * (h['level'] - 1)
            print(f"{indent}{'#' * h['level']} {h['text']}")
        
        print("\n💡 提示：要进行完整评估，请提供Ground Truth文件:")
        print("   python test_layer1_evaluation.py --layer1-output <dir> --ground-truth <file>")
        return
    
    # 读取Ground Truth
    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        if ground_truth_file.suffix == '.json':
            gt_data = json.load(f)
            reference_text = gt_data.get('text', '')
            reference_headings = gt_data.get('headings', None)
        else:
            reference_text = f.read()
            reference_headings = None
    
    print(f"✅ 读取Ground Truth: {len(reference_text)} 字符")
    
    # 进行完整评估
    print("\n📊 开始评估...")
    evaluation_result = evaluate_layer1(
        reference_text,
        extracted_text,
        reference_headings,
        None
    )
    
    # 显示结果
    print("\n" + "="*70)
    print("📊 Layer 1 评估结果")
    print("="*70)
    
    text_metrics = evaluation_result['text_extraction']
    print("\n1️⃣  文本提取精度:")
    print(f"  字符错误率 (CER): {text_metrics['cer']:.4f} (越小越好，0表示完美)")
    print(f"  词错误率 (WER):   {text_metrics['wer']:.4f} (越小越好，0表示完美)")
    print(f"  参考文本长度: {text_metrics['reference_chars']} 字符")
    print(f"  提取文本长度: {text_metrics['extracted_chars']} 字符")
    print(f"  长度比例: {text_metrics['length_ratio']:.2%}")
    
    heading_metrics = evaluation_result['heading_accuracy']
    print("\n2️⃣  标题层级准确率:")
    print(f"  召回率 (Recall):    {heading_metrics['recall']:.2%}")
    print(f"  精确率 (Precision): {heading_metrics['precision']:.2%}")
    print(f"  F1分数:             {heading_metrics['f1_score']:.2%}")
    print(f"  层级准确率:         {heading_metrics['level_match']:.2%}")
    print(f"  完全匹配率:         {heading_metrics['exact_match']:.2%}")
    print(f"  参考标题数: {heading_metrics['total_reference']}")
    print(f"  提取标题数: {heading_metrics['total_extracted']}")
    
    print(f"\n🎯 综合得分: {evaluation_result['overall_score']:.2f} / 100")
    
    # 保存评估结果
    eval_output_file = layer1_output_dir / "layer1_evaluation.json"
    with open(eval_output_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 评估结果已保存: {eval_output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='测试Layer 1评估指标')
    parser.add_argument('--demo', action='store_true', help='运行演示示例')
    parser.add_argument('--layer1-output', type=str, help='Layer 1输出目录')
    parser.add_argument('--ground-truth', type=str, help='Ground Truth文件路径')
    
    args = parser.parse_args()
    
    if args.demo:
        # 运行演示
        demo_text_metrics()
        demo_heading_metrics()
        
        print("\n" + "="*70)
        print("✅ 演示完成！")
        print("="*70)
        print("\n💡 使用说明:")
        print("  1. 准备Ground Truth数据（Markdown格式）")
        print("  2. 运行Layer 1处理获得输出")
        print("  3. 使用以下命令进行评估:")
        print("     python test_layer1_evaluation.py --layer1-output <dir> --ground-truth <file>")
    
    elif args.layer1_output:
        layer1_dir = Path(args.layer1_output)
        gt_file = Path(args.ground_truth) if args.ground_truth else None
        evaluate_from_layer1_output(layer1_dir, gt_file)
    
    else:
        print("使用方法:")
        print("  运行演示:        python test_layer1_evaluation.py --demo")
        print("  评估Layer 1:     python test_layer1_evaluation.py --layer1-output <dir> --ground-truth <file>")
        print("\n示例:")
        print("  python test_layer1_evaluation.py --demo")
        print("  python test_layer1_evaluation.py --layer1-output data/output/test/layer1 --ground-truth data/ground_truth/test.md")
