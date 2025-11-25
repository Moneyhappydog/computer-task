"""
文档分析器 - Layer 2核心模块
整合NLP特征提取和三层分类器，实现完整的语义理解流程
"""
from pathlib import Path
from typing import Dict, List
import json
import re

from .nlp_features import NLPFeatureExtractor, extract_structural_features
from .classifiers.hybrid_classifier import HybridClassifier
from .active_learning import ActiveLearningManager

# 导入工具模块
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

logger = setup_logger('document_analyzer')

class DocumentAnalyzer:
    """
    文档语义分析器 - Layer 2核心
    
    流程：
    1. 文本分块（按H2/H3标题）
    2. 特征提取（NLP + 结构化特征）
    3. 三层分类（规则 → LLM → 人工审核）
    4. 结果融合（置信度加权）
    """
    
    def __init__(self, use_ai: bool = True, chunk_size: int = 500):
        """
        初始化文档分析器
        
        Args:
            use_ai: 是否使用AI分类器
            chunk_size: 分块大小（字符数，用于备用分块策略）
        """
        logger.info("🧠 初始化文档分析器...")
        
        self.chunk_size = chunk_size
        self.use_ai = use_ai
        
        # 初始化NLP特征提取器
        self.nlp_extractor = NLPFeatureExtractor()
        
        # 初始化混合分类器
        self.classifier = HybridClassifier(use_ai=use_ai)
        
        # 初始化主动学习管理器
        self.active_learning = ActiveLearningManager()
        
        logger.info("✅ 文档分析器初始化完成")
    
    def analyze(self, markdown_content: str, metadata: Dict = None) -> Dict:
        """
        分析Markdown文档
        
        Args:
            markdown_content: Markdown内容
            metadata: Layer 1的元数据（可选）
            
        Returns:
            分析结果:
            {
                "metadata": {...},
                "chunks": [
                    {
                        "id": "chunk_1",
                        "title": "Installing Python",
                        "level": 2,
                        "content": "...",
                        "features": {...},
                        "classification": {
                            "type": "Task",
                            "confidence": 0.95,
                            "scores": {...}
                        }
                    }
                ],
                "statistics": {...}
            }
        """
        logger.info("=" * 70)
        logger.info("📊 开始语义分析...")
        logger.info("=" * 70)
        
        # Step 1: 文本分块
        logger.info("\n[Step 1/3] 文本分块...")
        chunks = self._chunk_by_headings(markdown_content)
        logger.info(f"  ✓ 分块完成：{len(chunks)} 个语义块")
        
        # Step 2 & 3: 特征提取 + 分类
        logger.info("\n[Step 2/3] 特征提取 + 分类...")
        analyzed_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"\n  [{i}/{len(chunks)}] 处理: {chunk['title'][:50]}...")
            
            # 提取特征
            features = self._extract_features(chunk)
            logger.info(f"    ✓ 特征提取完成")
            
            # 分类
            classification = self.classifier.classify(chunk, features)
            logger.info(
                f"    ✓ 分类: {classification['type']} "
                f"(置信度: {classification['confidence']:.2f})"
            )
            
            analyzed_chunks.append({
                **chunk,
                "features": features,
                "classification": classification
            })
        
        # Step 4: 计算统计信息
        logger.info("\n[Step 3/3] 计算统计信息...")
        statistics = self._compute_statistics(analyzed_chunks)
        
        logger.info("=" * 70)
        logger.info("✅ 语义分析完成！")
        logger.info(f"  总块数: {statistics['total_chunks']}")
        logger.info(f"  类型分布: {statistics['type_distribution']}")
        logger.info(f"  平均置信度: {statistics['overall_avg_confidence']:.2f}")
        logger.info("=" * 70)
        
        return {
            "metadata": metadata or {},
            "chunks": analyzed_chunks,
            "statistics": statistics
        }
    
    def _chunk_by_headings(self, content: str) -> List[Dict]:
        """
        按标题分块
        
        规则：
        - H2 (##) 和 H3 (###) 作为分块边界
        - 每个标题及其下属内容作为一个语义块
        
        Args:
            content: Markdown内容
            
        Returns:
            分块列表
        """
        # 按H2和H3标题分割
        pattern = r'^(#{2,3})\s+(.+)$'
        lines = content.split('\n')
        
        chunks = []
        current_chunk = None
        
        for line in lines:
            match = re.match(pattern, line)
            
            if match:
                # 保存上一个块
                if current_chunk and current_chunk["content"].strip():
                    chunks.append(current_chunk)
                
                # 开始新块
                level = len(match.group(1))
                title = match.group(2).strip()
                current_chunk = {
                    "id": f"chunk_{len(chunks) + 1}",
                    "title": title,
                    "level": level,
                    "content": ""
                }
            elif current_chunk is not None:
                current_chunk["content"] += line + "\n"
        
        # 添加最后一个块
        if current_chunk and current_chunk["content"].strip():
            chunks.append(current_chunk)
        
        # 如果没有找到标题，尝试按字符数分块
        if not chunks and content.strip():
            logger.warning("  ⚠️ 未找到H2/H3标题，使用字符数分块")
            chunks = self._chunk_by_size(content)
        
        return chunks
    
    def _chunk_by_size(self, content: str) -> List[Dict]:
        """按字符数分块（备用策略）"""
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        chunk_id = 1
        
        for line in lines:
            if len(current_chunk) + len(line) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append({
                        "id": f"chunk_{chunk_id}",
                        "title": f"Section {chunk_id}",
                        "level": 2,
                        "content": current_chunk
                    })
                    chunk_id += 1
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        # 添加最后一块
        if current_chunk.strip():
            chunks.append({
                "id": f"chunk_{chunk_id}",
                "title": f"Section {chunk_id}",
                "level": 2,
                "content": current_chunk
            })
        
        return chunks
    
    def _extract_features(self, chunk: Dict) -> Dict:
        """
        提取完整特征
        
        Args:
            chunk: 文本块
            
        Returns:
            特征字典（NLP特征 + 结构化特征）
        """
        content = chunk["content"]
        
        # NLP特征（词性、依存、实体等）
        nlp_features = self.nlp_extractor.extract_all_features(content)
        
        # 结构化特征（列表、表格、代码块等）
        structural_features = extract_structural_features(content)
        
        # 合并
        return {
            **nlp_features,
            **structural_features,
            "title": chunk["title"],
            "level": chunk["level"]
        }
    
    def _compute_statistics(self, chunks: List[Dict]) -> Dict:
        """计算统计信息"""
        type_counts = {}
        confidence_sum = {}
        confidence_count = {}
        needs_review_count = 0
        
        for chunk in chunks:
            classification = chunk["classification"]
            ctype = classification["type"]
            conf = classification["confidence"]
            
            # 统计类型分布
            type_counts[ctype] = type_counts.get(ctype, 0) + 1
            
            # 累计置信度（排除needs_review）
            if ctype != "needs_review":
                confidence_sum[ctype] = confidence_sum.get(ctype, 0) + conf
                confidence_count[ctype] = confidence_count.get(ctype, 0) + 1
            else:
                needs_review_count += 1
        
        # 计算平均置信度
        avg_confidence = {
            ctype: confidence_sum[ctype] / confidence_count[ctype]
            for ctype in confidence_sum
        }
        
        # 总体平均置信度
        total_conf = sum(confidence_sum.values())
        total_count = sum(confidence_count.values())
        overall_avg = total_conf / total_count if total_count > 0 else 0.0
        
        return {
            "total_chunks": len(chunks),
            "type_distribution": type_counts,
            "average_confidence": avg_confidence,
            "overall_avg_confidence": overall_avg,
            "needs_review": needs_review_count
        }
    
    def save_results(self, results: Dict, output_path: Path):
        """
        保存分析结果
        
        Args:
            results: 分析结果
            output_path: 输出路径
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 分析结果已保存: {output_path}")