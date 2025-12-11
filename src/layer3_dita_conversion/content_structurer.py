"""
Step 2: 内容结构化器
使用LLM将非结构化内容转换为结构化数据
"""
from typing import Dict, Any, List
import logging
import json
import re

from src.utils.ai_service import AIService
from .errors import StructureError, DITAConversionError

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
        self.used_ids = set()  # 跟踪已使用的ID，确保唯一性
        
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
            result = self._structure_task(content, title, metadata)
        elif content_type == 'Concept':
            result = self._structure_concept(content, title, metadata)
        elif content_type == 'Reference':
            result = self._structure_reference(content, title, metadata)
        else:
            raise StructureError(
                f"不支持的内容类型: {content_type}",
                "UNSUPPORTED_CONTENT_TYPE"
            )
        
        # 确保生成的ID唯一
        if result:
            self._ensure_unique_ids(result)
        
        return result
    
    def _structure_task(self, content: str, title: str, metadata: Dict) -> Dict:
        """结构化Task类型内容"""
        
        structured_data = None
        
        if self.use_ai:
            try:
                prompt = self._build_task_prompt(content, title)
                response = self.ai_service.generate(prompt)
                structured_data = self._parse_json_response(response)
                
                # 验证结构化结果是否有效
                if not structured_data or 'steps' not in structured_data:
                    raise StructureError(
                        "结构化结果无效，缺少必要字段",
                        "INVALID_STRUCTURED_DATA"
                    )
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM结构化Task失败: {e}，自动降级到规则提取")
                structured_data = None
        
        # 如果AI结构化失败或未使用AI，使用规则提取
        if structured_data is None:
            structured_data = self._extract_task_by_rules(content, title)
        
        # 验证必需字段
        structured_data.setdefault('task_id', self._generate_id(title))
        structured_data.setdefault('title', title)
        structured_data.setdefault('steps', [])
        
        logger.info(f"✓ Task结构化完成: {len(structured_data['steps'])} 个步骤")
        
        return structured_data
    
    def _structure_concept(self, content: str, title: str, metadata: Dict) -> Dict:
        """结构化Concept类型内容"""
        
        structured_data = None
        
        if self.use_ai:
            try:
                prompt = self._build_concept_prompt(content, title)
                response = self.ai_service.generate(prompt)
                structured_data = self._parse_json_response(response)
                
                # 验证结构化结果是否有效
                if not structured_data:
                    raise StructureError(
                        "结构化结果无效",
                        "INVALID_STRUCTURED_DATA"
                    )
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM结构化Concept失败: {e}，自动降级到规则提取")
                structured_data = None
        
        # 如果AI结构化失败或未使用AI，使用规则提取
        if structured_data is None:
            structured_data = self._extract_concept_by_rules(content, title)
        
        structured_data.setdefault('concept_id', self._generate_id(title))
        structured_data.setdefault('title', title)
        structured_data.setdefault('sections', [])
        
        logger.info(f"✓ Concept结构化完成: {len(structured_data['sections'])} 个章节")
        
        return structured_data
    
    def _structure_reference(self, content: str, title: str, metadata: Dict) -> Dict:
        """结构化Reference类型内容"""
        
        structured_data = None
        
        if self.use_ai:
            try:
                prompt = self._build_reference_prompt(content, title)
                response = self.ai_service.generate(prompt)
                structured_data = self._parse_json_response(response)
                
                # 验证结构化结果是否有效
                if not structured_data:
                    raise StructureError(
                        "结构化结果无效",
                        "INVALID_STRUCTURED_DATA"
                    )
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM结构化Reference失败: {e}，自动降级到规则提取")
                structured_data = None
        
        # 如果AI结构化失败或未使用AI，使用规则提取
        if structured_data is None:
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
      "cmd": "步骤的主要操作",
      "info": "步骤的补充说明（可选）",
      "example": "示例（可选）"
    }}
  ],
  "result": "预期结果（可选）",
  "example": "完整示例（可选）"
}}

