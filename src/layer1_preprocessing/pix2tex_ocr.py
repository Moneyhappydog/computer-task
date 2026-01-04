"""
pix2tex OCR模型实现
使用pix2tex进行公式识别
"""
from typing import Tuple, Optional
from PIL import Image
import warnings

try:
    from .formula_ocr import BaseFormulaOCR
except ImportError:
    import sys
    from pathlib import Path
    import importlib.util
    
    current_file = Path(__file__)
    formula_ocr_path = current_file.parent / "formula_ocr.py"
    
    if formula_ocr_path.exists():
        spec = importlib.util.spec_from_file_location("formula_ocr", formula_ocr_path)
        formula_ocr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(formula_ocr)
        BaseFormulaOCR = formula_ocr.BaseFormulaOCR
    else:
        from abc import ABC, abstractmethod
        class BaseFormulaOCR(ABC):
            @abstractmethod
            def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
                pass


class Pix2TexOCR(BaseFormulaOCR):
    """
    使用pix2tex进行公式OCR
    
    安装: pip install pix2tex
    首次使用会自动下载模型
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
            import pix2tex
            from pix2tex.cli import LatexOCR
            
            print("正在初始化pix2tex模型（首次使用会自动下载模型）...")
            
            # 创建LatexOCR实例
            # pix2tex会自动下载模型到用户目录
            self._model = LatexOCR()
            
            self._initialized = True
            print("✓ pix2tex模型初始化完成")
            
        except ImportError:
            raise ImportError(
                "pix2tex未安装。请运行: pip install pix2tex\n"
                "或者使用其他OCR模型（如DummyFormulaOCR）"
            )
        except Exception as e:
            raise RuntimeError(f"pix2tex模型初始化失败: {e}")
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        使用pix2tex识别公式图片
        
        Args:
            image: PIL.Image格式的公式图片
            
        Returns:
            (latex_str, confidence): LaTeX字符串和置信度（pix2tex不返回置信度，返回None）
        """
        self._initialize_model()
        
        try:
            # 使用pix2tex的predict方法
            latex = self._model(image)
            
            # pix2tex通常不返回置信度
            return latex, None
            
        except Exception as e:
            warnings.warn(f"pix2tex识别失败: {e}，返回空字符串")
            return "", None



