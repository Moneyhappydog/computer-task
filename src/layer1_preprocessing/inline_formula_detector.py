"""
行内公式检测模块
基于版面解析结果，检测PDF中的行内公式（inline formulas）

本模块只做行内公式检测，不处理块级公式和OCR识别。
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
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

# 导入块级公式检测模块
try:
    from .block_formula_detector import BlockFormula
except ImportError:
    import sys
    from pathlib import Path
    import importlib.util
    
    current_file = Path(__file__)
    block_detector_path = current_file.parent / "block_formula_detector.py"
    
    if block_detector_path.exists():
        spec = importlib.util.spec_from_file_location("block_formula_detector", block_detector_path)
        block_formula_detector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(block_formula_detector)
        BlockFormula = block_formula_detector.BlockFormula
    else:
        BlockFormula = None


@dataclass
class InlineFormulaConfig:
    """行内公式检测的配置参数"""
    # 评分阈值
    min_span_score: float = 0.3  # span 被认为是候选公式的最低置信度
    min_group_score: float = 0.4  # 一个合并后公式 group 被保留的最低置信度
    
    # 合并参数
    max_horizontal_gap_factor: float = 1.5  # 合并相邻 span 时允许的水平间距比例（相对于平均字符宽度）
    
    # 数学符号集合
    math_symbols: Set[str] = field(default_factory=lambda: {
        # 希腊字母
        'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
        'Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ', 'Ν', 'Ξ', 'Ο', 'Π', 'Ρ', 'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω',
        # 集合/逻辑符号
        '∈', '∉', '⊂', '⊃', '⊆', '⊇', '∪', '∩', '∅', '∀', '∃', '∧', '∨', '¬',
        # 算术/关系运算符
        '≤', '≥', '≠', '≈', '≡', '∝', '±', '×', '÷', '·',
        # 其它数学符号
        '∞', '√', '∑', '∏', '∫', '∂', '∇', '→', '←', '↔', '⇒', '⇐', '↦',
        # 上下标字符
        '²', '³', '¹', '⁰', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹',
        '₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉',
        '⁺', '⁻', '⁼', '⁽', '⁾',
        '₊', '₋', '₌', '₍', '₎',
    })
    
    # 数学字体关键词
    math_font_keywords: List[str] = field(default_factory=lambda: [
        'math', 'cmr', 'cmsy', 'cmmi', 'cmex', 'symbol', 'cambriamath',
        'msam', 'msbm', 'cambria math'
    ])
    
    # 行内公式正则模式
    inline_regex_patterns: List[str] = field(default_factory=lambda: [
        # 函数调用: f(x), g(y,z), softmax(p)
        r'\b\w+\s*\([^()]+\)',
        # 条件概率: p(y|x), p(x|y)
        r'p\s*\([^|]+\|[^)]+\)',
        # 下标符号: L_{KD}, L_seg, p_i, x_t
        r'\b[A-Z]\s*_{[A-Za-z0-9]+}',
        r'\b[A-Z]_[A-Za-z0-9]+',
        r'\b\w+_[0-9A-Za-z]+\b',
        # 上标符号: p^o, x^2
        r'\b\w+\^[0-9A-Za-z]+\b',
        # 分数形式: a/b, x/y
        r'\b\w+\s*/\s*\w+\b',
        # 带括号的表达式: (x+y), [a,b]
        r'[\(\[][^\(\)\[\]]*[\)\]]',
    ])
    
    # 权重配置
    weight_math_symbols: float = 0.4  # 数学符号权重
    weight_regex_match: float = 0.3  # 正则匹配权重
    weight_math_font: float = 0.2  # 数学字体权重
    weight_subscript_superscript: float = 0.2  # 上下标权重
    weight_size_deviation: float = 0.1  # 字号偏离权重
    
    # 自然语言惩罚系数
    natural_language_penalty: float = 0.6  # 如果看起来像自然语言，分数乘以这个系数


@dataclass
class InlineFormula:
    """行内公式数据结构"""
    page_number: int
    block_index: int
    line_index: int
    span_indices: List[int]  # 在该行 TextLine.spans 中的下标
    bbox: Tuple[float, float, float, float]
    text: str  # 拼接后的原始公式字符串
    score: float  # 被判定为行内公式的置信度


@dataclass
class LineStats:
    """行的统计信息"""
    avg_size: float  # 平均字号
    size_std: float  # 字号标准差
    avg_y_center: float  # 平均 y 中心位置
    avg_char_width: float  # 平均字符宽度
    math_symbol_ratio: float  # 数学符号比例


class InlineFormulaDetector:
    """行内公式检测器"""
    
    def __init__(self, config: Optional[InlineFormulaConfig] = None):
        """
        初始化行内公式检测器
        
        Args:
            config: 配置参数，如果为 None 则使用默认配置
        """
        self.config = config or InlineFormulaConfig()
        
        # 编译正则表达式
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.config.inline_regex_patterns
        ]
        
        # 可以加入括号、逗号等符号，用于合并时"吃进"
        self.adjacent_symbols = set('()[]=,;:')
    
    def detect_inline_formulas(
        self,
        pages: List[PageLayout],
        block_formulas: Optional[List[BlockFormula]] = None,
    ) -> List[InlineFormula]:
        """
        检测所有页面中的行内公式
        
        Args:
            pages: 页面布局列表
            block_formulas: 块级公式列表（可选），用于避免重复检测
            
        Returns:
            检测到的行内公式列表
        """
        inline_formulas = []
        
        # 构建块级公式覆盖的行集合（用于快速查找）
        block_formula_lines = self._build_block_formula_line_set(block_formulas) if block_formulas else set()
        
        # 遍历每个页面
        for page in pages:
            page_inline_formulas = self._detect_inline_formulas_in_page(
                page, block_formula_lines
            )
            inline_formulas.extend(page_inline_formulas)
        
        return inline_formulas
    
    def _build_block_formula_line_set(
        self, block_formulas: List[BlockFormula]
    ) -> set:
        """
        构建块级公式覆盖的行集合，用于快速查找
        
        Returns:
            set of (page_number, block_index, line_index)
        """
        line_set = set()
        for bf in block_formulas:
            for line_idx in bf.line_indices:
                line_set.add((bf.page_number, bf.block_index, line_idx))
        return line_set
    
    def _detect_inline_formulas_in_page(
        self,
        page: PageLayout,
        block_formula_lines: set,
    ) -> List[InlineFormula]:
        """
        检测单个页面中的行内公式
        
        Args:
            page: 页面布局
            block_formula_lines: 块级公式覆盖的行集合
            
        Returns:
            该页面检测到的行内公式列表
        """
        inline_formulas = []
        
        # 遍历每个文本块
        for block_idx, block in enumerate(page.blocks):
            # 遍历块中的每一行
            for line_idx, line in enumerate(block.lines):
                # 跳过属于块级公式的行
                line_key = (page.page_number, block_idx, line_idx)
                if line_key in block_formula_lines:
                    continue
                
                # 检测该行中的行内公式
                line_formulas = self._detect_inline_formulas_in_line(
                    page.page_number, block_idx, line_idx, line
                )
                inline_formulas.extend(line_formulas)
        
        return inline_formulas
    
    def _detect_inline_formulas_in_line(
        self,
        page_number: int,
        block_index: int,
        line_index: int,
        line: TextLine,
    ) -> List[InlineFormula]:
        """
        检测单行中的行内公式
        
        Args:
            page_number: 页码
            block_index: 块索引
            line_index: 行索引
            line: 文本行
            
        Returns:
            该行检测到的行内公式列表
        """
        if not line.spans:
            return []
        
        # 计算行的统计信息
        line_stats = self._compute_line_stats(line)
        
        # 对每个 span 打分
        candidate_spans = []
        for span_idx, span in enumerate(line.spans):
            score = self._score_span_as_formula(span, line, line_stats)
            if score >= self.config.min_span_score:
                candidate_spans.append((span_idx, span, score))
        
        if not candidate_spans:
            return []
        
        # 按 x0 排序
        candidate_spans.sort(key=lambda x: x[1].bbox[0])
        
        # 合并相邻候选为公式组
        formula_groups = self._group_candidate_spans(candidate_spans, line, line_stats)
        
        # 构造 InlineFormula 对象
        inline_formulas = []
        for group in formula_groups:
            span_indices, spans, group_score = group
            
            if group_score >= self.config.min_group_score:
                # 计算合并后的 bbox
                bbox = self._merge_bboxes([s.bbox for s in spans])
                
                # 拼接文本（按 x0 排序）
                sorted_spans = sorted(zip(span_indices, spans), key=lambda x: x[1].bbox[0])
                text = ''.join(s.text for _, s in sorted_spans)
                
                formula = InlineFormula(
                    page_number=page_number,
                    block_index=block_index,
                    line_index=line_index,
                    span_indices=span_indices,
                    bbox=bbox,
                    text=text,
                    score=group_score
                )
                inline_formulas.append(formula)
        
        return inline_formulas
    
    def _compute_line_stats(self, line: TextLine) -> LineStats:
        """计算行的统计信息"""
        if not line.spans:
            return LineStats(0, 0, 0, 0, 0)
        
        sizes = [s.size for s in line.spans if s.size > 0]
        y_centers = [(s.bbox[1] + s.bbox[3]) / 2 for s in line.spans]
        widths = [s.bbox[2] - s.bbox[0] for s in line.spans]
        texts = [s.text for s in line.spans if s.text]
        
        # 计算平均字号
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        
        # 计算字号标准差
        if len(sizes) > 1:
            size_variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
            size_std = size_variance ** 0.5
        else:
            size_std = 0
        
        # 计算平均 y 中心
        avg_y_center = sum(y_centers) / len(y_centers) if y_centers else 0
        
        # 计算平均字符宽度（假设每个字符宽度相近）
        total_width = sum(widths)
        total_chars = sum(len(t) for t in texts)
        avg_char_width = total_width / total_chars if total_chars > 0 else 0
        
        # 计算数学符号比例
        all_text = ''.join(texts)
        math_char_count = sum(1 for c in all_text if c in self.config.math_symbols)
        math_symbol_ratio = math_char_count / len(all_text) if all_text else 0
        
        return LineStats(
            avg_size=avg_size,
            size_std=size_std,
            avg_y_center=avg_y_center,
            avg_char_width=avg_char_width,
            math_symbol_ratio=math_symbol_ratio
        )
    
    def _score_span_as_formula(
        self,
        span: TextSpan,
        line: TextLine,
        line_stats: LineStats,
    ) -> float:
        """
        对单个 span 计算"公式程度"分数
        
        Args:
            span: 文本片段
            line: 所在行
            line_stats: 行的统计信息
            
        Returns:
            分数 [0, 1]
        """
        if not span.text:
            return 0.0
        
        score = 0.0
        text = span.text
        
        # 1. 检查是否包含数学符号
        math_char_count = sum(1 for c in text if c in self.config.math_symbols)
        if math_char_count > 0:
            math_ratio = math_char_count / len(text)
            score += self.config.weight_math_symbols * min(1.0, math_ratio * 2)  # 放大影响
        
        # 2. 检查是否匹配正则模式
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                score += self.config.weight_regex_match
                break  # 只加一次分
        
        # 3. 检查字体
        font_lower = span.font.lower() if span.font else ''
        if any(keyword in font_lower for keyword in self.config.math_font_keywords):
            score += self.config.weight_math_font
        
        # 4. 检查上下标字符
        if any(c in text for c in '^_²³¹⁰⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉'):
            score += self.config.weight_subscript_superscript
        
        # 5. 检查字号偏离
        if line_stats.avg_size > 0 and span.size > 0:
            size_ratio = span.size / line_stats.avg_size
            # 如果字号明显偏小（可能是上下标）或偏大，加分
            if size_ratio < 0.8 or size_ratio > 1.2:
                score += self.config.weight_size_deviation
        
        # 6. 检查基线偏离（上下标）
        if line_stats.avg_y_center > 0:
            y_center = (span.bbox[1] + span.bbox[3]) / 2
            y_deviation = abs(y_center - line_stats.avg_y_center)
            # 如果偏离超过行高的 20%，可能是上下标
            line_height = line.bbox[3] - line.bbox[1]
            if line_height > 0 and y_deviation / line_height > 0.2:
                score += self.config.weight_size_deviation * 0.5
        
        # 7. 自然语言惩罚
        if self._looks_like_natural_language(text):
            score *= self.config.natural_language_penalty
        
        return min(1.0, max(0.0, score))
    
    def _looks_like_natural_language(self, text: str) -> bool:
        """
        判断文本是否看起来像自然语言
        
        Args:
            text: 文本内容
            
        Returns:
            True 如果看起来像自然语言
        """
        if not text:
            return False
        
        # 如果包含大量空格和常见英文单词，可能是自然语言
        words = text.split()
        if len(words) > 2:
            # 检查是否主要是字母和空格
            alpha_ratio = sum(1 for c in text if c.isalpha() or c.isspace()) / len(text)
            if alpha_ratio > 0.8:
                # 检查是否包含常见英文单词（简单启发式）
                common_words = {'the', 'and', 'or', 'is', 'are', 'was', 'were', 'for', 'with', 'from', 'to', 'of', 'in', 'on', 'at'}
                text_lower = text.lower()
                if any(word in text_lower for word in common_words):
                    return True
        
        return False
    
    def _group_candidate_spans(
        self,
        candidate_spans: List[Tuple[int, TextSpan, float]],
        line: TextLine,
        line_stats: LineStats,
    ) -> List[Tuple[List[int], List[TextSpan], float]]:
        """
        将候选 spans 合并为公式组
        
        Args:
            candidate_spans: 候选 span 列表，每个元素为 (span_idx, span, score)
            line: 所在行
            line_stats: 行的统计信息
            
        Returns:
            公式组列表，每个元素为 (span_indices, spans, group_score)
        """
        if not candidate_spans:
            return []
        
        groups = []
        current_group = [candidate_spans[0]]
        
        # 计算合并阈值（水平间距）
        max_gap = line_stats.avg_char_width * self.config.max_horizontal_gap_factor
        if max_gap <= 0:
            max_gap = 10.0  # 默认值
        
        for i in range(1, len(candidate_spans)):
            prev_span_idx, prev_span, prev_score = candidate_spans[i - 1]
            curr_span_idx, curr_span, curr_score = candidate_spans[i]
            
            # 计算水平间距
            gap = curr_span.bbox[0] - prev_span.bbox[2]
            
            if gap <= max_gap:
                # 可以合并
                current_group.append(candidate_spans[i])
            else:
                # 不能合并，保存当前组并开始新组
                group = self._finalize_group(current_group, line)
                if group:
                    groups.append(group)
                current_group = [candidate_spans[i]]
        
        # 处理最后一组
        if current_group:
            group = self._finalize_group(current_group, line)
            if group:
                groups.append(group)
        
        return groups
    
    def _finalize_group(
        self,
        group_spans: List[Tuple[int, TextSpan, float]],
        line: TextLine,
    ) -> Optional[Tuple[List[int], List[TextSpan], float]]:
        """
        完成一个公式组的构建，包括"吃进"相邻的括号、逗号等
        
        Args:
            group_spans: 组内的候选 spans
            line: 所在行
            
        Returns:
            (span_indices, spans, group_score) 或 None
        """
        if not group_spans:
            return None
        
        # 获取组的边界
        group_span_indices = {idx for idx, _, _ in group_spans}
        min_x = min(s.bbox[0] for _, s, _ in group_spans)
        max_x = max(s.bbox[2] for _, s, _ in group_spans)
        
        # 尝试"吃进"相邻的符号
        expanded_indices = set(group_span_indices)
        for span_idx, span in enumerate(line.spans):
            if span_idx in expanded_indices:
                continue
            
            span_x0, span_x1 = span.bbox[0], span.bbox[2]
            span_text = span.text.strip() if span.text else ''
            
            # 如果 span 是括号、逗号等，且紧挨着组，则加入
            if span_text in self.adjacent_symbols:
                gap_left = span_x0 - max_x
                gap_right = min_x - span_x1
                
                # 如果间距很小（小于平均字符宽度），加入组
                if gap_left >= 0 and gap_left < 5:  # 在右侧
                    expanded_indices.add(span_idx)
                    max_x = max(max_x, span_x1)
                elif gap_right >= 0 and gap_right < 5:  # 在左侧
                    expanded_indices.add(span_idx)
                    min_x = min(min_x, span_x0)
        
        # 获取所有 spans
        final_spans = []
        final_scores = []
        for span_idx in sorted(expanded_indices):
            span = line.spans[span_idx]
            final_spans.append(span)
            
            # 查找原始分数（如果是候选）或给默认分数
            score = 0.3  # 默认分数
            for orig_idx, orig_span, orig_score in group_spans:
                if orig_idx == span_idx:
                    score = orig_score
                    break
            final_scores.append(score)
        
        # 计算组分数（取平均值）
        group_score = sum(final_scores) / len(final_scores) if final_scores else 0.0
        
        return (sorted(expanded_indices), final_spans, group_score)
    
    def _merge_bboxes(self, bboxes: List[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
        """合并多个 bbox"""
        if not bboxes:
            return (0, 0, 0, 0)
        
        x0 = min(b[0] for b in bboxes)
        y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes)
        y1 = max(b[3] for b in bboxes)
        
        return (x0, y0, x1, y1)


# ============================================================================
# 命令行使用示例
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 导入版面解析模块
    try:
        from .formula_layout import PDFLayoutExtractor
        from .block_formula_detector import BlockFormulaDetector
    except ImportError:
        # 直接运行时
        import importlib.util
        
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        
        # 导入 formula_layout
        formula_layout_path = current_file.parent / "formula_layout.py"
        spec1 = importlib.util.spec_from_file_location("formula_layout", formula_layout_path)
        formula_layout = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(formula_layout)
        PDFLayoutExtractor = formula_layout.PDFLayoutExtractor
        
        # 导入 block_formula_detector
        block_detector_path = current_file.parent / "block_formula_detector.py"
        spec2 = importlib.util.spec_from_file_location("block_formula_detector", block_detector_path)
        block_formula_detector = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(block_formula_detector)
        BlockFormulaDetector = block_formula_detector.BlockFormulaDetector
    
    if len(sys.argv) < 2:
        print("用法: python inline_formula_detector.py <pdf_path>")
        print("示例: python inline_formula_detector.py mypaper.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        print(f"正在解析PDF并检测行内公式: {pdf_path}")
        
        # 1. 版面解析
        layout_extractor = PDFLayoutExtractor(pdf_path)
        pages = layout_extractor.parse()
        print(f"✓ 版面解析完成，共 {len(pages)} 页\n")
        
        # 2. 块级公式检测（可选）
        block_detector = BlockFormulaDetector()
        block_formulas = block_detector.detect_block_formulas(pages)
        print(f"✓ 块级公式检测完成，发现 {len(block_formulas)} 个块级公式\n")
        
        # 3. 行内公式检测
        inline_detector = InlineFormulaDetector()
        inline_formulas = inline_detector.detect_inline_formulas(pages, block_formulas)
        
        print(f"✓ 行内公式检测完成，发现 {len(inline_formulas)} 个行内公式\n")
        
        # 4. 显示结果
        print("=" * 70)
        print("检测结果（前20个）:")
        print("=" * 70)
        
        for i, formula in enumerate(inline_formulas[:20], 1):
            print(
                f"\n行内公式 {i}:"
                f"\n  [Page {formula.page_number} | Block {formula.block_index} | Line {formula.line_index}]"
                f"\n  score={formula.score:.3f}"
                f"\n  bbox=({formula.bbox[0]:.1f}, {formula.bbox[1]:.1f}, {formula.bbox[2]:.1f}, {formula.bbox[3]:.1f})"
                f"\n  span_indices={formula.span_indices}"
                f"\n  text={formula.text!r}"
            )
        
        if len(inline_formulas) > 20:
            print(f"\n... (还有 {len(inline_formulas) - 20} 个行内公式)")
        
        # 5. 统计信息
        print(f"\n{'=' * 70}")
        print("统计信息:")
        print("=" * 70)
        
        formulas_by_page = {}
        for f in inline_formulas:
            page_num = f.page_number
            formulas_by_page[page_num] = formulas_by_page.get(page_num, 0) + 1
        
        print(f"  总行内公式数: {len(inline_formulas)}")
        print(f"  包含行内公式的页数: {len(formulas_by_page)}")
        if pages:
            print(f"  平均每页行内公式数: {len(inline_formulas) / len(pages):.2f}")
        
        if formulas_by_page:
            print(f"\n  每页行内公式分布（前10页）:")
            for page_num in sorted(formulas_by_page.keys())[:10]:
                print(f"    Page {page_num}: {formulas_by_page[page_num]} 个")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



