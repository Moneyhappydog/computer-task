"""
Step 4: 模板渲染器
使用Jinja2将结构化数据填充到DITA模板
"""
from pathlib import Path
from typing import Dict, Any
import logging
from jinja2 import Environment, FileSystemLoader, Template, TemplateError
import re

from .errors import TemplateError, DITAConversionError

logger = logging.getLogger(__name__)

class TemplateRenderer:
    """DITA模板渲染器"""
    
    def __init__(self, templates_dir: Path = None):
        """
        初始化模板渲染器
        
        Args:
            templates_dir: 模板目录路径
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = templates_dir
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # XML需要手动控制转义
        )
        
        # 添加自定义过滤器
        self.env.filters['escape_xml'] = self._escape_xml
        self.env.filters['format_id'] = self._format_id
        
        logger.info(f"✅ 模板渲染器初始化完成: {templates_dir}")
    
    def render(
        self,
        template_name: str,
        data: Dict[str, Any],
        auto_escape: bool = True
    ) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板文件名
            data: 数据字典
            auto_escape: 是否自动转义XML特殊字符
            
        Returns:
            渲染后的XML字符串
        """
        logger.info(f"🎨 渲染模板: {template_name}")
        
        try:
            # 加载模板
            template = self.env.get_template(template_name)
            
            # 预处理数据（自动转义）
            if auto_escape:
                data = self._escape_data(data)
            
            # 渲染
            xml_content = template.render(**data)
            
            # 后处理
            xml_content = self._post_process(xml_content)
            
            logger.info(f"✅ 模板渲染完成: {len(xml_content)} 字符")
            
            return xml_content
            
        except TemplateError as e:
            logger.error(f"❌ 模板渲染失败: {e}")
            raise TemplateError(
                f"模板渲染失败: {str(e)}",
                "TEMPLATE_RENDERING_FAILED",
                details={"template_name": template_name, "error": str(e)}
            )
    
    def render_task(self, data: Dict) -> str:
        """渲染Task类型"""
        return self.render('task.xml.j2', data)
    
    def render_concept(self, data: Dict) -> str:
        """渲染Concept类型"""
        return self.render('concept.xml.j2', data)
    
    def render_reference(self, data: Dict) -> str:
        """渲染Reference类型"""
        return self.render('reference.xml.j2', data)
    
    def _escape_data(self, data: Any) -> Any:
        """
        递归转义数据中的XML特殊字符
        
        Args:
            data: 原始数据
            
        Returns:
            转义后的数据
        """
        if isinstance(data, str):
            return self._escape_xml(data)
        elif isinstance(data, dict):
            return {k: self._escape_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._escape_data(item) for item in data]
        else:
            return data
    
    def _escape_xml(self, text: str) -> str:
        """
        转义XML特殊字符,但保留有效的DITA标签
        
        Args:
            text: 原始文本
            
        Returns:
            转义后的文本
        """
        if not isinstance(text, str):
            return text
        
        # 定义允许的DITA标签模式
        # 这些标签不会被转义
        allowed_tags = [
            r'<table[^>]*>[\s\S]*?</table>',  # table标签（必须先匹配，包含换行）
            r'<fig[^>]*>[\s\S]*?</fig>',  # figure标签（必须先匹配，包含换行）
            r'<p>.*?</p>',  # p标签（段落标签，必须在table和fig之后匹配）
            r'<codeblock[^>]*>[\s\S]*?</codeblock>',  # codeblock标签（用于公式）
            r'<equation-inline>.*?</equation-inline>',  # 行内公式标签
            r'<equation-block>[\s\S]*?</equation-block>',  # 块级公式标签
            r'<tgroup[^>]*>[\s\S]*?</tgroup>',  # tgroup标签
            r'<thead>[\s\S]*?</thead>',  # thead标签
            r'<tbody>[\s\S]*?</tbody>',  # tbody标签
            r'<row>[\s\S]*?</row>',  # row标签
            r'<entry[^>]*>.*?</entry>',  # entry标签
            r'<entry[^>]*/>',  # 自闭合entry标签
            r'<title>.*?</title>',  # title标签（用于表格标题）
            r'<image\s+[^>]*/>',  # 自闭合image标签
            r'<image\s+[^>]*>.*?</image>',  # 成对的image标签
            r'<b>.*?</b>',  # 粗体
            r'<i>.*?</i>',  # 斜体
            r'<ph>.*?</ph>',  # phrase
            r'<xref\s+[^>]*>.*?</xref>',  # 交叉引用
        ]
        
        # 提取所有允许的标签,用占位符替换
        placeholders = {}
        counter = 0
        
        for pattern in allowed_tags:
            for match in re.finditer(pattern, text, re.DOTALL):
                placeholder = f"__DITA_TAG_{counter}__"
                placeholders[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder, 1)
                counter += 1
        
        # 转义剩余的特殊字符
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;'
        }
        
        for char, escape in replacements.items():
            text = text.replace(char, escape)
        
        # 恢复占位符为原始标签
        for placeholder, original_tag in placeholders.items():
            text = text.replace(placeholder, original_tag)
        
        return text
    
    def _format_id(self, text: str) -> str:
        """
        格式化为符合DITA规范的ID
        
        Args:
            text: 原始文本
            
        Returns:
            格式化后的ID
        """
        # 转小写
        id_str = text.lower()
        
        # 移除特殊字符
        id_str = re.sub(r'[^a-z0-9\s_-]', '', id_str)
        
        # 空格替换为下划线
        id_str = re.sub(r'\s+', '_', id_str)
        
        # 移除首尾下划线
        id_str = id_str.strip('_')
        
        # 确保以字母开头
        if id_str and not id_str[0].isalpha():
            id_str = 'id_' + id_str
        
        return id_str or 'unnamed'
    
    def _post_process(self, xml_content: str) -> str:
        """
        后处理XML内容
        
        Args:
            xml_content: 原始XML
            
        Returns:
            处理后的XML
        """
        # 移除多余的空行
        xml_content = re.sub(r'\n\s*\n\s*\n', '\n\n', xml_content)
        
        # 确保XML声明在第一行
        if not xml_content.startswith('<?xml'):
            # 模板中已包含，这里不需要重复添加
            pass
        
        # 移除行尾空格
        lines = xml_content.split('\n')
        lines = [line.rstrip() for line in lines]
        xml_content = '\n'.join(lines)
        
        return xml_content
    
    def preview_template(self, template_name: str) -> str:
        """
        预览模板内容
        
        Args:
            template_name: 模板文件名
            
        Returns:
            模板内容
        """
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            raise TemplateError(
                f"模板不存在: {template_path}",
                "TEMPLATE_NOT_FOUND",
                details={"template_name": template_name, "path": str(template_path)}
            )
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    import json
    
    setup_logger("template_renderer")
    
    renderer = TemplateRenderer()
    
    # 测试Task渲染
    print("\n" + "="*70)
    print("测试 Task 渲染")
    print("="*70)
    
    task_data = {
        'task_id': 'task_install_python',
        'title': 'Installing Python',
        'short_description': 'Learn how to install Python on your system',
        'prerequisites': [
            'Administrator privileges',
            '20MB free disk space'
        ],
        'context': 'Python is required for running the application',
        'steps': [
            {
                'cmd': 'Download Python from python.org',
                'info': 'Choose the version matching your operating system'
            },
            {
                'cmd': 'Run the installer',
                'info': 'Make sure to check "Add Python to PATH"',
                'example': 'python-3.11.0-installer.exe'
            },
            {
                'cmd': 'Verify the installation',
                'info': 'Open a terminal and run: python --version'
            }
        ],
        'result': 'Python is now installed and ready to use'
    }
    
    try:
        xml = renderer.render_task(task_data)
        print(xml)
        
        # 保存到文件
        output_file = Path("data/output/test_task.dita")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"\n✅ 已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 渲染失败: {e}")
    
    # 测试Concept渲染
    print("\n" + "="*70)
    print("测试 Concept 渲染")
    print("="*70)
    
    concept_data = {
        'concept_id': 'concept_cloud_computing',
        'title': 'Cloud Computing',
        'short_description': 'Understanding cloud computing technology',
        'introduction': 'Cloud computing is the delivery of computing services over the internet.',
        'definition': 'A model for enabling ubiquitous, on-demand access to shared computing resources.',
        'sections': [
            {
                'id': 'characteristics',
                'title': 'Key Characteristics',
                'content': 'Cloud computing offers on-demand self-service, broad network access, and rapid elasticity.'
            },
            {
                'id': 'models',
                'title': 'Service Models',
                'content': 'Common models include Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS).',
                'example': 'AWS EC2 is an example of IaaS.'
            }
        ],
        'note': 'Cloud computing has revolutionized how organizations manage IT resources.'
    }
    
    try:
        xml = renderer.render_concept(concept_data)
        print(xml)
        
        output_file = Path("data/output/test_concept.dita")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"\n✅ 已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 渲染失败: {e}")