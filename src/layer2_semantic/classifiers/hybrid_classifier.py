"""
混合分类器
整合 Tier 1（规则）、Tier 2（LLM）、Tier 3（主动学习）
"""
from typing import Dict

from .rule_based_classifier import RuleBasedClassifier
from .llm_classifier import LLMClassifier
from .fusion_engine import FusionEngine

# 导入工具模块
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

logger = setup_logger('hybrid_classifier')

class HybridClassifier:
    """混合分类器 - 整合三层分类器"""
    
    def __init__(
        self,
        use_ai: bool = True,
        tier1_weight: float = 0.3,
        tier2_weight: float = 0.7,
        confidence_threshold: float = 0.6,
        tier1_high_confidence: float = 0.9
    ):
        """
        初始化混合分类器
        
        Args:
            use_ai: 是否使用AI（Tier 2）
            tier1_weight: Tier 1权重
            tier2_weight: Tier 2权重
            confidence_threshold: 融合后触发Tier 3的阈值
            tier1_high_confidence: Tier 1跳过Tier 2的阈值
        """
        logger.info("🎯 初始化混合分类器...")
        
        # Tier 1: 规则分类器
        self.rule_classifier = RuleBasedClassifier()
        
        # Tier 2: LLM分类器
        self.llm_classifier = LLMClassifier(use_ai=use_ai)
        
        # 融合引擎
        self.fusion_engine = FusionEngine(
            tier1_weight=tier1_weight,
            tier2_weight=tier2_weight,
            confidence_threshold=confidence_threshold
        )
        
        self.use_ai = use_ai
        self.tier1_high_confidence = tier1_high_confidence
        
        logger.info("✅ 混合分类器初始化完成")
    
    def classify(self, chunk: Dict, features: Dict) -> Dict:
        """
        三层分类流程
        
        流程：
        1. Tier 1: 规则分类
           - 如果置信度 >= 0.9，直接返回
        2. Tier 2: LLM分类
           - 调用Few-shot LLM
        3. 融合结果
           - 置信度加权平均
        4. Tier 3检查
           - 如果融合置信度 < 0.6，标记为需要人工审核
        
        Args:
            chunk: 文本块
            features: 提取的特征
            
        Returns:
            最终分类结果
        """
        # ==================== Tier 1: 规则分类 ====================
        tier1_result = self.rule_classifier.classify(chunk, features)
        
        # 如果Tier 1置信度非常高，直接返回（跳过LLM，节省成本）
        if tier1_result['confidence'] >= self.tier1_high_confidence:
            logger.info(
                f"  ✅ Tier 1高置信度 ({tier1_result['confidence']:.2f})，"
                f"跳过LLM: {tier1_result['type']}"
            )
            return tier1_result
        
        # ==================== Tier 2: LLM分类 ====================
        tier2_result = self.llm_classifier.classify(chunk, features)
        
        # ==================== 融合结果 ====================
        fused_result = self.fusion_engine.fuse(tier1_result, tier2_result)
        
        # ==================== Tier 3: 检查是否需要人工审核 ====================
        # 注意：mark_for_review 在 DocumentAnalyzer 中调用
        # 这里只返回融合结果，由上层决定是否触发Tier 3
        
        if fused_result['needs_review']:
            logger.warning(
                f"  ⚠️ 置信度过低 ({fused_result['confidence']:.2f})，"
                f"建议人工审核"
            )
        
        return fused_result