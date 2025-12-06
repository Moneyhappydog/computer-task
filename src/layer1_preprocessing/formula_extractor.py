"""
公式提取器
从 PDF 文档中提取公式图片，并使用 OCR 转换为 LaTeX 代码
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import re
from PIL import Image
import io
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class FormulaExtractor:
    """公式提取与 LaTeX 转换器"""
    
    def __init__(self, output_base_dir: Path = None, use_ocr: bool = True):
        """
        初始化公式提取器
        
        Args:
            output_base_dir: 公式图片输出根目录，默认为 data/output
            use_ocr: 是否使用 OCR 将公式转换为 LaTeX（需要安装 pix2tex）
        """
        if output_base_dir is None:
            from src.utils.config import Config
            output_base_dir = Config.OUTPUT_DIR
        
        self.output_base_dir = Path(output_base_dir)
        self.use_ocr = use_ocr
        
        # 尝试导入 pix2tex
        self.ocr_model = None
        if use_ocr:
            try:
                from pix2tex.cli import LatexOCR
                self.ocr_model = LatexOCR()
                logger.info("✅ LaTeX OCR 模型加载成功")
            except ImportError:
                logger.warning("⚠️ pix2tex 未安装，无法进行公式 OCR")
                logger.warning("安装命令: pip install pix2tex")
                self.use_ocr = False
            except Exception as e:
                logger.warning(f"⚠️ LaTeX OCR 模型加载失败: {e}")
                self.use_ocr = False
        
        logger.info("✅ 公式提取器初始化完成")
    
    def extract_formulas_from_pdf(
        self,
        pdf_path: Path,
        doc_name: str,
        min_formula_height: int = 15,
        min_formula_width: int = 30
    ) -> Dict[str, Any]:
        """
        从 PDF 中提取公式图片
        
        Args:
            pdf_path: PDF 文件路径
            doc_name: 文档名称（不含扩展名），用作文件夹名
            min_formula_height: 最小公式高度（像素），用于过滤噪声
            min_formula_width: 最小公式宽度（像素）
        
        Returns:
            {
                'formula_mapping': {'page2_formula3': '../formulas/page2_formula3.png', ...},
                'formula_latex': {'page2_formula3': '\\frac{a}{b}', ...},
                'formula_dir': '/absolute/path/to/formulas',
                'total_formulas': 10,
                'saved_formulas': 10,
                'ocr_success': 8,
                'ocr_failed': 2
            }
        """
        logger.info(f"开始提取公式: PDF={pdf_path}, 文档={doc_name}")
        
        # 创建公式输出目录: data/output/{doc_name}/formulas
        formula_dir = self.output_base_dir / doc_name / "formulas"
        formula_dir.mkdir(parents=True, exist_ok=True)
        
        formula_mapping = {}
        formula_latex = {}
        total_count = 0
        saved_count = 0
        ocr_success = 0
        ocr_failed = 0
        
        try:
            # 打开 PDF
            doc = fitz.open(pdf_path)
            logger.info(f"PDF 总页数: {len(doc)}")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                logger.debug(f"处理第 {page_num + 1} 页...")
                
                # 提取页面中的图片和公式区域
                formulas = self._detect_formulas_on_page(
                    page, 
                    page_num,
                    min_formula_height,
                    min_formula_width
                )
                
                # 保存提取的公式
                for formula_idx, formula_data in enumerate(formulas):
                    total_count += 1
                    
                    # 生成文件名: page{页码}_formula{编号}
                    formula_name = f"page{page_num + 1}_formula{formula_idx + 1}"
                    formula_filename = f"{formula_name}.png"
                    formula_path = formula_dir / formula_filename
                    
                    try:
                        # 保存公式图片
                        formula_image = formula_data['image']
                        formula_image.save(formula_path, 'PNG')
                        
                        # 记录相对路径（相对于 Markdown 文件所在的 layer1 目录）
                        relative_path = f"../formulas/{formula_filename}"
                        formula_mapping[formula_name] = relative_path
                        
                        saved_count += 1
                        logger.debug(f"已保存公式: {formula_filename}")
                        
                        # OCR 识别公式
                        if self.use_ocr and self.ocr_model:
                            try:
                                latex_code = self._ocr_formula_to_latex(formula_image)
                                formula_latex[formula_name] = latex_code
                                ocr_success += 1
                                logger.debug(f"OCR 成功: {formula_name} -> {latex_code[:50]}...")
                            except Exception as e:
                                ocr_failed += 1
                                logger.warning(f"OCR 失败 {formula_name}: {e}")
                                # 保存空的 LaTeX，后续可以手动补充
                                formula_latex[formula_name] = ""
                        
                    except Exception as e:
                        logger.warning(f"保存公式失败 {formula_filename}: {e}")
            
            doc.close()
            
        except Exception as e:
            logger.error(f"提取公式时出错: {e}")
            raise
        
        result = {
            'formula_mapping': formula_mapping,
            'formula_latex': formula_latex,
            'formula_dir': str(formula_dir),
            'relative_formula_dir': f"{doc_name}/formulas",
            'total_formulas': total_count,
            'saved_formulas': saved_count,
            'ocr_success': ocr_success,
            'ocr_failed': ocr_failed
        }
        
        logger.info(f"✅ 公式提取完成: 总数={total_count}, 成功={saved_count}, OCR成功={ocr_success}")
        
        return result
    
    def _detect_formulas_on_page(
        self,
        page: fitz.Page,
        page_num: int,
        min_height: int,
        min_width: int
    ) -> List[Dict[str, Any]]:
        """
        检测页面中的公式区域
        
        策略：
        1. 提取页面中的所有图片块（独立公式图片）
        2. 分析文本块，检测内联公式（基于数学符号、字体、上下标）
        3. 根据位置和大小过滤
        
        Args:
            page: PDF 页面对象
            page_num: 页码
            min_height: 最小高度
            min_width: 最小宽度
        
        Returns:
            公式数据列表 [{'image': PIL.Image, 'bbox': (x0, y0, x1, y1), 'type': 'image'}, ...]
        """
        formulas = []
        
        # 方法 1: 提取页面中的所有图片（可能包含公式）
        image_list = page.get_images(full=True)
        
        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                
                # 获取图片位置
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                
                rect = rects[0]  # 使用第一个矩形
                bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
                width = rect.width
                height = rect.height
                
                # 过滤太小的图片（可能是图标、装饰等）
                if width < min_width or height < min_height:
                    continue
                
                # 提取图片数据
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                
                # 转换为 PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # 判断是否可能是公式（简单启发式规则）
                is_likely_formula = self._is_likely_formula(image, width, height)
                
                if is_likely_formula:
                    formulas.append({
                        'image': image,
                        'bbox': bbox,
                        'type': 'embedded_image',
                        'page': page_num + 1
                    })
                    logger.debug(f"检测到潜在公式图片: page {page_num + 1}, bbox={bbox}")
                
            except Exception as e:
                logger.debug(f"处理图片 {img_index} 时出错: {e}")
                continue
        
        # 方法 2: 基于文本分析检测内联公式
        inline_formulas = self._detect_inline_formulas(page, page_num, min_height, min_width)
        formulas.extend(inline_formulas)
        
        return formulas
    
    def _is_likely_formula(self, image: Image.Image, width: float, height: float) -> bool:
        """
        判断图片是否可能是公式
        
        启发式规则：
        1. 长宽比接近公式（一般是横向的，长宽比 > 1）
        2. 尺寸适中（不是超大图片）
        3. 颜色简单（公式通常是黑白或简单色彩）
        4. 主要是黑白色（排除彩色照片）
        
        Args:
            image: PIL Image 对象
            width: 图片宽度
            height: 图片高度
        
        Returns:
            是否可能是公式
        """
        # 规则 1: 长宽比检查（公式通常是横向的）
        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio < 0.5 or aspect_ratio > 20:
            # 太窄或太宽，可能不是公式
            return False
        
        # 规则 2: 尺寸检查（排除过大的图片，如插图、照片）
        if width > 600 or height > 300:
            # 公式通常不会太大
            return False
        
        # 规则 3: 排除过小的图片（可能是图标、装饰）
        if width < 30 or height < 10:
            return False
        
        # 规则 4: 颜色复杂度检查（公式通常颜色简单）
        try:
            # 转为灰度图检查
            gray_image = image.convert('L')
            colors = gray_image.getcolors(maxcolors=256)
            
            if colors:
                # 公式通常颜色数量很少（主要是黑白）
                if len(colors) > 30:
                    return False
                
                # 检查是否主要是黑白色
                # 计算亮度分布
                total_pixels = sum(count for count, _ in colors)
                dark_pixels = sum(count for count, value in colors if value < 128)
                light_pixels = sum(count for count, value in colors if value >= 128)
                
                # 如果亮度分布过于均匀，可能是照片
                if 0.3 < (dark_pixels / total_pixels) < 0.7:
                    # 检查是否是彩色图片
                    if image.mode in ('RGB', 'RGBA'):
                        # 计算颜色方差，彩色照片方差大
                        import numpy as np
                        img_array = np.array(image)
                        if len(img_array.shape) == 3:
                            color_variance = np.var(img_array, axis=(0, 1)).mean()
                            if color_variance > 1000:  # 彩色照片方差通常很大
                                return False
        except Exception:
            pass
        
        # 默认认为可能是公式
        return True
    
    def _detect_inline_formulas(
        self,
        page: fitz.Page,
        page_num: int,
        min_height: int,
        min_width: int
    ) -> List[Dict[str, Any]]:
        """
        检测页面中的内联公式（与文本混排的公式）
        
        策略：
        1. 提取页面的详细文本信息（包括字体、位置）
        2. 识别数学符号、特殊字体、上下标
        3. 截取识别到的公式区域为图片
        
        Args:
            page: PDF 页面对象
            page_num: 页码
            min_height: 最小高度
            min_width: 最小宽度
        
        Returns:
            公式数据列表
        """
        formulas = []
        
        # 数学符号集合（常见的 LaTeX 数学符号）
        math_symbols = {
            '∑', '∏', '∫', '∬', '∭', '∮', '∂', '∇', '√', '∛', '∜',
            '≤', '≥', '≠', '≈', '≡', '∞', '±', '×', '÷', '∝', '∼',
            'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
            'ν', 'ξ', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
            'Γ', 'Δ', 'Θ', 'Λ', 'Ξ', 'Π', 'Σ', 'Φ', 'Ψ', 'Ω',
            '∈', '∉', '⊂', '⊃', '⊆', '⊇', '∪', '∩', '∅', '∀', '∃',
            '→', '←', '↔', '⇒', '⇐', '⇔', '↑', '↓', '⊕', '⊗'
        }
        
        # 数学字体名称关键词
        math_font_keywords = [
            'math', 'cmmi', 'cmsy', 'cmex', 'msam', 'msbm',
            'mathtype', 'symbol', 'times-italic', 'timesi',
            'cambria-math', 'latinmodern-math'
        ]
        
        try:
            # 获取详细文本信息
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])
            
            formula_candidates = []
            line_formulas = []  # 存储行级公式
            
            for block in blocks:
                if block.get("type") != 0:  # 只处理文本块
                    continue
                
                lines = block.get("lines", [])
                
                for line in lines:
                    spans = line.get("spans", [])
                    
                    # 检查整行是否是公式（块级公式检测）
                    line_formula = self._detect_line_formula(line, page_num)
                    if line_formula:
                        line_formulas.append(line_formula)
                        continue  # 如果整行是公式，跳过 span 级检测
                    
                    for span in spans:
                        text = span.get("text", "")
                        font = span.get("font", "").lower()
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        
                        # 检查是否包含数学符号
                        has_math_symbol = any(sym in text for sym in math_symbols)
                        
                        # 检查是否是数学字体
                        is_math_font = any(keyword in font for keyword in math_font_keywords)
                        
                        # 检查是否包含上下标模式（如 x^2, a_i）
                        has_superscript = '^' in text or '²' in text or '³' in text
                        has_subscript = '_' in text or '₀' in text or '₁' in text
                        
                        # 检查是否包含分数、括号等模式
                        has_fraction_pattern = '/' in text and any(c.isdigit() for c in text)
                        has_complex_brackets = text.count('(') + text.count('[') + text.count('{') > 1
                        
                        # 综合判断
                        is_formula = (
                            has_math_symbol or 
                            (is_math_font and len(text.strip()) > 1) or
                            has_superscript or 
                            has_subscript or
                            has_fraction_pattern or
                            has_complex_brackets
                        )
                        
                        if is_formula:
                            confidence = self._calculate_formula_confidence(
                                text, font, has_math_symbol, is_math_font
                            )
                            
                            # 只保留置信度较高的候选
                            if confidence >= 0.3:  # 设置最低置信度阈值
                                formula_candidates.append({
                                    'text': text,
                                    'bbox': bbox,
                                    'font': font,
                                    'confidence': confidence
                                })
            
            # 合并相邻的公式候选（同一行的连续公式片段）
            merged_formulas = self._merge_adjacent_formulas(formula_candidates, max_gap=20.0)
            
            # 合并行级公式和片段级公式
            all_formulas = line_formulas + merged_formulas
            
            # 为每个检测到的公式区域截图
            for idx, formula_info in enumerate(all_formulas):
                bbox = formula_info['bbox']
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                # 过滤太小的区域（提高最小宽度要求）
                if width < max(min_width, 40) or height < min_height:
                    continue
                
                # 过滤置信度太低的
                if formula_info['confidence'] < 0.4:
                    continue
                
                # 扩展边界（留一些边距）
                margin = 2
                expanded_bbox = fitz.Rect(
                    max(0, bbox[0] - margin),
                    max(0, bbox[1] - margin),
                    min(page.rect.width, bbox[2] + margin),
                    min(page.rect.height, bbox[3] + margin)
                )
                
                try:
                    # 截取区域为图片
                    pix = page.get_pixmap(clip=expanded_bbox, matrix=fitz.Matrix(2, 2))  # 2倍分辨率
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    formulas.append({
                        'image': image,
                        'bbox': tuple(bbox),
                        'type': 'inline_formula',
                        'page': page_num + 1,
                        'text': formula_info['text'],
                        'confidence': formula_info['confidence']
                    })
                    
                    logger.debug(f"检测到内联公式: page {page_num + 1}, text='{formula_info['text'][:30]}...', confidence={formula_info['confidence']:.2f}")
                    
                except Exception as e:
                    logger.debug(f"截取公式区域失败: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"分析页面文本时出错: {e}")
        
        return formulas
    
    def _detect_line_formula(
        self,
        line: Dict,
        page_num: int
    ) -> Optional[Dict[str, Any]]:
        """
        检测整行是否是块级公式（display formula）
        
        块级公式特征：
        1. 独立成行（通常居中或缩进）
        2. 包含多个数学符号
        3. 整行几乎都是数学内容
        4. 可能包含求和、积分、分数等复杂结构
        
        Args:
            line: 行对象
            page_num: 页码
        
        Returns:
            公式信息字典，如果不是公式则返回 None
        """
        spans = line.get("spans", [])
        if not spans:
            return None
        
        # 合并整行文本
        full_text = ''.join(span.get("text", "") for span in spans)
        full_text = full_text.strip()
        
        # 空行或过短
        if len(full_text) < 3:
            return None
        
        # 数学符号集合
        math_symbols = {
            '∑', '∏', '∫', '∬', '∭', '∮', '∂', '∇', '√', '∛', '∜',
            '≤', '≥', '≠', '≈', '≡', '∞', '±', '×', '÷', '∝', '∼',
            'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
            'ν', 'ξ', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
            'Γ', 'Δ', 'Θ', 'Λ', 'Ξ', 'Π', 'Σ', 'Φ', 'Ψ', 'Ω',
            '∈', '∉', '⊂', '⊃', '⊆', '⊇', '∪', '∩', '∅', '∀', '∃',
            '→', '←', '↔', '⇒', '⇐', '⇔', '↑', '↓', '⊕', '⊗'
        }
        
        # 计算数学符号数量
        math_symbol_count = sum(1 for char in full_text if char in math_symbols)
        
        # 计算数学字体 span 数量
        math_font_count = 0
        italic_count = 0
        for span in spans:
            font = span.get("font", "").lower()
            if any(kw in font for kw in ['math', 'cmmi', 'cmsy', 'symbol', 'timesi']):
                math_font_count += 1
            if 'italic' in font or 'timesi' in font:
                italic_count += 1
        
        # 检查是否包含上下标
        has_superscript = any(c in full_text for c in '^²³⁰¹⁴⁵⁶⁷⁸⁹')
        has_subscript = any(c in full_text for c in '_₀₁₂₃₄₅₆₇₈₉')
        
        # 检查是否包含括号（多层括号是公式特征）
        bracket_count = full_text.count('(') + full_text.count('[') + full_text.count('{')
        
        # 检查是否包含等号或关系运算符
        has_equation = any(op in full_text for op in ['=', '≠', '≈', '≤', '≥', '<', '>'])
        
        # 检查是否居中（块级公式通常居中）
        line_bbox = line.get("bbox", (0, 0, 0, 0))
        
        # 综合判断
        is_block_formula = False
        confidence = 0.0
        
        # 规则 1: 有多个数学符号（强特征）
        if math_symbol_count >= 2:
            is_block_formula = True
            confidence += 0.4 + min(math_symbol_count * 0.1, 0.3)
        
        # 规则 2: 包含求和、积分等复杂符号
        complex_symbols = {'∑', '∏', '∫', '∬', '∭', '∮', '∂', '∇'}
        if any(sym in full_text for sym in complex_symbols):
            is_block_formula = True
            confidence += 0.5
        
        # 规则 3: 多个数学字体 + 上下标
        if math_font_count >= 3 and (has_superscript or has_subscript):
            is_block_formula = True
            confidence += 0.3
        
        # 规则 4: 包含等号且有括号
        if has_equation and bracket_count >= 2:
            is_block_formula = True
            confidence += 0.2
        
        # 规则 5: 几乎全是斜体（变量）+ 运算符
        if italic_count >= len(spans) * 0.6 and (has_equation or math_symbol_count > 0):
            is_block_formula = True
            confidence += 0.2
        
        if not is_block_formula or confidence < 0.5:
            return None
        
        # 计算整行的边界框
        min_x = min(span.get("bbox", (999999, 0, 0, 0))[0] for span in spans)
        min_y = min(span.get("bbox", (0, 999999, 0, 0))[1] for span in spans)
        max_x = max(span.get("bbox", (0, 0, 0, 0))[2] for span in spans)
        max_y = max(span.get("bbox", (0, 0, 0, 999999))[3] for span in spans)
        
        return {
            'text': full_text,
            'bbox': (min_x, min_y, max_x, max_y),
            'confidence': min(confidence, 1.0),
            'font': 'line-formula',
            'type': 'block_formula'
        }
    
    def _calculate_formula_confidence(
        self,
        text: str,
        font: str,
        has_math_symbol: bool,
        is_math_font: bool
    ) -> float:
        """
        计算文本块是公式的置信度
        
        Args:
            text: 文本内容
            font: 字体名称
            has_math_symbol: 是否包含数学符号
            is_math_font: 是否是数学字体
        
        Returns:
            置信度分数 (0-1)
        """
        score = 0.0
        
        if has_math_symbol:
            score += 0.6  # 提高数学符号权重
        
        if is_math_font:
            score += 0.2
        
        # 检查复杂度（字符种类多样性）
        unique_chars = len(set(text))
        if unique_chars > 3:
            score += 0.1
        
        # 检查是否包含运算符
        operators = {'+', '-', '=', '<', '>', '∈', '∀', '∃', '×', '÷'}
        if any(op in text for op in operators):
            score += 0.15
        
        # 检查是否包含括号（公式常见）
        if any(ch in text for ch in '()[]{}'):
            score += 0.1
        
        # 惩罚纯文本（没有数学特征）
        if not has_math_symbol and not is_math_font:
            score *= 0.5
        
        return min(score, 1.0)
    
    def _merge_adjacent_formulas(
        self,
        candidates: List[Dict],
        max_gap: float = 10.0
    ) -> List[Dict]:
        """
        合并相邻的公式片段（同一行的连续公式）
        
        Args:
            candidates: 公式候选列表
            max_gap: 最大间隔距离（像素）
        
        Returns:
            合并后的公式列表
        """
        if not candidates:
            return []
        
        # 按垂直位置排序（同一行的在一起）
        candidates.sort(key=lambda x: (x['bbox'][1], x['bbox'][0]))
        
        merged = []
        current_group = [candidates[0]]
        
        for i in range(1, len(candidates)):
            prev_bbox = current_group[-1]['bbox']
            curr_bbox = candidates[i]['bbox']
            
            # 检查是否在同一行（y坐标相近）
            vertical_gap = abs(curr_bbox[1] - prev_bbox[1])
            horizontal_gap = curr_bbox[0] - prev_bbox[2]
            
            if vertical_gap < 5 and horizontal_gap < max_gap:
                # 同一行且距离近，合并
                current_group.append(candidates[i])
            else:
                # 新的一组
                if current_group:
                    merged.append(self._merge_group(current_group))
                current_group = [candidates[i]]
        
        # 处理最后一组
        if current_group:
            merged.append(self._merge_group(current_group))
        
        return merged
    
    def _merge_group(self, group: List[Dict]) -> Dict:
        """
        合并一组公式片段
        
        Args:
            group: 公式片段列表
        
        Returns:
            合并后的公式信息
        """
        # 合并文本
        text = ' '.join(item['text'] for item in group)
        
        # 合并边界框
        min_x = min(item['bbox'][0] for item in group)
        min_y = min(item['bbox'][1] for item in group)
        max_x = max(item['bbox'][2] for item in group)
        max_y = max(item['bbox'][3] for item in group)
        
        # 平均置信度
        avg_confidence = sum(item['confidence'] for item in group) / len(group)
        
        return {
            'text': text,
            'bbox': (min_x, min_y, max_x, max_y),
            'confidence': avg_confidence,
            'font': group[0]['font']
        }
    
    def _ocr_formula_to_latex(self, image: Image.Image) -> str:
        """
        使用 OCR 将公式图片转换为 LaTeX 代码
        
        Args:
            image: PIL Image 对象
        
        Returns:
            LaTeX 代码字符串
        """
        if not self.ocr_model:
            raise RuntimeError("OCR 模型未加载")
        
        # 使用 pix2tex 进行 OCR
        latex_code = self.ocr_model(image)
        
        # 清理和格式化 LaTeX 代码
        latex_code = latex_code.strip()
        
        return latex_code
    
    def save_latex_to_json(
        self,
        formula_latex: Dict[str, str],
        doc_name: str
    ) -> Path:
        """
        将 LaTeX 代码保存到 JSON 文件
        
        Args:
            formula_latex: 公式 LaTeX 映射
            doc_name: 文档名称
        
        Returns:
            JSON 文件路径
        """
        import json
        
        output_file = self.output_base_dir / doc_name / "formulas" / "formulas_latex.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formula_latex, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ LaTeX 代码已保存到: {output_file}")
        
        return output_file
    
    def get_formula_statistics(self, formula_mapping: Dict) -> Dict[str, Any]:
        """
        获取公式统计信息
        
        Args:
            formula_mapping: 公式路径映射
        
        Returns:
            统计信息字典
        """
        total_formulas = len(formula_mapping)
        
        # 按页码分组统计
        page_distribution = {}
        for formula_name in formula_mapping.keys():
            # formula_name 格式: "page2_formula3"
            if 'page' in formula_name and '_formula' in formula_name:
                page_num = formula_name.split('_formula')[0]  # "page2"
                page_distribution[page_num] = page_distribution.get(page_num, 0) + 1
        
        return {
            'total_formulas': total_formulas,
            'page_distribution': page_distribution,
            'pages_with_formulas': len(page_distribution)
        }


# 测试代码
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    import sys
    
    setup_logger("formula_extractor")
    
    print("📊 公式提取器测试")
    print("="*70)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        doc_name = pdf_path.stem
    else:
        # 默认测试文件
        pdf_path = Path("data/input/2023CVPR-CoMFormer.pdf")
        doc_name = "test_formulas"
    
    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        sys.exit(1)
    
    # 创建提取器
    extractor = FormulaExtractor(use_ocr=True)
    
    # 提取公式
    result = extractor.extract_formulas_from_pdf(
        pdf_path,
        doc_name=doc_name
    )
    
    print(f"\n✅ 提取结果:")
    print(f"  公式目录: {result['formula_dir']}")
    print(f"  总公式数: {result['total_formulas']}")
    print(f"  成功保存: {result['saved_formulas']}")
    print(f"  OCR 成功: {result['ocr_success']}")
    print(f"  OCR 失败: {result['ocr_failed']}")
    
    # 保存 LaTeX 代码
    if result['formula_latex']:
        latex_file = extractor.save_latex_to_json(
            result['formula_latex'],
            doc_name
        )
        print(f"  LaTeX 文件: {latex_file}")
    
    # 统计信息
    stats = extractor.get_formula_statistics(result['formula_mapping'])
    print(f"\n📈 统计信息:")
    print(f"  总公式数: {stats['total_formulas']}")
    print(f"  包含公式的页数: {stats['pages_with_formulas']}")
    print(f"  页码分布: {stats['page_distribution']}")
    
    # 显示部分 LaTeX 示例
    if result['formula_latex']:
        print(f"\n📝 LaTeX 示例（前 3 个）:")
        for i, (name, latex) in enumerate(list(result['formula_latex'].items())[:3]):
            print(f"  {name}: {latex}")
