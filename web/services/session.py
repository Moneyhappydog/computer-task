"""
会话管理服务
管理文档处理会话的生命周期
"""
import uuid
import time
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionManager:
    """会话管理器（使用全局单例）"""
    
    _instance = None  # 单例实例
    _sessions = {}    # 全局会话存储
    
    def __new__(cls):
        """确保只有一个实例"""
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._sessions = {}  # 初始化会话存储
            logger.info("🔧 SessionManager 单例已创建")
        return cls._instance
    
    def create_session(self, file_path: str, filename: str) -> str:
        """
        创建新会话
        
        Args:
            file_path: 文件路径
            filename: 文件名
            
        Returns:
            session_id: 会话ID
        """
        session_id = str(uuid.uuid4())
        
        session = {
            'id': session_id,
            'filename': filename,
            'file_path': file_path,
            'status': 'uploaded',  # uploaded, processing, completed, error
            'progress': 0,
            'created_at': time.time(),
            'updated_at': time.time(),
            'layers': {
                'layer1': {'status': 'pending', 'progress': 0, 'message': ''},
                'layer2': {'status': 'pending', 'progress': 0, 'message': ''},
                'layer3': {'status': 'pending', 'progress': 0, 'message': ''},
                'layer4': {'status': 'pending', 'progress': 0, 'message': ''}
            },
            'result': None,
            'error': None
        }
        
        SessionManager._sessions[session_id] = session
        logger.info(f"✅ 会话已创建: {session_id} ({filename})")
        logger.info(f"📊 当前会话总数: {len(SessionManager._sessions)}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            session: 会话信息，不存在返回None
        """
        session = SessionManager._sessions.get(session_id)
        
        if session:
            logger.debug(f"🔍 获取会话: {session_id} (状态: {session.get('status')})")
        else:
            logger.warning(f"⚠️ 会话不存在: {session_id}")
            logger.warning(f"📋 现有会话列表: {list(SessionManager._sessions.keys())}")
        
        return session
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        更新会话信息
        
        Args:
            session_id: 会话ID
            **kwargs: 要更新的字段
            
        Returns:
            success: 是否成功
        """
        if session_id not in SessionManager._sessions:
            logger.error(f"❌ 更新失败，会话不存在: {session_id}")
            return False
        
        session = SessionManager._sessions[session_id]
        session.update(kwargs)
        session['updated_at'] = time.time()
        
        logger.info(f"🔄 会话已更新: {session_id} - {kwargs}")
        
        return True
    
    def update_layer_progress(
        self, 
        session_id: str, 
        layer: str, 
        progress: int,
        status: str = 'processing',
        message: str = ''
    ) -> bool:
        """
        更新层级进度
        
        Args:
            session_id: 会话ID
            layer: 层级名称 (layer1, layer2, layer3, layer4)
            progress: 进度 (0-100)
            status: 状态
            message: 消息
            
        Returns:
            success: 是否成功
        """
        if session_id not in SessionManager._sessions:
            logger.error(f"❌ 更新层级进度失败，会话不存在: {session_id}")
            return False
        
        session = SessionManager._sessions[session_id]
        
        if layer not in session['layers']:
            logger.error(f"❌ 层级不存在: {layer}")
            return False
        
        session['layers'][layer].update({
            'status': status,
            'progress': progress,
            'message': message
        })
        
        # 计算总体进度（四层平均）
        total_progress = sum(
            layer_info['progress'] 
            for layer_info in session['layers'].values()
        ) / 4
        
        session['progress'] = int(total_progress)
        session['updated_at'] = time.time()
        
        logger.debug(f"📊 {layer} 进度: {progress}% - {message}")
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            success: 是否成功
        """
        if session_id in SessionManager._sessions:
            session = SessionManager._sessions.pop(session_id)
            logger.info(f"🗑️ 会话已删除: {session_id}")
            
            # 清理文件
            try:
                file_path = Path(session.get('file_path', ''))
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"🗑️ 文件已删除: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ 文件删除失败: {e}")
            
            return True
        
        logger.warning(f"⚠️ 删除失败，会话不存在: {session_id}")
        return False
    
    def list_sessions(self) -> Dict[str, Dict]:
        """
        列出所有会话
        
        Returns:
            sessions: 会话列表
        """
        logger.info(f"📋 当前会话总数: {len(SessionManager._sessions)}")
        return SessionManager._sessions.copy()
    
    def cleanup_old_sessions(self, max_age: int = 3600) -> int:
        """
        清理旧会话
        
        Args:
            max_age: 最大保留时间（秒），默认1小时
            
        Returns:
            count: 清理的会话数
        """
        current_time = time.time()
        to_delete = []
        
        for session_id, session in SessionManager._sessions.items():
            age = current_time - session.get('created_at', 0)
            if age > max_age and session.get('status') in ['completed', 'error']:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            self.delete_session(session_id)
        
        if to_delete:
            logger.info(f"🧹 清理了 {len(to_delete)} 个旧会话")
        
        return len(to_delete)


# 全局单例实例
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    获取会话管理器单例
    
    Returns:
        SessionManager: 会话管理器实例
    """
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
        logger.info("🔧 获取 SessionManager 单例")
    
    return _session_manager