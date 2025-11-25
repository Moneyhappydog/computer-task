"""
Step 1: 模板选择器
根据内容类型选择对应的DITA模板
"""
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TemplateSelector:
    """DITA模板选择器"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        初始化模板选择器
        
        Args:
            templates_dir: 模板目录路径，默认为当前模块下的templates/
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = templates_dir
        
        # 映射内容类型到模板文件
        self.template_map = {
            'Task': 'task.xml.j2',
            'Concept': 'concept.xml.j2',
            'Reference': 'reference.xml.j2'
        }
        
        # 验证模板文件存在
        self._validate_templates()
        
        logger.info(f"✅ 模板选择器初始化完成: {self.templates_dir}")
    
    def _validate_templates(self):
        """验证所有模板文件存在"""
        missing_templates = []
        
        for dita_type, template_file in self.template_map.items():
            template_path = self.templates_dir / template_file
            if not template_path.exists():
                missing_templates.append(template_file)
        
        if missing_templates:
            logger.warning(f"⚠️  缺失模板文件: {missing_templates}")
        else:
            logger.info(f"✓ 所有模板文件完整 ({len(self.template_map)} 个)")
    
    def select_template(self, content_type: str) -> Path:
        """
        选择对应的模板文件
        
        Args:
            content_type: 内容类型 (Task/Concept/Reference)
            
        Returns:
            模板文件路径
            
        Raises:
            ValueError: 如果内容类型不支持
            FileNotFoundError: 如果模板文件不存在
        """
        if content_type not in self.template_map:
            raise ValueError(
                f"不支持的内容类型: {content_type}. "
                f"支持的类型: {list(self.template_map.keys())}"
            )
        
        template_file = self.template_map[content_type]
        template_path = self.templates_dir / template_file
        
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        logger.info(f"📄 选择模板: {content_type} → {template_file}")
        
        return template_path
    
    def get_template_info(self, content_type: str) -> Dict:
        """
        获取模板信息
        
        Args:
            content_type: 内容类型
            
        Returns:
            模板信息字典
        """
        template_path = self.select_template(content_type)
        
        return {
            'type': content_type,
            'template_file': template_path.name,
            'template_path': str(template_path),
            'exists': template_path.exists(),
            'size': template_path.stat().st_size if template_path.exists() else 0
        }
    
    def list_available_templates(self) -> Dict[str, str]:
        """
        列出所有可用模板
        
        Returns:
            类型到模板文件的映射
        """
        return self.template_map.copy()


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    setup_logger("template_selector")
    
    selector = TemplateSelector()
    
    print("\n" + "="*70)
    print("可用模板:")
    print("="*70)
    
    for content_type, template_file in selector.list_available_templates().items():
        info = selector.get_template_info(content_type)
        print(f"\n{content_type}:")
        print(f"  文件: {info['template_file']}")
        print(f"  存在: {'✓' if info['exists'] else '✗'}")
        print(f"  大小: {info['size']} bytes")
    
    # 测试选择
    print("\n" + "="*70)
    print("测试选择:")
    print("="*70)
    
    for content_type in ['Task', 'Concept', 'Reference']:
        try:
            template_path = selector.select_template(content_type)
            print(f"✓ {content_type}: {template_path}")
        except Exception as e:
            print(f"✗ {content_type}: {e}")