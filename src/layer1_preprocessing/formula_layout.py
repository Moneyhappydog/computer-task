"""
PDF 版面解析模块
专门用于从 PDF 中提取干净的页面结构（块 / 行 / span），作为后续公式检测和 OCR 的基础。

本模块仅做版面解析，不包含公式识别和 OCR 功能。
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path
import fitz  # PyMuPDF


@dataclass
class TextSpan:
    """文本片段（span）"""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font: str
    size: float
    flags: int
    color: int
    
    def __repr__(self):
        return f"TextSpan(text={self.text[:20]!r}, bbox={self.bbox}, font={self.font}, size={self.size:.1f})"


@dataclass
class TextLine:
    """文本行"""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    spans: List[TextSpan] = field(default_factory=list)
    
    def __repr__(self):
        return f"TextLine(text={self.text[:30]!r}, bbox={self.bbox}, spans={len(self.spans)})"


@dataclass
class TextBlock:
    """文本块"""
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    lines: List[TextLine] = field(default_factory=list)
    
    def __repr__(self):
        return f"TextBlock(bbox={self.bbox}, lines={len(self.lines)})"


@dataclass
class PageLayout:
    """页面布局结构"""
    page_number: int
    width: float
    height: float
    blocks: List[TextBlock] = field(default_factory=list)
    
    def __repr__(self):
        return f"PageLayout(page={self.page_number}, size=({self.width:.1f}x{self.height:.1f}), blocks={len(self.blocks)})"


class PDFLayoutExtractor:
    """PDF 版面解析器"""
    
    def __init__(self, pdf_path: str, debug: bool = False):
        """
        初始化版面解析器
        
        Args:
            pdf_path: PDF 文件路径
            debug: 是否启用调试模式（输出详细信息）
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        self.debug = debug
    
    def parse(self) -> List[PageLayout]:
        """
        解析整个 PDF，返回每一页的 PageLayout 列表
        
        Returns:
            PageLayout 列表，每个元素对应一页
        """
        doc = fitz.open(str(self.pdf_path))
        pages = []
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_layout = self._parse_page(page, page_num + 1)
                pages.append(page_layout)
        finally:
            doc.close()
        
        return pages
    
    def _parse_page(self, page: fitz.Page, page_number: int) -> PageLayout:
        """
        解析单页
        
        Args:
            page: PyMuPDF 页面对象
            page_number: 页码（从1开始）
        
        Returns:
            PageLayout 对象
        """
        # 获取页面尺寸
        rect = page.rect
        width = rect.width
        height = rect.height
        
        # 优先使用 "dict" 格式，因为它直接有 "text" 字段
        # "rawdict" 格式只有 "chars" 字段，需要手动提取文本
        text_dict = page.get_text("dict")
        
        # 收集所有 spans
        all_spans = []
        
        # 遍历所有 blocks（包括文本块和非文本块）
        for block in text_dict.get("blocks", []):
            # 检查 block 类型：0=文本, 1=图片
            block_type = block.get("type", 0)
            
            # 只处理文本块
            if block_type != 0:
                continue
            
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                if "spans" not in line:
                    continue
                    
                for span in line["spans"]:
                    # 获取文本内容 - dict格式直接有text字段
                    text = span.get("text", "")
                    
                    # 处理None值：转换为空字符串
                    if text is None:
                        text = ""
                    
                    # 注意：这里不跳过空字符串，因为空格也是有效的文本内容
                    # 只有在bbox无效时才跳过
                    
                    # 提取 span 信息
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    
                    # 基本验证：确保 bbox 有4个元素
                    if len(bbox) < 4:
                        continue
                    
                    x0, y0, x1, y1 = bbox[0], bbox[1], bbox[2], bbox[3]
                    
                    # 验证 bbox 是否合理（允许非常小的区域，但宽度和高度必须 > 0）
                    if x1 <= x0 or y1 <= y0:
                        continue
                    
                    # 如果 bbox 太小（可能是噪声），也跳过
                    span_width = x1 - x0
                    span_height = y1 - y0
                    if span_width < 0.1 or span_height < 0.1:
                        continue
                    
                    font = span.get("font", "Unknown")
                    size = span.get("size", 0)
                    
                    # 允许字体大小为 0（某些特殊字符可能如此），但给出默认值
                    if size <= 0:
                        # 根据 bbox 高度估算字体大小
                        size = span_height * 0.8  # 粗略估算
                        if size <= 0:
                            size = 10.0  # 默认值
                    
                    flags = span.get("flags", 0)
                    color = span.get("color", 0)
                    
                    # 创建 TextSpan 对象 - 关键：确保text字段被正确赋值
                    text_span = TextSpan(
                        text=str(text) if text is not None else "",  # 确保text不为None
                        bbox=(float(x0), float(y0), float(x1), float(y1)),
                        font=str(font) if font else "Unknown",
                        size=float(size),
                        flags=int(flags),
                        color=int(color)
                    )
                    all_spans.append(text_span)
        
        # 调试信息
        if self.debug:
            total_blocks = len(text_dict.get("blocks", []))
            text_blocks = sum(1 for b in text_dict.get("blocks", []) if b.get("type", 0) == 0)
            non_empty_spans = sum(1 for s in all_spans if s.text and s.text.strip())
            print(f"  [调试] Page {page_number}: 总blocks={total_blocks}, 文本blocks={text_blocks}, "
                  f"提取到spans={len(all_spans)}, 非空spans={non_empty_spans}")
        
        # 将 spans 聚类成行
        lines = self._group_spans_into_lines(all_spans)
        
        if self.debug:
            print(f"  [调试] Page {page_number}: 聚类成 {len(lines)} 行")
        
        # 将行聚类成块
        blocks = self._group_lines_into_blocks(lines)
        
        if self.debug:
            print(f"  [调试] Page {page_number}: 聚类成 {len(blocks)} 个文本块")
        
        # 创建 PageLayout
        return PageLayout(
            page_number=page_number,
            width=width,
            height=height,
            blocks=blocks
        )
    
    def _group_spans_into_lines(self, spans: List[TextSpan]) -> List[TextLine]:
        """
        将 spans 聚类成 TextLine
        
        算法思路：
        1. 计算每个 span 的垂直中心位置
        2. 按垂直中心排序
        3. 使用动态阈值（基于字体大小）判断是否属于同一行
        4. 行内按 x 坐标排序 spans
        
        Args:
            spans: TextSpan 列表
        
        Returns:
            TextLine 列表
        """
        if not spans:
            return []
        
        # 计算每个 span 的垂直中心，并添加索引以便后续排序
        spans_with_y_center = []
        for span in spans:
            y0, y1 = span.bbox[1], span.bbox[3]
            y_center = (y0 + y1) / 2
            spans_with_y_center.append((y_center, span))
        
        # 按垂直中心升序排序
        spans_with_y_center.sort(key=lambda x: x[0])
        
        # 计算平均字体大小（用于动态阈值）
        avg_font_size = sum(s.size for s in spans) / len(spans) if spans else 10.0
        
        # 聚类成行
        lines = []
        current_line_spans = []
        current_line_y_center = None
        
        for y_center, span in spans_with_y_center:
            if current_line_y_center is None:
                # 第一行
                current_line_spans = [span]
                current_line_y_center = y_center
            else:
                # 计算阈值：max(1.5, 0.4 * 平均字体大小)
                threshold = max(1.5, 0.4 * avg_font_size)
                
                # 判断是否属于当前行
                if abs(y_center - current_line_y_center) < threshold:
                    current_line_spans.append(span)
                    # 更新当前行的平均 y_center（加权平均）
                    current_line_y_center = (
                        current_line_y_center * (len(current_line_spans) - 1) + y_center
                    ) / len(current_line_spans)
                else:
                    # 创建新行
                    if current_line_spans:
                        line = self._create_line_from_spans(current_line_spans)
                        lines.append(line)
                    current_line_spans = [span]
                    current_line_y_center = y_center
        
        # 处理最后一行
        if current_line_spans:
            line = self._create_line_from_spans(current_line_spans)
            lines.append(line)
        
        return lines
    
    def _create_line_from_spans(self, spans: List[TextSpan]) -> TextLine:
        """
        从 spans 创建 TextLine
        
        Args:
            spans: 属于同一行的 TextSpan 列表
        
        Returns:
            TextLine 对象
        """
        # 按 x0 排序 spans
        spans_sorted = sorted(spans, key=lambda s: s.bbox[0])
        
        # 计算行的 bbox（所有 spans bbox 的并集）
        x0_min = min(s.bbox[0] for s in spans_sorted)
        y0_min = min(s.bbox[1] for s in spans_sorted)
        x1_max = max(s.bbox[2] for s in spans_sorted)
        y1_max = max(s.bbox[3] for s in spans_sorted)
        
        # 拼接文本（直接拼接，不添加额外空格，因为span之间可能已经有间距信息）
        # 注意：如果span.text为空字符串（空格），也要保留
        text = "".join(s.text if s.text else " " for s in spans_sorted)
        
        return TextLine(
            text=text,
            bbox=(x0_min, y0_min, x1_max, y1_max),
            spans=spans_sorted
        )
    
    def _group_lines_into_blocks(self, lines: List[TextLine]) -> List[TextBlock]:
        """
        将行聚类成 TextBlock
        
        算法思路：
        1. 按 y0 排序所有行
        2. 计算正文平均行距
        3. 使用动态阈值判断行是否属于同一块
        
        Args:
            lines: TextLine 列表
        
        Returns:
            TextBlock 列表
        """
        if not lines:
            return []
        
        # 按 y0 升序排序
        lines_sorted = sorted(lines, key=lambda l: l.bbox[1])
        
        # 计算正文平均行距
        vertical_gaps = []
        for i in range(len(lines_sorted) - 1):
            current_line = lines_sorted[i]
            next_line = lines_sorted[i + 1]
            gap = next_line.bbox[1] - current_line.bbox[3]  # next_line.y0 - current_line.y1
            if gap > 0:  # 只统计正的行距
                vertical_gaps.append(gap)
        
        # 使用中位数作为平均行距（比均值更稳健）
        if vertical_gaps:
            vertical_gaps_sorted = sorted(vertical_gaps)
            median_idx = len(vertical_gaps_sorted) // 2
            avg_line_gap = vertical_gaps_sorted[median_idx]
        else:
            # 如果没有行距数据，使用默认值
            avg_line_gap = 5.0
        
        # 聚类成块
        blocks = []
        current_block_lines = []
        
        for i, line in enumerate(lines_sorted):
            if not current_block_lines:
                # 第一个块
                current_block_lines = [line]
            else:
                # 计算与当前块最后一行的垂直间距
                last_line = current_block_lines[-1]
                vertical_gap = line.bbox[1] - last_line.bbox[3]
                
                # 阈值：1.5 * 平均行距
                threshold = 1.5 * avg_line_gap
                
                if vertical_gap < threshold:
                    # 属于当前块
                    current_block_lines.append(line)
                else:
                    # 创建新块
                    if current_block_lines:
                        block = self._create_block_from_lines(current_block_lines)
                        blocks.append(block)
                    current_block_lines = [line]
        
        # 处理最后一个块
        if current_block_lines:
            block = self._create_block_from_lines(current_block_lines)
            blocks.append(block)
        
        return blocks
    
    def _create_block_from_lines(self, lines: List[TextLine]) -> TextBlock:
        """
        从行创建 TextBlock
        
        Args:
            lines: 属于同一块的 TextLine 列表
        
        Returns:
            TextBlock 对象
        """
        # 计算块的 bbox（所有行 bbox 的并集）
        x0_min = min(l.bbox[0] for l in lines)
        y0_min = min(l.bbox[1] for l in lines)
        x1_max = max(l.bbox[2] for l in lines)
        y1_max = max(l.bbox[3] for l in lines)
        
        return TextBlock(
            bbox=(x0_min, y0_min, x1_max, y1_max),
            lines=lines
        )


