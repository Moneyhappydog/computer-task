"""
准备Ground Truth数据
帮助用户从原始文档中提取或标注Ground Truth
"""

import json
from pathlib import Path
import argparse
from src.evaluation.layer1_metrics import extract_headings


def create_ground_truth_template(output_file: Path):
    """创建Ground Truth模板文件
    
    Args:
        output_file: 输出文件路径
    """
    template = {
        "source_document": "原始文档路径",
        "text": "这里粘贴完整的参考文本（Ground Truth）\n\n可以手动从PDF复制，或使用其他工具提取",
        "headings": [
            {
                "level": 1,
                "text": "Introduction",
                "line_number": 1
            },
            {
                "level": 2,
                "text": "Background",
                "line_number": 5
            }
        ],
        "notes": "可选：添加备注信息"
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Ground Truth模板已创建: {output_file}")
    print("\n📝 请按以下步骤准备Ground Truth:")
    print("  1. 打开模板文件")
    print("  2. 填写 'source_document' 字段")
    print("  3. 在 'text' 字段粘贴参考文本")
    print("  4. 可选：手动标注 'headings' 列表（或使用 --auto-extract）")
    print("  5. 保存文件")


def extract_from_markdown(markdown_file: Path, output_file: Path):
    """从Markdown文件自动提取Ground Truth
    
    Args:
        markdown_file: Markdown文件路径
        output_file: 输出JSON文件路径
    """
    print(f"📄 读取Markdown文件: {markdown_file}")
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # 自动提取标题
    headings = extract_headings(markdown_text)
    
    print(f"✅ 提取完成: {len(headings)} 个标题")
    
    # 创建Ground Truth数据
    ground_truth = {
        "source_document": str(markdown_file),
        "text": markdown_text,
        "headings": headings,
        "notes": "自动从Markdown文件提取"
    }
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Ground Truth已保存: {output_file}")
    print(f"\n📊 统计信息:")
    print(f"  文本长度: {len(markdown_text)} 字符")
    print(f"  标题数量: {len(headings)}")
    print(f"  标题层级分布:")
    
    level_dist = {}
    for h in headings:
        level = h['level']
        level_dist[level] = level_dist.get(level, 0) + 1
    
    for level in sorted(level_dist.keys()):
        print(f"    H{level}: {level_dist[level]} 个")


def validate_ground_truth(ground_truth_file: Path):
    """验证Ground Truth文件格式
    
    Args:
        ground_truth_file: Ground Truth文件路径
    """
    print(f"🔍 验证Ground Truth文件: {ground_truth_file}")
    
    try:
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查必需字段
        required_fields = ['text']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print(f"❌ 缺少必需字段: {missing_fields}")
            return False
        
        # 检查文本
        if not data['text'] or len(data['text'].strip()) < 10:
            print("⚠️  'text' 字段内容过短或为空")
        
        # 检查标题
        if 'headings' in data:
            headings = data['headings']
            print(f"✅ 标题数量: {len(headings)}")
            
            for i, h in enumerate(headings):
                if 'level' not in h or 'text' not in h:
                    print(f"⚠️  标题 {i+1} 缺少 'level' 或 'text' 字段")
        else:
            print("⚠️  未找到 'headings' 字段（将自动从文本提取）")
        
        print("\n✅ Ground Truth文件格式正确！")
        print(f"   文本长度: {len(data['text'])} 字符")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def show_comparison(layer1_output_dir: Path, ground_truth_file: Path):
    """显示Layer 1输出与Ground Truth的对比
    
    Args:
        layer1_output_dir: Layer 1输出目录
        ground_truth_file: Ground Truth文件
    """
    print("\n" + "="*70)
    print("📊 对比：Layer 1输出 vs Ground Truth")
    print("="*70)
    
    # 读取Layer 1输出
    layer1_result_file = layer1_output_dir / "layer1_result.json"
    if not layer1_result_file.exists():
        print(f"❌ 未找到Layer 1输出: {layer1_result_file}")
        return
    
    with open(layer1_result_file, 'r', encoding='utf-8') as f:
        layer1_data = json.load(f)
    
    extracted_text = layer1_data.get('markdown', '')
    extracted_headings = extract_headings(extracted_text)
    
    # 读取Ground Truth
    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    
    reference_text = gt_data.get('text', '')
    reference_headings = gt_data.get('headings')
    if not reference_headings:
        reference_headings = extract_headings(reference_text)
    
    # 显示对比
    print(f"\n📄 文本长度对比:")
    print(f"  Ground Truth: {len(reference_text)} 字符")
    print(f"  Layer 1输出:  {len(extracted_text)} 字符")
    print(f"  差异: {abs(len(reference_text) - len(extracted_text))} 字符")
    print(f"  比例: {len(extracted_text) / len(reference_text):.2%}")
    
    print(f"\n📑 标题数量对比:")
    print(f"  Ground Truth: {len(reference_headings)} 个标题")
    print(f"  Layer 1输出:  {len(extracted_headings)} 个标题")
    
    print(f"\n📑 标题详细对比:")
    print(f"\n{'='*35} Ground Truth {'='*35}")
    for h in reference_headings[:10]:
        indent = "  " * (h['level'] - 1)
        print(f"{indent}{'#' * h['level']} {h['text']}")
    if len(reference_headings) > 10:
        print(f"  ... 还有 {len(reference_headings) - 10} 个标题")
    
    print(f"\n{'='*35} Layer 1 输出 {'='*35}")
    for h in extracted_headings[:10]:
        indent = "  " * (h['level'] - 1)
        print(f"{indent}{'#' * h['level']} {h['text']}")
    if len(extracted_headings) > 10:
        print(f"  ... 还有 {len(extracted_headings) - 10} 个标题")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='准备Ground Truth数据')
    parser.add_argument('--create-template', type=str, help='创建Ground Truth模板文件')
    parser.add_argument('--from-markdown', type=str, help='从Markdown文件提取Ground Truth')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--validate', type=str, help='验证Ground Truth文件')
    parser.add_argument('--compare', action='store_true', help='对比Layer 1输出和Ground Truth')
    parser.add_argument('--layer1-output', type=str, help='Layer 1输出目录（用于对比）')
    parser.add_argument('--ground-truth', type=str, help='Ground Truth文件（用于对比）')
    
    args = parser.parse_args()
    
    if args.create_template:
        output_path = Path(args.output) if args.output else Path(args.create_template)
        create_ground_truth_template(output_path)
    
    elif args.from_markdown:
        markdown_path = Path(args.from_markdown)
        output_path = Path(args.output) if args.output else markdown_path.with_suffix('.gt.json')
        extract_from_markdown(markdown_path, output_path)
    
    elif args.validate:
        validate_ground_truth(Path(args.validate))
    
    elif args.compare:
        if not args.layer1_output or not args.ground_truth:
            print("❌ 对比需要同时指定 --layer1-output 和 --ground-truth")
        else:
            show_comparison(Path(args.layer1_output), Path(args.ground_truth))
    
    else:
        print("使用方法:")
        print("\n1. 创建模板:")
        print("   python prepare_ground_truth.py --create-template gt_template.json")
        print("\n2. 从Markdown自动提取:")
        print("   python prepare_ground_truth.py --from-markdown file.md --output gt.json")
        print("\n3. 验证Ground Truth:")
        print("   python prepare_ground_truth.py --validate gt.json")
        print("\n4. 对比评估:")
        print("   python prepare_ground_truth.py --compare --layer1-output data/output/test/layer1 --ground-truth gt.json")
