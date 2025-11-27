"""
处理路由
执行文档转换处理
"""
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit
from pathlib import Path
import logging
import threading
import time
import traceback

from web.app import socketio
from web.services.session import get_session_manager

bp = Blueprint('process', __name__, url_prefix='/api/process')
logger = logging.getLogger(__name__)

@bp.route('/start/<session_id>', methods=['POST'])
def start_processing(session_id):
    """
    启动处理
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON: {success, message}
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        return jsonify({'error': '会话不存在'}), 404
    
    if session['status'] != 'uploaded':
        return jsonify({'error': '会话状态不正确'}), 400
    
    # 更新状态
    session_manager.update_session(session_id, status='processing')
    
    # ✅ 获取当前 Flask app 实例
    app = current_app._get_current_object()
    
    # 在后台线程中处理（传递 app）
    thread = threading.Thread(
        target=process_document,
        args=(app, session_id)  # ← 传递 app
    )
    thread.daemon = True
    thread.start()
    
    logger.info(f"🚀 开始处理会话: {session_id}")
    
    return jsonify({
        'success': True,
        'message': '处理已启动',
        'session_id': session_id
    })

@bp.route('/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """
    获取处理状态
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON: 会话信息
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        return jsonify({'error': '会话不存在'}), 404
    
    return jsonify(session)

def process_document(app, session_id: str):  # ← 接收 app 参数
    """
    处理文档（后台线程）- 使用统一的ProcessingPipeline服务
    
    Args:
        app: Flask 应用实例
        session_id: 会话ID
    """
    # ✅ 在后台线程中创建应用上下文
    with app.app_context():
        logger.info(f"🚀 开始处理会话: {session_id}")
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        
        if not session:
            logger.error(f"❌ 会话不存在: {session_id}")
            return
            
        session_manager.update_session(session_id, status='processing', progress=0)
        
        # 获取会话信息
        input_file = session.get('input_file')
        output_dir = session.get('output_dir')
        
        if not input_file or not output_dir:
            error_msg = "会话信息不完整，缺少输入文件或输出目录"
            logger.error(f"❌ {error_msg}: {session_id}")
            session_manager.update_session(session_id, status='error', error=error_msg)
            return
        
        try:
            input_file_path = Path(input_file)
            output_dir_path = Path(output_dir)
            
            logger.info(f"📂 输入文件: {input_file}")
            logger.info(f"📂 输出目录: {output_dir}")
            
            # 进度推送函数
            def push_progress(stage, progress, message, **kwargs):
                """推送进度到前端"""
                data = {
                    'session_id': session_id,
                    'stage': stage,
                    'progress': progress,
                    'message': message,
                    **kwargs
                }
                
                # 更新会话
                if stage.startswith('layer'):
                    session_manager.update_layer_progress(
                        session_id,
                        stage,
                        progress,
                        status='processing' if progress < 100 else 'completed',
                        message=message
                    )
                
                # WebSocket推送 - 使用线程安全的方式
                try:
                    socketio.emit('progress_update', data, namespace='/process')
                except Exception as ws_error:
                    logger.warning(f"WebSocket推送失败: {ws_error}")
                logger.info(f"📊 {stage}: {progress}% - {message}")
            
            # 使用统一的ProcessingPipeline服务
            config = get_config()
            pipeline = ProcessingPipeline(config)
            
            # 定义进度回调函数
            def progress_callback(layer, progress, message, details=None, result=None):
                """
                进度回调函数
                """
                # 更新进度
                session_manager.update_layer_progress(session_id, layer, progress, message)
                push_progress(layer, progress, message, details, result)
                
                # 更新会话总进度
                if progress == 100:
                    # 计算总进度
                    layers = {'layer1': 25, 'layer2': 50, 'layer3': 75, 'layer4': 100}
                    if layer in layers:
                        total_progress = layers[layer]
                        session_manager.update_session(session_id, progress=total_progress)
            
            # 执行处理流程
            result = pipeline.process(
                input_file=str(input_file_path),
                output_dir=str(output_dir_path),
                progress_callback=progress_callback
            )
            
            # ========== 完成 ==========
            
            # ========== 完成 ==========
            if result['success']:
                # 更新会话
                session_manager.update_session(
                    session_id,
                    status='completed',
                    progress=100,
                    result=result,
                    output_dir=str(output_dir)
                )
                
                push_progress('complete', 100, '处理完成！', result=result)
                logger.info(f"✅ 处理完成: {session_id}")
            else:
                error_msg = result.get('error', '处理失败')
                logger.error(f"❌ {error_msg}: {session_id}")
                
                # 更新会话
                session_manager.update_session(
                    session_id,
                    status='error',
                    error=error_msg
                )
                
                # 推送错误 - 使用线程安全的方式
                try:
                    socketio.emit('progress_update', {
                        'session_id': session_id,
                        'stage': 'error',
                        'progress': 0,
                        'message': error_msg,
                        'error': str(error_msg)
                    }, namespace='/process')
                except Exception as ws_error:
                    logger.warning(f"WebSocket错误推送失败: {ws_error}")
        
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            logger.error(f"❌ {error_msg}\n{traceback.format_exc()}")
            
            # 更新会话
            session_manager.update_session(
                session_id,
                status='error',
                error=error_msg
            )
            
            # 推送错误 - 使用线程安全的方式
            try:
                socketio.emit('progress_update', {
                    'session_id': session_id,
                    'stage': 'error',
                    'progress': 0,
                    'message': error_msg,
                    'error': str(e)
                }, namespace='/process')
            except Exception as ws_error:
                logger.warning(f"WebSocket错误推送失败: {ws_error}")

# WebSocket事件
@socketio.on('connect', namespace='/process')
def handle_connect():
    """客户端连接"""
    logger.info("🔌 客户端连接到 /process")

@socketio.on('disconnect', namespace='/process')
def handle_disconnect():
    """客户端断开"""
    logger.info("🔌 客户端断开 /process")

@socketio.on('subscribe', namespace='/process')
def handle_subscribe(data):
    """订阅会话更新"""
    session_id = data.get('session_id')
    logger.info(f"📡 订阅会话: {session_id}")
    emit('subscribed', {'session_id': session_id})