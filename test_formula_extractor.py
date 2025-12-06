"""
测试公式提取器
使用 2023CVPR-CoMFormer.pdf 进行测试
"""
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.layer1_preprocessing.formula_extractor import FormulaExtractor

def test_formula_extraction():
    """测试公式提取功能"""
    
    # 设置日志
    setup_logger("test_formula_extractor")
    
    print("=" * 80)
    print("📊 公式提取器测试")
    print("=" * 80)
    
    # 测试文件路径
    pdf_path = Path("data/input/2023CVPR-CoMFormer.pdf")
    doc_name = "2023CVPR-CoMFormer"
    
    # 检查文件是否存在
    if not pdf_path.exists():
        print(f"\n❌ 错误: PDF 文件不存在: {pdf_path}")
        print(f"   请确保文件路径正确")
        return False
    
    print(f"\n📄 测试文件: {pdf_path}")
    print(f"📁 输出目录: data/output/{doc_name}/formulas/")
    print(f"\n{'=' * 80}")
    
    try:
        # 创建提取器（启用 OCR）
        print("\n🔧 初始化公式提取器...")
        extractor = FormulaExtractor(use_ocr=True)
        
        # 提取公式
        print("\n🔍 开始提取公式...")
        print("   - 检测独立公式图片")
        print("   - 检测内联公式（数学符号、字体分析）")
        print("   - OCR 转换为 LaTeX")
        print()
        
        result = extractor.extract_formulas_from_pdf(
            pdf_path,
            doc_name=doc_name,
            min_formula_height=10,  # 降低最小高度，捕获更多公式
            min_formula_width=20    # 降低最小宽度
        )
        
        # 显示结果
        print(f"\n{'=' * 80}")
        print("✅ 提取完成！")
        print(f"{'=' * 80}")
        
        print(f"\n📊 统计信息:")
        print(f"   公式目录: {result['formula_dir']}")
        print(f"   总公式数: {result['total_formulas']}")
        print(f"   成功保存: {result['saved_formulas']}")
        print(f"   OCR 成功: {result['ocr_success']}")
        print(f"   OCR 失败: {result['ocr_failed']}")
        
        # 保存 LaTeX 代码到 JSON
        if result['formula_latex']:
            print(f"\n💾 保存 LaTeX 代码...")
            latex_file = extractor.save_latex_to_json(
                result['formula_latex'],
                doc_name
            )
            print(f"   文件路径: {latex_file}")
        
        # 详细统计
        stats = extractor.get_formula_statistics(result['formula_mapping'])
        print(f"\n📈 详细统计:")
        print(f"   总公式数: {stats['total_formulas']}")
        print(f"   包含公式的页数: {stats['pages_with_formulas']}")
        
        if stats['page_distribution']:
            print(f"\n📄 页码分布:")
            for page, count in sorted(stats['page_distribution'].items()):
                print(f"   {page}: {count} 个公式")
        
        # 显示部分 LaTeX 示例
        if result['formula_latex']:
            print(f"\n📝 LaTeX 示例（前 5 个）:")
            for i, (name, latex) in enumerate(list(result['formula_latex'].items())[:5]):
                print(f"\n   [{i+1}] {name}:")
                # 截断过长的 LaTeX
                if len(latex) > 80:
                    print(f"      {latex[:77]}...")
                else:
                    print(f"      {latex}")
        
        # 显示公式映射示例
        if result['formula_mapping']:
            print(f"\n🗺️  公式路径映射（前 3 个）:")
            for i, (name, path) in enumerate(list(result['formula_mapping'].items())[:3]):
                print(f"   {name} -> {path}")
        
        print(f"\n{'=' * 80}")
        print("✨ 测试完成！")
        print(f"{'=' * 80}")
        
        # 提示查看结果
        print(f"\n💡 提示:")
        print(f"   1. 查看提取的公式图片: {result['formula_dir']}")
        print(f"   2. 查看 LaTeX 代码: {result['formula_dir']}/formulas_latex.json")
        print(f"   3. 检查日志文件了解详细信息")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_formula_extraction_no_ocr():
    """测试公式提取功能（不使用 OCR）"""
    
    # 设置日志
    setup_logger("test_formula_extractor_no_ocr")
    
    print("\n" + "=" * 80)
    print("📊 公式提取器测试（不使用 OCR）")
    print("=" * 80)
    
    # 测试文件路径
    pdf_path = Path("data/input/2023CVPR-CoMFormer.pdf")
    doc_name = "2023CVPR-CoMFormer_no_ocr"
    
    if not pdf_path.exists():
        print(f"\n❌ 错误: PDF 文件不存在: {pdf_path}")
        return False
    
    print(f"\n📄 测试文件: {pdf_path}")
    
    try:
        # 创建提取器（不启用 OCR）
        print("\n🔧 初始化公式提取器（不使用 OCR）...")
        extractor = FormulaExtractor(use_ocr=False)
        
        # 提取公式
        print("\n🔍 开始提取公式...")
        result = extractor.extract_formulas_from_pdf(
            pdf_path,
            doc_name=doc_name,
            min_formula_height=10,
            min_formula_width=20
        )
        
        print(f"\n✅ 提取完成！")
        print(f"   总公式数: {result['total_formulas']}")
        print(f"   成功保存: {result['saved_formulas']}")
        print(f"   公式目录: {result['formula_dir']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("开始测试公式提取器")
    print("🚀" * 40 + "\n")
    
    # 测试 1: 带 OCR
    success1 = test_formula_extraction()
    
    # 测试 2: 不带 OCR（可选，如果 pix2tex 安装失败）
    # success2 = test_formula_extraction_no_ocr()
    
    print("\n" + "🎉" * 40)
    if success1:
        print("所有测试通过！")
    else:
        print("部分测试失败，请检查错误信息")
    print("🎉" * 40 + "\n")
