"""
测试References提取模块
"""
import argparse
import json
import logging
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接导入文件，避免通过包导入
import importlib.util
spec = importlib.util.spec_from_file_location(
    "references_extractor",
    project_root / "src" / "layer3_dita_conversion" / "references_extractor.py"
)
references_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(references_extractor_module)
ReferencesExtractor = references_extractor_module.ReferencesExtractor

import logging

def main():
    parser = argparse.ArgumentParser(
        description='测试References提取模块',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从Layer1 Markdown提取（必需）
  python test_references_extraction.py --markdown data/output/2023CVPR-CoMFormer/layer1/2023CVPR-CoMFormer.md
  
  # 指定输出目录
  python test_references_extraction.py --markdown ... --output data/output/2023CVPR-CoMFormer/layer3
  
  # 同时提供Layer2 JSON（可选，仅用于辅助信息）
  python test_references_extraction.py --markdown ... --layer2 ...
  
  # 禁用引文链接化
  python test_references_extraction.py --layer2 ... --no-linkify
        """
    )
    
    parser.add_argument(
        '--markdown',
        type=str,
        required=True,
        help='Layer1的Markdown文件路径（必需，主要数据源）'
    )
    
    parser.add_argument(
        '--layer2',
        type=str,
        help='Layer2结果JSON文件路径（可选，仅用于辅助信息）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Layer3输出目录（默认: layer2目录的父目录/layer3）'
    )
    
    parser.add_argument(
        '--no-linkify',
        action='store_true',
        help='禁用正文引文链接化'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 确定输入文件
    markdown_path = Path(args.markdown)
    layer2_path = Path(args.layer2) if args.layer2 else None
    
    # 验证输入文件
    if not markdown_path.exists():
        print(f"[ERROR] Layer1 Markdown文件不存在: {markdown_path}")
        return 1
    
    if layer2_path and not layer2_path.exists():
        print(f"[WARNING] Layer2 JSON文件不存在: {layer2_path}，将仅使用Layer1 Markdown")
        layer2_path = None
    
    # 确定输出目录
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = markdown_path.parent.parent / "layer3"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("[TEST] 测试References提取模块")
    print("="*70)
    print(f"输入:")
    print(f"  Layer1 Markdown (主要数据源): {markdown_path}")
    if layer2_path:
        print(f"  Layer2 JSON (辅助信息): {layer2_path}")
    print(f"输出目录: {output_dir}")
    print(f"引文链接化: {'禁用' if args.no_linkify else '启用'}")
    print("="*70 + "\n")
    
    # 处理References
    extractor = ReferencesExtractor()
    
    try:
        # 从Layer1 Markdown提取References（主要数据源）
        print(f"[INFO] 从Layer1 Markdown提取References: {markdown_path}")
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        extract_result = extractor.extract_from_markdown(markdown_content)
        
        if not extract_result['success']:
            print("[ERROR] References提取失败")
            print(f"警告: {extract_result.get('warnings', [])}")
            return 1
        
        references = extract_result['references']
        statistics = extract_result['statistics']
        warnings = extract_result.get('warnings', [])
        
        # 生成DITA文件
        dita_filename = "014_reference_References.dita"
        dita_path = output_dir / dita_filename
        
        success = extractor.generate_dita(
            references=references,
            output_path=dita_path,
            topic_id="refs"
        )
        
        if not success:
            print("[ERROR] DITA文件生成失败")
            return 1
        
        # 生成ref_index.json
        ref_index_path = output_dir / "ref_index.json"
        extractor.generate_ref_index(references, ref_index_path)
        
        # 验证DITA文件
        validation_result = extractor.validate_dita(dita_path)
        
        # 链接化正文中的引文（可选）
        linkified_count = 0
        missing_refs_all = []
        
        if not args.no_linkify:
            print("[INFO] 开始链接化正文中的引文")
            
            # 读取ref_index
            import json
            with open(ref_index_path, 'r', encoding='utf-8') as f:
                ref_index = json.load(f)
            # 转换key为int
            ref_index = {int(k): v for k, v in ref_index.items()}
            
            # 查找所有DITA文件（除了References文件本身）
            dita_files = [
                f for f in output_dir.glob("*.dita")
                if f.name != dita_filename
            ]
            
            for dita_file in dita_files:
                count, missing = extractor.linkify_citations_in_dita(
                    dita_file=dita_file,
                    ref_index=ref_index,
                    references_dita_filename=dita_filename
                )
                linkified_count += count
                missing_refs_all.extend(missing)
        
        # 生成结果
        result = {
            'success': True,
            'dita_file': str(dita_path),
            'ref_index_file': str(ref_index_path),
            'statistics': {
                'total_references': statistics['total'],
                'min_number': statistics['min_number'],
                'max_number': statistics['max_number'],
                'missing_numbers': statistics['missing_numbers'],
                'linkified_count': linkified_count,
                'missing_refs_in_body': list(set(missing_refs_all))
            },
            'validation': validation_result,
            'warnings': warnings
        }
        
        if result['success']:
            print("\n" + "="*70)
            print("[SUCCESS] 测试成功!")
            print("="*70)
            print(f"生成的DITA文件: {result['dita_file']}")
            print(f"引用索引文件: {result['ref_index_file']}")
            print(f"\n统计信息:")
            stats = result['statistics']
            print(f"  参考文献总数: {stats['total_references']}")
            print(f"  编号范围: {stats['min_number']}-{stats['max_number']}")
            if stats['missing_numbers']:
                print(f"  缺失编号: {stats['missing_numbers']}")
            print(f"  链接化引文数: {stats['linkified_count']}")
            if stats['missing_refs_in_body']:
                print(f"  正文中缺失的引用: {stats['missing_refs_in_body']}")
            
            print(f"\n验证结果:")
            validation = result['validation']
            print(f"  有效性: {'通过' if validation['valid'] else '失败'}")
            print(f"  条目数: {validation['li_count']}")
            print(f"  包含表格: {'是' if validation['has_table'] else '否'}")
            if validation['errors']:
                print(f"  错误:")
                for error in validation['errors']:
                    print(f"    - {error}")
            if validation['warnings']:
                print(f"  警告:")
                for warning in validation['warnings']:
                    print(f"    - {warning}")
            
            if result.get('warnings'):
                print(f"\n处理警告:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
            
            print("="*70)
            return 0
        else:
            print("\n" + "="*70)
            print("[ERROR] 测试失败!")
            print("="*70)
            print(f"错误: {result.get('error', '未知错误')}")
            if result.get('warnings'):
                print(f"警告:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
            print("="*70)
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

