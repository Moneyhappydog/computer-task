"""
测试Layer 4 - 多语言翻译功能
"""
from pathlib import Path
from src.utils.config import Config
from src.layer4_translation import (
    DITATranslator, 
    MultiLanguageConverter,
    translate_dita_to_multiple_languages
)

def test_translator_basic():
    """测试基础翻译功能"""
    print("\n" + "="*70)
    print("🧪 测试1: 基础文本翻译")
    print("="*70)
    
    # 创建翻译器（不使用AI，使用占位符）
    translator = DITATranslator(use_ai=False)
    
    # 测试文本
    test_texts = {
        'en': "Hello, World!",
        'zh-CN': "你好，世界！",
        'ja': "こんにちは、世界！",
        'ko': "안녕하세요, 세계!",
        'fr': "Bonjour le monde!",
    }
    
    print("\n📝 测试翻译到不同语言:")
    for lang, text in test_texts.items():
        translated = translator.translate_text(
            text="这是一段测试文本",
            target_lang=lang
        )
        print(f"  → {lang}: {translated}")
    
    print("\n✅ 基础翻译测试完成")
    return True

def test_dita_file_translation():
    """测试DITA文件翻译"""
    print("\n" + "="*70)
    print("🧪 测试2: DITA文件翻译")
    print("="*70)
    
    # 使用Layer 3生成的测试文件
    source_dir = Config.OUTPUT_DIR / "test_templates"
    
    if not source_dir.exists():
        print("⚠️  未找到测试文件，请先运行 test_layer3.py")
        return False
    
    # 创建翻译器
    translator = DITATranslator(use_ai=False)
    
    # 选择一个文件进行翻译
    source_file = source_dir / "task_example.dita"
    
    if not source_file.exists():
        print(f"⚠️  文件不存在: {source_file}")
        return False
    
    # 翻译为多种语言
    languages = ['en', 'ja', 'ko']
    output_dir = Config.OUTPUT_DIR / "test_translation"
    
    print(f"\n📄 源文件: {source_file.name}")
    print(f"🌍 目标语言: {', '.join(languages)}")
    
    for lang in languages:
        lang_dir = output_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = lang_dir / source_file.name
        
        success = translator.translate_dita_file(
            input_file=source_file,
            output_file=output_file,
            target_lang=lang
        )
        
        if success:
            print(f"  ✅ {lang}: {output_file}")
        else:
            print(f"  ❌ {lang}: 翻译失败")
    
    print(f"\n📁 翻译文件保存在: {output_dir}")
    print("✅ DITA文件翻译测试完成")
    
    return True

def test_batch_translation():
    """测试批量翻译"""
    print("\n" + "="*70)
    print("🧪 测试3: 批量多语言转换")
    print("="*70)
    
    # 使用Layer 3的完整转换输出
    source_dir = Config.OUTPUT_DIR / "test_full_conversion"
    
    if not source_dir.exists() or not list(source_dir.glob("*.dita*")):
        print("⚠️  未找到DITA文件，请先运行 test_layer3.py")
        return False
    
    # 统计源文件
    dita_files = list(source_dir.glob("*.dita"))
    map_files = list(source_dir.glob("*.ditamap"))
    
    print(f"\n📊 源文件统计:")
    print(f"  DITA主题: {len(dita_files)} 个")
    print(f"  DITA Map: {len(map_files)} 个")
    
    # 创建多语言转换器
    converter = MultiLanguageConverter(use_ai=False)
    
    # 目标语言
    target_languages = ['en', 'ja', 'zh-TW']
    
    print(f"\n🌍 目标语言: {', '.join(target_languages)}")
    
    # 执行转换
    output_dir = Config.OUTPUT_DIR / "multilingual"
    
    results = converter.convert_to_languages(
        source_dir=source_dir,
        output_base_dir=output_dir,
        target_languages=target_languages,
        source_lang='zh-CN'
    )
    
    # 显示结果
    print(f"\n📊 转换结果:")
    print(f"  处理语言数: {results['total_languages']}")
    
    for lang, stats in results['languages'].items():
        print(f"\n  {stats['name']} ({lang}):")
        print(f"    成功: {stats['success']} 个文件")
        print(f"    失败: {stats['failed']} 个文件")
        print(f"    输出: {stats['output_dir']}")
    
    print(f"\n📁 多语言文件保存在: {output_dir}")
    print("✅ 批量翻译测试完成")
    
    return True

def test_supported_languages():
    """测试支持的语言列表"""
    print("\n" + "="*70)
    print("🧪 测试4: 支持的语言列表")
    print("="*70)
    
    converter = MultiLanguageConverter(use_ai=False)
    languages = converter.get_supported_languages()
    
    print(f"\n🌍 当前支持 {len(languages)} 种语言:\n")
    
    for code, name in languages.items():
        print(f"  {code:8} → {name}")
    
    print("\n✅ 语言列表测试完成")
    return True

def test_with_ai():
    """测试AI翻译（可选）"""
    print("\n" + "="*70)
    print("🧪 测试5: AI翻译（真实翻译）")
    print("="*70)
    
    # 创建AI翻译器
    translator = DITATranslator(use_ai=True)
    
    # 测试文本
    test_text = "人工智能正在改变世界。"
    
    print(f"\n📝 原文: {test_text}")
    print("\n🌍 翻译结果:")
    
    for lang in ['en', 'ja', 'ko', 'fr']:
        translated = translator.translate_text(test_text, lang)
        lang_name = DITATranslator.SUPPORTED_LANGUAGES[lang]
        print(f"  {lang_name:12} → {translated}")
    
    print("\n✅ AI翻译测试完成")
    return True

def show_output_structure():
    """显示输出目录结构"""
    print("\n" + "="*70)
    print("📂 输出目录结构")
    print("="*70)
    
    multilingual_dir = Config.OUTPUT_DIR / "multilingual"
    
    if not multilingual_dir.exists():
        print("⚠️  多语言目录不存在")
        return
    
    print(f"\n{multilingual_dir}/")
    for lang_dir in sorted(multilingual_dir.iterdir()):
        if lang_dir.is_dir():
            file_count = len(list(lang_dir.glob("*.dita*")))
            print(f"├── {lang_dir.name}/ ({file_count} 个文件)")
            
            # 显示前3个文件
            for i, file in enumerate(sorted(lang_dir.glob("*.dita*"))[:3]):
                prefix = "│   ├──" if i < 2 else "│   └──"
                print(f"{prefix} {file.name}")
            
            if file_count > 3:
                print(f"│   └── ... 还有 {file_count - 3} 个文件")

if __name__ == "__main__":
    print("🧪 开始测试 Layer 4 - 多语言翻译...\n")
    
    # 测试1: 基础翻译
    test_translator_basic()
    
    # 测试2: DITA文件翻译
    test_dita_file_translation()
    
    # 测试3: 批量翻译
    test_batch_translation()
    
    # 测试4: 支持的语言
    test_supported_languages()
    
    # 测试5: AI翻译（可选）
    print("\n" + "="*70)
    print("⚠️  准备测试AI翻译，这将消耗API额度")
    print("="*70)
    
    user_input = input("是否测试AI翻译？(y/n): ").strip().lower()
    
    if user_input == 'y':
        test_with_ai()
    else:
        print("⏭️  跳过AI翻译测试")
    
    # 显示输出结构
    show_output_structure()
    
    print("\n" + "="*70)
    print("✅ Layer 4 测试完成！")
    print("="*70)
    
    print("\n📊 查看翻译结果:")
    print(f"  {Config.OUTPUT_DIR / 'multilingual'}")