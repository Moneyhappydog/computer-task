"""
公式截图 + OCR + LaTeX 抽取模块
负责将检测到的公式区域截图，并通过OCR模型转换为LaTeX字符串
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Literal, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
import json

# 导入前面模块的数据结构
try:
    # 作为包导入
    from .block_formula_detector import BlockFormula
    from .inline_formula_detector import InlineFormula
except ImportError:
    # 直接运行时的导入方式
    import sys
    import importlib.util
    
    current_file = Path(__file__)
    
    # 导入 block_formula_detector
    block_detector_path = current_file.parent / "block_formula_detector.py"
    if block_detector_path.exists():
        spec1 = importlib.util.spec_from_file_location("block_formula_detector", block_detector_path)
        block_formula_detector = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(block_formula_detector)
        BlockFormula = block_formula_detector.BlockFormula
    else:
        BlockFormula = None
    
    # 导入 inline_formula_detector
    inline_detector_path = current_file.parent / "inline_formula_detector.py"
    if inline_detector_path.exists():
        spec2 = importlib.util.spec_from_file_location("inline_formula_detector", inline_detector_path)
        inline_formula_detector = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(inline_formula_detector)
        InlineFormula = inline_formula_detector.InlineFormula
    else:
        InlineFormula = None


FormulaType = Literal["block", "inline"]


class BaseFormulaOCR(ABC):
    """公式OCR模型的抽象基类"""
    
    @abstractmethod
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        输入一张 PIL.Image 格式的公式截图，
        返回 (latex_str, confidence)，若无法提供置信度，可返回 (latex_str, None)。
        
        Args:
            image: PIL.Image 格式的公式图片
            
        Returns:
            (latex_str, confidence): LaTeX字符串和置信度（可选）
        """
        pass


class DummyFormulaOCR(BaseFormulaOCR):
    """
    示例/占位OCR实现
    实际使用时请替换成真正的公式OCR模型（如pix2tex、texocr等）
    """
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        占位实现：返回一个固定的dummy LaTeX字符串
        
        Args:
            image: PIL.Image 格式的公式图片
            
        Returns:
            (latex_str, None): 固定的dummy LaTeX字符串，无置信度
        """
        # 实际使用时请替换成真正的公式OCR模型
        # 例如：
        # from pix2tex import cli as pix2tex_cli
        # latex = pix2tex_cli.predict(image)
        return r"\mathrm{dummy\_formula}", None


class Pix2TexOCR(BaseFormulaOCR):
    """
    使用pix2tex的真实OCR实现
    需要安装: pip install pix2tex
    """
    
    def __init__(self):
        """初始化pix2tex OCR模型"""
        self._model = None
        self._initialized = False
    
    def _initialize_model(self):
        """延迟初始化模型（首次使用时加载）"""
        if self._initialized:
            return
        
        try:
            # 尝试导入pix2tex
            # pix2tex的API可能因版本而异，尝试多种方式
            try:
                # 方式1: 使用pix2tex.api（如果可用）
                from pix2tex.api import latex as pix2tex_latex
                self._predict_func = lambda img: pix2tex_latex(img)
                self._use_api = True
            except ImportError:
                try:
                    # 方式2: 使用pix2tex.cli（命令行接口）
                    from pix2tex import cli as pix2tex_cli
                    self._cli = pix2tex_cli
                    self._use_api = False
                except ImportError:
                    raise ImportError(
                        "pix2tex未安装。请运行: pip install pix2tex\n"
                        "或者使用: pip install pix2tex[gui]"
                    )
            
            self._initialized = True
        except Exception as e:
            if "ImportError" in str(type(e)):
                raise
            raise RuntimeError(f"pix2tex模型初始化失败: {e}")
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        使用pix2tex进行公式OCR
        
        Args:
            image: PIL.Image 格式的公式图片
            
        Returns:
            (latex_str, None): LaTeX字符串（pix2tex不返回置信度）
        """
        self._initialize_model()
        
        try:
            if self._use_api:
                # 使用API方式（直接传入PIL Image）
                latex = self._predict_func(image)
            else:
                # 使用临时文件方式（保存图片后调用cli）
                import tempfile
                import os
                
                # 保存临时图片
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    image.save(tmp_file.name, 'PNG')
                    tmp_path = tmp_file.name
                
                try:
                    # 调用pix2tex命令行接口
                    if hasattr(self._cli, 'predict'):
                        latex = self._cli.predict(tmp_path)
                    else:
                        # 如果cli没有predict方法，尝试其他方式
                        from pix2tex import cli
                        latex = cli.predict(tmp_path)
                finally:
                    # 清理临时文件
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            # 清理LaTeX字符串
            if latex:
                latex = latex.strip()
                # 移除可能的换行符
                latex = ' '.join(latex.split())
            
            return latex, None  # pix2tex不返回置信度
            
        except Exception as e:
            # OCR失败时返回空字符串
            print(f"  ⚠️ pix2tex OCR失败: {e}")
            import traceback
            traceback.print_exc()
            return "", None


