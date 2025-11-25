"""
NLP特征提取器
使用spaCy进行深度NLP分析，提取Task/Concept/Reference判别特征
"""
import spacy
from typing import Dict, List
import re
from pathlib import Path

class NLPFeatureExtractor:
    """NLP特征提取器 - 使用spaCy进行深度语言分析"""
    
    def __init__(self):
        """初始化spaCy模型"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️ spaCy英文模型未安装，正在下载...")
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
    
    def extract_all_features(self, text: str) -> Dict:
        """
        提取所有NLP特征
        
        Args:
            text: 输入文本
            
        Returns:
            完整特征字典
        """
        doc = self.nlp(text)
        
        return {
            # === 统计特征 ===
            "word_count": len([token for token in doc if not token.is_punct]),
            "sentence_count": len(list(doc.sents)),
            "avg_sentence_length": self._avg_sentence_length(doc),
            
            # === 词性特征 ===
            "verb_count": len([token for token in doc if token.pos_ == "VERB"]),
            "noun_count": len([token for token in doc if token.pos_ == "NOUN"]),
            "adj_count": len([token for token in doc if token.pos_ == "ADJ"]),
            
            # === Task特征 ===
            "imperative_verbs": self._count_imperative_verbs(doc),
            "action_verbs": self._count_action_verbs(doc),
            
            # === Concept特征 ===
            "has_definition": self._detect_definition_pattern(doc),
            "is_statements": self._count_is_statements(doc),
            
            # === Reference特征 ===
            "named_entities": len(doc.ents),
            "entity_types": [ent.label_ for ent in doc.ents],
            
            # === 依存关系特征 ===
            "dependency_patterns": self._analyze_dependencies(doc)
        }
    
    def _avg_sentence_length(self, doc) -> float:
        """计算平均句子长度"""
        sents = list(doc.sents)
        if not sents:
            return 0.0
        return sum(len(sent) for sent in sents) / len(sents)
    
    def _count_imperative_verbs(self, doc) -> int:
        """
        检测祈使句中的动词
        规则：句首动词原形 (VB) 且不是问句
        """
        count = 0
        for sent in doc.sents:
            tokens = [t for t in sent if not t.is_punct and not t.is_space]
            if tokens and tokens[0].pos_ == "VERB" and tokens[0].tag_ == "VB":
                # 排除疑问句
                if not sent.text.strip().endswith('?'):
                    count += 1
        return count
    
    def _count_action_verbs(self, doc) -> int:
        """
        统计动作动词
        常见Task动词：install, download, click, run, configure, etc.
        """
        action_verbs = {
            'install', 'download', 'click', 'run', 'execute', 'configure',
            'setup', 'create', 'delete', 'update', 'modify', 'copy', 'move',
            'open', 'close', 'save', 'load', 'start', 'stop', 'restart',
            'enable', 'disable', 'select', 'choose', 'enter', 'type', 'press',
            'set', 'add', 'remove', 'edit', 'change', 'verify', 'check'
        }
        
        count = 0
        for token in doc:
            if token.lemma_.lower() in action_verbs:
                count += 1
        return count
    
    def _detect_definition_pattern(self, doc) -> bool:
        """
        检测定义模式
        模式：X is/are/means/refers to Y
        """
        definition_patterns = [
            r'\b\w+ is (a|an|the)?\s*\w+',
            r'\b\w+ are \w+',
            r'\b\w+ means \w+',
            r'\b\w+ refers to \w+',
            r'\b\w+ can be defined as',
            r'\b\w+ represents \w+'
        ]
        
        text = doc.text.lower()
        for pattern in definition_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _count_is_statements(self, doc) -> int:
        """
        统计"is/are"陈述句
        Concept文档通常包含大量陈述性句子
        """
        count = 0
        for sent in doc.sents:
            for token in sent:
                if token.lemma_ == "be" and token.pos_ == "AUX":
                    count += 1
                    break
        return count
    
    def _analyze_dependencies(self, doc) -> Dict:
        """
        分析依存关系模式
        
        Returns:
            依存关系统计
        """
        dep_counts = {}
        for token in doc:
            dep = token.dep_
            dep_counts[dep] = dep_counts.get(dep, 0) + 1
        
        return {
            "nsubj": dep_counts.get("nsubj", 0),  # 主语
            "dobj": dep_counts.get("dobj", 0),    # 直接宾语
            "prep": dep_counts.get("prep", 0),    # 介词
            "compound": dep_counts.get("compound", 0)  # 复合词
        }


def extract_structural_features(content: str) -> Dict:
    """
    提取结构化特征（非NLP）
    
    Args:
        content: Markdown内容
        
    Returns:
        结构化特征字典
    """
    return {
        # === 列表特征 ===
        "has_numbered_list": bool(re.search(r'^\d+\.', content, re.MULTILINE)),
        "has_bullet_list": bool(re.search(r'^[-*+]\s', content, re.MULTILINE)),
        "list_items": len(re.findall(r'^(\d+\.|\*|-|\+)\s', content, re.MULTILINE)),
        
        # === 表格特征 ===
        "has_table": '|' in content and '---' in content,
        "table_count": content.count('|---'),
        
        # === 代码特征 ===
        "has_code_block": '```' in content,
        "code_blocks": content.count('```') // 2,
        "has_inline_code": '`' in content and '```' not in content,
        
        # === 标题特征 ===
        "heading_count": len(re.findall(r'^#{1,6}\s', content, re.MULTILINE)),
        "max_heading_level": max(
            [len(m.group(1)) for m in re.finditer(r'^(#{1,6})\s', content, re.MULTILINE)],
            default=0
        ),
        
        # === 链接和图片 ===
        "has_links": bool(re.search(r'\[.*?\]\(.*?\)', content)),
        "has_images": bool(re.search(r'!\[.*?\]\(.*?\)', content)),
        "image_count": len(re.findall(r'!\[.*?\]\(.*?\)', content)),
        
        # === 长度特征 ===
        "char_count": len(content),
        "line_count": content.count('\n') + 1
    }