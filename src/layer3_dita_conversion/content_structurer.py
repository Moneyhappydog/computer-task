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
        return f"""你将把输入内容结构化为符合 DITA 片段规范的 JSON。只输出 JSON，不要输出任何解释文字、不要 Markdown、不要代码围栏。

标题: {title}

内容:
{content}

=== 输出 JSON（严格遵循；缺失字段就省略） ===
{{
  "title": "任务标题",
  "short_description": "简短描述（可选）",
  "prerequisites": ["前提条件1", "前提条件2"],
  "context": "背景说明（可选）",
  "steps": [
    {{
      "cmd": "明确的操作指令（必须是动作）",
      "info": "可选：DITA片段（见下方语法）",
      "example": "可选：DITA片段（见下方语法）"
    }}
  ],
  "result": "预期结果（可选）",
  "example": "完整示例（可选，DITA片段语法同上）"
}}

=== DITA 片段语法（适用于 info / example 等字符串字段，必须严格遵守） ===
你输出的字符串只能由以下“单元”拼接而成：
1) 段落单元（只能包含纯文本 + 行内公式）：
   <p>...文本...<equation-inline>LaTeX</equation-inline>...文本...</p>
2) 块单元（必须独立成段，不能在 <p> 内）：
   - 公式块：<codeblock outputclass="math">纯净LaTeX</codeblock>
   - 表格块：<table><title>...</title><tgroup cols="N">...</tgroup></table>
   - 图片块：<fig><title>...</title><image href="..." alt="..."/></fig>

拼接格式只能是：单元之间用两个换行分隔：
<p>...</p>\\n\\n<codeblock ...>...</codeblock>\\n\\n<p>...</p>

硬性禁止：
- 禁止 <p><p> 嵌套
- 禁止 <table>/<fig>/<codeblock> 出现在 <p> 内
- 禁止把块单元与文本写在同一行（块单元前后必须是 \\n\\n）

=== 图片规则（必须执行） ===
- 每个 <fig> 必须同时满足：
  - <title> 非空：无法识别则用 "Caption unavailable (OCR)"
  - alt 非空：无法识别则用 "Figure"
- href：
  - 若路径不确定或文件不一定存在：用 href="MISSING_ASSET/<expected_filename>.png"
  - expected_filename 规则：优先使用输入里出现的文件名；否则用 "page_<page>_image_<idx>.png"；再不行用 "unknown.png"

=== 表格规则（必须执行） ===
- 仅当“至少2列 且 至少2行数据”才输出 <table>；否则改写为段落或列表（但列表也要放在 <p> 里描述，不要伪表）。
- 列数归一化算法（必须照做）：
  1) 计算所有行的最大列数 = N（包括表头行与数据行）
  2) tgroup cols="N"
  3) 每一行的 entry 数必须等于 N：不足补空字符串；超过则把多余内容合并到最后一列并用分号隔开

=== 公式规则（必须执行） ===
- 行内公式：只用 <equation-inline>，且一个公式只能一个标签，禁止拆分。
- 块公式：只用 <codeblock outputclass="math">，并且 LaTeX 必须纯净：
  - 不允许出现 &amp; &lt; &gt; 等 HTML 实体（必须反转义）
  - 不允许输出 "..." 作为公式内容；无法识别则输出 "MISSING_EQUATION"
- 若正文出现“(1)(2)...”引用：块公式尽量用 \\tag{{n}} 保留编号；无法恢复则在公式内容末尾写 "% missing tag n"（作为LaTeX注释）并仍输出 MISSING_EQUATION。

=== 输出前自检（必须完成后再输出） ===
检查你输出 JSON 中所有字符串字段：
1) 是否出现 "<p><p>" 或 "<p>...<table>" 或 "<p>...<fig>" 或 "<p>...<codeblock" ？若有，必须改为按语法拆分并用 \\n\\n 分隔。
2) 是否有 <fig> 的 title/alt 为空？若有，补占位文本。
3) 是否有表格 cols 与行 entry 数不一致？按归一化算法修复。
4) 是否有公式包含 HTML 实体或 "..."？清洗或改为 MISSING_EQUATION。
现在输出最终 JSON。
"""

    def _build_concept_prompt(self, content: str, title: str) -> str:
        return f"""你将把输入内容结构化为符合 DITA 片段规范的 JSON。只输出 JSON，不要输出任何解释文字、不要 Markdown、不要代码围栏。

标题: {title}

内容:
{content}

=== 输出 JSON（严格遵循；缺失字段就省略） ===
{{
  "title": "概念标题",
  "short_description": "简短描述（可选）",
  "introduction": "引言（可选，可使用DITA片段语法）",
  "definition": "定义（可选，可使用DITA片段语法）",
  "sections": [
    {{
      "id": "section_1",
      "title": "章节标题（可选）",
      "content": "DITA片段（必须遵守下方语法）",
      "example": "可选：DITA片段"
    }}
  ],
  "note": "注意事项（可选，可使用DITA片段语法）"
}}

=== DITA 片段语法（适用于 introduction/definition/sections[].content/example/note） ===
允许的单元只有两类：
1) 段落单元：<p>纯文本 + 行内公式</p>
2) 块单元：<fig>...</fig> 或 <table>...</table> 或 <codeblock outputclass="math">...</codeblock>

拼接规则：单元之间必须用 \\n\\n 分隔，块单元必须独立成段。
严禁：
- <p><p> 嵌套
- 块单元在 <p> 内
- 块单元与文本同一行

=== 公式规则（最高优先级） ===
- 行内：<equation-inline>LaTeX</equation-inline>（一个公式一个标签，禁止拆分）
- 块级：<codeblock outputclass="math">纯净LaTeX</codeblock>（必须独立成段）
- LaTeX 清洗：必须反转义 HTML 实体（&amp;→&, &lt;→<, &gt;→>），禁止出现 "..."
- 编号：若你在输入中识别到 (1)(2)(3)... 序列引用：
  - 尽量在块公式 LaTeX 末尾保留 \\tag{{n}}
  - 若发现缺号，必须在 JSON 顶层增加：
    "missing_equation_tags": [缺失编号列表]

=== 表格规则（严格校验 + 归一化） ===
- 仅当 ≥2列 且 ≥2行数据 才输出 <table>；否则输出为段落描述，禁止伪表。
- 列数归一化算法（必须照做）：
  - N = 所有行最大列数
  - tgroup cols="N"
  - 每行 entry 数必须= N，不足补空，超出合并入最后一列
- title 必须非空：无法识别则用 "Table (OCR)"

=== 图片规则（完整性） ===
- 每个 fig 必须：
  - <title> 非空：无法识别则 "Caption unavailable (OCR)"
  - alt 非空：无法识别则 "Figure"
- href：若不确定存在，用 href="MISSING_ASSET/<expected_filename>.png"
- 若有多张图，按出现顺序输出，尽量保持 Figure 编号一致。

=== 输出前自检（必须完成） ===
对所有 DITA 片段字段执行检查与修复：
1) 不得出现 "<p><p>"；不得出现 "<p>...<table/fig/codeblock"
2) 所有块单元必须前后都有 \\n\\n
3) 表格 cols 与 entry 数一致
4) 公式无 HTML 实体且不为 "..."
现在输出最终 JSON。
"""

    
    def _build_reference_prompt(self, content: str, title: str) -> str:
        return f"""你将把输入内容结构化为符合 DITA 片段规范的 JSON。只输出 JSON，不要输出任何解释文字、不要 Markdown、不要代码围栏。

标题: {title}

内容:
{content}

=== 输出 JSON（严格遵循；缺失字段就省略） ===
{{
  "title": "参考标题",
  "short_description": "简短描述（可选）",
  "introduction": "可选：DITA片段",
  "properties": [
    {{
      "name": "属性名",
      "value": "属性值",
      "description": "描述（可选）"
    }}
  ],
  "table": {{
    "columns": ["列1", "列2"],
    "rows": [
      ["A", "B"]
    ]
  }},
  "sections": [
    {{
      "id": "section_1",
      "title": "章节标题（可选）",
      "content": "DITA片段（必须遵守下方语法）"
    }}
  ]
}}

=== 语言规则 ===
保持原文语言，不要翻译。

=== DITA 片段语法（适用于 introduction/sections[].content 等字符串） ===
- 段落单元：<p>纯文本 + 行内公式</p>
- 块单元：<fig>...</fig> / <table>...</table> / <codeblock outputclass="math">...</codeblock>
- 单元之间必须 \\n\\n 分隔
- 严禁：<p><p> 嵌套；严禁块单元在 <p> 内

=== 公式规则 ===
- 行内：<equation-inline>LaTeX</equation-inline>（不可拆分）
- 块级：<codeblock outputclass="math">纯净LaTeX</codeblock>（必须独立成段）
- 必须反转义 HTML 实体；禁止输出 "..."；无法识别则 "MISSING_EQUATION"

=== 表格规则 ===
- 若内容是“参数表/配置表”类：优先填充 JSON 的 table 字段（columns/rows），并确保每行列数一致。
- 若必须在 content 中输出 DITA 表：
  - 仅当 ≥2列且≥2行数据
  - 使用 <table><title>...</title><tgroup cols="N">...</tgroup></table>
  - title 非空：无法识别则 "Table (OCR)"
  - cols/entry 数必须一致（不足补空，超出合并入最后列）

=== 图片规则 ===
- fig 格式：<fig><title>...</title><image href="..." alt="..."/></fig>
- title/alt 必须非空
- 路径不确定：href="MISSING_ASSET/<expected_filename>.png"

=== 输出前自检 ===
1) DITA 片段字段是否存在嵌套 p 或块在 p 内？修复为按单元拆分 + \\n\\n
2) 表格列数一致性
3) 公式是否纯净、非 "..."
现在输出最终 JSON。
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
        # 先提取并标记表格，避免被分段打散
        content = self._mark_tables(content)
        
        # 转换Markdown图片为DITA格式
        content = self._convert_markdown_images_to_dita(content)
        
        # 使用__FIG_END__和__TABLE_END__标记来辅助分段
        content = content.replace('__FIG_END__', '\n\n')
        content = content.replace('__TABLE_END__', '\n\n')
        
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
    
    def _mark_tables(self, content: str) -> str:
        """
        检测Markdown表格并转换为DITA table格式
        使用占位符标记，避免表格被分段打散
        
        Args:
            content: 包含Markdown表格的内容
            
        Returns:
            转换后的内容
        """
        lines = content.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 检测表格分隔线 |---|---| 或 |----|----| 
            if re.match(r'^\s*\|[\s\-:]+\|\s*$', line.strip()) or re.match(r'^\s*\|[-:\s|]+\|\s*$', line.strip()):
                # 向上查找表头行（可能有多行）
                header_lines = []
                j = i - 1
                while j >= 0 and '|' in lines[j]:
                    header_lines.insert(0, lines[j])
                    j -= 1
                
                # 检测表格标题（可能在表头上面1-2行）
                table_title = None
                title_idx = j  # j现在指向表头之前的行
                if title_idx >= 0:
                    potential_title = lines[title_idx].strip()
                    # 检测是否是"Table X. ..."格式
                    if re.match(r'^Table\s+\d+\.', potential_title, re.IGNORECASE):
                        table_title = potential_title
                
                # 提取数据行
                data_rows_raw = []
                k = i + 1
                while k < len(lines):
                    data_line = lines[k].strip()
                    if not data_line or '|' not in data_line:
                        break
                    data_rows_raw.append(data_line)
                    k += 1
                
                # 如果找到了表格内容，生成DITA table
                if header_lines or data_rows_raw:
                    # 解析表头
                    headers = []
                    for header_line in header_lines:
                        cells = [cell.strip() for cell in header_line.split('|')]
                        # 移除首尾空字符串
                        cells = [c for c in cells if c]
                        if cells:
                            headers.append(cells)
                    
                    # 解析数据行
                    data_rows = []
                    for data_line in data_rows_raw:
                        cells = [cell.strip() for cell in data_line.split('|')]
                        cells = [c for c in cells if c or True]  # 保留空单元格
                        # 移除首尾空字符串（来自行首尾的|）
                        if cells and cells[0] == '':
                            cells = cells[1:]
                        if cells and cells[-1] == '':
                            cells = cells[:-1]
                        if cells:
                            data_rows.append(cells)
                    
                    # 生成DITA table
                    dita_table = self._generate_dita_table_from_lines(headers, data_rows, table_title)
                    
                    # 清除已添加到result_lines中的表头行
                    for _ in header_lines:
                        if result_lines and '|' in result_lines[-1]:
                            result_lines.pop()
                    
                    # 如果有表格标题，也从result_lines中移除
                    if table_title and result_lines:
                        if table_title in result_lines[-1]:
                            result_lines.pop()
                    
                    result_lines.append(dita_table)
                    result_lines.append('\n__TABLE_END__\n')  # 添加分段标记
                    
                    # 跳到表格结束位置
                    i = k
                    continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def _generate_dita_table_from_lines(self, header_lines: list, data_rows: list, title: str = None) -> str:
        """
        从解析的表格行生成DITA table XML（智能版本）
        
        自动检测：
        1. 实际列数（从所有行的最大单元格数）
        2. 混合表头（部分单元格包含空格分隔的子列）
        3. 跨列合并（根据单元格位置和空单元格自动推断）
        
        Args:
            header_lines: 表头行列表（可能多行）
            data_rows: 数据行列表
            title: 表格标题（可选）
            
        Returns:
            DITA table XML字符串
        """
        # === 第一步：智能解析所有行，检测真实列结构 ===
        all_rows = header_lines + data_rows
        if not all_rows:
            return ''
        
        # 分析每行的单元格，检测是否有子列（空格分隔的值）
        expanded_rows = []
        max_cols = 0
        
        for row in all_rows:
            # 检查每个单元格是否包含多个空格分隔的值
            expanded_row = []
            for cell in row:
                cell_stripped = cell.strip()
                if not cell_stripped:
                    expanded_row.append('')
                    continue
                
                # 检测单元格是否包含多列数据
                # 模式1: "1-100 101-150" (空格分隔的多个数值/标识)
                # 模式2: "PS KD AD" (多个短标识符)
                parts = cell_stripped.split()
                
                # 如果分割后有多个部分且每个部分都很短，可能是多列
                if len(parts) > 1 and all(len(p) < 15 for p in parts):
                    # 检查是否是数值类型或简短标识符
                    if all(bool(re.match(r'^[\d\.\-XxOo✓✗]+$', p)) or len(p) <= 6 for p in parts):
                        expanded_row.extend(parts)
                        continue
                
                expanded_row.append(cell_stripped)
            
            expanded_rows.append(expanded_row)
            max_cols = max(max_cols, len(expanded_row))
        
        if max_cols == 0:
            return ''
        
        # 统一所有行的列数（补齐空单元格）
        for row in expanded_rows:
            while len(row) < max_cols:
                row.append('')
        
        # 分离表头和数据
        num_headers = len(header_lines)
        header_rows_expanded = expanded_rows[:num_headers]
        data_rows_expanded = expanded_rows[num_headers:]
        
        # === 第二步：生成DITA XML ===
        table_xml = ['<table>']
        
        if title:
            table_xml.append(f'  <title>{title}</title>')
        
        table_xml.append(f'  <tgroup cols="{max_cols}">')
        
        # colspec定义
        for col_idx in range(max_cols):
            table_xml.append(f'    <colspec colname="col{col_idx+1}"/>')
        
        # 表头：智能检测跨列合并
        if header_rows_expanded:
            table_xml.append('    <thead>')
            
            for header_row in header_rows_expanded:
                table_xml.append('      <row>')
                
                # 检测连续空单元格模式，用于跨列合并
                col_idx = 0
                while col_idx < max_cols:
                    cell = header_row[col_idx]
                    
                    if cell:
                        # 非空单元格：检查后续是否有空单元格（可能是跨列）
                        span = 1
                        while col_idx + span < max_cols and not header_row[col_idx + span]:
                            span += 1
                        
                        if span > 1:
                            namest = f"col{col_idx+1}"
                            nameend = f"col{col_idx+span}"
                            table_xml.append(f'        <entry namest="{namest}" nameend="{nameend}">{cell}</entry>')
                        else:
                            table_xml.append(f'        <entry>{cell}</entry>')
                        
                        col_idx += span
                    else:
                        # 空单元格
                        table_xml.append(f'        <entry/>')
                        col_idx += 1
                
                table_xml.append('      </row>')
            
            table_xml.append('    </thead>')
        
        # 表体
        if data_rows_expanded:
            table_xml.append('    <tbody>')
            
            for row in data_rows_expanded:
                table_xml.append('      <row>')
                for cell in row:
                    table_xml.append(f'        <entry>{cell if cell else ""}</entry>')
                table_xml.append('      </row>')
            
            table_xml.append('    </tbody>')
        
        table_xml.append('  </tgroup>')
        table_xml.append('</table>')
        
        return '\n'.join(table_xml)
    
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