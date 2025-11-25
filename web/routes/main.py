"""
主路由模块
"""
from flask import Blueprint, render_template, request, session, redirect, url_for
import uuid
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """上传页面"""
    if request.method == 'POST':
        # 创建新会话
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        session['upload_time'] = datetime.now().isoformat()
        
        # 重定向到处理页面
        return redirect(url_for('main.process', session_id=session_id))
    
    return render_template('upload.html')

@bp.route('/process')
def process():
    """处理页面"""
    session_id = request.args.get('session_id') or session.get('session_id')
    
    if not session_id:
        return redirect(url_for('main.index'))
    
    return render_template('process.html', session_id=session_id)

@bp.route('/result/<session_id>')
def result(session_id):
    """结果页面"""
    return render_template('result.html', session_id=session_id)

@bp.route('/history')
def history():
    """历史记录页面"""
    return render_template('history.html')

@bp.route('/help')
def help():
    """帮助文档页面"""
    return render_template('help.html')

@bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')