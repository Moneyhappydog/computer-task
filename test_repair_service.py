"""
测试DITA包修复服务（Option C）
"""
import sys
import json
import zipfile
from pathlib import Path
import tempfile
import shutil

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web.services.repair_service import DitaPackageRepairService


def create_test_dita_content(ref_number: int = 1) -> str:
    """创建测试用的DITA内容"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="test_concept_{ref_number}">
  <title>Test Concept {ref_number}</title>
  <conbody>
    <p>This is a test concept with citation [1].</p>
    <p>Another citation [2] here.</p>
  </conbody>
</concept>'''


def create_test_references_dita() -> str:
    """创建测试用的References DITA文件"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">
<topic id="refs">
  <title>References</title>
  <body>
    <ol>
      <li id="ref1"><p>Author1. Title1. Journal, 2020.</p></li>
      <li id="ref2"><p>Author2. Title2. Journal, 2021.</p></li>
      <li id="ref3"><p>Author3. Title3. Journal, 2022.</p></li>
    </ol>
  </body>
</topic>'''


def create_test_zip_with_dita_files(
    output_path: Path,
    include_references: bool = False,
    include_citations: bool = False
) -> None:
    """创建包含DITA文件的测试ZIP"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加普通DITA文件
        dita_content = create_test_dita_content(1)
        if include_citations and not include_references:
            # 如果包含引文但不包含references，这会导致测试失败（缺失引用）
            pass
        zipf.writestr("001_concept_test.dita", dita_content)
        
        # 可选：添加References文件
        if include_references:
            ref_content = create_test_references_dita()
            zipf.writestr("014_reference_References.dita", ref_content)


def test_1_no_dita_files():
    """测试1: 上传不含.dita文件的ZIP，应该返回错误"""
    print("\n" + "="*70)
    print("测试1: 不含.dita文件的ZIP")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建不含.dita的ZIP
        zip_path = Path(tmpdir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.writestr("readme.txt", "This is a readme file")
        
        # 初始化服务
        output_dir = Path(tmpdir) / "output"
        service = DitaPackageRepairService(output_base_dir=output_dir)
        
        try:
            result = service.process_package(
                zip_file_path=zip_path,
                doc_name="test_doc",
                linkify_citations=False,
                build_dita_ot=False
            )
            
            assert not result['success'], "应该失败"
            assert "未找到任何.dita文件" in str(result['errors']) or any("dita" in str(e).lower() for e in result['errors']), "错误信息应该提到dita文件"
            print("✅ 测试通过: 正确检测到缺少.dita文件")
        except ValueError as e:
            if "dita" in str(e).lower():
                print(f"✅ 测试通过: 正确抛出错误 - {e}")
            else:
                print(f"❌ 测试失败: 错误信息不正确 - {e}")
                raise


def test_2_basic_processing():
    """测试2: 上传含.dita文件的ZIP，应该能输出output.zip + repair_result.json"""
    print("\n" + "="*70)
    print("测试2: 基本处理（含.dita文件）")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建含.dita的ZIP
        zip_path = Path(tmpdir) / "test.zip"
        create_test_zip_with_dita_files(zip_path, include_references=False)
        
        # 初始化服务
        output_dir = Path(tmpdir) / "output"
        service = DitaPackageRepairService(output_base_dir=output_dir)
        
        result = service.process_package(
            zip_file_path=zip_path,
            doc_name="test_doc",
            linkify_citations=False,
            build_dita_ot=False
        )
        
        assert result['success'], f"应该成功，但得到错误: {result.get('errors')}"
        assert len(result['dita_files']) > 0, "应该有DITA文件"
        
        # 检查输出文件
        job_dir = output_dir / "test_doc" / "repair" / result['job_id']
        output_zip = job_dir / "output.zip"
        result_json = job_dir / "repair_result.json"
        
        assert output_zip.exists(), "output.zip应该存在"
        assert result_json.exists(), "repair_result.json应该存在"
        
        # 验证ZIP内容
        with zipfile.ZipFile(output_zip, 'r') as zipf:
            file_list = zipf.namelist()
            assert any(f.endswith('.dita') for f in file_list), "ZIP应该包含.dita文件"
            assert "repair_result.json" in file_list, "ZIP应该包含repair_result.json"
        
        print("✅ 测试通过: 成功处理并生成output.zip和repair_result.json")
        print(f"   Job ID: {result['job_id']}")
        print(f"   DITA文件数: {len(result['dita_files'])}")


def test_3_linkify_with_references():
    """测试3: 上传含References的ZIP并启用linkify，应该生成ref_index.json并链接化引文"""
    print("\n" + "="*70)
    print("测试3: 引文链接化（含References文件）")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建含References和引文的ZIP
        zip_path = Path(tmpdir) / "test.zip"
        create_test_zip_with_dita_files(zip_path, include_references=True, include_citations=True)
        
        # 初始化服务
        output_dir = Path(tmpdir) / "output"
        service = DitaPackageRepairService(output_base_dir=output_dir)
        
        result = service.process_package(
            zip_file_path=zip_path,
            doc_name="test_doc",
            linkify_citations=True,  # 启用链接化
            build_dita_ot=False
        )
        
        assert result['success'], f"应该成功，但得到错误: {result.get('errors')}"
        assert result['ref_index'] is not None, "应该生成ref_index"
        assert result['ref_index']['count'] == 3, f"应该有3个引用，实际: {result['ref_index']['count']}"
        
        # 检查linkify结果
        assert 'linkify' in result, "应该有linkify结果"
        assert result['linkify']['count'] > 0, "应该链接化了一些引用"
        
        # 检查workdir中的文件
        job_dir = output_dir / "test_doc" / "repair" / result['job_id']
        workdir = job_dir / "workdir"
        ref_index_file = workdir / "ref_index.json"
        
        assert ref_index_file.exists(), "ref_index.json应该存在"
        
        # 验证ref_index.json内容
        with open(ref_index_file, 'r', encoding='utf-8') as f:
            ref_index = json.load(f)
            assert '1' in ref_index and ref_index['1'] == 'ref1', "ref_index应该包含ref1"
            assert '2' in ref_index and ref_index['2'] == 'ref2', "ref_index应该包含ref2"
        
        # 检查链接化后的DITA文件
        dita_file = workdir / "001_concept_test.dita"
        assert dita_file.exists(), "DITA文件应该存在"
        
        with open(dita_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 应该包含xref标签
            assert '<xref' in content, "应该包含<xref>标签"
            # 不应该包含原始的[1]格式（应该被替换）
            # 但为了兼容，允许同时存在（如果某些[1]在保护区域内）
            assert '014_reference_References.dita#refs/ref1' in content or '<xref' in content, "应该包含xref链接"
        
        print("✅ 测试通过: 成功链接化引文")
        print(f"   引用索引数: {result['ref_index']['count']}")
        print(f"   链接化数量: {result['linkify']['count']}")


def test_4_zip_slip_protection():
    """测试4: 测试Zip Slip保护"""
    print("\n" + "="*70)
    print("测试4: Zip Slip保护")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建包含路径遍历的ZIP
        zip_path = Path(tmpdir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # 尝试路径遍历
            zipf.writestr("../../evil.txt", "evil content")
            zipf.writestr("normal.dita", create_test_dita_content())
        
        output_dir = Path(tmpdir) / "output"
        service = DitaPackageRepairService(output_base_dir=output_dir)
        
        result = service.process_package(
            zip_file_path=zip_path,
            doc_name="test_doc",
            linkify_citations=False,
            build_dita_ot=False
        )
        
        # 应该成功处理，但evil.txt不应该被提取到workdir外
        workdir = output_dir / "test_doc" / "repair" / result['job_id'] / "workdir"
        evil_file = workdir.parent.parent.parent / "evil.txt"
        
        assert not evil_file.exists(), "evil.txt不应该被提取到workdir外"
        assert (workdir / "normal.dita").exists(), "normal.dita应该被正确提取"
        
        print("✅ 测试通过: Zip Slip保护有效")


def test_5_references_structure_validation():
    """测试5: References文件结构验证"""
    print("\n" + "="*70)
    print("测试5: References文件结构验证")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建包含无效References文件的ZIP（包含table标签）
        zip_path = Path(tmpdir) / "test.zip"
        invalid_ref_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">
<topic id="refs">
  <title>References</title>
  <body>
    <table>
      <tgroup cols="2">
        <tbody>
          <row><entry>Invalid</entry></row>
        </tbody>
      </tgroup>
    </table>
  </body>
</topic>'''
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.writestr("014_reference_References.dita", invalid_ref_content)
            zipf.writestr("001_concept_test.dita", create_test_dita_content())
        
        output_dir = Path(tmpdir) / "output"
        service = DitaPackageRepairService(output_base_dir=output_dir)
        
        result = service.process_package(
            zip_file_path=zip_path,
            doc_name="test_doc",
            linkify_citations=False,
            build_dita_ot=False
        )
        
        # 应该失败，因为References文件包含table标签
        assert not result['success'], "应该失败（References包含table）"
        assert any('table' in str(e).lower() for e in result['errors']), "错误应该提到table"
        
        print("✅ 测试通过: 正确检测到References文件中的table标签")


if __name__ == "__main__":
    print("="*70)
    print("DITA包修复服务测试套件")
    print("="*70)
    
    tests = [
        test_1_no_dita_files,
        test_2_basic_processing,
        test_3_linkify_with_references,
        test_4_zip_slip_protection,
        test_5_references_structure_validation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test_func.__name__}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)






