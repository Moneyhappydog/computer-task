"""
单元测试：References提取（使用[60]-[62]后跟表格的片段）
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

# 直接导入文件，避免通过包导入
import importlib.util
spec = importlib.util.spec_from_file_location(
    "references_extractor",
    project_root / "src" / "layer3_dita_conversion" / "references_extractor.py"
)
references_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(references_extractor_module)
ReferencesExtractor = references_extractor_module.ReferencesExtractor


def test_references_extraction():
    """测试References提取（[60]-[62]片段）"""
    
    # 测试数据：包含[60]-[62]和表格的片段（需要包含 ## References 标题）
    test_markdown = """## References

[60] H. Zhao, J. Shi, X. Qi, X. Wang, and J. Jia. Pyramid scene parsing network. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2017. (page 2).

[61] Hengshuang Zhao, Yi Zhang, Shu Liu, Jianping Shi, Chen Change Loy, Dahua Lin, and Jiaya Jia. Psanet: Pointwise spatial attention network for scene parsing. In Proceedings of the IEEE European Conference on Computer Vision (ECCV), 2018. (page 2).

[62] Bolei Zhou, Hang Zhao, Xavier Puig, Sanja Fidler, Adela Barriuso, and Antonio Torralba. Scene parsing through ade20k dataset. In *Proceedings of the IEEE Conference* on Computer Vision and Pattern Recognition (CVPR), 2017. (pages 5, 15).
---
<!-- Page 12 -->

|           | 50-50 (11 tasks)   |        |      |      |
|-----------|--------------------|--------|------|------|
| Method    | 1-50               | 51-150 | avg  | all  |
| FT        | 0.0                | 14.3   | 23.1 | 9.5  |
| MiB       | 33.6               | 16.3   | 31.8 | 22.1 |

Table 6. Continual Panoptic Segmentation results on ADE20K dataset on 50-50 setting in PQ. Table 7. Continual Semantic Segmentation results on ADE20K dataset on 50-50 setting in mIoU.

## Appendix A. Additional Quantitative Results
"""
    
    print("="*70)
    print("单元测试：References提取（[60]-[62]片段）")
    print("="*70)
    
    extractor = ReferencesExtractor()
    
    # 测试1: 提取References
    print("\n测试1: 提取References...")
    result = extractor.extract_from_markdown(test_markdown)
    
    assert result['success'], f"提取失败: {result.get('warnings', [])}"
    assert len(result['references']) == 3, f"应该提取3个条目，实际: {len(result['references'])}"
    
    # 验证条目编号
    assert result['references'][0]['number'] == 60, "第一个条目应该是[60]"
    assert result['references'][1]['number'] == 61, "第二个条目应该是[61]"
    assert result['references'][2]['number'] == 62, "第三个条目应该是[62]"
    
    print(f"✅ 提取成功: {len(result['references'])} 个条目")
    print(f"   条目: [60], [61], [62]")
    
    # 验证没有包含表格内容
    for ref in result['references']:
        ref_text = ref['text'].lower()
        assert '|' not in ref_text, f"条目 {ref['number']} 不应包含表格标记 '|'"
        assert '50-50' not in ref_text, f"条目 {ref['number']} 不应包含表格内容 '50-50'"
        assert 'method' not in ref_text or ref['number'] in [60, 61, 62], f"条目 {ref['number']} 不应包含表格内容"
        assert 'table 6' not in ref_text and 'table 7' not in ref_text, f"条目 {ref['number']} 不应包含表格标题"
    
    print("✅ 验证通过: 没有表格内容混入")
    
    # 验证清洗：页码引用应被移除
    for ref in result['references']:
        assert '(page' not in ref['text'].lower(), f"条目 {ref['number']} 应已移除页码引用"
        assert '(pages' not in ref['text'].lower(), f"条目 {ref['number']} 应已移除页码引用"
    
    print("✅ 验证通过: 页码引用已清洗")
    
    # 测试2: 生成DITA
    print("\n测试2: 生成DITA文件...")
    # 使用项目data目录作为输出
    project_root = Path(__file__).parent
    test_output_dir = project_root / "data" / "output" / "references_test" / "layer3"
    test_output_dir.mkdir(parents=True, exist_ok=True)
    dita_path = test_output_dir / "014_reference_References.dita"
        
        success = extractor.generate_dita(
            references=result['references'],
            output_path=dita_path,
            topic_id="refs"
        )
        
        assert success, "DITA文件生成失败"
        assert dita_path.exists(), "DITA文件不存在"
        
        # 读取并验证内容
        dita_content = dita_path.read_text(encoding='utf-8')
        
        # 检查<li id="refN">数量
        li_matches = re.findall(r'<li\s+id=["\']ref\d+["\']', dita_content)
        assert len(li_matches) == 3, f"应该有3个<li id='refN'>条目，实际: {len(li_matches)}"
        
        # 检查是否包含<table>（禁止）
        has_table = bool(re.search(r'<table\b', dita_content, re.IGNORECASE))
        assert not has_table, f"DITA文件包含<table>标签，这是不允许的"
        
        # 检查基本结构
        assert '<topic id="refs">' in dita_content or "<topic id='refs'>" in dita_content, "应该包含<topic id='refs'>"
        assert '<title>References</title>' in dita_content, "应该包含<title>References</title>"
        assert '<ol>' in dita_content, "应该包含<ol>标签"
        
        print(f"✅ DITA文件生成成功: {len(li_matches)} 个条目")
        print(f"✅ 验证通过: 没有<table>标签")
        print(f"   输出文件: {dita_path}")
    
    # 测试3: 验证DITA文件
    print("\n测试3: 验证DITA文件...")
    # 使用相同的输出目录
    dita_path = test_output_dir / "014_reference_References.dita"
        
        extractor.generate_dita(
            references=result['references'],
            output_path=dita_path,
            topic_id="refs"
        )
        
        validation_result = extractor.validate_references_dita(dita_path)
        
        assert validation_result['valid'], f"验证失败: {validation_result['errors']}"
        assert validation_result['li_count'] == 3, f"应该有3个条目，实际: {validation_result['li_count']}"
        assert not validation_result['has_table'], "不应该包含表格"
        assert validation_result['has_topic_refs'], "应该包含<topic id='refs'>"
        assert validation_result['has_ol'], "应该包含<ol>"
        
        print(f"✅ 验证通过: {validation_result}")
    
    # 测试4: 生成ref_index.json
    print("\n测试4: 生成ref_index.json...")
    # 使用相同的输出目录
    ref_index_path = test_output_dir / "ref_index.json"
        
        extractor.generate_ref_index(result['references'], ref_index_path)
        
        assert ref_index_path.exists(), "ref_index.json不存在"
        
        import json
        with open(ref_index_path, 'r', encoding='utf-8') as f:
            ref_index = json.load(f)
        
        assert '60' in ref_index and ref_index['60'] == 'ref60', "ref_index应包含60->ref60"
        assert '61' in ref_index and ref_index['61'] == 'ref61', "ref_index应包含61->ref61"
        assert '62' in ref_index and ref_index['62'] == 'ref62', "ref_index应包含62->ref62"
        
        print(f"✅ ref_index.json生成成功: {ref_index}")
        print(f"   输出文件: {ref_index_path}")
    
    print("\n" + "="*70)
    print("✅ 所有测试通过！")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        test_references_extraction()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

