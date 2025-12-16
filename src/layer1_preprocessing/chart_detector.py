"""
图表检测器
识别图表内容并过滤OCR乱码
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class ChartDetector:
    """图表检测与过滤器"""
    
    def __init__(self):
        """初始化图表检测器"""
        # 图表特征模式
        self.chart_patterns = [
            # 散落的数字（坐标轴）
            r'^\d+[\s\n]+\d+[\s\n]+\d+',
            # 单个孤立的数字行
            r'^\d{1,5}$',
            # 图表常见词
            r'(图|Fig|Figure|Chart|Graph)\s*\d+',
            # 刻度标签
            r'^\d+[,\s]+\d+[,\s]+\d+',
        ]
        
        logger.info("✅ 图表检测器初始化完成")
    
    def is_chart_text(self, text: str) -> bool:
        """
        判断文本是否是图表OCR产生的乱码
        
        特征：
        1. 大量单个数字行
        2. 散落的坐标轴数字
        3. 文本密度低（字符少但行数多）
        4. 缺乏连贯的句子结构
        
        Args:
            text: 文本内容
        
        Returns:
            True 表示是图表文本，False 表示是正常文本
        """
        if not text or len(text.strip()) < 5:
            return False
        
        lines = text.strip().split('\n')
        if len(lines) < 3:
            return False
        
        # 特征1: 单数字行占比
        single_number_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped and stripped.replace(',', '').replace('.', '').isdigit():
                single_number_lines += 1
        
        single_number_ratio = single_number_lines / len(lines)
        if single_number_ratio > 0.4:  # 超过40%是单数字行
            logger.debug(f"检测到图表文本 (单数字行比例: {single_number_ratio:.2f})")
            return True
        
        # 特征2: 平均每行字符数
        total_chars = sum(len(line.strip()) for line in lines)
        avg_chars_per_line = total_chars / len(lines)
        if avg_chars_per_line < 5:  # 平均每行少于5个字符
            logger.debug(f"检测到图表文本 (平均每行字符数: {avg_chars_per_line:.1f})")
            return True
        
        # 特征3: 包含典型图表标记
        for pattern in self.chart_patterns:
            if re.search(pattern, text, re.MULTILINE):
                logger.debug(f"检测到图表文本 (匹配模式: {pattern})")
                return True
        
        # 特征4: 非标点符号的单字符行占比
        single_char_lines = 0
        for line in lines:
            stripped = line.strip()
            if len(stripped) == 1 and not stripped in '，。、；：""''！？':
                single_char_lines += 1
        
        if single_char_lines / len(lines) > 0.3:
            logger.debug(f"检测到图表文本 (单字符行占比: {single_char_lines/len(lines):.2f})")
            return True
        
        return False
    
    def clean_markdown(self, markdown: str, image_mapping: Dict[str, str]) -> str:
        """
        清理Markdown中的图表OCR乱码
        
        策略：
        1. 检测图片引用附近的文本块
        2. 判断是否是图表OCR乱码
        3. 删除乱码，保留图片引用
        
        Args:
            markdown: 原始Markdown文本
            image_mapping: 图片映射 {'image_name': 'path'}
        
        Returns:
            清理后的Markdown文本
        """
        if not image_mapping:
            return markdown
        
        logger.info(f"开始清理图表OCR乱码...")
        
        lines = markdown.split('\n')
        cleaned_lines = []
        i = 0
        removed_blocks = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 检测图片引用
            if re.match(r'!\[.*?\]\(.*?\)', line):
                # 找到图片引用，检查前后文本
                cleaned_lines.append(line)
                
                # 收集图片后的文本块（直到遇到空行或下一个图片）
                text_block = []
                j = i + 1
                while j < len(lines) and lines[j].strip() and not re.match(r'!\[.*?\]\(.*?\)', lines[j]):
                    text_block.append(lines[j])
                    j += 1
                
                # 判断是否是图表乱码
                if text_block:
                    block_text = '\n'.join(text_block)
                    if self.is_chart_text(block_text):
                        logger.debug(f"移除图表乱码块 (行 {i+1}-{j})")
                        removed_blocks += 1
                        i = j  # 跳过这个文本块
                        continue
                
                cleaned_lines.extend(text_block)
                i = j
            else:
                cleaned_lines.append(line)
                i += 1
        
        result = '\n'.join(cleaned_lines)
        
        if removed_blocks > 0:
            logger.success(f"✓ 清理完成: 移除了 {removed_blocks} 个图表乱码块")
        else:
            logger.info("未检测到图表乱码")
        
        return result
    
    def filter_chart_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        过滤页面中的图表OCR文本
        
        Args:
            pages: 页面列表 [{'page': 1, 'text': '...', 'images': [...]}, ...]
        
        Returns:
            过滤后的页面列表
        """
        filtered_pages = []
        
        for page in pages:
            page_text = page.get('text', '')
            
            # 如果整页都是图表（有图片且文本是乱码）
            if page.get('images') and self.is_chart_text(page_text):
                logger.debug(f"页面 {page.get('page')} 为图表页，清空OCR文本")
                filtered_page = page.copy()
                filtered_page['text'] = f"![图表]({page['images'][0]})" if page['images'] else ""
                filtered_pages.append(filtered_page)
            else:
                filtered_pages.append(page)
        
        return filtered_pages


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.logger import setup_logger
    
    setup_logger("chart_detector")
    
    detector = ChartDetector()
    
    # 测试1: 图表乱码
    chart_text = """
    100
    200
    300
    400
    500
    
    X轴
    Y轴
    
    数据1
    数据2
    """
    
    print("测试1: 图表乱码")
    print(f"是否是图表: {detector.is_chart_text(chart_text)}")
    
    # 测试2: 正常文本
    normal_text = """
    这是一段正常的文本内容。
    它包含完整的句子结构。
    文字是连贯的，有实际含义。
    不是散落的数字和标签。
    """
    
    print("\n测试2: 正常文本")
    print(f"是否是图表: {detector.is_chart_text(normal_text)}")
    
    # 测试3: 清理Markdown
    test_markdown = """
# 文档标题

这是正常文本。

![图表1](../images/chart1.png)

100
200
300
X轴
Y轴

这是另一段正常文本。

![图表2](../images/chart2.png)

50
150
250

正常结尾文本。
"""
    
    print("\n测试3: 清理Markdown")
    cleaned = detector.clean_markdown(test_markdown, {'chart1': '../images/chart1.png', 'chart2': '../images/chart2.png'})
    print("清理后的Markdown:")
    print(cleaned)
