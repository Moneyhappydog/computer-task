"""
回归测试：References提取功能
测试2023CVPR-CoMFormer.md + ref_index.json
"""
import sys
import logging
from pathlib import Path
import re

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

# 直接导入模块
import importlib.util
spec = importlib.util.spec_from_file_location(
    "references_extractor",
    project_root / "src" / "layer3_dita_conversion" / "references_extractor.py"
)
references_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(references_extractor_module)
ReferencesExtractor = references_extractor_module.ReferencesExtractor

spec = importlib.util.spec_from_file_location(
    "references_processor",
    project_root / "src" / "layer3_dita_conversion" / "references_processor.py"
)
references_processor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(references_processor_module)
ReferencesProcessor = references_processor_module.ReferencesProcessor


def test_regression():
    """回归测试：使用实际的2023CVPR-CoMFormer.md文件"""
    
    print("="*70)
    print("回归测试：References提取功能")
    print("="*70)
    
    # 输入文件
    markdown_file = project_root / "data" / "output" / "2023CVPR-CoMFormer" / "layer1" / "2023CVPR-CoMFormer.md"
    output_dir = project_root / "data" / "output" / "2023CVPR-CoMFormer" / "layer3"
    
    if not markdown_file.exists():
        print(f"❌ 测试文件不存在: {markdown_file}")
        print("   请确保已运行Layer1生成Markdown文件")
        return False
    
    print(f"\n输入文件: {markdown_file}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 创建处理器
        processor = ReferencesProcessor(linkify_citations=False)  # 暂时禁用链接化以专注于提取
        
        # 处理References
        print("\n🔄 处理References...")
        result = processor.process(
            layer3_output_dir=output_dir,
            markdown_path=markdown_file,
            layer2_result_path=None
        )
        
        if not result['success']:
            print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")
            return False
        
        print("\n✅ 处理成功！")
        
        # 读取生成的文件
        dita_file = output_dir / "014_reference_References.dita"
        ref_index_file = output_dir / "ref_index.json"
        
        assert dita_file.exists(), "DITA文件不存在"
        assert ref_index_file.exists(), "ref_index.json不存在"
        
        print(f"\n📄 生成的文件:")
        print(f"   {dita_file}")
        print(f"   {ref_index_file}")
        
        # 读取DITA内容
        dita_content = dita_file.read_text(encoding='utf-8')
        
        # 测试1: 验证ref1..ref62连续存在
        print("\n测试1: 验证ref1..ref62连续存在...")
        li_matches = re.findall(r'<li\s+id=["\']ref(\d+)["\']', dita_content)
        li_numbers = sorted(int(num) for num in li_matches)
        
        assert len(li_numbers) == 62, f"应该有62个条目，实际: {len(li_numbers)}"
        assert li_numbers[0] == 1, f"第一个条目应该是ref1，实际: ref{li_numbers[0]}"
        assert li_numbers[-1] == 62, f"最后一个条目应该是ref62，实际: ref{li_numbers[-1]}"
        
        # 检查连续性
        expected_numbers = set(range(1, 63))
        actual_numbers = set(li_numbers)
        missing_numbers = sorted(expected_numbers - actual_numbers)
        
        assert not missing_numbers, f"缺失编号: {missing_numbers}"
        
        print(f"✅ 通过: 找到连续的ref1..ref62，共{len(li_numbers)}个条目")
        
        # 测试2: 验证输出中不含星号斜体标记和反引号
        print("\n测试2: 验证输出中不含Markdown格式标记...")
        
        # 检查星号（不应该有孤立的*用于斜体，但可以有<ph>标签）
        # 不应该有 *text* 这种原始Markdown格式
        has_markdown_italic = bool(re.search(r'\*[^*]+\*', dita_content))
        assert not has_markdown_italic, f"发现Markdown斜体标记 *...*"
        
        # 检查反引号
        has_backticks = '`' in dita_content
        assert not has_backticks, f"发现反引号 `"
        
        # 检查是否已转换为DITA标签
        has_ph_italic = '<ph outputclass="italic">' in dita_content
        
        print(f"✅ 通过: 没有Markdown格式标记")
        if has_ph_italic:
            print(f"   ✅ 已正确转换为DITA <ph outputclass='italic'>标签")
        
        # 测试3: 验证输出中不含<table>
        print("\n测试3: 验证输出中不含<table>...")
        has_table = bool(re.search(r'<table\b', dita_content, re.IGNORECASE))
        assert not has_table, f"发现<table>标签（不允许）"
        
        print(f"✅ 通过: 没有<table>标签")
        
        # 测试4: 验证ref_index.json
        print("\n测试4: 验证ref_index.json...")
        import json
        with open(ref_index_file, 'r', encoding='utf-8') as f:
            ref_index = json.load(f)
        
        assert '1' in ref_index and ref_index['1'] == 'ref1', "ref_index应包含1->ref1"
        assert '62' in ref_index and ref_index['62'] == 'ref62', "ref_index应包含62->ref62"
        assert len(ref_index) == 62, f"ref_index应该有62个条目，实际: {len(ref_index)}"
        
        print(f"✅ 通过: ref_index.json包含62个映射")
        
        # 测试5: 使用validate_references_dita进行强校验
        print("\n测试5: 强校验验证...")
        extractor = ReferencesExtractor()
        validation_result = extractor.validate_references_dita(
            dita_file,
            ref_index_path=ref_index_file
        )
        
        assert validation_result['valid'], f"强校验失败: {validation_result.get('errors', [])}"
        assert validation_result['li_count'] == 62, f"期望62个条目，实际: {validation_result['li_count']}"
        assert not validation_result['has_table'], "不应该包含表格"
        
        print(f"✅ 通过: 强校验验证成功")
        print(f"   条目数: {validation_result['li_count']}")
        print(f"   含表格: {validation_result['has_table']}")
        print(f"   结构完整: {validation_result['has_topic_refs'] and validation_result['has_ol']}")
        
        # 显示一些统计信息
        stats = result.get('statistics', {})
        print(f"\n📊 统计信息:")
        print(f"   提取条目数: {stats.get('total_references', 0)}")
        print(f"   编号范围: {stats.get('min_number', 'N/A')}-{stats.get('max_number', 'N/A')}")
        print(f"   结束原因: {stats.get('end_reason', 'N/A')}")
        print(f"   过滤表格行: {stats.get('filtered_table_lines', 0)}")
        print(f"   过滤分页标记: {stats.get('filtered_page_markers', 0)}")
        
        print("\n" + "="*70)
        print("✅ 所有回归测试通过！")
        print("="*70)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_regression()
    sys.exit(0 if success else 1)







