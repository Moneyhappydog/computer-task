"""
测试并行处理管道：Marker + 公式提取 + 表格提取 + AI合并
"""
from pathlib import Path
import sys

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.layer1_preprocessing.pdf_processor import PDFProcessor
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_parallel_pipeline():
    """
    测试完整的并行处理流程
    """
    logger.info("="*80)
    logger.info("🚀 测试并行PDF处理管道")
    logger.info("="*80)
    
    # 输入文件
    pdf_path = Path("data/input/2023CVPR-CoMFormer.pdf")
    
    if not pdf_path.exists():
        logger.error(f"测试文件不存在: {pdf_path}")
        return
    
    try:
        # 初始化处理器（启用所有功能）
        logger.info("\n📦 初始化PDF处理器...")
        processor = PDFProcessor(
            use_marker=True,       # 使用Marker提取基础MD
            use_ocr=True,          # 启用OCR备选
            extract_tables=True,   # 启用表格提取（Table Transformer + AI审核）
            tables_as_images=True, # 表格保存为图片
            extract_formulas=True, # 启用公式提取（GPT-4o）
            use_ai_merge=True      # 启用AI智能合并
        )
        
        # 处理PDF
        logger.info("\n🎬 开始处理PDF...")
        result = processor.process(pdf_path)
        
        # 打印结果
        logger.info("\n" + "="*80)
        logger.info("📊 处理结果统计")
        logger.info("="*80)
        
        if result['success']:
            metadata = result['metadata']
            logger.info(f"✅ 处理成功")
            logger.info(f"📄 文件: {metadata['file_name']}")
            logger.info(f"📝 提取方法: {metadata['method']}")
            logger.info(f"📖 总页数: {metadata['pages']}")
            logger.info(f"🖼️  图片数量: {metadata['image_count']}")
            logger.info(f"🧮 公式提取: {'是' if metadata.get('formula_extracted') else '否'}")
            logger.info(f"📊 审核通过的表格: {metadata.get('verified_tables', 0)}")
            logger.info(f"📂 图片目录: {metadata['image_dir']}")
            logger.info(f"📄 基础MD: {metadata.get('base_output_file')}")
            logger.info(f"✨ 最终MD: {metadata['output_file']}")
            
            # 显示文档长度
            md_length = len(result['markdown'])
            logger.info(f"📏 文档长度: {md_length} 字符")
            
            logger.info("\n" + "="*80)
            logger.info("🎉 测试完成！")
            logger.info("="*80)
            
            # 提示查看结果
            logger.info("\n💡 查看结果:")
            logger.info(f"   基础版本: {metadata.get('base_output_file')}")
            logger.info(f"   最终版本: {metadata['output_file']}")
            
            # 显示处理流程
            logger.info("\n📋 处理流程:")
            logger.info("   1️⃣  Marker提取基础MD ✅")
            logger.info("   2️⃣  并行提取 (公式 + 表格) ✅")
            logger.info("   3️⃣  AI智能合并 ✅")
            
        else:
            logger.error(f"❌ 处理失败: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parallel_pipeline()
