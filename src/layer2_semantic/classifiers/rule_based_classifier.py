"""
规则分类器 - Tier 1
使用硬编码规则进行快速分类，处理80%的明显案例
"""
from typing import Dict

# 导入工具模块
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

logger = setup_logger('rule_classifier')

class RuleBasedClassifier:
    """基于规则的分类器 - Tier 1"""
    
    def classify(self, chunk: Dict, features: Dict) -> Dict:
        """
        使用规则进行分类
        
        规则优先级：
        1. 强特征规则（置信度 0.9+）
        2. 组合特征规则（置信度 0.7-0.9）
        3. 弱特征规则（置信度 0.5-0.7）
        
        Args:
            chunk: 文本块
            features: 提取的特征
            
        Returns:
            分类结果:
            {
                "type": "Task|Concept|Reference",
                "confidence": 0.0-1.0,
                "scores": {"Task": 0.x, "Concept": 0.y, "Reference": 0.z},
                "matched_rules": ["rule_name1", "rule_name2"]
            }
        """
        scores = {"Task": 0.0, "Concept": 0.0, "Reference": 0.0}
        matched_rules = []
        
        # ==================== Task规则 ====================
        
        # 强规则1: 编号列表 + 高密度祈使动词
        if features.get('has_numbered_list') and features.get('imperative_verbs', 0) >= 5:
            scores["Task"] += 0.5
            matched_rules.append("strong_task_numbered_imperatives")
        
        # 强规则2: 编号列表 + 动作动词
        if features.get('has_numbered_list') and features.get('action_verbs', 0) >= 5:
            scores["Task"] += 0.4
            matched_rules.append("numbered_list_with_actions")
        
        # 中等规则3: 项目符号列表 + 动作动词
        if features.get('has_bullet_list') and features.get('action_verbs', 0) >= 4:
            scores["Task"] += 0.3
            matched_rules.append("bullet_list_with_actions")
        
        # 中等规则4: 高密度祈使动词（无列表）
        if features.get('imperative_verbs', 0) >= 3:
            scores["Task"] += 0.25
            matched_rules.append("high_imperative_verbs")
        
        # 弱规则5: 标题包含Task关键词
        task_keywords = ['install', 'configure', 'setup', 'create', 'how to', 'guide', 
                         'step', 'tutorial', 'walkthrough', 'procedure']
        title_lower = chunk['title'].lower()
        if any(kw in title_lower for kw in task_keywords):
            scores["Task"] += 0.2
            matched_rules.append("task_title_keyword")
        
        # 弱规则6: 动作动词密度高
        if features.get('action_verbs', 0) >= 7:
            scores["Task"] += 0.15
            matched_rules.append("high_action_verb_density")
        
        # ==================== Reference规则 ====================
        
        # 强规则7: 多个表格
        if features.get('table_count', 0) >= 2:
            scores["Reference"] += 0.5
            matched_rules.append("strong_reference_multiple_tables")
        
        # 强规则8: 单个表格 + 少文本
        if features.get('has_table') and features.get('word_count', 0) < 200:
            scores["Reference"] += 0.4
            matched_rules.append("table_low_text")
        
        # 中等规则9: 标题包含Reference关键词
        ref_keywords = ['api', 'parameter', 'specification', 'reference', 'command', 
                        'syntax', 'function', 'method', 'class', 'attribute', 'property']
        if any(kw in title_lower for kw in ref_keywords):
            scores["Reference"] += 0.35
            matched_rules.append("reference_title_keyword")
        
        # 中等规则10: 大量代码块 + 少文本
        if features.get('code_blocks', 0) >= 3 and features.get('word_count', 0) < 300:
            scores["Reference"] += 0.3
            matched_rules.append("code_heavy_low_text")
        
        # 弱规则11: 有表格
        if features.get('has_table'):
            scores["Reference"] += 0.2
            matched_rules.append("has_table")
        
        # 弱规则12: 高密度命名实体
        if features.get('named_entities', 0) >= 5:
            scores["Reference"] += 0.15
            matched_rules.append("high_named_entities")
        
        # ==================== Concept规则 ====================
        
        # 强规则13: 定义模式 + 高"is"陈述
        if features.get('has_definition') and features.get('is_statements', 0) >= 4:
            scores["Concept"] += 0.5
            matched_rules.append("strong_concept_definition_statements")
        
        # 中等规则14: 有定义模式
        if features.get('has_definition'):
            scores["Concept"] += 0.35
            matched_rules.append("has_definition_pattern")
        
        # 中等规则15: 高密度"is"陈述句
        if features.get('is_statements', 0) >= 3:
            scores["Concept"] += 0.3
            matched_rules.append("high_is_statements")
        
        # 中等规则16: 标题包含Concept关键词
        concept_keywords = ['what is', 'overview', 'introduction', 'understanding', 
                            'concept', 'about', 'explanation', 'theory', 'background']
        if any(kw in title_lower for kw in concept_keywords):
            scores["Concept"] += 0.3
            matched_rules.append("concept_title_keyword")
        
        # 弱规则17: 描述性语言（少动作动词，多名词）
        if (features.get('action_verbs', 0) < 2 and 
            features.get('noun_count', 0) > features.get('verb_count', 1)):
            scores["Concept"] += 0.25
            matched_rules.append("descriptive_language")
        
        # 弱规则18: 高命名实体（3-5个，适中）
        if 3 <= features.get('named_entities', 0) <= 5:
            scores["Concept"] += 0.15
            matched_rules.append("moderate_named_entities")
        
        # 弱规则19: 无列表，无表格（纯文本）
        if (not features.get('has_numbered_list') and 
            not features.get('has_bullet_list') and 
            not features.get('has_table')):
            scores["Concept"] += 0.1
            matched_rules.append("pure_text_no_structure")
        
        # ==================== 决策逻辑 ====================
        
        # 归一化分数
        total_score = sum(scores.values())
        if total_score > 0:
            scores = {k: v / total_score for k, v in scores.items()}
        else:
            # 默认Concept（最保守的选择）
            scores = {"Task": 0.0, "Concept": 1.0, "Reference": 0.0}
            matched_rules.append("default_concept")
        
        # 选择最高分类型
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        logger.info(
            f"  📏 规则分类: {best_type} "
            f"(置信度: {confidence:.2f}, "
            f"匹配规则: {len(matched_rules)})"
        )
        
        return {
            "type": best_type,
            "confidence": confidence,
            "scores": scores,
            "matched_rules": matched_rules
        }