# ============================================================================
# 命令行调试示例
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python formula_layout.py <pdf_path>")
        print("示例: python formula_layout.py mypaper.pdf")
        print("示例: python formula_layout.py \"E:\\path\\to\\paper.pdf\"")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        print(f"正在解析 PDF: {pdf_path}")
        extractor = PDFLayoutExtractor(pdf_path, debug=True)
        pages = extractor.parse()
        
        print(f"\n解析完成！共 {len(pages)} 页\n")
        
        # 统计非空span比例
        total_spans = 0
        non_empty_spans = 0
        for p in pages:
            for b in p.blocks:
                for ln in b.lines:
                    for sp in ln.spans:
                        total_spans += 1
                        if sp.text and sp.text.strip():
                            non_empty_spans += 1
        
        print(f"统计信息:")
        print(f"  总span数: {total_spans}")
        print(f"  非空span数: {non_empty_spans}")
        if total_spans > 0:
            ratio = non_empty_spans / total_spans
            print(f"  非空比例: {ratio:.1%}")
        print()
        
        # 简单打印前几页、前几个 block/line 的结构
        for page in pages[:2]:
            print(f"=== Page {page.page_number} ({page.width:.1f} x {page.height:.1f}) ===")
            print(f"  共 {len(page.blocks)} 个文本块\n")
            
            for bi, block in enumerate(page.blocks[:5]):
                print(f"  [Block {bi}] bbox={block.bbox}")
                print(f"    包含 {len(block.lines)} 行")
                
                for li, line in enumerate(block.lines[:5]):
                    print(f"      (Line {li}) bbox={line.bbox}")
                    print(f"        text={line.text[:80]!r}")
                    print(f"        spans={len(line.spans)}")
                    
                    # 可选：显示前几个 span 的详细信息
                    if line.spans and li == 0:  # 只显示第一行的前3个span
                        for si, span in enumerate(line.spans[:3]):
                            print(f"          Span {si}: {span.text[:30]!r} "
                                  f"(font={span.font}, size={span.size:.1f})")
                
                if len(block.lines) > 5:
                    print(f"      ... (还有 {len(block.lines) - 5} 行)")
                print()
            
            if len(page.blocks) > 5:
                print(f"  ... (还有 {len(page.blocks) - 5} 个块)")
            print()
        
        if len(pages) > 2:
            print(f"... (还有 {len(pages) - 2} 页)")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