class Pix2TexOCR(BaseFormulaOCR):
    """
    使用pix2tex的真实OCR实现
    需要安装: pip install pix2tex
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化pix2tex OCR模型
        
        Args:
            model_path: 模型路径（可选，默认使用pix2tex的默认模型）
        """
        self.model_path = model_path
        self._model = None
        self._initialized = False
    
    def _initialize_model(self):
        """延迟初始化模型（首次使用时加载）"""
        if self._initialized:
            return
        
        try:
            from pix2tex import cli as pix2tex_cli
            from pix2tex.model import get_model
            from pix2tex.utils import get_minimal_parser
            
            # 初始化pix2tex
            # pix2tex使用命令行接口，需要特殊处理
            self._pix2tex_cli = pix2tex_cli
            self._initialized = True
        except ImportError:
            raise ImportError(
                "pix2tex未安装。请运行: pip install pix2tex\n"
                "或者使用: pip install pix2tex[gui]"
            )
        except Exception as e:
            raise RuntimeError(f"pix2tex模型初始化失败: {e}")
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        使用pix2tex进行公式OCR
        
        Args:
            image: PIL.Image 格式的公式图片
            
        Returns:
            (latex_str, None): LaTeX字符串（pix2tex不返回置信度）
        """
        self._initialize_model()
        
        try:
            # pix2tex的API可能因版本而异
            # 方法1: 使用cli接口（如果可用）
            if hasattr(self._pix2tex_cli, 'predict'):
                latex = self._pix2tex_cli.predict(image)
            else:
                # 方法2: 使用命令行方式（保存临时图片）
                import tempfile
                import os
                
                # 保存临时图片
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    image.save(tmp_file.name, 'PNG')
                    tmp_path = tmp_file.name
                
                try:
                    # 调用pix2tex命令行
                    from pix2tex import cli
                    latex = cli.predict(tmp_path)
                finally:
                    # 清理临时文件
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            # 清理LaTeX字符串
            if latex:
                latex = latex.strip()
            
            return latex, None  # pix2tex不返回置信度
            
        except Exception as e:
            # OCR失败时返回空字符串
            print(f"  ⚠️ pix2tex OCR失败: {e}")
            return "", None


class SimplePix2TexOCR(BaseFormulaOCR):
    """
    简化版pix2tex OCR实现（使用更简单的API）
    适用于pix2tex的某些版本
    """
    
    def __init__(self):
        """初始化简化版pix2tex OCR"""
        self._model = None
        self._initialized = False
    
    def _initialize_model(self):
        """延迟初始化模型"""
        if self._initialized:
            return
        
        try:
            # 尝试导入pix2tex
            try:
                from pix2tex.api import latex
                self._api_latex = latex
                self._use_api = True
            except ImportError:
                # 如果api不可用，尝试cli
                from pix2tex import cli
                self._cli = cli
                self._use_api = False
            
            self._initialized = True
        except ImportError:
            raise ImportError(
                "pix2tex未安装。请运行: pip install pix2tex"
            )
        except Exception as e:
            raise RuntimeError(f"pix2tex模型初始化失败: {e}")
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        使用pix2tex进行公式OCR（简化版）
        
        Args:
            image: PIL.Image 格式的公式图片
            
        Returns:
            (latex_str, None): LaTeX字符串
        """
        self._initialize_model()
        
        try:
            if self._use_api:
                # 使用API方式
                latex_str = self._api_latex(image)
            else:
                # 使用临时文件方式
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    image.save(tmp_file.name, 'PNG')
                    tmp_path = tmp_file.name
                
                try:
                    # 调用pix2tex
                    latex_str = self._cli.predict(tmp_path)
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            if latex_str:
                latex_str = latex_str.strip()
            
            return latex_str, None
            
        except Exception as e:
            print(f"  ⚠️ pix2tex OCR失败: {e}")
            return "", None


