"""
测试Layer 1评估（无Ground Truth版本）
适用于只有PDF文件的实际场景
"""

import json
import argparse
from pathlib import Path
from src.evaluation.layer1_metrics_no_gt import (
    evaluate_layer1_without_gt,
    generate_evaluation_report
)


def evaluate_from_layer1_output(layer1_output_dir: Path, pdf_path: Path = None):
    """从Layer 1输出进行评估（无需Ground Truth）
    
    Args:
        layer1_output_dir: Layer 1的输出目录
        pdf_path: 原始PDF路径（可选）
    """
    print("\n" + "="*70)
    print("📊 Layer 1 评估（无Ground Truth模式）")
    print("="*70)
    
    # 读取Layer 1结果
    layer1_result_file = layer1_output_dir / "layer1_result.json"
    if not layer1_result_file.exists():
        # 尝试读取Markdown文件
        md_files = list(layer1_output_dir.glob("*.md"))
        if not md_files:
            print(f"❌ 未找到Layer 1输出文件: {layer1_output_dir}")
            return
        
        markdown_file = md_files[0]
        print(f"📄 读取Markdown文件: {markdown_file.name}")
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        metadata = None
        print(f"✅ 读取成功: {len(markdown_content)} 字符")
    else:
        print(f"📄 读取Layer 1结果: {layer1_result_file.name}")
        
        with open(layer1_result_file, 'r', encoding='utf-8') as f:
            layer1_result = json.load(f)
        
        if not layer1_result.get('success', False):
            print(f"❌ Layer 1处理失败: {layer1_result.get('error')}")
            return
        
        markdown_content = layer1_result.get('markdown', '')
        metadata = layer1_result.get('metadata', {})
        
        print(f"✅ 读取成功: {len(markdown_content)} 字符")
        print(f"   方法: {metadata.get('method', 'N/A')}")
        print(f"   页数: {metadata.get('pages', 'N/A')}")
    
    # 进行评估
    print("\n📊 开始评估...")
    evaluation_result = evaluate_layer1_without_gt(
        markdown_content,
        pdf_path,
        metadata
    )
    
    # 生成报告
    report = generate_evaluation_report(evaluation_result)
    print(report)
    
    # 保存结果
    eval_output_file = layer1_output_dir / "layer1_evaluation_no_gt.json"
    with open(eval_output_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
    
    report_file = layer1_output_dir / "layer1_evaluation_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 评估结果已保存:")
    print(f"   JSON: {eval_output_file}")
    print(f"   报告: {report_file}")
    
    # 给出建议
    print("\n💡 改进建议:")
    overall_score = evaluation_result['overall_score']
    
    if overall_score >= 90:
        print("   ✅ 提取质量优秀，可直接用于后续处理")
    elif overall_score >= 75:
        print("   ✅ 提取质量良好，建议检查以下问题:")
    elif overall_score >= 60:
        print("   ⚠️  提取质量一般，需要注意以下问题:")
    else:
        print("   ❌ 提取质量较差，强烈建议优化以下问题:")
    
    # 具体建议
    if 'heading_hierarchy' in evaluation_result:
        issues = evaluation_result['heading_hierarchy']['issues']
        if issues:
            print("\n   标题结构问题:")
            for issue in issues[:3]:
                print(f"   - {issue}")
    
    if 'quality' in evaluation_result:
        issues = evaluation_result['quality']['issues']
        if issues:
            print("\n   提取质量问题:")
            for issue in issues[:3]:
                print(f"   - {issue}")
    
    if 'pdf_comparison' in evaluation_result:
        pdf = evaluation_result['pdf_comparison']
        if 'warning' in pdf and pdf['warning']:
            print(f"\n   完整性警告:")
            print(f"   - {pdf['warning']}")


def quick_check(pdf_path: Path):
    """快速检查PDF并评估（临时处理）
    
    Args:
        pdf_path: PDF文件路径
    """
    print("\n" + "="*70)
    print("🚀 快速评估模式")
    print("="*70)
    print(f"📄 处理文件: {pdf_path.name}\n")
    
    # 使用Layer 1处理
    from src.layer1_preprocessing import PDFProcessor
    
    print("1️⃣  使用Marker提取PDF内容...")
    processor = PDFProcessor(use_marker=True, use_ocr=True)
    result = processor.process(pdf_path)
    
    if not result['success']:
        print(f"❌ 提取失败: {result.get('error')}")
        return
    
    print(f"✅ 提取成功: {len(result['markdown'])} 字符\n")
    
    # 进行评估
    print("2️⃣  进行质量评估...")
    evaluation_result = evaluate_layer1_without_gt(
        result['markdown'],
        pdf_path,
        result['metadata']
    )
    
    # 显示报告
    report = generate_evaluation_report(evaluation_result)
    print(report)
    
    # 保存到临时目录
    from src.utils.config import Config
    temp_dir = Config.OUTPUT_DIR / "quick_check"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存评估结果
    eval_file = temp_dir / f"{pdf_path.stem}_evaluation.json"
    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
    
    # 保存报告
    report_file = temp_dir / f"{pdf_path.stem}_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 结果已保存到: {temp_dir}")