注意:
1. 每个步骤的cmd必须是明确的操作指令
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
        # 转换Markdown图片为DITA格式
        content = self._convert_markdown_images_to_dita(content)
        
        steps = []
        
        # 匹配编号列表 (1. xxx, 2. xxx)
        numbered_pattern = r'^\s*(\d+)\.\s*(.+)$'
        for line in content.split('\n'):
            match = re.match(numbered_pattern, line)
            if match:
                steps.append({
                    'cmd': match.group(2).strip(),
                    'info': None
                })
        
        # 如果没有找到编号列表，尝试破折号列表
        if not steps:
            bullet_pattern = r'^\s*[-*]\s*(.+)$'
            for line in content.split('\n'):
                match = re.match(bullet_pattern, line)
                if match:
                    steps.append({
                        'cmd': match.group(1).strip(),
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
        # 转换Markdown图片为DITA格式
        content = self._convert_markdown_images_to_dita(content)
        
        # 使用__FIG_END__标记来辅助分段
        # 将__FIG_END__作为段落分隔的信号
        content = content.replace('__FIG_END__', '\n\n')
        
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
        # 转换Markdown图片为DITA格式
        content = self._convert_markdown_images_to_dita(content)
        
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
    
    def _convert_markdown_images_to_dita(self, content: str) -> str:
        """
        将Markdown格式的图片链接转换为DITA的fig+image标签
        并尝试合并后续的图片说明文字
        
        Args:
            content: 包含Markdown图片链接的内容
            
        Returns:
            转换后的内容
        """
        # 分行处理，以便识别图片和说明的上下文
        lines = content.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 匹配Markdown图片语法: ![alt text](path)
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            image_match = re.search(image_pattern, line)
            
            if image_match:
                alt_text = image_match.group(1)
                image_path = image_match.group(2)
                
                # 生成基础image标签
                if alt_text:
                    image_tag = f'<image href="{image_path}" alt="{alt_text}"/>'
                else:
                    image_tag = f'<image href="{image_path}"/>'
                
                # 检查后续几行是否是图片说明（可能有空行分隔）
                caption = None
                caption_end_idx = i
                
                # 向前查找最多3行
                for j in range(1, min(4, len(lines) - i)):
                    next_line = lines[i + j].strip()
                    
                    # 跳过空行
                    if not next_line:
                        continue
                    
                    # 匹配常见的图片说明模式
                    caption_pattern = r'^(Figure|Fig\.|图|图片|图示|图表)\s*[\d\.]+[:\s].*'
                    if re.match(caption_pattern, next_line, re.IGNORECASE):
                        caption = next_line
                        caption_end_idx = i + j
                        break
                    else:
                        # 如果遇到非空行但不是图片说明，停止查找
                        break
                
                # 将图片包裹在<fig>标签中
                if caption:
                    # 有说明：图片+说明都在fig中
                    # 在说明后添加段落分隔标记，以便后续分段处理
                    fig_content = f'<fig>\n        {image_tag}\n        <p>{caption}</p>\n      </fig>\n\n__FIG_END__\n'
                    i = caption_end_idx  # 跳到说明行
                else:
                    # 无说明：只包裹图片
                    fig_content = f'<fig>\n        {image_tag}\n      </fig>\n\n__FIG_END__\n'
                
                # 替换原行中的图片语法
                result_line = re.sub(image_pattern, fig_content, line)
                result_lines.append(result_line)
            else:
                result_lines.append(line)
            
            i += 1
        
        return '\n'.join(result_lines)
    
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
        
        # 确保ID唯一
        base_id = id_str or 'unnamed'
        unique_id = base_id
        counter = 1
        
        while unique_id in self.used_ids:
            unique_id = f"{base_id}_{counter}"
            counter += 1
        
        self.used_ids.add(unique_id)
        return unique_id
    
    def _ensure_unique_ids(self, structured_data: Dict):
        """
        确保结构化数据中的所有ID都是唯一的
        
        Args:
            structured_data: 结构化数据字典
        """
        # 检查主要ID字段
        for id_field in ['task_id', 'concept_id', 'reference_id']:
            if id_field in structured_data:
                original_id = structured_data[id_field]
                if original_id in self.used_ids:
                    # 生成新的唯一ID
                    new_id = self._generate_id(original_id)
                    structured_data[id_field] = new_id
                else:
                    self.used_ids.add(original_id)
        
        # 检查sections中的ID
        if 'sections' in structured_data:
            for section in structured_data['sections']:
                if 'id' in section:
                    original_id = section['id']
                    if original_id in self.used_ids:
                        # 生成新的唯一ID
                        new_id = self._generate_id(original_id)
                        section['id'] = new_id
                    else:
                        self.used_ids.add(original_id)


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