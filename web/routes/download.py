"""
下载路由
下载处理结果
"""
from flask import Blueprint, send_file, jsonify, current_app
from pathlib import Path
import zipfile
import io
import logging

from web.services.session import get_session_manager

bp = Blueprint('download', __name__, url_prefix='/api/download')
logger = logging.getLogger(__name__)

@bp.route('/result/<session_id>', methods=['GET'])
def download_result(session_id):
    """
    下载处理结果（ZIP压缩包）
    
    Args:
        session_id: 会话ID
        
    Returns:
        ZIP文件
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        return jsonify({'error': '会话不存在'}), 404
    
    if session['status'] != 'completed':
        return jsonify({'error': '处理未完成'}), 400
    
    try:
        output_dir = Path(session.get('output_dir'))
        
        if not output_dir.exists():
            return jsonify({'error': '输出目录不存在'}), 404
        
        # 创建ZIP文件（在内存中）
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加所有输出文件
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)
        
        memory_file.seek(0)
        
        filename = f"dita_output_{session['filename'].rsplit('.', 1)[0]}.zip"
        
        logger.info(f"📦 下载结果: {session_id}")
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"❌ 下载失败: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/file/<session_id>/<path:filename>', methods=['GET'])
def download_file(session_id, filename):
    """
    下载单个文件
    
    Args:
        session_id: 会话ID
        filename: 文件名（相对路径）
        
    Returns:
        文件
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        return jsonify({'error': '会话不存在'}), 404
    
    try:
        output_dir = Path(session.get('output_dir'))
        file_path = output_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': '文件不存在'}), 404
        
        # 安全检查：确保文件在输出目录内
        if not str(file_path.resolve()).startswith(str(output_dir.resolve())):
            return jsonify({'error': '非法文件路径'}), 403
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"❌ 下载文件失败: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/list/<session_id>', methods=['GET'])
def list_files(session_id):
    """
    列出输出文件
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON: {files: [...]}
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        return jsonify({'error': '会话不存在'}), 404
    
    if session['status'] != 'completed':
        return jsonify({'error': '处理未完成'}), 400
    
    try:
        output_dir = Path(session.get('output_dir'))
        
        if not output_dir.exists():
            return jsonify({'files': []})
        
        files = []
        for file_path in output_dir.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(output_dir)
                files.append({
                    'name': file_path.name,
                    'path': str(rel_path),
                    'size': file_path.stat().st_size,
                    'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
                })
        
        return jsonify({'files': files})
    
    except Exception as e:
        logger.error(f"❌ 列出文件失败: {e}")
        return jsonify({'error': str(e)}), 500