def batch_evaluate(input_dir: Path):
    """批量评估目录下的所有PDF
    
    Args:
        input_dir: 包含PDF文件的目录
    """
    print("\n" + "="*70)
    print("📊 批量评估模式")
    print("="*70)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ 未找到PDF文件: {input_dir}")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件\n")
    
    results_summary = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(pdf_files)}] 处理: {pdf_path.name}")
        print(f"{'='*70}")
        
        # 检查是否已有Layer 1输出
        from src.utils.config import Config
        output_dir = Config.OUTPUT_DIR / pdf_path.stem / "layer1"
        
        if output_dir.exists():
            print(f"✅ 使用已有输出: {output_dir}")
            evaluate_from_layer1_output(output_dir, pdf_path)
        else:
            print(f"📄 运行快速评估...")
            quick_check(pdf_path)
        
        # 读取评估结果
        eval_file = output_dir / "layer1_evaluation_no_gt.json" if output_dir.exists() else \
                    Config.OUTPUT_DIR / "quick_check" / f"{pdf_path.stem}_evaluation.json"
        
        if eval_file.exists():
            with open(eval_file, 'r', encoding='utf-8') as f:
                eval_result = json.load(f)
            
            results_summary.append({
                'file': pdf_path.name,
                'score': eval_result['overall_score'],
                'structure_score': eval_result['structure']['structure_richness_score'],
                'heading_score': eval_result['heading_hierarchy']['score'],
                'quality_score': eval_result['quality']['quality_score']
            })
    
    # 显示汇总
    print("\n" + "="*70)
    print("📊 批量评估汇总")
    print("="*70)
    
    print(f"\n{'文件名':<40} {'综合得分':>10} {'结构':>8} {'标题':>8} {'质量':>8}")
    print("-" * 80)
    
    for result in sorted(results_summary, key=lambda x: x['score'], reverse=True):
        print(f"{result['file']:<40} {result['score']:>10.1f} {result['structure_score']:>8.1f} "
              f"{result['heading_score']:>8.1f} {result['quality_score']:>8.1f}")
    
    # 统计
    if results_summary:
        avg_score = sum(r['score'] for r in results_summary) / len(results_summary)
        print("-" * 80)
        print(f"{'平均分':<40} {avg_score:>10.1f}")
        print(f"\n✅ 已处理 {len(results_summary)} 个文件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Layer 1评估（无Ground Truth）')
    parser.add_argument('--layer1-output', type=str, help='Layer 1输出目录')
    parser.add_argument('--pdf', type=str, help='原始PDF路径（用于对比）')
    parser.add_argument('--quick-check', type=str, help='快速检查单个PDF')
    parser.add_argument('--batch', type=str, help='批量评估目录下的PDF')
    
    args = parser.parse_args()
    
    if args.layer1_output:
        layer1_dir = Path(args.layer1_output)
        pdf_path = Path(args.pdf) if args.pdf else None
        evaluate_from_layer1_output(layer1_dir, pdf_path)
    
    elif args.quick_check:
        pdf_path = Path(args.quick_check)
        if not pdf_path.exists():
            print(f"❌ 文件不存在: {pdf_path}")
        else:
            quick_check(pdf_path)
    
    elif args.batch:
        input_dir = Path(args.batch)
        if not input_dir.exists():
            print(f"❌ 目录不存在: {input_dir}")
        else:
            batch_evaluate(input_dir)
    
    else:
        print("使用方法:")
        print("\n1. 评估已有Layer 1输出:")
        print("   python test_layer1_evaluation_no_gt.py --layer1-output data/output/test/layer1 --pdf original.pdf")
        print("\n2. 快速检查单个PDF:")
        print("   python test_layer1_evaluation_no_gt.py --quick-check test.pdf")
        print("\n3. 批量评估:")
        print("   python test_layer1_evaluation_no_gt.py --batch data/input/")
        print("\n示例:")
        print("   python test_layer1_evaluation_no_gt.py --quick-check data/input/paper.pdf")
