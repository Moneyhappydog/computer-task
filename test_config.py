"""
测试配置和环境
"""
from src.utils.config import Config

def test_config():
    """测试配置加载"""
    print("\n" + "="*70)
    print("🧪 测试配置加载")
    print("="*70)
    
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过！")
        
        # 显示配置
        Config.show()
        
        return True
        
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        return False

if __name__ == "__main__":
    success = test_config()
    
    if success:
        print("\n✅ 环境配置正常，可以继续下一步！")
    else:
        print("\n❌ 请先修复配置问题")