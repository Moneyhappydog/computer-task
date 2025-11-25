"""
WebSocket事件处理
"""
from flask_socketio import emit, join_room, leave_room
from flask import request
import logging

logger = logging.getLogger(__name__)

def register_socketio_events(socketio):
    """
    注册WebSocket事件处理器
    
    Args:
        socketio: SocketIO实例
    """
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接事件"""
        logger.info(f'客户端连接: {request.sid}')
        emit('connected', {'message': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接事件"""
        logger.info(f'客户端断开连接: {request.sid}')
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """加入会话房间"""
        session_id = data.get('session_id')
        if session_id:
            join_room(session_id)
            logger.info(f'客户端 {request.sid} 加入会话房间: {session_id}')
            emit('joined_session', {'session_id': session_id})
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """离开会话房间"""
        session_id = data.get('session_id')
        if session_id:
            leave_room(session_id)
            logger.info(f'客户端 {request.sid} 离开会话房间: {session_id}')
            emit('left_session', {'session_id': session_id})
    
    @socketio.on('ping')
    def handle_ping():
        """心跳检测"""
        emit('pong', {'timestamp': str(request.timestamp)})
    
    logger.info('✅ WebSocket事件处理器注册完成')