"""
上传路由
处理文件上传
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
import uuid

from web.services.session import get_session_manager

bp = Blueprint('upload', __name__, url_prefix='/api/upload')
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=['POST'])
def upload_file():
    """
    上传文件
    
    Returns:
        JSON: {session_id, filename, file_size}
    """
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'不支持的文件类型。支持: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # 安全的文件名
        filename = secure_filename(file.filename)
        
        # ✅ 先生成 session_id
        session_id = str(uuid.uuid4())
        
        # 创建文件保存目录
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        session_folder = upload_folder / session_id
        session_folder.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = session_folder / filename
        file.save(str(file_path))
        
        file_size = file_path.stat().st_size
        
        logger.info(f"📁 文件已保存: {file_path} ({file_size} bytes)")
        
        # ✅ 创建会话（传入完整路径和文件名）
        session_manager = get_session_manager()
        created_session_id = session_manager.create_session(
            file_path=str(file_path),  # ← 完整路径
            filename=filename          # ← 文件名
        )
        
        # ✅ 验证 session_id 匹配
        if created_session_id != session_id:
            logger.warning(f"⚠️ Session ID 不匹配: 生成={session_id}, 创建={created_session_id}")
            session_id = created_session_id  # 使用 SessionManager 生成的 ID
        
        # 更新会话信息（添加文件大小）
        session_manager.update_session(
            session_id,
            file_size=file_size
        )
        
        logger.info(f"✅ 文件上传成功: {filename} (session: {session_id})")
        
        # ✅ 验证会话存在
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"❌ 会话创建后立即丢失: {session_id}")
            raise Exception("会话创建失败")
        
        logger.info(f"✅ 会话验证成功: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'file_size': file_size
        })
    
    except Exception as e:
        logger.error(f"❌ 文件上传失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500