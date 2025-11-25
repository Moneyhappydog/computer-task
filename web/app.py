"""
Flask Web应用主文件
"""
import os
import sys
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 初始化 SocketIO
socketio = SocketIO()

def create_app(config=None):
    """
    创建Flask应用实例
    
    Args:
        config: 配置对象
        
    Returns:
        Flask: Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__)
    
    # 加载配置
    if config is None:
        from web.config import get_config
        config = get_config()
    
    app.config.from_object(config)
    
    # 确保必要的目录存在
    create_directories(app)
    
    # 初始化 SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS', '*'),
        async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading')
    )
    
    # 注册WebSocket事件处理器
    register_socketio_events(socketio)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册模板过滤器
    register_template_filters(app)
    
    return app

def register_socketio_events(socketio):
    """
    注册WebSocket事件处理器
    
    Args:
        socketio: SocketIO实例
    """
    try:
        from web.services.socketio_events import register_socketio_events as register_events
        register_events(socketio)
        app.logger.info("✓ WebSocket事件处理器注册完成")
    except ImportError as e:
        app.logger.warning(f"⚠ WebSocket事件处理器注册失败: {e}")

def create_directories(app):
    """
    创建必要的目录
    
    Args:
        app: Flask应用实例
    """
    directories = [
        app.config.get('UPLOAD_FOLDER', 'uploads'),
        app.config.get('OUTPUT_FOLDER', 'data/output'),
        app.config.get('LOG_DIR', 'logs'),
        'web/static/uploads',
        'web/static/outputs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def register_blueprints(app):
    """
    注册蓝图
    
    Args:
        app: Flask应用实例
    """
    try:
        # 导入路由蓝图
        from web.routes.main import bp as main_bp
        from web.routes.api import bp as api_bp
        
        # 注册蓝图
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
        
        app.logger.info("✓ 蓝图注册完成")
    except ImportError as e:
        app.logger.error(f"✗ 蓝图注册失败: {e}")
        raise

def register_error_handlers(app):
    """
    注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    try:
        from web.errors import init_error_handlers
        init_error_handlers(app)
        app.logger.info("✓ 错误处理器注册完成")
    except ImportError as e:
        app.logger.warning(f"⚠ 错误处理器注册失败: {e}")

def register_template_filters(app):
    """
    注册模板过滤器
    
    Args:
        app: Flask应用实例
    """
    from datetime import datetime
    
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """格式化日期时间"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return value.strftime(format)
    
    @app.template_filter('filesize')
    def format_filesize(bytes):
        """格式化文件大小"""
        if bytes is None:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    app.logger.info("✓ 模板过滤器注册完成")

# 如果直接运行此文件
if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)