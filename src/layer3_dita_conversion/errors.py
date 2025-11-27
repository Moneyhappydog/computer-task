"""
统一错误处理模块
定义DITA转换过程中的标准错误类型和格式
"""
from typing import Optional, Dict, Any


class DITAConversionError(Exception):
    """
    DITA转换过程中的统一异常类
    """
    def __init__(
        self,
        message: str,
        error_code: str,
        component: str,
        details: Optional[Dict[str, Any]] = None,
        is_warning: bool = False
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码（如 "TEMPLATE_NOT_FOUND", "STRUCTURE_VALIDATION_FAILED"）
            component: 出错的组件（如 "TemplateRenderer", "ContentStructurer"）
            details: 详细错误信息（可选）
            is_warning: 是否为警告（默认False）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.component = component
        self.details = details or {}
        self.is_warning = is_warning
        
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含错误信息的字典
        """
        return {
            "message": self.message,
            "error_code": self.error_code,
            "component": self.component,
            "details": self.details,
            "is_warning": self.is_warning
        }
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            格式化的错误字符串
        """
        prefix = "警告" if self.is_warning else "错误"
        return f"{prefix} [{self.error_code}] ({self.component}): {self.message}"


class TemplateError(DITAConversionError):
    """
    模板相关错误
    """
    def __init__(self,
                 message: str,
                 error_code: str = "TEMPLATE_ERROR",
                 details: Optional[Dict[str, Any]] = None,
                 is_warning: bool = False):
        super().__init__(message, error_code, "TemplateRenderer", details, is_warning)


class StructureError(DITAConversionError):
    """
    内容结构相关错误
    """
    def __init__(self,
                 message: str,
                 error_code: str = "STRUCTURE_ERROR",
                 details: Optional[Dict[str, Any]] = None,
                 is_warning: bool = False):
        super().__init__(message, error_code, "ContentStructurer", details, is_warning)


class ConstraintError(DITAConversionError):
    """
    约束验证相关错误
    """
    def __init__(self,
                 message: str,
                 error_code: str = "CONSTRAINT_ERROR",
                 details: Optional[Dict[str, Any]] = None,
                 is_warning: bool = False):
        super().__init__(message, error_code, "ConstraintEngine", details, is_warning)


class XMLValidationError(DITAConversionError):
    """
    XML验证相关错误
    """
    def __init__(self,
                 message: str,
                 error_code: str = "XML_VALIDATION_ERROR",
                 details: Optional[Dict[str, Any]] = None,
                 is_warning: bool = False):
        super().__init__(message, error_code, "XMLValidator", details, is_warning)


class ConverterError(DITAConversionError):
    """
    转换器主流程错误
    """
    def __init__(self,
                 message: str,
                 error_code: str = "CONVERTER_ERROR",
                 details: Optional[Dict[str, Any]] = None,
                 is_warning: bool = False):
        super().__init__(message, error_code, "DITAConverter", details, is_warning)


class ErrorHandler:
    """
    错误处理器
    管理错误的收集、分类和报告
    """
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def add_error(self, error: DITAConversionError):
        """
        添加错误
        
        Args:
            error: DITAConversionError实例
        """
        if error.is_warning:
            self.warnings.append(error)
        else:
            self.errors.append(error)
    
    def add_errors(self, errors: list):
        """
        批量添加错误
        
        Args:
            errors: 错误列表
        """
        for error in errors:
            if isinstance(error, DITAConversionError):
                self.add_error(error)
            else:
                # 兼容旧格式的字符串错误
                self.add_error(ConverterError(
                    str(error),
                    "LEGACY_ERROR",
                    "Unknown"
                ))
    
    def get_results(self) -> Dict[str, Any]:
        """
        获取错误处理结果
        
        Returns:
            包含错误、警告和统计信息的字典
        """
        return {
            "errors": [err.to_dict() for err in self.errors],
            "warnings": [warn.to_dict() for warn in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "has_errors": len(self.errors) > 0,
            "has_warnings": len(self.warnings) > 0
        }
    
    def clear(self):
        """
        清空错误和警告
        """
        self.errors = []
        self.warnings = []
