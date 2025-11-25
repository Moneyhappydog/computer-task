"""
AI服务 - 统一的LLM调用接口
整合千问API和Claude，提供文档分析专用方法
"""
from openai import OpenAI
from typing import Dict, List, Optional
import json
from .logger import setup_logger
from .config import Config

logger = setup_logger('ai_service')

class AIService:
    """AI服务 - 统一的LLM调用接口"""
    
    def __init__(self, provider: str = "qwen"):
        """
        初始化AI服务
        
        Args:
            provider: AI提供商，'qwen'（千问）或'claude'（Anthropic）
        """
        self.provider = provider
        
        if provider == "qwen":
            self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL
            )
            self.model = Config.OPENAI_MODEL
            logger.info(f"✅ 千问API初始化: {self.model}")
            
        elif provider == "claude":
            if not Config.ANTHROPIC_API_KEY:
                raise ValueError("未配置ANTHROPIC_API_KEY")
            
            from anthropic import Anthropic
            self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = Config.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022"
            logger.info(f"✅ Claude API初始化: {self.model}")
            
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False
    ) -> str:
        """
        生成文本（简化接口）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度
            max_tokens: 最大token数
            json_mode: 是否返回JSON
            
        Returns:
            生成的文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages, temperature, max_tokens, json_mode)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False
    ) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            temperature: 温度（0-1，越高越随机）
            max_tokens: 最大生成token数
            json_mode: 是否启用JSON模式（仅千问支持）
            
        Returns:
            AI的回复文本
        """
        try:
            if self.provider == "qwen":
                return self._chat_qwen(messages, temperature, max_tokens, json_mode)
            elif self.provider == "claude":
                return self._chat_claude(messages, temperature, max_tokens)
        except Exception as e:
            logger.error(f"❌ AI调用失败: {e}")
            raise
    
    def _chat_qwen(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """调用千问API（OpenAI兼容格式）"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 如果启用JSON模式
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content
        
        # 记录token使用量
        usage = response.usage
        logger.debug(
            f"Token使用: 输入={usage.prompt_tokens}, "
            f"输出={usage.completion_tokens}, "
            f"总计={usage.total_tokens}"
        )
        
        return content
    
    def _chat_claude(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用Claude API"""
        # Claude需要单独提取system消息
        system_msg = None
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        kwargs = {
            "model": self.model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_msg:
            kwargs["system"] = system_msg
        
        response = self.client.messages.create(**kwargs)
        
        content = response.content[0].text
        
        # 记录token使用量
        logger.debug(
            f"Token使用: 输入={response.usage.input_tokens}, "
            f"输出={response.usage.output_tokens}"
        )
        
        return content
    
    # ==================== 文档分析专用方法 ====================
    
    def analyze_structure(self, text: str) -> Dict:
        """
        分析文档结构
        
        Args:
            text: 文档文本
            
        Returns:
            {
                "sections": [
                    {"level": 1, "title": "Introduction"},
                    {"level": 2, "title": "Background"},
                ],
                "document_type": "tutorial|reference|concept|task",
                "main_topics": ["主题1", "主题2", ...],
                "complexity": "beginner|intermediate|advanced"
            }
        """
        prompt = f"""分析以下技术文档的结构，以JSON格式返回：

文档内容（前5000字符）：
{text[:5000]}

请提取：
1. sections: 所有章节标题和层级（level: 1-6）
2. document_type: 文档类型（tutorial/reference/concept/task之一）
3. main_topics: 3-5个主要技术主题
4. complexity: 难度级别（beginner/intermediate/advanced）

JSON格式示例：
{{
    "sections": [
        {{"level": 1, "title": "Introduction"}},
        {{"level": 2, "title": "Prerequisites"}}
    ],
    "document_type": "tutorial",
    "main_topics": ["Python", "API", "Authentication"],
    "complexity": "intermediate"
}}
"""
        
        messages = [
            {"role": "system", "content": "你是专业的技术文档分析助手，擅长识别文档结构。"},
            {"role": "user", "content": prompt}
        ]
        
        logger.info("🔍 正在分析文档结构...")
        response = self.chat(messages, temperature=0.3, json_mode=True)
        
        result = json.loads(response)
        logger.info(f"✅ 结构分析完成: {result['document_type']}, {len(result['sections'])} 个章节")
        
        return result
    
    def classify_content(self, text: str, context: str = "") -> str:
        """
        分类内容为DITA类型
        
        Args:
            text: 要分类的文本段落
            context: 上下文信息
            
        Returns:
            "concept" | "task" | "reference" | "troubleshooting"
        """
        prompt = f"""将以下技术文档段落分类为DITA信息类型之一：

段落内容：
{text[:1000]}

上下文：
{context[:500] if context else "无"}

DITA类型定义：
- concept: 概念性说明（什么是、为什么、原理）
- task: 操作步骤（怎么做、步骤、指南）
- reference: 参考资料（API文档、参数列表、配置项）
- troubleshooting: 故障排查（问题、原因、解决方案）

只返回一个单词：concept/task/reference/troubleshooting
"""
        
        messages = [
            {"role": "system", "content": "你是DITA文档专家，擅长内容分类。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.1, max_tokens=10)
        
        # 清理响应
        dita_type = response.strip().lower()
        
        # 验证返回值
        valid_types = ["concept", "task", "reference", "troubleshooting"]
        if dita_type not in valid_types:
            logger.warning(f"⚠️ 未识别的DITA类型: {dita_type}，默认使用concept")
            dita_type = "concept"
        
        return dita_type
    
    def extract_metadata(self, text: str) -> Dict:
        """
        提取文档元数据
        
        Args:
            text: 文档文本
            
        Returns:
            {
                "title": "文档标题",
                "author": "作者",
                "version": "版本号",
                "keywords": ["关键词1", "关键词2"],
                "summary": "简短摘要"
            }
        """
        prompt = f"""提取以下技术文档的元数据，以JSON格式返回：

文档内容（前3000字符）：
{text[:3000]}

请提取：
1. title: 文档标题（如果没有明确标题，根据内容生成一个）
2. author: 作者（如果文档中提到）
3. version: 版本号（如果有）
4. keywords: 5-8个关键技术术语
5. summary: 100字以内的内容摘要

JSON格式示例：
{{
    "title": "Python API Authentication Guide",
    "author": "",
    "version": "1.0",
    "keywords": ["Python", "API", "OAuth", "Authentication", "Security"],
    "summary": "本文档介绍如何在Python应用中实现API认证..."
}}
"""
        
        messages = [
            {"role": "system", "content": "你是专业的技术文档分析助手。"},
            {"role": "user", "content": prompt}
        ]
        
        logger.info("🔍 正在提取元数据...")
        response = self.chat(messages, temperature=0.3, json_mode=True)
        
        result = json.loads(response)
        logger.info(f"✅ 元数据提取完成: {result['title']}")
        
        return result