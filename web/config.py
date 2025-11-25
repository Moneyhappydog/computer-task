"""
Web应用配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置"""
    
    # 应用密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 文件上传
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 52428800))  # 默认50MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_DIR', 'data/output')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}
    
    # Session配置
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    SESSION_CLEANUP_INTERVAL = int(os.environ.get('SESSION_CLEANUP_INTERVAL', 300))
    
    # SocketIO配置
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/web.log')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    
    # API配置
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 300))
    
    # 核心配置文件路径
    CORE_CONFIG_PATH = os.environ.get('CORE_CONFIG_PATH', 'config/config.yaml')
    
    # 输入输出目录
    INPUT_DIR = os.environ.get('INPUT_DIR', 'data/input')
    
    # 处理配置
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 2000))
    OCR_LANG = os.environ.get('OCR_LANG', 'chi_sim+eng')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境使用更安全的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
    
    # 生产环境限制CORS
    cors_origins = os.environ.get('CORS_ORIGINS', '')
    if cors_origins:
        SOCKETIO_CORS_ALLOWED_ORIGINS = cors_origins.split(',')

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 使用临时目录
    UPLOAD_FOLDER = 'test_uploads'
    OUTPUT_FOLDER = 'test_outputs'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """
    获取配置对象
    
    Args:
        env: 环境名称 (development/production/testing)
        
    Returns:
        Config: 配置对象
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])