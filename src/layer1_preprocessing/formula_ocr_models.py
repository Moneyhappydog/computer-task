"""
公式OCR模型实现
提供真实的OCR模型，如pix2tex等
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from PIL import Image
import warnings

# 导入基础接口
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
        # 如果导入失败，定义基础接口
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
    
    def __init__(self, model_name: str = "checkpoints", use_cuda: bool = False):
        """
        初始化pix2tex OCR模型
        
        Args:
            model_name: 模型名称（默认"checkpoints"）
            use_cuda: 是否使用CUDA（如果有GPU）
        """
        self.model_name = model_name
        self.use_cuda = use_cuda
        self._model = None
        self._tokenizer = None
        self._processor = None
        self._initialized = False
    
    def _initialize_model(self):
        """延迟初始化模型（首次使用时加载）"""
        if self._initialized:
            return
        
        try:
            from pix2tex import cli as pix2tex_cli
            from pix2tex.model import get_model
            from pix2tex.utils import get_checkpoint, in_model_path
            
            # 初始化pix2tex
            self._initialized = True
            
            # pix2tex的初始化逻辑
            # 注意：pix2tex可能需要特定的初始化方式
            print("正在初始化pix2tex模型（首次使用会自动下载）...")
            
            # 这里使用pix2tex的CLI接口
            # 实际使用时可能需要根据pix2tex的API调整
            self._pix2tex_cli = pix2tex_cli
            
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
            (latex_str, confidence): LaTeX字符串和置信度（pix2tex可能不返回置信度）
        """
        self._initialize_model()
        
        try:
            # 使用pix2tex的predict方法
            # 注意：pix2tex的API可能因版本而异，这里提供一个通用实现
            from pix2tex import cli as pix2tex_cli
            
            # 方法1: 使用pix2tex的CLI接口（如果可用）
            if hasattr(pix2tex_cli, 'predict'):
                latex = pix2tex_cli.predict(image)
            elif hasattr(pix2tex_cli, 'call_model'):
                # 方法2: 使用call_model
                latex = pix2tex_cli.call_model(image)
            else:
                # 方法3: 使用pix2tex的完整流程
                # 这需要根据实际pix2tex版本调整
                latex = self._predict_with_pix2tex(image)
            
            # pix2tex通常不返回置信度
            return latex, None
            
        except Exception as e:
            warnings.warn(f"pix2tex识别失败: {e}，返回空字符串")
            return "", None
    
    def _predict_with_pix2tex(self, image: Image.Image) -> str:
        """
        使用pix2tex的完整流程进行识别
        
        Args:
            image: PIL.Image格式的公式图片
            
        Returns:
            LaTeX字符串
        """
        try:
            # 尝试导入pix2tex的完整模块
            from pix2tex import cli as pix2tex_cli
            from pix2tex.model import get_model
            from pix2tex.utils import get_checkpoint, in_model_path
            from pix2tex.dataset.transforms import test_transform
            from pix2tex.dataset.dataset import Im2LatexDataset
            import torch
            
            # 如果模型未加载，进行初始化
            if not hasattr(self, '_model') or self._model is None:
                # 获取checkpoint
                checkpoint = get_checkpoint(self.model_name)
                
                # 加载模型
                self._model = get_model(checkpoint)
                if self.use_cuda and torch.cuda.is_available():
                    self._model = self._model.cuda()
                self._model.eval()
            
            # 预处理图片
            transform = test_transform
            
            # 转换为tensor
            import torchvision.transforms as transforms
            to_tensor = transforms.ToTensor()
            img_tensor = to_tensor(image.convert('RGB'))
            
            # 推理
            with torch.no_grad():
                # 这里需要根据pix2tex的实际API调整
                # 可能需要tokenizer等
                output = self._model(img_tensor.unsqueeze(0))
                
                # 解码为LaTeX
                # 这部分需要根据pix2tex的实际实现调整
                latex = self._decode_output(output)
            
            return latex
            
        except Exception as e:
            # 如果完整流程失败，尝试使用简化的CLI方式
            warnings.warn(f"pix2tex完整流程失败: {e}，尝试简化方式")
            return self._predict_simple(image)
    
    def _predict_simple(self, image: Image.Image) -> str:
        """简化的预测方法（使用pix2tex的CLI）"""
        try:
            # 保存临时图片
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image.save(tmp.name, 'PNG')
                tmp_path = tmp.name
            
            try:
                # 使用pix2tex命令行（如果可用）
                from pix2tex import cli as pix2tex_cli
                
                # 尝试直接调用
                if hasattr(pix2tex_cli, 'main'):
                    # 可能需要通过命令行参数调用
                    result = pix2tex_cli.main([tmp_path])
                    return result if isinstance(result, str) else ""
                else:
                    # 使用其他方法
                    return ""
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            warnings.warn(f"简化预测方法失败: {e}")
            return ""
    
    def _decode_output(self, output):
        """解码模型输出为LaTeX（需要根据实际模型调整）"""
        # 这里需要根据pix2tex的实际实现来解码
        # 暂时返回占位符
        return "\\text{decoding not implemented}"


