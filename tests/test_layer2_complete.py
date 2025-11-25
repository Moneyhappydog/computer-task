"""
Layer 2 完整测试
测试语义理解层的所有组件
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.layer2_semantic import DocumentAnalyzer, NLPFeatureExtractor, ActiveLearningManager

def test_nlp_features():
    """测试NLP特征提取器"""
    print("\n" + "="*70)
    print("测试 1: NLP特征提取器")
    print("="*70)
    
    extractor = NLPFeatureExtractor()
    
    # Task示例
    task_text = """
    Installing Python on Windows:
    1. Download the installer from python.org
    2. Run the installer
    3. Check "Add to PATH"
    4. Click Install
    5. Verify installation
    """
    
    features = extractor.extract_all_features(task_text)
    
    print("\n📊 Task文本特征:")
    print(f"  - 祈使动词: {features['imperative_verbs']}")
    print(f"  - 动作动词: {features['action_verbs']}")
    print(f"  - 词数: {features['word_count']}")
    print(f"  - 句子数: {features['sentence_count']}")
    
    # Concept示例
    concept_text = """
    Python is a high-level programming language. 
    It is designed for readability and simplicity.
    Python supports multiple programming paradigms.
    """
    
    features = extractor.extract_all_features(concept_text)
    
    print("\n📊 Concept文本特征:")
    print(f"  - 定义模式: {features['has_definition']}")
    print(f"  - 'is'陈述: {features['is_statements']}")
    print(f"  - 祈使动词: {features['imperative_verbs']}")
    
    print("\n✅ NLP特征提取器测试通过")


def test_rule_classifier():
    """测试规则分类器"""
    print("\n" + "="*70)
    print("测试 2: 规则分类器")
    print("="*70)
    
    from src.layer2_semantic.classifiers import RuleBasedClassifier
    from src.layer2_semantic.nlp_features import extract_structural_features
    
    classifier = RuleBasedClassifier()
    extractor = NLPFeatureExtractor()
    
    # Task示例
    task_chunk = {
        "id": "test_1",
        "title": "Installing Python",
        "content": """
1. Download Python from python.org
2. Run the installer
3. Select "Add to PATH"
4. Click Install
5. Verify by running python --version
        """
    }
    
    nlp_features = extractor.extract_all_features(task_chunk['content'])
    struct_features = extract_structural_features(task_chunk['content'])
    features = {**nlp_features, **struct_features, "title": task_chunk["title"]}
    
    result = classifier.classify(task_chunk, features)
    
    print(f"\n📋 Task示例分类结果:")
    print(f"  - 类型: {result['type']}")
    print(f"  - 置信度: {result['confidence']:.2f}")
    print(f"  - 分数: Task={result['scores']['Task']:.2f}, "
          f"Concept={result['scores']['Concept']:.2f}, "
          f"Reference={result['scores']['Reference']:.2f}")
    print(f"  - 匹配规则: {len(result['matched_rules'])} 条")
    
    assert result['type'] == 'Task', "Task分类失败"
    assert result['confidence'] > 0.5, "置信度过低"
    
    print("\n✅ 规则分类器测试通过")


def test_document_analyzer():
    """测试文档分析器"""
    print("\n" + "="*70)
    print("测试 3: 文档分析器（完整流程）")
    print("="*70)
    
    analyzer = DocumentAnalyzer(use_ai=False)  # 暂时不使用AI
    
    markdown_content = """
# Python编程入门

## 什么是Python

Python is a high-level programming language created by Guido van Rossum.
It is designed for code readability and simplicity.
Python supports multiple programming paradigms including object-oriented and functional programming.

## 安装Python

Follow these steps to install Python:

1. Visit the official Python website at python.org
2. Download the latest version for your operating system
3. Run the installer
4. Make sure to check "Add Python to PATH"
5. Click Install and wait for completion
6. Verify installation by opening terminal and typing: python --version

## Python语法参考

