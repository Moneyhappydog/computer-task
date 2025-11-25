"""
配置管理模块
负责加载和验证所有配置项
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# 加载.env文件
load_dotenv()

class Config:
    """项目配置类 - 所有配置的统一入口"""
    
    # ===== 项目根目录 =====
    ROOT_DIR = Path(__file__).parent.parent.parent
    
    # ===== 千问API配置 =====
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen-plus")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # ===== Anthropic API配置（可选）=====
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
    
    # ===== 工具路径配置 =====
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
    DITA_OT_DIR = ROOT_DIR / os.getenv("DITA_OT_DIR", "dita-ot/dita-ot-4.3.5")
    POPPLER_PATH = os.getenv("POPPLER_PATH")  # pdf2image需要
    
    # ===== 目录配置 =====
    CONFIG_DIR = ROOT_DIR / "config"
    INPUT_DIR = ROOT_DIR / os.getenv("INPUT_DIR", "data/input")
    OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "data/output")
    TEMPLATE_DIR = ROOT_DIR / "data/templates"
    LOG_DIR = ROOT_DIR / os.getenv("LOG_DIR", "logs")
    
    # ===== 日志配置 =====
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # ===== 处理配置 =====
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
    OCR_LANG = os.getenv("OCR_LANG", "chi_sim+eng")
    
    @classmethod
    def validate(cls):
        """
        验证配置是否完整
        检查必需的API Key和目录
        """
        errors = []
        warnings = []
        
        # 检查必需的API Key
        if not cls.OPENAI_API_KEY:
            errors.append("❌ OPENAI_API_KEY 未设置，请检查.env文件")
        
        # 检查DITA-OT是否存在
        if not cls.DITA_OT_DIR.exists():
            warnings.append(f"⚠️  DITA-OT目录不存在: {cls.DITA_OT_DIR}")
            warnings.append(f"   请确保已解压dita-ot-4.3.5到dita-ot目录")
        
        # 创建必需的目录
        for dir_path in [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.TEMPLATE_DIR, cls.LOG_DIR, cls.CONFIG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 检查Tesseract是否安装
        import shutil
        if not shutil.which(cls.TESSERACT_CMD):
            warnings.append(f"⚠️  Tesseract未找到，OCR功能将不可用")
            warnings.append(f"   如需使用OCR，请安装Tesseract-OCR")
        
        # 输出错误
        if errors:
            error_msg = "\n配置错误:\n" + "\n".join(errors)
            raise ValueError(error_msg)
        
        # 输出警告
        if warnings:
            for w in warnings:
                print(w)
        
        return True
    
    @classmethod
    def show(cls):
        """显示当前配置信息（用于调试）"""
        print("=" * 70)
        print("📋 DITA转换器配置信息")
        print("=" * 70)
        print(f"AI模型:        {cls.OPENAI_MODEL}")
        print(f"API地址:       {cls.OPENAI_BASE_URL}")
        print(f"API Key:       {cls.OPENAI_API_KEY[:20]}... (已隐藏)")
        print(f"DITA-OT:       {cls.DITA_OT_DIR}")
        print(f"输入目录:      {cls.INPUT_DIR}")
        print(f"输出目录:      {cls.OUTPUT_DIR}")
        print(f"模板目录:      {cls.TEMPLATE_DIR}")
        print(f"日志目录:      {cls.LOG_DIR}")
        print(f"日志级别:      {cls.LOG_LEVEL}")
        print(f"最大并发:      {cls.MAX_WORKERS}")
        print(f"分块大小:      {cls.CHUNK_SIZE}")
        print(f"OCR语言:       {cls.OCR_LANG}")
        print("=" * 70)