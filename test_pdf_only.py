#!/usr/bin/env python3
"""
测试PDF处理器
"""
from pathlib import Path
import sys
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.layer1_preprocessing.file_router import FileRouter

def test_pdf_processing():
    """测试PDF处理"""
    print("=== 测试PDF处理器 ===")
    
    # 测试文件
    input_file = project_root / "data" / "input" / "test.pdf"
    
    if not input_file.exists():
        print(f"❌ 测试文件不存在: {input_file}")
        return False
    
    try:
        # 创建文件路由器
        file_router = FileRouter()
        
        # 处理文件
        print(f"📄 处理文件: {input_file}")
        result = file_router.process_file(input_file)
        
        # 显示结果
        print(f"✅ 处理成功: {result.get('success', False)}")
        
        if result.get('success'):
            markdown = result.get('markdown', '')
            pages = result.get('pages', [])
            metadata = result.get('metadata', {})
            
            print(f"📊 统计信息:")
            print(f"   - 文本长度: {len(markdown)} 字符")
            print(f"   - 页数: {len(pages)}")
            print(f"   - 处理方法: {metadata.get('method', 'unknown')}")
            
            # 显示前200字符
            if markdown:
                print(f"📝 前200字符:")
                print(f"   {repr(markdown[:200])}")
            else:
                print("❌ 没有提取到文本内容")
            
            # 显示第一页信息
            if pages:
                first_page = pages[0]
                page_text = first_page.get('text', '')
                print(f"📄 第一页:")
                print(f"   - 文本长度: {len(page_text)} 字符")
                if page_text:
                    print(f"   - 前100字符: {repr(page_text[:100])}")
                print(f"   - 图片数量: {len(first_page.get('images', []))}")
            
            return True
        else:
            print(f"❌ 处理失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pdf_processing()