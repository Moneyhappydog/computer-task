"""
主动学习管理器 - Tier 3
管理需要人工审核的低置信度案例，持续改进系统
"""
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime

# 导入工具模块
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

logger = setup_logger('active_learning')

class ActiveLearningManager:
    """主动学习管理器 - Tier 3分类器"""
    
    def __init__(self, review_dir: Path = None):
        """
        初始化主动学习管理器
        
        Args:
            review_dir: 人工审核队列目录
        """
        if review_dir is None:
            review_dir = Path("data/review_queue")
        
        self.review_dir = Path(review_dir)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        
        self.training_set_path = self.review_dir / "training_set.jsonl"
        self.pending_review_path = self.review_dir / "pending_review.json"
        
        logger.info(f"📚 主动学习管理器初始化: {review_dir}")
    
    def mark_for_review(
        self,
        chunk: Dict,
        tier1_result: Dict,
        tier2_result: Dict
    ) -> Dict:
        """
        标记需要人工审核的案例
        
        当两层分类器都不确定时（置信度过低），提交给人工审核
        
        Args:
            chunk: 文本块
            tier1_result: Tier 1分类结果
            tier2_result: Tier 2分类结果
            
        Returns:
            审核请求结果
        """
        review_item = {
            "chunk_id": chunk["id"],
            "title": chunk["title"],
            "content": chunk["content"][:500] + "...",  # 仅保存前500字符
            "timestamp": datetime.now().isoformat(),
            "tier1": {
                "type": tier1_result["type"],
                "confidence": tier1_result["confidence"],
                "matched_rules": tier1_result.get("matched_rules", [])
            },
            "tier2": {
                "type": tier2_result["type"],
                "confidence": tier2_result["confidence"],
                "reasoning": tier2_result.get("reasoning", "")
            },
            "status": "pending",
            "human_label": None
        }
        
        # 加载现有队列
        pending = self._load_pending_queue()
        pending.append(review_item)
        
        # 保存
        with open(self.pending_review_path, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=2, ensure_ascii=False)
        
        logger.warning(
            f"⚠️ 块 '{chunk['title'][:30]}...' 需要人工审核 "
            f"(Tier1: {tier1_result['type']}/{tier1_result['confidence']:.2f}, "
            f"Tier2: {tier2_result['type']}/{tier2_result['confidence']:.2f})"
        )
        
        return {
            "type": "needs_review",
            "confidence": 0.0,
            "scores": {"Task": 0.33, "Concept": 0.33, "Reference": 0.33},
            "reasoning": "Low confidence from both classifiers, marked for human review",
            "review_id": review_item["chunk_id"]
        }
    
    def submit_human_label(self, chunk_id: str, human_label: str):
        """
        提交人工标注结果
        
        Args:
            chunk_id: 块ID
            human_label: 人工标注结果 (Task/Concept/Reference)
        """
        if human_label not in ["Task", "Concept", "Reference"]:
            raise ValueError(f"无效的标注: {human_label}")
        
        # 从待审核队列中找到该项
        pending = self._load_pending_queue()
        
        found = False
        for item in pending:
            if item["chunk_id"] == chunk_id:
                item["human_label"] = human_label
                item["status"] = "reviewed"
                item["reviewed_at"] = datetime.now().isoformat()
                
                # 添加到训练集
                self._add_to_training_set(item)
                
                logger.info(f"✅ 人工标注已记录: {chunk_id} → {human_label}")
                found = True
                break
        
        if not found:
            logger.error(f"❌ 未找到待审核项: {chunk_id}")
            return
        
        # 保存更新后的队列
        with open(self.pending_review_path, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=2, ensure_ascii=False)
    
    def _load_pending_queue(self) -> List[Dict]:
        """加载待审核队列"""
        if self.pending_review_path.exists():
            with open(self.pending_review_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _add_to_training_set(self, reviewed_item: Dict):
        """将审核后的项添加到训练集"""
        training_example = {
            "title": reviewed_item["title"],
            "content": reviewed_item["content"],
            "label": reviewed_item["human_label"],
            "timestamp": reviewed_item["reviewed_at"],
            "tier1_prediction": reviewed_item["tier1"]["type"],
            "tier2_prediction": reviewed_item["tier2"]["type"],
            "tier1_confidence": reviewed_item["tier1"]["confidence"],
            "tier2_confidence": reviewed_item["tier2"]["confidence"]
        }
        
        # 追加到训练集文件（JSONL格式，每行一个JSON）
        with open(self.training_set_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
        
        logger.info(f"📖 训练集已更新: {self.training_set_path}")
    
    def get_pending_count(self) -> int:
        """获取待审核数量"""
        pending = self._load_pending_queue()
        return sum(1 for item in pending if item["status"] == "pending")
    
    def get_pending_items(self) -> List[Dict]:
        """获取所有待审核项"""
        pending = self._load_pending_queue()
        return [item for item in pending if item["status"] == "pending"]
    
    def export_training_data(self, output_path: Path):
        """
        导出训练数据为JSON格式
        
        Args:
            output_path: 输出路径
        """
        if not self.training_set_path.exists():
            logger.warning("⚠️ 训练集为空")
            return
        
        training_data = []
        with open(self.training_set_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    training_data.append(json.loads(line))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 训练数据已导出: {output_path} ({len(training_data)} 条)")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        pending = self._load_pending_queue()
        
        total = len(pending)
        pending_count = sum(1 for item in pending if item["status"] == "pending")
        reviewed_count = sum(1 for item in pending if item["status"] == "reviewed")
        
        # 统计训练集大小
        training_count = 0
        if self.training_set_path.exists():
            with open(self.training_set_path, 'r', encoding='utf-8') as f:
                training_count = sum(1 for line in f if line.strip())
        
        return {
            "total_items": total,
            "pending": pending_count,
            "reviewed": reviewed_count,
            "training_set_size": training_count
        }