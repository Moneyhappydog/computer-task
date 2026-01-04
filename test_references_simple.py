"""
简化版References测试脚本
直接测试References提取，不依赖复杂导入
"""
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

def test_references(markdown_file: str, output_dir: str = None, no_linkify: bool = False):
    """测试References提取
    
    Args:
        markdown_file: Markdown文件路径
        output_dir: 输出目录（默认：data/output/{doc_name}/layer3/）
        no_linkify: 是否禁用引文链接化
    """
    markdown_path = Path(markdown_file).resolve()
    
    if not markdown_path.exists():
        print(f"❌ 错误: 文件不存在: {markdown_path}")
        return False
    
    if output_dir:
        output_path = Path(output_dir).resolve()
    else:
        # 默认输出路径：data/output/{doc_name}/layer3/
        # 如果输入是 data/output/2023CVPR-CoMFormer/layer1/xxx.md
        # 输出到 data/output/2023CVPR-CoMFormer/layer3/
        if 'layer1' in markdown_path.parts:
            # 找到layer1所在的目录（通常是doc_name目录）
            layer1_idx = markdown_path.parts.index('layer1')
            doc_dir = Path(*markdown_path.parts[:layer1_idx+1]).parent
            output_path = doc_dir / "layer3"
        else:
            # 如果不在layer1目录下，使用data/output/下的layer3
            project_root = Path(__file__).parent
            output_path = project_root / "data" / "output" / "references_test" / "layer3"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("📚 References提取测试")
    print("="*70)
    print(f"输入: {markdown_path}")
    print(f"输出: {output_path}")
    print(f"链接化: {not no_linkify}")
    print("="*70)
    
    try:
        # 导入模块
        print("\n🔄 导入模块...")
        from src.layer3_dita_conversion.references_processor import ReferencesProcessor
        
        # 创建处理器
        processor = ReferencesProcessor(linkify_citations=not no_linkify)
        
        # 处理
        print("🔄 处理References...")
        result = processor.process(
            layer3_output_dir=output_path,
            markdown_path=markdown_path,
            layer2_result_path=None
        )
        
        # 显示结果
        print("\n" + "="*70)
        if result['success']:
            print("✅ 成功!")
            print("="*70)
            
            stats = result.get('statistics', {})
            print(f"\n📊 统计:")
            print(f"   条目数: {stats.get('total_references', 0)}")
            print(f"   编号: {stats.get('min_number', 'N/A')}-{stats.get('max_number', 'N/A')}")
            if stats.get('missing_numbers'):
                print(f"   缺失: {stats['missing_numbers']}")
            print(f"   链接化: {stats.get('linkified_count', 0)}")
            
            validation = result.get('validation', {})
            if validation:
                print(f"\n✅ 验证:")
                print(f"   <li>数量: {validation.get('li_count', 0)}")
                print(f"   含表格: {'是' if validation.get('has_table') else '否'}")
                print(f"   文件大小: {validation.get('file_size', 0)} 字节")
            
            dita_file = output_path / "014_reference_References.dita"
            print(f"\n📄 输出文件:")
            print(f"   {dita_file}")
            
            if dita_file.exists():
                # 预览前3个条目
                content = dita_file.read_text(encoding='utf-8')
                import re
                matches = list(re.finditer(r'<li\s+id="ref(\d+)"[^>]*><p>(.*?)</p></li>', content, re.DOTALL))
                if matches:
                    print(f"\n📋 预览（前3个条目）:")
                    for i, m in enumerate(matches[:3], 1):
                        num = m.group(1)
                        text = m.group(2).strip()[:60].replace('\n', ' ')
                        print(f"   {i}. [ref{num}] {text}...")
            
            return True
        else:
            print("❌ 失败!")
            print("="*70)
            print(f"错误: {result.get('error', '未知')}")
            if result.get('validation_errors'):
                print(f"验证错误: {result['validation_errors']}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("\n提示: 请确保:")
        print("  1. 在项目根目录运行")
        print("  2. 已安装所有依赖")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='测试References提取')
    parser.add_argument('markdown', help='Markdown文件路径')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('--no-linkify', action='store_true', help='禁用引文链接化')
    
    args = parser.parse_args()
    
    success = test_references(
        markdown_file=args.markdown,
        output_dir=args.output,
        no_linkify=args.no_linkify
    )
    
    sys.exit(0 if success else 1)

