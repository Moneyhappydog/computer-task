"""
日志管理模块
使用loguru提供彩色日志和文件日志
"""
from loguru import logger
from pathlib import Path
from datetime import datetime
import sys

def setup_logger(name: str = "dita-converter", log_dir: Path = None):
    """
    设置并配置loguru日志记录器
    
    Args:
        name: 日志器名称（用于生成日志文件名）
        log_dir: 日志目录（默认使用Config.LOG_DIR）
        
    Returns:
        配置好的logger实例
    """
    from .config import Config
    
    # 使用默认日志目录
    if log_dir is None:
        log_dir = Config.LOG_DIR
    
    # 移除默认的控制台处理器
    logger.remove()
    
    # ===== 添加控制台处理器（彩色输出）=====
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=Config.LOG_LEVEL
    )
    
    # ===== 添加文件处理器（详细日志）=====
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        log_file,
        rotation="500 MB",      # 单个日志文件最大500MB
        retention="10 days",    # 保留10天
        compression="zip",      # 自动压缩旧日志
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",          # 文件记录DEBUG级别
        encoding="utf-8"
    )
    
    logger.info(f"✓ 日志系统初始化完成: {log_file}")
    
    return logger

# 创建默认logger实例（供其他模块导入使用）
log = setup_logger()