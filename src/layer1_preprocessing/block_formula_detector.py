"""
块级公式检测模块
基于版面解析结果，检测PDF中的块级公式（display equations）

本模块只做块级公式检测，不处理行内公式和OCR识别。
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import re
from pathlib import Path

# 导入版面解析模块的结构
try:
    # 作为包导入
    from .formula_layout import PageLayout, TextBlock, TextLine, TextSpan
except ImportError:
    # 直接运行时的导入方式
    import sys
    from pathlib import Path
    import importlib.util
    
    # 查找 formula_layout 模块
    current_file = Path(__file__)
    formula_layout_path = current_file.parent / "formula_layout.py"
    
    if formula_layout_path.exists():
        spec = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
        formula_layout = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(formula_layout)
        PageLayout = formula_layout.PageLayout
        TextBlock = formula_layout.TextBlock
        TextLine = formula_layout.TextLine
        TextSpan = formula_layout.TextSpan
    else:
        raise ImportError(f"Cannot find formula_layout.py at {formula_layout_path}")


@dataclass
class BlockFormulaConfig:
    """块级公式检测的配置参数"""
    # 评分阈值
    min_block_score: float = 0.35  # 块级别公式的最小得分阈值（降低以检测更多公式）
    min_line_score: float = 0.45  # 行级别公式的最小得分阈值
    
    # 文本特征阈值
    min_math_char_ratio: float = 0.15  # 数学符号字符比例最小值
    min_digit_ratio: float = 0.05  # 数字比例最小值
    
    # 版式特征阈值
    center_tolerance: float = 20.0  # 居中判断的容差值（像素）
    gap_factor_for_isolation: float = 1.5  # 公式块上下间距应该是正文行距的倍数
    
    # 权重配置（用于评分函数）
    weight_math_char_ratio: float = 0.2  # 数学符号比例权重（降低，因为文本可能为空）
    weight_font: float = 0.4  # 字体特征权重（提高，因为字体信息最可靠）
    weight_centered: float = 0.2  # 居中特征权重
    weight_gap: float = 0.15  # 间距特征权重
    weight_line_count: float = 0.05  # 行数特征权重
    
    # 其他
    max_formula_lines: int = 10  # 单个公式块的最大行数


@dataclass
class BlockFormula:
    """块级公式数据结构"""
    page_number: int
    block_index: int
    line_indices: List[int]  # 该公式所覆盖的行索引列表
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    text: str  # 所有行文本拼接
    score: float  # 置信度（0-1）
    
    def __repr__(self):
        return (f"BlockFormula(page={self.page_number}, block={self.block_index}, "
                f"lines={self.line_indices}, score={self.score:.2f})")


class BlockFormulaDetector:
    """块级公式检测器"""
    
    def __init__(self, config: Optional[BlockFormulaConfig] = None):
        """
        初始化块级公式检测器
        
        Args:
            config: 配置参数，如果为None则使用默认配置
        """
        self.config = config or BlockFormulaConfig()
        
        # 数学符号集合（用于计算数学字符比例）
        self.math_chars = set('=+-*/^_[](){}<≤≥≠∑∫√∞∈∉⊂⊃∪∩∧∨¬→←↔∀∃∴∵αβγδεζηθικλμνξοπρστυφχψω'
                             'ΔΘΛΞΠΣΦΨΩ∂∇±×÷≤≥≠≈≡∝∞√∑∏∫∂∇∩∪∈∉⊂⊃⊆⊇∧∨¬→←↔∀∃')
        
        # 数学关键词（用于识别公式模式）- 使用原始字符串，反斜杠需要转义
        self.math_keywords = [
            r'\\sum', r'\\prod', r'\\int', r'\\frac', r'\\sqrt', r'\\log', r'\\exp',
            r'\\sin', r'\\cos', r'\\tan', r'\\max', r'\\min', r'\\lim', r'\\inf',
            r'L_', r'R_', r'f_', r'g_', r'h_', r'x_', r'y_', r'z_',
            r'\\mathcal', r'\\mathbb', r'\\mathbf', r'\\mathrm',
            r'\|\|', r'\\cdot', r'\\times'
        ]
        
        # 数学字体关键词
        self.math_font_keywords = [
            'math', 'cmr', 'cmmi', 'cmsy', 'symbol', 'cambriamath',
            'cmex', 'msam', 'msbm'
        ]
    
    def detect_block_formulas(self, pages: List[PageLayout]) -> List[BlockFormula]:
        """
        检测所有页面中的块级公式
        
        Args:
            pages: 所有页面的 PageLayout 列表
        
        Returns:
            检测到的块级公式列表
        """
        all_formulas = []
        
        for page in pages:
            page_formulas = self._detect_formulas_in_page(page)
            all_formulas.extend(page_formulas)
        
        return all_formulas
    
    def _detect_formulas_in_page(self, page: PageLayout) -> List[BlockFormula]:
        """
        检测单页中的块级公式
        
        Args:
            page: 页面布局结构
        
        Returns:
            该页检测到的块级公式列表
        """
        if not page.blocks:
            return []
        
        # 计算页面的平均行距（用于判断公式块的隔离程度）
        avg_line_gap = self._estimate_average_line_gap(page)
        
        formulas = []
        
        # 遍历每个文本块
        for block_idx, block in enumerate(page.blocks):
            # 计算块的公式得分
            block_score = self._score_block_as_formula(block, page, avg_line_gap)
            
            # 如果整个块得分足够高，认为整个块是公式
            if block_score >= self.config.min_block_score:
                formula = self._create_formula_from_block(
                    page.page_number, block_idx, block, block_score
                )
                formulas.append(formula)
            else:
                # 检查块内是否有单独的行是公式
                line_formulas = self._detect_formulas_in_block(
                    page.page_number, block_idx, block, page, avg_line_gap
                )
                formulas.extend(line_formulas)
        
        return formulas
    
    def _estimate_average_line_gap(self, page: PageLayout) -> float:
        """
        估算页面的平均行距
        
        Args:
            page: 页面布局结构
        
        Returns:
            平均行距（像素）
        """
        gaps = []
        
        for block in page.blocks:
            for i in range(len(block.lines) - 1):
                current_line = block.lines[i]
                next_line = block.lines[i + 1]
                
                gap = next_line.bbox[1] - current_line.bbox[3]  # next_line.y0 - current_line.y1
                if gap > 0:
                    gaps.append(gap)
        
        if not gaps:
            return 10.0  # 默认行距
        
        # 使用中位数作为平均行距（更稳健）
        gaps_sorted = sorted(gaps)
        median_idx = len(gaps_sorted) // 2
        return gaps_sorted[median_idx]
    
    def _score_block_as_formula(
        self, 
        block: TextBlock, 
        page: PageLayout, 
        avg_line_gap: float
    ) -> float:
        """
        计算文本块作为公式的得分
        
        Args:
            block: 文本块
            page: 页面布局
            avg_line_gap: 平均行距
        
        Returns:
            得分（0-1）
        """
        if not block.lines:
            return 0.0
        
        # 1. 文本特征
        block_text = self._get_block_text(block)
        text_features = self._extract_text_features(block_text)
        
        # 2. 字体特征
        font_features = self._extract_font_features(block)
        
        # 3. 版式特征
        layout_features = self._extract_layout_features(block, page, avg_line_gap)
        
        # 综合评分
        # 如果文本为空或很短，更依赖字体和版式特征
        block_text = self._get_block_text(block)
        has_text = block_text and len(block_text.strip()) > 0
        
        if has_text:
            # 有文本时，使用完整的特征评分
            score = (
                self.config.weight_math_char_ratio * text_features['math_char_ratio'] +
                self.config.weight_font * font_features['math_font_score'] +
                self.config.weight_centered * layout_features['centered_score'] +
                self.config.weight_gap * layout_features['gap_score'] +
                self.config.weight_line_count * layout_features['line_count_score']
            )
            
            # 如果包含明显的自然语言特征，降低分数
            if text_features['has_natural_language']:
                score *= 0.7
        else:
            # 无文本时，主要依赖字体特征和版式特征
            # 字体特征权重增加
            font_weight = self.config.weight_font * 2.0  # 字体权重翻倍
            score = (
                font_weight * font_features['math_font_score'] +
                self.config.weight_centered * layout_features['centered_score'] +
                self.config.weight_gap * layout_features['gap_score'] +
                self.config.weight_line_count * layout_features['line_count_score']
            )
            # 如果字体特征很强，直接给高分
            if font_features['math_font_score'] > 0.5:
                score = max(score, font_features['math_font_score'] * 0.8)
        
        return min(1.0, max(0.0, score))
    
    def _score_line_as_formula(
        self,
        line: TextLine,
        block: TextBlock,
        page: PageLayout
    ) -> float:
        """
        计算单行作为公式的得分
        
        Args:
            line: 文本行
            block: 所属文本块
            page: 页面布局
        
        Returns:
            得分（0-1）
        """
        # 文本特征
        text_features = self._extract_text_features(line.text)
        
        # 字体特征
        font_score = 0.0
        if line.spans:
            math_font_count = sum(
                1 for span in line.spans
                if self._is_math_font(span.font)
            )
            font_score = math_font_count / len(line.spans)
        
        # 版式特征（简化版，单行公式通常居中）
        centered_score = self._calculate_centered_score(line.bbox, page)
        
        # 综合评分（行级别更注重文本和字体特征）
        score = (
            0.5 * text_features['math_char_ratio'] +
            0.3 * font_score +
            0.2 * centered_score
        )
        
        if text_features['has_natural_language']:
            score *= 0.6
        
        return min(1.0, max(0.0, score))
    
    def _extract_text_features(self, text: str) -> dict:
        """
        提取文本特征
        
        Args:
            text: 文本内容
        
        Returns:
            特征字典
        """
        if not text:
            return {
                'math_char_ratio': 0.0,
                'digit_ratio': 0.0,
                'alpha_ratio': 0.0,
                'has_math_keywords': False,
                'has_natural_language': False
            }
        
        text_len = len(text)
        if text_len == 0:
            return {
                'math_char_ratio': 0.0,
                'digit_ratio': 0.0,
                'alpha_ratio': 0.0,
                'has_math_keywords': False,
                'has_natural_language': False
            }
        
        # 统计各类字符
        math_char_count = sum(1 for c in text if c in self.math_chars)
        digit_count = sum(1 for c in text if c.isdigit())
        alpha_count = sum(1 for c in text if c.isalpha())
        
        # 计算比例（归一化到0-1）
        math_char_ratio = min(1.0, math_char_count / text_len)
        digit_ratio = min(1.0, digit_count / text_len)
        alpha_ratio = min(1.0, alpha_count / text_len)
        
        # 检查数学关键词
        has_math_keywords = any(
            re.search(keyword, text, re.IGNORECASE)
            for keyword in self.math_keywords
        )
        
        # 检查是否为自然语言（简单启发式：包含常见英文单词）
        common_words = ['the', 'and', 'or', 'is', 'are', 'was', 'were', 'for', 'with']
        has_natural_language = any(
            word in text.lower() for word in common_words
        )
        
        # 如果数学字符比例高，提高分数
        if math_char_ratio > 0.3:
            math_char_ratio = min(1.0, math_char_ratio * 1.5)
        
        return {
            'math_char_ratio': math_char_ratio,
            'digit_ratio': digit_ratio,
            'alpha_ratio': alpha_ratio,
            'has_math_keywords': has_math_keywords,
            'has_natural_language': has_natural_language
        }
    
    def _extract_font_features(self, block: TextBlock) -> dict:
        """
        提取字体特征
        
        Args:
            block: 文本块
        
        Returns:
            字体特征字典
        """
        if not block.lines:
            return {'math_font_score': 0.0, 'avg_font_size': 0.0}
        
        total_spans = 0
        math_font_count = 0
        font_sizes = []
        
        for line in block.lines:
            for span in line.spans:
                total_spans += 1
                if self._is_math_font(span.font):
                    math_font_count += 1
                if span.size > 0:
                    font_sizes.append(span.size)
        
        math_font_score = math_font_count / total_spans if total_spans > 0 else 0.0
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0.0
        
        return {
            'math_font_score': math_font_score,
            'avg_font_size': avg_font_size
        }
    
    def _extract_layout_features(
        self,
        block: TextBlock,
        page: PageLayout,
        avg_line_gap: float
    ) -> dict:
        """
        提取版式特征
        
        Args:
            block: 文本块
            page: 页面布局
            avg_line_gap: 平均行距
        
        Returns:
            版式特征字典
        """
        # 居中得分
        centered_score = self._calculate_centered_score(block.bbox, page)
        
        # 行数得分（1-3行最佳）
        line_count = len(block.lines)
        if line_count == 0:
            line_count_score = 0.0
        elif 1 <= line_count <= 3:
            line_count_score = 1.0
        elif line_count <= 5:
            line_count_score = 0.7
        elif line_count <= self.config.max_formula_lines:
            line_count_score = 0.5
        else:
            line_count_score = 0.2
        
        # 间距得分（检查上下间距是否大于平均行距）
        gap_score = self._calculate_gap_score(block, page, avg_line_gap)
        
        # 块宽度比例
        block_width = block.bbox[2] - block.bbox[0]
        width_ratio = block_width / page.width if page.width > 0 else 1.0
        
        # 如果宽度明显小于页面宽度，可能是居中公式
        if width_ratio < 0.8:
            centered_score = min(1.0, centered_score * 1.2)
        
        return {
            'centered_score': centered_score,
            'gap_score': gap_score,
            'line_count_score': line_count_score,
            'width_ratio': width_ratio
        }
    
    def _calculate_centered_score(
        self,
        bbox: Tuple[float, float, float, float],
        page: PageLayout
    ) -> float:
        """
        计算是否居中的得分
        
        Args:
            bbox: 边界框
            page: 页面布局
        
        Returns:
            居中得分（0-1）
        """
        if page.width <= 0:
            return 0.0
        
        left_margin = bbox[0]
        right_margin = page.width - bbox[2]
        
        # 计算左右边距的差异
        margin_diff = abs(left_margin - right_margin)
        
        # 如果差异小于容差值，认为居中
        if margin_diff <= self.config.center_tolerance:
            return 1.0
        
        # 差异越大，得分越低
        normalized_diff = min(1.0, margin_diff / (page.width * 0.3))
        return 1.0 - normalized_diff
    
    def _calculate_gap_score(
        self,
        block: TextBlock,
        page: PageLayout,
        avg_line_gap: float
    ) -> float:
        """
        计算间距得分（公式块上下应该有较大间距）
        
        Args:
            block: 文本块
            page: 页面布局
            avg_line_gap: 平均行距
        
        Returns:
            间距得分（0-1）
        """
        if not page.blocks:
            return 0.5
        
        block_y0 = block.bbox[1]
        block_y1 = block.bbox[3]
        
        # 查找上一个和下一个块
        prev_block = None
        next_block = None
        
        for i, other_block in enumerate(page.blocks):
            if other_block == block:
                if i > 0:
                    prev_block = page.blocks[i - 1]
                if i < len(page.blocks) - 1:
                    next_block = page.blocks[i + 1]
                break
        
        gap_above = 0.0
        gap_below = 0.0
        
        if prev_block:
            gap_above = block_y0 - prev_block.bbox[3]
        else:
            gap_above = block_y0  # 页面顶部
        
        if next_block:
            gap_below = next_block.bbox[1] - block_y1
        else:
            gap_below = page.height - block_y1  # 页面底部
        
        # 判断间距是否显著大于平均行距
        threshold = avg_line_gap * self.config.gap_factor_for_isolation
        
        score = 0.0
        if gap_above >= threshold:
            score += 0.5
        if gap_below >= threshold:
            score += 0.5
        
        return score
    
    def _is_math_font(self, font_name: str) -> bool:
        """
        判断是否为数学字体
        
        Args:
            font_name: 字体名称
        
        Returns:
            是否为数学字体
        """
        if not font_name:
            return False
        
        font_lower = font_name.lower()
        return any(keyword in font_lower for keyword in self.math_font_keywords)
    
    def _get_block_text(self, block: TextBlock) -> str:
        """
        获取文本块的所有文本（拼接所有行）
        
        Args:
            block: 文本块
        
        Returns:
            拼接后的文本
        """
        texts = []
        for line in block.lines:
            if line.text:
                texts.append(line.text)
        return " ".join(texts)
    
    def _detect_formulas_in_block(
        self,
        page_number: int,
        block_idx: int,
        block: TextBlock,
        page: PageLayout,
        avg_line_gap: float
    ) -> List[BlockFormula]:
        """
        检测块内的单独公式行（混合块中的公式）
        
        Args:
            page_number: 页码
            block_idx: 块索引
            block: 文本块
            page: 页面布局
            avg_line_gap: 平均行距
        
        Returns:
            检测到的公式列表
        """
        formulas = []
        
        # 对每一行计算公式得分
        for line_idx, line in enumerate(block.lines):
            line_score = self._score_line_as_formula(line, block, page)
            
            if line_score >= self.config.min_line_score:
                # 创建单行公式
                formula = BlockFormula(
                    page_number=page_number,
                    block_index=block_idx,
                    line_indices=[line_idx],
                    bbox=line.bbox,
                    text=line.text or "",
                    score=line_score
                )
                formulas.append(formula)
        
        # 如果连续多行都是公式，尝试合并
        if len(formulas) > 1:
            formulas = self._merge_consecutive_formulas(formulas, block)
        
        return formulas
    
    def _merge_consecutive_formulas(
        self,
        formulas: List[BlockFormula],
        block: TextBlock
    ) -> List[BlockFormula]:
        """
        合并连续行的公式
        
        Args:
            formulas: 公式列表
            block: 所属文本块
        
        Returns:
            合并后的公式列表
        """
        if not formulas:
            return []
        
        # 按行索引排序
        formulas_sorted = sorted(formulas, key=lambda f: f.line_indices[0])
        
        merged = []
        current_formula = formulas_sorted[0]
        
        for next_formula in formulas_sorted[1:]:
            current_last = current_formula.line_indices[-1]
            next_first = next_formula.line_indices[0]
            
            # 如果行索引连续，合并
            if next_first == current_last + 1:
                # 合并行索引
                current_formula.line_indices.extend(next_formula.line_indices)
                
                # 合并bbox
                x0 = min(current_formula.bbox[0], next_formula.bbox[0])
                y0 = min(current_formula.bbox[1], next_formula.bbox[1])
                x1 = max(current_formula.bbox[2], next_formula.bbox[2])
                y1 = max(current_formula.bbox[3], next_formula.bbox[3])
                current_formula.bbox = (x0, y0, x1, y1)
                
                # 合并文本
                current_formula.text += "\n" + next_formula.text
                
                # 取平均得分
                current_formula.score = (current_formula.score + next_formula.score) / 2
            else:
                # 不连续，保存当前公式，开始新公式
                merged.append(current_formula)
                current_formula = next_formula
        
        merged.append(current_formula)
        return merged
    
    def _create_formula_from_block(
        self,
        page_number: int,
        block_idx: int,
        block: TextBlock,
        score: float
    ) -> BlockFormula:
        """
        从文本块创建公式对象
        
        Args:
            page_number: 页码
            block_idx: 块索引
            block: 文本块
            score: 公式得分
        
        Returns:
            BlockFormula对象
        """
        # 所有行的索引
        line_indices = list(range(len(block.lines)))
        
        # 合并所有行的文本
        texts = []
        for line in block.lines:
            if line.text:
                texts.append(line.text)
        text = "\n".join(texts)
        
        return BlockFormula(
            page_number=page_number,
            block_index=block_idx,
            line_indices=line_indices,
            bbox=block.bbox,
            text=text,
            score=score
        )


# ============================================================================
# 命令行使用示例
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 导入版面解析模块
    from .formula_layout import PDFLayoutExtractor
    
    if len(sys.argv) < 2:
        print("用法: python block_formula_detector.py <pdf_path>")
        print("示例: python block_formula_detector.py mypaper.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        print(f"正在解析PDF并检测块级公式: {pdf_path}")
        
        # 1. 版面解析
        layout_extractor = PDFLayoutExtractor(pdf_path)
        pages = layout_extractor.parse()
        print(f"✓ 版面解析完成，共 {len(pages)} 页\n")
        
        # 2. 公式检测
        detector = BlockFormulaDetector()
        formulas = detector.detect_block_formulas(pages)
        
        print(f"✓ 检测完成，共发现 {len(formulas)} 个块级公式\n")
        
        # 3. 显示结果
        print("=" * 70)
        print("检测结果（前10个）:")
        print("=" * 70)
        
        for i, formula in enumerate(formulas[:10]):
            print(f"\n公式 {i+1}:")
            print(f"  页码: {formula.page_number}")
            print(f"  块索引: {formula.block_index}")
            print(f"  行索引: {formula.line_indices}")
            print(f"  得分: {formula.score:.3f}")
            print(f"  边界框: ({formula.bbox[0]:.1f}, {formula.bbox[1]:.1f}, "
                  f"{formula.bbox[2]:.1f}, {formula.bbox[3]:.1f})")
            print(f"  文本预览: {formula.text[:100]!r}...")
        
        if len(formulas) > 10:
            print(f"\n... (还有 {len(formulas) - 10} 个公式)")
        
        # 4. 统计信息
        print(f"\n{'=' * 70}")
        print("统计信息:")
        print("=" * 70)
        
        formulas_by_page = {}
        for formula in formulas:
            page_num = formula.page_number
            if page_num not in formulas_by_page:
                formulas_by_page[page_num] = 0
            formulas_by_page[page_num] += 1
        
        print(f"  总公式数: {len(formulas)}")
        print(f"  包含公式的页数: {len(formulas_by_page)}")
        print(f"  平均每页公式数: {len(formulas) / len(pages):.2f}")
        
        if formulas_by_page:
            print(f"\n  每页公式分布:")
            for page_num in sorted(formulas_by_page.keys()):
                print(f"    Page {page_num}: {formulas_by_page[page_num]} 个")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