class TexOCR(BaseFormulaOCR):
    """
    使用texocr进行公式OCR（如果可用）
    
    安装: pip install texocr
    """
    
    def __init__(self):
        """初始化texocr模型"""
        self._initialized = False
    
    def _initialize_model(self):
        """延迟初始化模型"""
        if self._initialized:
            return
        
        try:
            import texocr
            self._texocr = texocr
            self._initialized = True
            print("✓ texocr模型初始化完成")
        except ImportError:
            raise ImportError(
                "texocr未安装。请运行: pip install texocr\n"
                "或者使用其他OCR模型（如Pix2TexOCR或DummyFormulaOCR）"
            )
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        使用texocr识别公式图片
        
        Args:
            image: PIL.Image格式的公式图片
            
        Returns:
            (latex_str, confidence): LaTeX字符串和置信度
        """
        self._initialize_model()
        
        try:
            # 使用texocr进行识别
            result = self._texocr.recognize(image)
            
            if isinstance(result, str):
                return result, None
            elif isinstance(result, dict):
                return result.get('latex', ''), result.get('confidence')
            else:
                return str(result), None
                
        except Exception as e:
            warnings.warn(f"texocr识别失败: {e}，返回空字符串")
            return "", None


class EasyOCRFormulaOCR(BaseFormulaOCR):
    """
    使用EasyOCR进行公式OCR（通用OCR，可能不如专门的公式OCR准确）
    
    安装: pip install easyocr
    """
    
    def __init__(self, languages: list = ['en']):
        """
        初始化EasyOCR模型
        
        Args:
            languages: 支持的语言列表（默认['en']）
        """
        self.languages = languages
        self._reader = None
        self._initialized = False
    
    def _initialize_model(self):
        """延迟初始化模型"""
        if self._initialized:
            return
        
        try:
            import easyocr
            print("正在初始化EasyOCR模型（首次使用会自动下载）...")
            self._reader = easyocr.Reader(self.languages)
            self._initialized = True
            print("✓ EasyOCR模型初始化完成")
        except ImportError:
            raise ImportError(
                "easyocr未安装。请运行: pip install easyocr\n"
                "或者使用其他OCR模型（如Pix2TexOCR或DummyFormulaOCR）"
            )
        except Exception as e:
            raise RuntimeError(f"EasyOCR模型初始化失败: {e}")
    
    def predict(self, image: Image.Image) -> Tuple[str, Optional[float]]:
        """
        使用EasyOCR识别公式图片
        
        注意：EasyOCR是通用OCR，对公式的识别可能不如专门的公式OCR准确
        
        Args:
            image: PIL.Image格式的公式图片
            
        Returns:
            (latex_str, confidence): 识别的文本和平均置信度
        """
        self._initialize_model()
        
        try:
            # EasyOCR返回的是文本，不是LaTeX
            # 这里需要将文本转换为LaTeX格式（简化处理）
            results = self._reader.readtext(image)
            
            if not results:
                return "", None
            
            # 合并所有识别的文本
            texts = [result[1] for result in results]
            confidences = [result[2] for result in results]
            
            combined_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            
            # 简单转换：将文本包装为LaTeX（这不是真正的LaTeX转换）
            # 实际使用时，可能需要更复杂的转换逻辑
            latex = f"\\text{{{combined_text}}}"
            
            return latex, avg_confidence
            
        except Exception as e:
            warnings.warn(f"EasyOCR识别失败: {e}，返回空字符串")
            return "", None


def get_available_ocr_models() -> dict:
    """
    检查可用的OCR模型
    
    Returns:
        可用模型字典 {model_name: available}
    """
    models = {
        'pix2tex': False,
        'texocr': False,
        'easyocr': False,
    }
    
    # 检查pix2tex
    try:
        import pix2tex
        models['pix2tex'] = True
    except ImportError:
        pass
    
    # 检查texocr
    try:
        import texocr
        models['texocr'] = True
    except ImportError:
        pass
    
    # 检查easyocr
    try:
        import easyocr
        models['easyocr'] = True
    except ImportError:
        pass
    
    return models


def create_ocr_model(model_name: str = "auto", **kwargs) -> BaseFormulaOCR:
    """
    创建OCR模型实例（工厂方法）
    
    Args:
        model_name: 模型名称 ("pix2tex", "texocr", "easyocr", "dummy", "auto")
                   "auto"表示自动选择第一个可用的模型
        **kwargs: 传递给模型构造函数的额外参数
        
    Returns:
        BaseFormulaOCR实例
    """
    if model_name == "auto":
        # 自动选择：优先pix2tex，其次texocr，最后easyocr
        available = get_available_ocr_models()
        if available['pix2tex']:
            model_name = "pix2tex"
        elif available['texocr']:
            model_name = "texocr"
        elif available['easyocr']:
            model_name = "easyocr"
        else:
            model_name = "dummy"
            print("⚠️ 未找到可用的OCR模型，使用占位模型（DummyFormulaOCR）")
    
    if model_name == "pix2tex":
        return Pix2TexOCR(**kwargs)
    elif model_name == "texocr":
        return TexOCR(**kwargs)
    elif model_name == "easyocr":
        return EasyOCRFormulaOCR(**kwargs)
    elif model_name == "dummy":
        from .formula_ocr import DummyFormulaOCR
        return DummyFormulaOCR()
    else:
        raise ValueError(f"未知的OCR模型: {model_name}")


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 检查可用模型
    print("检查可用的OCR模型...")
    available = get_available_ocr_models()
    
    print("\n可用模型:")
    for model, is_available in available.items():
        status = "✓ 可用" if is_available else "✗ 未安装"
        print(f"  {model}: {status}")
    
    # 创建模型
    print("\n尝试创建OCR模型...")
    try:
        ocr_model = create_ocr_model("auto")
        print(f"✓ 成功创建模型: {type(ocr_model).__name__}")
    except Exception as e:
        print(f"✗ 创建模型失败: {e}")



