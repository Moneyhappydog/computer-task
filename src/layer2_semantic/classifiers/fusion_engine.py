"""
结果融合引擎
实现置信度加权平均融合 Tier 1 和 Tier 2 的分类结果
"""
from typing import Dict, List

# 导入工具模块
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

logger = setup_logger('fusion_engine')

class FusionEngine:
    """多分类器结果融合引擎"""
    
    def __init__(
        self,
        tier1_weight: float = 0.3,
        tier2_weight: float = 0.7,
        confidence_threshold: float = 0.6
    ):
        """
        初始化融合引擎
        
        Args:
            tier1_weight: Tier 1（规则）权重
            tier2_weight: Tier 2（LLM）权重
            confidence_threshold: 置信度阈值（低于此值触发Tier 3人工审核）
        """
        self.weights = {
            "tier1": tier1_weight,
            "tier2": tier2_weight
        }
        self.confidence_threshold = confidence_threshold
        
        # 验证权重和为1
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"权重和必须为1，当前为 {total_weight}")
        
        logger.info(
            f"🔀 融合引擎初始化: "
            f"Tier1={tier1_weight:.1f}, "
            f"Tier2={tier2_weight:.1f}, "
            f"阈值={confidence_threshold:.1f}"
        )
    
    def fuse(self, tier1_result: Dict, tier2_result: Dict) -> Dict:
        """
        融合两个分类器的结果
        
        使用置信度加权平均：
        final_score(type) = score1(type) * w1 + score2(type) * w2
        
        Args:
            tier1_result: Tier 1结果
            tier2_result: Tier 2结果
            
        Returns:
            融合后的结果:
            {
                "type": "Task|Concept|Reference",
                "confidence": 0.0-1.0,
                "scores": {"Task": 0.x, "Concept": 0.y, "Reference": 0.z},
                "reasoning": "Fusion explanation",
                "needs_review": True/False,
                "components": {
                    "tier1": {...},
                    "tier2": {...}
                }
            }
        """
        # 加权平均分数
        fused_scores = {}
        content_types = ['Task', 'Concept', 'Reference']
        
        for ctype in content_types:
            score1 = tier1_result['scores'].get(ctype, 0.0)
            score2 = tier2_result['scores'].get(ctype, 0.0)
            
            fused_score = (
                score1 * self.weights['tier1'] +
                score2 * self.weights['tier2']
            )
            fused_scores[ctype] = fused_score
        
        # 归一化（确保总和为1）
        total = sum(fused_scores.values())
        if total > 0:
            fused_scores = {k: v / total for k, v in fused_scores.items()}
        
        # 选择最高分
        best_type = max(fused_scores, key=fused_scores.get)
        final_confidence = fused_scores[best_type]
        
        # 生成推理说明
        reasoning = self._generate_reasoning(
            best_type,
            tier1_result,
            tier2_result,
            fused_scores,
            final_confidence
        )
        
        # 判断是否需要人工审核
        needs_review = final_confidence < self.confidence_threshold
        
        return {
            "type": best_type,
            "confidence": final_confidence,
            "scores": fused_scores,
            "reasoning": reasoning,
            "needs_review": needs_review,
            "components": {
                "tier1": {
                    "type": tier1_result['type'],
                    "confidence": tier1_result['confidence'],
                    "matched_rules": tier1_result.get('matched_rules', [])
                },
                "tier2": {
                    "type": tier2_result['type'],
                    "confidence": tier2_result['confidence'],
                    "reasoning": tier2_result.get('reasoning', '')
                }
            }
        }
    
    def _generate_reasoning(
        self,
        final_type: str,
        tier1: Dict,
        tier2: Dict,
        fused_scores: Dict,
        final_confidence: float
    ) -> str:
        """生成融合推理说明"""
        
        tier1_type = tier1['type']
        tier2_type = tier2['type']
        tier1_conf = tier1['confidence']
        tier2_conf = tier2['confidence']
        
        # 情况1: 两层分类器完全一致
        if tier1_type == tier2_type == final_type:
            return (
                f"Strong agreement: Both classifiers predict {final_type} "
                f"(Rules: {tier1_conf:.2f}, LLM: {tier2_conf:.2f})"
            )
        
        # 情况2: 规则分类器主导
        elif tier1_type == final_type and tier1_conf > 0.8:
            return (
                f"Rule-based classifier dominates: {final_type} with high confidence "
                f"({tier1_conf:.2f}), LLM suggested {tier2_type} ({tier2_conf:.2f})"
            )
        
        # 情况3: LLM分类器主导
        elif tier2_type == final_type and tier2_conf > 0.8:
            return (
                f"LLM classifier dominates: {final_type} with high confidence "
                f"({tier2_conf:.2f}), Rules suggested {tier1_type} ({tier1_conf:.2f})"
            )
        
        # 情况4: 融合解决冲突
        elif tier1_type != tier2_type:
            return (
                f"Fusion resolved conflict: Rules={tier1_type}({tier1_conf:.2f}), "
                f"LLM={tier2_type}({tier2_conf:.2f}), Final={final_type}({final_confidence:.2f})"
            )
        
        # 情况5: 其他情况
        else:
            return (
                f"Weighted fusion result: {final_type} "
                f"(confidence: {final_confidence:.2f})"
            )