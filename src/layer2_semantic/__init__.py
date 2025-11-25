"""
Layer 2: 语义理解层 (Semantic Understanding Layer)

功能：
- Step 1: 文本分块（按H2/H3标题）
- Step 2: 特征提取（spaCy NLP完整分析）
- Step 3: 三层分类器
  - Tier 1: 规则引擎（快速分类80%案例）
  - Tier 2: Few-shot LLM（处理边界案例）
  - Tier 3: 主动学习（人工审核）
- Step 4: 结果融合（置信度加权平均）

输出：
{
    "chunks": [
        {
            "id": "chunk_1",
            "title": "Installing Python",
            "content": "...",
            "features": {...},
            "classification": {
                "type": "Task",
                "confidence": 0.95,
                "scores": {"Task": 0.95, "Concept": 0.03, "Reference": 0.02}
            }
        }
    ]
}
"""

from .document_analyzer import DocumentAnalyzer
from .nlp_features import NLPFeatureExtractor
from .active_learning import ActiveLearningManager

__all__ = [
    'DocumentAnalyzer',
    'NLPFeatureExtractor',
    'ActiveLearningManager'
]

__version__ = '1.0.0'