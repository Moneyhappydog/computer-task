#!/usr/bin/env python3
"""
Web应用启动脚本
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web.app import create_app, socketio
from web.config import get_config

def setup_logging(log_level):
    """
    配置日志
    
    Args:
        log_level: 日志级别
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/web.log', encoding='utf-8')
        ]
    )

def create_directories(config):
    """
    创建必要的目录
    
    Args:
        config: 配置对象
    """
    directories = [
        config.UPLOAD_FOLDER,
        config.OUTPUT_FOLDER,
        'logs',
        'web/static/uploads',
        'web/static/outputs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='DITA Converter Web Server')
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='服务器地址 (默认: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='服务器端口 (默认: 5000)'
    )
    parser.add_argument(
        '--env',
        choices=['development', 'production', 'testing'],
        default='development',
        help='运行环境 (默认: development)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日志级别 (默认: INFO)'
    )
    
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ['FLASK_ENV'] = args.env
    
    # 获取配置
    config = get_config(args.env)
    
    # 配置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 创建目录
    create_directories(config)
    
    # 创建应用
    app = create_app(config)
    
    # 启动信息
    logger.info("=" * 70)
    logger.info("🚀 DITA Converter Web Server Starting...")
    logger.info("=" * 70)
    logger.info(f"📝 环境: {args.env}")
    logger.info(f"🌐 地址: http://{args.host}:{args.port}")
    logger.info(f"🔧 调试模式: {'启用' if args.debug or config.DEBUG else '禁用'}")
    logger.info(f"📊 日志级别: {args.log_level}")
    logger.info("=" * 70)
    
    try:
        # 启动服务器
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug or config.DEBUG,
            use_reloader=args.env == 'development'
        )
    except KeyboardInterrupt:
        logger.info("\n👋 服务器正在关闭...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()