"""
单元测试：References提取模块
测试从Markdown提取References并生成DITA
"""
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.layer3_dita_conversion.references_extractor import ReferencesExtractor
import re


def test_references_extraction():
    """测试References提取功能"""
    
    # 测试数据：来自2023CVPR-CoMFormer.md的末尾部分
    test_markdown = """<!-- Page 9 -->

## References

[1] Nicolas Carion, Francisco Massa, Gabriel Synnaeve, Nicolas Usunier, Alexander Kirillov, and Sergey Zagoruyko. Endto-end object detection with transformers. In *ECCV*, pages 213–229. Springer, 2020. (pages 2, 5).

[2] Fabio Cermelli, Dario Fontanel, Antonio Tavera, Marco Ciccone, and Barbara Caputo. Incremental learning in semantic segmentation from image labels. In *CVPR*, pages 4371– 4381, 2022. (page 2).

[3] Fabio Cermelli, Antonino Geraci, Dario Fontanel, and Barbara Caputo. Modeling missing annotations for incremental learning in object detection. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 3700–3710, 2022. (pages 1, 2).

---
<!-- Page 12 -->

|           | 50-50 (11 tasks)   |        |      |      |
|-----------|--------------------|--------|------|------|
| Method    | 1-50               | 51-150 | avg  | all  |
| FT        | 0.0                | 14.3   | 23.1 | 9.5  |
| MiB       | 33.6               | 16.3   | 31.8 | 22.1 |

Table 6. Continual Panoptic Segmentation results on ADE20K dataset on 50-50 setting in PQ.

## Appendix A. Additional Quantitative Results
"""
    
    print("="*70)
    print("单元测试：References提取")
    print("="*70)
    
    # 1. 创建提取器
    extractor = ReferencesExtractor()
    
    # 2. 提取References
    print("\n步骤1: 提取References...")
    result = extractor.extract_from_markdown(test_markdown)
    
    assert result['success'], f"提取失败: {result.get('warnings', [])}"
    assert len(result['references']) >= 3, f"应该至少提取3个条目，实际: {len(result['references'])}"
    
    print(f"✅ 提取成功: {len(result['references'])} 个条目")
    print(f"   编号范围: {result['statistics']['min_number']}-{result['statistics']['max_number']}")
    
    # 验证条目内容
    assert result['references'][0]['number'] == 1, "第一个条目应该是[1]"
    assert result['references'][1]['number'] == 2, "第二个条目应该是[2]"
    assert result['references'][2]['number'] == 3, "第三个条目应该是[3]"
    
    # 验证没有包含表格内容
    for ref in result['references']:
        ref_text = ref['text'].lower()
        assert '|' not in ref_text, f"条目 {ref['number']} 不应包含表格标记 '|'"
        assert '50-50' not in ref_text, f"条目 {ref['number']} 不应包含表格内容 '50-50'"
        assert 'method' not in ref_text or 'method' in ref_text and 'method' in ref_text.split()[0:3], "检查方法名是否误判为表格"
    
    print("✅ 验证通过: 没有表格内容混入")
    
    # 3. 生成DITA文件
    print("\n步骤2: 生成DITA文件...")
    with tempfile.TemporaryDirectory() as tmpdir:
        dita_path = Path(tmpdir) / "014_reference_References.dita"
        
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
        li_count = len(li_matches)
        
        assert li_count >= 3, f"应该有至少3个<li id='refN'>条目，实际: {li_count}"
        
        # 检查是否包含<table>（禁止）
        has_table = bool(re.search(r'<table\b', dita_content, re.IGNORECASE))
        assert not has_table, f"DITA文件包含<table>标签，这是不允许的。内容预览: {dita_content[:500]}"
        
        # 检查基本结构
        assert '<topic' in dita_content, "应该包含<topic>标签"
        assert '<title>References</title>' in dita_content, "应该包含<title>References</title>"
        assert '<ol>' in dita_content, "应该包含<ol>标签"
        
        print(f"✅ DITA文件生成成功: {li_count} 个条目")
        print(f"✅ 验证通过: 没有<table>标签")
    
    # 4. 验证DITA文件
    print("\n步骤3: 验证DITA文件...")
    with tempfile.TemporaryDirectory() as tmpdir:
        dita_path = Path(tmpdir) / "014_reference_References.dita"
        
        extractor.generate_dita(
            references=result['references'],
            output_path=dita_path,
            topic_id="refs"
        )
        
        validation_result = extractor.validate_dita(dita_path)
        
        assert validation_result['valid'], f"验证失败: {validation_result['errors']}"
        assert validation_result['li_count'] >= 3, f"应该有至少3个条目，实际: {validation_result['li_count']}"
        assert not validation_result['has_table'], "不应该包含表格"
        
        print(f"✅ 验证通过: {validation_result}")
    
    print("\n" + "="*70)
    print("✅ 所有测试通过！")
    print("="*70)


if __name__ == "__main__":
    test_references_extraction()







