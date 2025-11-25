"""
Step 2: 内容结构化器
使用LLM将非结构化内容转换为结构化数据
"""
from typing import Dict, Any, List
import logging
import json
import re

from src.utils.ai_service import AIService

logger = logging.getLogger(__name__)

class ContentStructurer:
    """内容结构化器 - 使用LLM提取结构"""
    
    def __init__(self, use_ai: bool = True):
        """
        初始化内容结构化器
        
        Args:
            use_ai: 是否使用AI服务
        """
        self.use_ai = use_ai
        self.ai_service = AIService() if use_ai else None
        
        logger.info(f"✅ 内容结构化器初始化完成 (AI: {use_ai})")
    
    def structure_content(
        self,
        content: str,
        title: str,
        content_type: str,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        结构化内容
        
        Args:
            content: 原始内容
            title: 标题
            content_type: 内容类型 (Task/Concept/Reference)
            metadata: 附加元数据
            
        Returns:
            结构化数据字典
        """
        logger.info(f"🔨 开始结构化: {content_type} - {title}")
        
        # 根据类型选择结构化方法
        if content_type == 'Task':
            return self._structure_task(content, title, metadata)
        elif content_type == 'Concept':
            return self._structure_concept(content, title, metadata)
        elif content_type == 'Reference':
            return self._structure_reference(content, title, metadata)
        else:
            raise ValueError(f"不支持的内容类型: {content_type}")
    
    def _structure_task(self, content: str, title: str, metadata: Dict) -> Dict:
        """结构化Task类型内容"""
        
        if self.use_ai:
            prompt = self._build_task_prompt(content, title)
            response = self.ai_service.generate(prompt)
            structured_data = self._parse_json_response(response)
        else:
            # 规则提取（备用方案）
            structured_data = self._extract_task_by_rules(content, title)
        
        # 验证必需字段
        structured_data.setdefault('task_id', self._generate_id(title))
        structured_data.setdefault('title', title)
        structured_data.setdefault('steps', [])
        
        logger.info(f"✓ Task结构化完成: {len(structured_data['steps'])} 个步骤")
        
        return structured_data
    
    def _structure_concept(self, content: str, title: str, metadata: Dict) -> Dict:
        """结构化Concept类型内容"""
        
        if self.use_ai:
            prompt = self._build_concept_prompt(content, title)
            response = self.ai_service.generate(prompt)
            structured_data = self._parse_json_response(response)
        else:
            structured_data = self._extract_concept_by_rules(content, title)
        
        structured_data.setdefault('concept_id', self._generate_id(title))
        structured_data.setdefault('title', title)
        structured_data.setdefault('sections', [])
        
        logger.info(f"✓ Concept结构化完成: {len(structured_data['sections'])} 个章节")
        
        return structured_data
    
    def _structure_reference(self, content: str, title: str, metadata: Dict) -> Dict:
        """结构化Reference类型内容"""
        
        if self.use_ai:
            prompt = self._build_reference_prompt(content, title)
            response = self.ai_service.generate(prompt)
            structured_data = self._parse_json_response(response)
        else:
            structured_data = self._extract_reference_by_rules(content, title)
        
        structured_data.setdefault('reference_id', self._generate_id(title))
        structured_data.setdefault('title', title)
        
        logger.info(f"✓ Reference结构化完成")
        
        return structured_data
    
    # ========== LLM Prompt构建 ==========
    
    def _build_task_prompt(self, content: str, title: str) -> str:
        """构建Task结构化提示词"""
        return f"""提取以下Task内容的结构化信息。

标题: {title}

内容:
{content}

请输出JSON格式（不要有其他说明文字）:
{{
  "title": "任务标题",
  "short_description": "简短描述（可选）",
  "prerequisites": ["前提条件1", "前提条件2"],
  "context": "背景说明（可选）",
  "steps": [
    {{
      "command": "步骤的主要操作",
      "info": "步骤的补充说明（可选）",
      "example": "示例（可选）"
    }}
  ],
  "result": "预期结果（可选）",
  "example": "完整示例（可选）"
}}

注意:
1. 每个步骤的command必须是明确的操作指令
2. steps至少包含1个步骤
3. 如果没有某个字段的信息就省略
"""
    
    def _build_concept_prompt(self, content: str, title: str) -> str:
        """构建Concept结构化提示词"""
        return f"""提取以下Concept内容的结构化信息。

标题: {title}

内容:
{content}

请输出JSON格式（不要有其他说明文字）:
{{
  "title": "概念标题",
  "short_description": "简短描述（可选）",
  "introduction": "引言",
  "definition": "定义（如果有明确定义）",
  "sections": [
    {{
      "id": "section_1",
      "title": "章节标题（可选）",
      "content": "章节内容",
      "example": "示例（可选）"
    }}
  ],
  "note": "注意事项（可选）"
}}

注意:
1. introduction是核心概念的介绍
2. sections包含详细说明的各个方面
3. 如果内容中有明确的定义部分，提取到definition字段
"""
    
    def _build_reference_prompt(self, content: str, title: str) -> str:
        """构建Reference结构化提示词"""
        return f"""提取以下Reference内容的结构化信息。

标题: {title}

内容:
{content}

请输出JSON格式（不要有其他说明文字）:
{{
  "title": "参考标题",
  "short_description": "简短描述（可选）",
  "introduction": "引言（可选）",
  "properties": [
    {{
      "name": "属性名",
      "value": "属性值",
      "description": "描述"
    }}
  ],
  "table": {{
    "columns": ["列1", "列2", "列3"],
    "rows": [
      ["单元格1", "单元格2", "单元格3"],
      ["单元格4", "单元格5", "单元格6"]
    ]
  }},
  "sections": [
    {{
      "id": "section_1",
      "title": "章节标题（可选）",
      "content": "章节内容"
    }}
  ]
}}

注意:
1. properties用于参数列表、配置项等
2. table用于表格数据
3. 根据实际内容选择使用properties或table或都使用
"""
    
    # ========== 响应解析 ==========
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        解析LLM的JSON响应
        
        Args:
            response: LLM原始响应
            
        Returns:
            解析后的字典
        """
        try:
            # 移除可能的markdown代码块标记
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*$', '', response)
            response = response.strip()
            
            data = json.loads(response)
            logger.debug(f"✓ JSON解析成功")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.debug(f"原始响应: {response[:200]}")
            
            # 尝试修复常见问题
            return self._try_fix_json(response)
    
    def _try_fix_json(self, response: str) -> Dict:
        """尝试修复常见的JSON错误"""
        # 尝试1: 移除注释
        response = re.sub(r'//.*?\n', '\n', response)
        
        # 尝试2: 修复未闭合的引号
        # ... 更多修复逻辑
        
        try:
            return json.loads(response)
        except:
            logger.error("JSON修复失败，返回空结构")
            return {}
    
    # ========== 规则提取（备用方案） ==========
    
    def _extract_task_by_rules(self, content: str, title: str) -> Dict:
        """使用规则提取Task结构（不依赖LLM）"""
        steps = []
        
        # 匹配编号列表 (1. xxx, 2. xxx)
        numbered_pattern = r'^\s*(\d+)\.\s*(.+)$'
        for line in content.split('\n'):
            match = re.match(numbered_pattern, line)
            if match:
                steps.append({
                    'command': match.group(2).strip(),
                    'info': None
                })
        
        # 如果没有找到编号列表，尝试破折号列表
        if not steps:
            bullet_pattern = r'^\s*[-*]\s*(.+)$'
            for line in content.split('\n'):
                match = re.match(bullet_pattern, line)
                if match:
                    steps.append({
                        'command': match.group(1).strip(),
                        'info': None
                    })
        
        return {
            'task_id': self._generate_id(title),
            'title': title,
            'steps': steps,
            'prerequisites': None,
            'result': None
        }
    
    def _extract_concept_by_rules(self, content: str, title: str) -> Dict:
        """使用规则提取Concept结构"""
        # 简单分段
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        sections = []
        for i, para in enumerate(paragraphs):
            sections.append({
                'id': f'section_{i+1}',
                'title': None,
                'content': para
            })
        
        return {
            'concept_id': self._generate_id(title),
            'title': title,
            'introduction': paragraphs[0] if paragraphs else '',
            'sections': sections[1:] if len(sections) > 1 else []
        }
    
    def _extract_reference_by_rules(self, content: str, title: str) -> Dict:
        """使用规则提取Reference结构"""
        # 尝试检测表格
        table = self._detect_markdown_table(content)
        
        return {
            'reference_id': self._generate_id(title),
            'title': title,
            'table': table,
            'properties': None
        }
    
    def _detect_markdown_table(self, content: str) -> Dict:
        """检测Markdown表格"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # 检测表格分隔线 |---|---|
            if re.match(r'\s*\|[\s\-:]+\|', line):
                if i > 0:
                    # 上一行是表头
                    header_line = lines[i-1]
                    headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
                    
                    # 后续行是数据
                    rows = []
                    for data_line in lines[i+1:]:
                        if not data_line.strip() or not '|' in data_line:
                            break
                        cells = [cell.strip() for cell in data_line.split('|')[1:-1]]
                        if cells:
                            rows.append(cells)
                    
                    return {
                        'columns': headers,
                        'rows': rows
                    }
        
        return None
    
    # ========== 工具方法 ==========
    
    def _generate_id(self, title: str) -> str:
        """
        生成符合DITA规范的ID
        
        Args:
            title: 标题
            
        Returns:
            符合规范的ID字符串
        """
        # 转小写，移除特殊字符，空格替换为下划线
        id_str = title.lower()
        id_str = re.sub(r'[^a-z0-9\s_-]', '', id_str)
        id_str = re.sub(r'\s+', '_', id_str)
        id_str = id_str.strip('_')
        
        # ID必须以字母开头
        if id_str and not id_str[0].isalpha():
            id_str = 'id_' + id_str
        
        return id_str or 'unnamed'


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("content_structurer")
    
    structurer = ContentStructurer(use_ai=True)
    
    # 测试Task
    task_content = """
    Before you begin, ensure you have Python 3.8 or higher installed.
    
    Follow these steps to install the package:
    
    1. Download the package from the official website
    2. Run the installer with administrator privileges
    3. Verify the installation by running `program --version`
    
    After successful installation, you should see the version number.
    """
    
    print("\n" + "="*70)
    print("测试 Task 结构化")
    print("="*70)
    
    result = structurer.structure_content(
        content=task_content,
        title="Installing the Software",
        content_type='Task'
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))