@dataclass
class FormulaOCRResult:
    """公式OCR结果数据结构"""
    formula_id: str  # 唯一ID，例如 "block_page3_0001" 或 "inline_page5_0010"
    formula_type: FormulaType  # "block" or "inline"
    page_number: int
    block_index: Optional[int]  # 对于inline一般有意义；对于特殊情况也可以为None
    line_index: Optional[int]  # inline公式才有；block公式可以为None
    span_indices: Optional[List[int]]  # inline公式才有
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    image_path: str  # 截图文件的相对/绝对路径
    latex: str  # OCR输出的LaTeX字符串
    ocr_confidence: Optional[float]  # 如果模型返回置信度；否则为None
    detector_score: Optional[float]  # block/inline检测时的score
    source_text: Optional[str]  # 检测阶段的原始text（BlockFormula.text / InlineFormula.text）
    
    def to_dict(self) -> dict:
        """转换为字典（用于JSON序列化）"""
        return asdict(self)


class FormulaOCRProcessor:
    """公式OCR处理器：负责截图、OCR调用和结果组装"""
    
    def __init__(
        self,
        pdf_path: str,
        ocr_model: BaseFormulaOCR,
        output_dir: str = "formula_images",
        zoom: float = 2.0,
        padding: int = 2,
    ):
        """
        初始化公式OCR处理器
        
        Args:
            pdf_path: 源PDF文件路径
            ocr_model: 实现了BaseFormulaOCR接口的OCR模型实例
            output_dir: 截图保存目录
            zoom: 截图时的放大系数（例如2.0表示2x放大，有利于OCR）
            padding: 在bbox外四周额外扩展的像素（视觉上多一点空白）
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        self.ocr_model = ocr_model
        self.output_dir = Path(output_dir)
        self.zoom = zoom
        self.padding = padding
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 打开PDF文档（延迟到run方法中打开，避免长时间占用）
        self._doc = None
    
    def _open_doc(self):
        """打开PDF文档（延迟加载）"""
        if self._doc is None:
            self._doc = fitz.open(str(self.pdf_path))
        return self._doc
    
    def _close_doc(self):
        """关闭PDF文档"""
        if self._doc is not None:
            self._doc.close()
            self._doc = None
    
    def _extract_formula_image(
        self,
        page_number: int,
        bbox: Tuple[float, float, float, float],
        formula_id: str,
    ) -> Tuple[str, Image.Image]:
        """
        从PDF中提取公式区域的截图
        
        Args:
            page_number: 页码（从1开始）
            bbox: 公式边界框 (x0, y0, x1, y1)
            formula_id: 公式ID（用于文件命名）
            
        Returns:
            (image_path, image): 图片路径和PIL.Image对象
        """
        doc = self._open_doc()
        
        # 转换为0-based索引
        page_idx = page_number - 1
        if page_idx < 0 or page_idx >= len(doc):
            raise ValueError(f"页码 {page_number} 超出范围 [1, {len(doc)}]")
        
        page = doc[page_idx]
        page_rect = page.rect
        
        # 解析bbox
        x0, y0, x1, y1 = bbox
        
        # 应用padding（在PDF坐标系中）
        # padding需要根据zoom调整，这里简单处理：在PDF坐标中扩展
        padding_pdf = self.padding / self.zoom
        
        # 扩展bbox，但不要超出页面边界
        x0_clipped = max(0, x0 - padding_pdf)
        y0_clipped = max(0, y0 - padding_pdf)
        x1_clipped = min(page_rect.width, x1 + padding_pdf)
        y1_clipped = min(page_rect.height, y1 + padding_pdf)
        
        # 构造裁剪矩形
        rect = fitz.Rect(x0_clipped, y0_clipped, x1_clipped, y1_clipped)
        
        # 应用zoom（放大系数）
        mat = fitz.Matrix(self.zoom, self.zoom)
        
        # 渲染为pixmap
        pix = page.get_pixmap(matrix=mat, clip=rect)
        
        # 转换为PIL.Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # 生成文件路径
        # 按page/type分类存储
        page_dir = self.output_dir / f"page_{page_number:04d}"
        page_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = page_dir / f"{formula_id}.png"
        
        # 保存图片
        image.save(str(image_path), 'PNG')
        
        return (str(image_path), image)
    
    def _process_block_formula(
        self,
        formula: BlockFormula,
        global_index: int,
    ) -> Optional[FormulaOCRResult]:
        """
        处理单个块级公式
        
        Args:
            formula: BlockFormula对象
            global_index: 全局索引（用于生成formula_id）
            
        Returns:
            FormulaOCRResult对象，如果处理失败则返回None
        """
        try:
            # 生成formula_id
            formula_id = f"block_page{formula.page_number}_idx{global_index:04d}"
            
            # 提取公式图片
            image_path, image = self._extract_formula_image(
                formula.page_number,
                formula.bbox,
                formula_id
            )
            
            # 调用OCR模型
            try:
                latex, ocr_confidence = self.ocr_model.predict(image)
                
                # 如果OCR返回空字符串，使用降级处理
                if not latex or not latex.strip():
                    latex = formula.text or ""
                    ocr_confidence = None
            except Exception as e:
                # OCR异常处理：使用原始文本作为降级
                print(f"  ⚠️ OCR处理失败 (formula_id={formula_id}): {e}")
                latex = formula.text or ""
                ocr_confidence = None
            
            # 构造结果对象
            result = FormulaOCRResult(
                formula_id=formula_id,
                formula_type="block",
                page_number=formula.page_number,
                block_index=formula.block_index,
                line_index=None,  # block公式没有line_index
                span_indices=None,  # block公式没有span_indices
                bbox=formula.bbox,
                image_path=image_path,
                latex=latex,
                ocr_confidence=ocr_confidence,
                detector_score=formula.score,
                source_text=formula.text,
            )
            
            return result
            
        except Exception as e:
            print(f"  ⚠️ 处理块级公式失败 (page={formula.page_number}, block={formula.block_index}): {e}")
            return None
    
    def _process_inline_formula(
        self,
        formula: InlineFormula,
        global_index: int,
    ) -> Optional[FormulaOCRResult]:
        """
        处理单个行内公式
        
        Args:
            formula: InlineFormula对象
            global_index: 全局索引（用于生成formula_id）
            
        Returns:
            FormulaOCRResult对象，如果处理失败则返回None
        """
        try:
            # 生成formula_id
            formula_id = f"inline_page{formula.page_number}_idx{global_index:04d}"
            
            # 提取公式图片
            image_path, image = self._extract_formula_image(
                formula.page_number,
                formula.bbox,
                formula_id
            )
            
            # 调用OCR模型
            try:
                latex, ocr_confidence = self.ocr_model.predict(image)
                
                # 如果OCR返回空字符串，使用降级处理
                if not latex or not latex.strip():
                    latex = formula.text or ""
                    ocr_confidence = None
            except Exception as e:
                # OCR异常处理：使用原始文本作为降级
                print(f"  ⚠️ OCR处理失败 (formula_id={formula_id}): {e}")
                latex = formula.text or ""
                ocr_confidence = None
            
            # 构造结果对象
            result = FormulaOCRResult(
                formula_id=formula_id,
                formula_type="inline",
                page_number=formula.page_number,
                block_index=formula.block_index,
                line_index=formula.line_index,
                span_indices=formula.span_indices,
                bbox=formula.bbox,
                image_path=image_path,
                latex=latex,
                ocr_confidence=ocr_confidence,
                detector_score=formula.score,
                source_text=formula.text,
            )
            
            return result
            
        except Exception as e:
            print(f"  ⚠️ 处理行内公式失败 (page={formula.page_number}, block={formula.block_index}, line={formula.line_index}): {e}")
            return None
    
    def run(
        self,
        block_formulas: Optional[List[BlockFormula]] = None,
        inline_formulas: Optional[List[InlineFormula]] = None,
    ) -> List[FormulaOCRResult]:
        """
        对所有块级公式和行内公式进行截图和OCR处理
        
        Args:
            block_formulas: 块级公式列表（可选）
            inline_formulas: 行内公式列表（可选）
            
        Returns:
            FormulaOCRResult列表
        """
        results = []
        
        # 打开PDF文档
        self._open_doc()
        
        try:
            # 处理块级公式
            if block_formulas:
                print(f"处理 {len(block_formulas)} 个块级公式...")
                for idx, formula in enumerate(block_formulas):
                    result = self._process_block_formula(formula, idx)
                    if result:
                        results.append(result)
                    if (idx + 1) % 10 == 0:
                        print(f"  已处理 {idx + 1}/{len(block_formulas)} 个块级公式")
            
            # 处理行内公式
            if inline_formulas:
                print(f"处理 {len(inline_formulas)} 个行内公式...")
                block_count = len(block_formulas) if block_formulas else 0
                for idx, formula in enumerate(inline_formulas):
                    result = self._process_inline_formula(formula, block_count + idx)
                    if result:
                        results.append(result)
                    if (idx + 1) % 10 == 0:
                        print(f"  已处理 {idx + 1}/{len(inline_formulas)} 个行内公式")
        
        finally:
            # 关闭PDF文档
            self._close_doc()
        
        print(f"\n✓ OCR处理完成，共 {len(results)} 个公式")
        return results
    
    def save_results_to_json(
        self,
        results: List[FormulaOCRResult],
        json_path: str,
    ) -> None:
        """
        将OCR结果保存为JSON文件
        
        Args:
            results: FormulaOCRResult列表
            json_path: JSON文件保存路径
        """
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典列表
        results_dict = [result.to_dict() for result in results]
        
        # 保存为JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_formulas': len(results),
                'block_count': sum(1 for r in results if r.formula_type == 'block'),
                'inline_count': sum(1 for r in results if r.formula_type == 'inline'),
                'formulas': results_dict
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✓ OCR结果已保存到: {json_path}")


# ============================================================================
# 命令行使用示例
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 导入前面模块（处理导入问题）
    try:
        from .formula_layout import PDFLayoutExtractor
        from .block_formula_detector import BlockFormulaDetector
        from .inline_formula_detector import InlineFormulaDetector
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
        
        # 导入 inline_formula_detector
        inline_detector_path = current_file.parent / "inline_formula_detector.py"
        spec3 = importlib.util.spec_from_file_location("inline_formula_detector", inline_detector_path)
        inline_formula_detector = importlib.util.module_from_spec(spec3)
        spec3.loader.exec_module(inline_formula_detector)
        InlineFormulaDetector = inline_formula_detector.InlineFormulaDetector
    
    if len(sys.argv) < 2:
        print("用法: python formula_ocr.py <pdf_path> [output_dir]")
        print("示例: python formula_ocr.py mypaper.pdf")
        print("示例: python formula_ocr.py mypaper.pdf formula_images")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "formula_images"
    
    try:
        print("=" * 70)
        print("公式OCR处理流程")
        print("=" * 70)
        print(f"\nPDF: {Path(pdf_path).name}\n")
        
        # 1. 版面解析
        print("步骤1: 版面解析...")
        layout_extractor = PDFLayoutExtractor(pdf_path)
        pages = layout_extractor.parse()
        print(f"✓ 解析完成，共 {len(pages)} 页\n")
        
        # 2. 块级公式检测
        print("步骤2: 检测块级公式...")
        block_detector = BlockFormulaDetector()
        block_formulas = block_detector.detect_block_formulas(pages)
        print(f"✓ 检测完成，发现 {len(block_formulas)} 个块级公式\n")
        
        # 3. 行内公式检测
        print("步骤3: 检测行内公式...")
        inline_detector = InlineFormulaDetector()
        inline_formulas = inline_detector.detect_inline_formulas(pages, block_formulas)
        print(f"✓ 检测完成，发现 {len(inline_formulas)} 个行内公式\n")
        
        # 4. 公式OCR
        print("步骤4: 公式OCR处理...")
        ocr_model = DummyFormulaOCR()  # 实际使用时替换成真正的OCR模型
        processor = FormulaOCRProcessor(
            pdf_path,
            ocr_model,
            output_dir=output_dir,
            zoom=2.0,
            padding=2
        )
        
        results = processor.run(
            block_formulas=block_formulas,
            inline_formulas=inline_formulas
        )
        
        print(f"\n✓ OCR处理完成，共 {len(results)} 个公式\n")
        
        # 5. 保存JSON结果
        json_path = Path(output_dir) / "formula_ocr_results.json"
        processor.save_results_to_json(results, str(json_path))
        
        # 6. 简单打印前几个结果
        print(f"\n{'=' * 70}")
        print("OCR结果示例（前10个）:")
        print("=" * 70)
        
        for r in results[:10]:
            print(f"\n公式 {r.formula_id}:")
            print(f"  类型: {r.formula_type}")
            print(f"  页码: {r.page_number}")
            print(f"  图片: {r.image_path}")
            print(f"  LaTeX: {r.latex[:80]!r}")
            print(f"  OCR置信度: {r.ocr_confidence}")
            print(f"  检测得分: {r.detector_score:.3f}")
        
        if len(results) > 10:
            print(f"\n... (还有 {len(results) - 10} 个公式)")
        
        print(f"\n{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

