"""
测试 Layer 2 内容融合功能
将 Layer 1 的多模态输出（文本、公式、表格）融合为高质量 Markdown
"""
import sys
from pathlib import Path
from src.layer2_semantic.content_fusion import ContentFusionProcessor

def test_fusion(doc_name: str):
    print("="*70)
    print(f"🧪 测试 Layer 2 内容融合: {doc_name}")
    print("="*70)
    
    try:
        # 初始化处理器 (会自动读取环境变量中的 API Key)
        processor = ContentFusionProcessor()
        
        # 执行融合
        result = processor.fuse_document(doc_name)
        
        if result['success']:
            print(f"\n✅ 融合成功!")
            print(f"   处理页数: {result['pages_processed']}")
            print(f"   输出文件: {result['output_file']}")
            
            # 读取并显示前500字符
            output_path = Path(result['output_file'])
            content = output_path.read_text(encoding='utf-8')
            print(f"\n📄 融合内容预览 (前500字符):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
        else:
            print("❌ 融合失败")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 默认测试刚才处理的文档
    doc_name = "2023CVPR-CoMFormer"
    
    # 检查 Layer 1 输出是否存在
    layer1_md = Path(f"data/output/{doc_name}/layer1/{doc_name}.md")
    if not layer1_md.exists():
        print(f"⚠️  未找到 Layer 1 输出文件: {layer1_md}")
        print("   请先运行 test_layer1.py 生成数据")
        sys.exit(1)
        
    test_fusion(doc_name)