| Syntax | Description | Example |
|--------|-------------|---------|
| print() | Output text | print("Hello") |
| if/else | Conditional | if x > 0: ... |
| for | Loop | for i in range(10): ... |
| def | Function | def my_func(): ... |
    """
    
    results = analyzer.analyze(markdown_content)
    
    print(f"\n📊 分析结果:")
    print(f"  - 总块数: {results['statistics']['total_chunks']}")
    print(f"  - 类型分布: {results['statistics']['type_distribution']}")
    print(f"  - 平均置信度: {results['statistics']['overall_avg_confidence']:.2f}")
    
    print(f"\n📦 分块详情:")
    for i, chunk in enumerate(results['chunks'], 1):
        print(f"  {i}. {chunk['title']}")
        print(f"     类型: {chunk['classification']['type']} "
              f"(置信度: {chunk['classification']['confidence']:.2f})")
    
    # 验证分类结果
    types = [c['classification']['type'] for c in results['chunks']]
    assert 'Concept' in types, "应该识别出Concept类型"
    assert 'Task' in types, "应该识别出Task类型"
    
    print("\n✅ 文档分析器测试通过")


def test_active_learning():
    """测试主动学习管理器"""
    print("\n" + "="*70)
    print("测试 4: 主动学习管理器")
    print("="*70)
    
    al_manager = ActiveLearningManager()
    
    # 模拟低置信度案例
    chunk = {
        "id": "test_uncertain",
        "title": "Test Content",
        "content": "This is a test content that is uncertain..."
    }
    
    tier1 = {
        "type": "Task",
        "confidence": 0.55,
        "matched_rules": ["rule1"]
    }
    
    tier2 = {
        "type": "Concept",
        "confidence": 0.58,
        "reasoning": "Uncertain classification"
    }
    
    # 标记为需要审核
    result = al_manager.mark_for_review(chunk, tier1, tier2)
    
    print(f"\n📝 审核请求:")
    print(f"  - 类型: {result['type']}")
    print(f"  - 审核ID: {result.get('review_id', 'N/A')}")
    
    # 获取待审核数量
    pending_count = al_manager.get_pending_count()
    print(f"  - 待审核数量: {pending_count}")
    
    # 模拟人工标注
    if pending_count > 0:
        al_manager.submit_human_label("test_uncertain", "Task")
        print(f"  - 人工标注已提交: Task")
    
    # 获取统计信息
    stats = al_manager.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"  - 总数: {stats['total_items']}")
    print(f"  - 待审核: {stats['pending']}")
    print(f"  - 已审核: {stats['reviewed']}")
    print(f"  - 训练集大小: {stats['training_set_size']}")
    
    print("\n✅ 主动学习管理器测试通过")


def test_fusion_engine():
    """测试融合引擎"""
    print("\n" + "="*70)
    print("测试 5: 融合引擎")
    print("="*70)
    
    from src.layer2_semantic.classifiers import FusionEngine
    
    engine = FusionEngine(
        tier1_weight=0.3,
        tier2_weight=0.7,
        confidence_threshold=0.6
    )
    
    # 模拟两层分类器结果
    tier1_result = {
        "type": "Task",
        "confidence": 0.75,
        "scores": {"Task": 0.75, "Concept": 0.15, "Reference": 0.10},
        "matched_rules": ["rule1", "rule2"]
    }
    
    tier2_result = {
        "type": "Task",
        "confidence": 0.85,
        "scores": {"Task": 0.85, "Concept": 0.10, "Reference": 0.05},
        "reasoning": "Clear task structure"
    }
    
    # 融合
    fused = engine.fuse(tier1_result, tier2_result)
    
    print(f"\n🔀 融合结果:")
    print(f"  - 类型: {fused['type']}")
    print(f"  - 置信度: {fused['confidence']:.2f}")
    print(f"  - 需要审核: {fused['needs_review']}")
    print(f"  - 推理: {fused['reasoning']}")
    print(f"  - 分数: Task={fused['scores']['Task']:.2f}, "
          f"Concept={fused['scores']['Concept']:.2f}, "
          f"Reference={fused['scores']['Reference']:.2f}")
    
    assert fused['type'] == 'Task', "融合结果应为Task"
    assert fused['confidence'] > tier1_result['confidence'], "融合应提高置信度"
    
    print("\n✅ 融合引擎测试通过")


def main():
    """运行所有测试"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║          Layer 2 Semantic Understanding - 完整测试         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    try:
        test_nlp_features()
        test_rule_classifier()
        test_fusion_engine()
        test_active_learning()
        test_document_analyzer()
        
        print("\n" + "="*70)
        print("🎉 所有测试通过！Layer 2 功能正常！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)