"""
独立测试脚本：仅测试References提取功能
从Layer1 Markdown提取References并生成DITA文件
"""
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置基础日志（避免loguru依赖）
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# 直接导入需要的模块（避免导入整个converter）
try:
    from src.layer3_dita_conversion.references_extractor import ReferencesExtractor
    from src.layer3_dita_conversion.references_processor import ReferencesProcessor
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("提示: 请确保已安装所有依赖，或在项目根目录运行")
    sys.exit(1)


def test_references_extraction(markdown_path: Path, output_dir: Path, linkify: bool = True):
    """测试References提取功能
    
    Args:
        markdown_path: Layer1 Markdown文件路径
        output_dir: 输出目录
        linkify: 是否链接化正文引文
    """
    print("="*70)
    print("📚 References提取测试")
    print("="*70)
    print(f"输入文件: {markdown_path}")
    print(f"输出目录: {output_dir}")
    print(f"链接化引文: {linkify}")
    print("="*70)
    
    # 检查输入文件
    if not markdown_path.exists():
        print(f"❌ 错误: Markdown文件不存在: {markdown_path}")
        return False
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 创建处理器
        processor = ReferencesProcessor(linkify_citations=linkify)
        
        # 处理References
        print("\n🔄 开始处理References...")
        result = processor.process(
            layer3_output_dir=output_dir,
            markdown_path=markdown_path,
            layer2_result_path=None  # 不使用Layer2
        )
        
        # 显示结果
        print("\n" + "="*70)
        if result['success']:
            print("✅ References处理成功！")
            print("="*70)
            
            stats = result.get('statistics', {})
            print(f"\n📊 统计信息:")
            print(f"   提取条目数: {stats.get('total_references', 0)}")
            print(f"   编号范围: {stats.get('min_number', 'N/A')}-{stats.get('max_number', 'N/A')}")
            print(f"   缺失编号: {stats.get('missing_numbers', [])}")
            print(f"   链接化数量: {stats.get('linkified_count', 0)}")
            
            if stats.get('missing_numbers'):
                print(f"   ⚠️  警告: 发现缺失编号: {stats['missing_numbers']}")
            
            # 验证信息
            validation = result.get('validation', {})
            if validation:
                print(f"\n✅ 验证结果:")
                print(f"   条目数: {validation.get('li_count', 0)}")
                print(f"   包含表格: {'是' if validation.get('has_table') else '否'}")
                print(f"   文件大小: {validation.get('file_size', 0)} 字节")
            
            # 输出文件路径
            dita_file = output_dir / "014_reference_References.dita"
            ref_index_file = output_dir / "ref_index.json"
            
            print(f"\n📄 输出文件:")
            print(f"   DITA文件: {dita_file}")
            print(f"   引用索引: {ref_index_file}")
            
            if dita_file.exists():
                # 显示前几个条目预览
                print(f"\n📋 DITA文件预览（前5个条目）:")
                content = dita_file.read_text(encoding='utf-8')
                import re
                li_matches = list(re.finditer(r'<li\s+id="ref(\d+)"[^>]*><p>(.*?)</p></li>', content, re.DOTALL))
                for i, match in enumerate(li_matches[:5], 1):
                    ref_num = match.group(1)
                    ref_text = match.group(2)[:80].replace('\n', ' ')
                    print(f"   {i}. [ref{ref_num}] {ref_text}...")
                if len(li_matches) > 5:
                    print(f"   ... 还有 {len(li_matches) - 5} 个条目")
            
            # 警告信息
            warnings = result.get('warnings', [])
            if warnings:
                print(f"\n⚠️  警告信息:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            return True
            
        else:
            print("❌ References处理失败！")
            print("="*70)
            print(f"\n错误信息: {result.get('error', '未知错误')}")
            
            validation_errors = result.get('validation_errors', [])
            if validation_errors:
                print(f"\n验证错误:")
                for err in validation_errors:
                    print(f"   - {err}")
            
            warnings = result.get('warnings', [])
            if warnings:
                print(f"\n警告信息:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            return False
            
    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='测试References提取功能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试指定Markdown文件
  python test_references_only.py --markdown data/output/2023CVPR-CoMFormer/layer1/2023CVPR-CoMFormer.md
  
  # 指定输出目录
  python test_references_only.py --markdown input.md --output output_dir
  
  # 禁用引文链接化
  python test_references_only.py --markdown input.md --no-linkify
        """
    )
    
    parser.add_argument(
        '--markdown',
        type=str,
        required=True,
        help='Layer1 Markdown文件路径'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出目录（默认：Markdown文件所在目录的../layer3_refs_test）'
    )
    
    parser.add_argument(
        '--no-linkify',
        action='store_true',
        help='禁用正文引文链接化'
    )
    
    args = parser.parse_args()
    
    # 解析路径
    markdown_path = Path(args.markdown).resolve()
    
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        # 默认输出目录：data/output/{doc_name}/layer3/
        # 如果输入是 data/output/2023CVPR-CoMFormer/layer1/xxx.md
        # 输出到 data/output/2023CVPR-CoMFormer/layer3/
        if 'layer1' in markdown_path.parts:
            # 找到layer1所在的目录（通常是doc_name目录）
            layer1_idx = markdown_path.parts.index('layer1')
            doc_dir = Path(*markdown_path.parts[:layer1_idx+1]).parent
            output_dir = doc_dir / "layer3"
        else:
            # 如果不在layer1目录下，使用data/output/下的layer3
            project_root = Path(__file__).parent
            output_dir = project_root / "data" / "output" / "references_test" / "layer3"
    
    # 运行测试
    success = test_references_extraction(
        markdown_path=markdown_path,
        output_dir=output_dir,
        linkify=not args.no_linkify
    )
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

