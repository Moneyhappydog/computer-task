"""
API路由模块
"""
import os
import uuid
import shutil
import threading
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import traceback

bp = Blueprint('api', __name__)

# 存储会话信息
sessions = {}

def allowed_file(filename):
    """
    检查文件类型是否允许
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否允许
    """
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/upload', methods=['POST'])
@bp.route('/upload/', methods=['POST'])  # 同时支持带斜杠
def upload_file():
    """
    处理文件上传
    
    Returns:
        JSON响应
    """
    try:
        current_app.logger.info("收到文件上传请求")
        
        # 检查是否有文件
        if 'file' not in request.files:
            current_app.logger.warning("请求中没有文件")
            return jsonify({
                'success': False,
                'error': '没有文件'
            }), 400
        
        file = request.files['file']
        current_app.logger.info(f"文件名: {file.filename}")
        
        # 检查文件名
        if not file.filename or file.filename == '':
            current_app.logger.warning("文件名为空")
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            current_app.logger.warning(f"不支持的文件类型: {file.filename}")
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型。支持的格式: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}'
            }), 400
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        current_app.logger.info(f"生成会话ID: {session_id}")
        
        # 创建上传目录
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        # 安全的文件名
        filename = secure_filename(file.filename)
        file_path = upload_folder / f"{session_id}_{filename}"
        
        # 保存文件
        current_app.logger.info(f"保存文件到: {file_path}")
        file.save(str(file_path))
        
        # 获取文件信息
        file_size = file_path.stat().st_size
        current_app.logger.info(f"文件大小: {file_size} 字节")
        
        # 保存会话信息
        sessions[session_id] = {
            'session_id': session_id,
            'filename': filename,
            'file_path': str(file_path),
            'file_size': file_size,
            'upload_time': datetime.now().isoformat(),
            'status': 'uploaded',
            'progress': 0,
            'message': '文件上传成功，等待处理'
        }
        
        current_app.logger.info(f"上传成功: {session_id}")
        
        # 返回JSON响应
        response = jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'file_size': file_size,
            'message': '文件上传成功'
        })
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except Exception as e:
        current_app.logger.error(f"上传失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}'
        }), 500

@bp.route('/convert/<session_id>', methods=['POST'])
@bp.route('/process/start/<session_id>', methods=['POST'])
def convert_file(session_id):
    """
    开始转换
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON响应
    """
    try:
        current_app.logger.info(f"开始转换: {session_id}")
        
        # 检查会话是否存在
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session_info = sessions[session_id]
        
        # 修复：使用 force=True 和 silent=True
        try:
            options = request.get_json(force=True, silent=True) or {}
        except Exception as e:
            current_app.logger.warning(f"无法解析JSON: {e}, 使用空选项")
            options = {}
        
        current_app.logger.info(f"转换选项: {options}")
        
        # 更新会话状态
        session_info['status'] = 'converting'
        session_info['options'] = options
        session_info['start_time'] = datetime.now().isoformat()
        session_info['progress'] = 10
        session_info['message'] = '正在初始化转换...'
        
        # ✅ 保存应用实例，用于后台线程
        app = current_app._get_current_object()
        
        # ✅ 使用后台线程处理，避免阻塞请求
        def background_convert():
            """后台转换任务"""
            # ✅ 在后台线程中推入应用上下文
            with app.app_context():
                try:
                    app.logger.info(f"后台转换开始: {session_id}")
                    
                    # 导入处理流水线
                    from web.services.pipeline import ProcessingPipeline
                    
                    # 创建输出目录
                    output_dir = Path(app.config['OUTPUT_FOLDER']) / session_id
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 初始化流水线
                    pipeline = ProcessingPipeline()
                    
                    # 定义进度回调函数
                    def progress_callback(stage, progress, data):
                        """进度回调函数"""
                        session_info['current_stage'] = stage
                        session_info['stage_progress'] = progress
                        session_info['stage_data'] = data
                        
                        # 计算总进度
                        stage_weights = {
                            'layer1': 20,
                            'layer2': 40,
                            'layer3': 70,
                            'layer4': 90,
                            'complete': 100
                        }
                        
                        base_progress = stage_weights.get(stage, 0)
                        stage_progress = progress / 100 * (stage_weights.get(stage, 0) - list(stage_weights.values())[list(stage_weights.keys()).index(stage) - 1] if list(stage_weights.keys()).index(stage) > 0 else 0)
                        total_progress = min(100, base_progress + stage_progress)
                        
                        session_info['progress'] = int(total_progress)
                        session_info['message'] = data.get('message', f'{stage} 处理中...')
                        
                        # 发送WebSocket消息（如果可用）
                        try:
                            from web.app import socketio
                            socketio.emit('progress_update', {
                                'session_id': session_id,
                                'stage': stage,
                                'progress': int(total_progress),
                                'stage_progress': progress,
                                'message': data.get('message'),
                                'data': data
                            })
                        except Exception as socket_error:
                            app.logger.warning(f"WebSocket发送失败: {socket_error}")
                        
                        app.logger.info(f"进度更新: {stage} {progress}% - {data.get('message')}")
                    
                    # 执行转换
                    input_file = Path(session_info['file_path'])
                    result = pipeline.process(
                        input_file=input_file,
                        output_dir=output_dir,
                        progress_callback=progress_callback
                    )
                    
                    # 保存结果
                    session_info['result'] = result
                    session_info['status'] = 'completed' if result['success'] else 'error'
                    session_info['progress'] = 100
                    session_info['complete_time'] = datetime.now().isoformat()
                    
                    if result['success']:
                        session_info['message'] = '🎉 转换完成！'
                        session_info['output_dir'] = str(output_dir / 'final_dita')
                        
                        # 发送完成通知
                        try:
                            from web.app import socketio
                            socketio.emit('conversion_complete', {
                                'session_id': session_id,
                                'output_dir': session_info['output_dir'],
                                'result': result
                            })
                        except Exception as socket_error:
                            app.logger.warning(f"WebSocket发送失败: {socket_error}")
                    else:
                        session_info['message'] = f'❌ 转换失败: {result.get("errors", ["未知错误"])[0]}'
                        session_info['error'] = result.get('errors', ["未知错误"])
                        
                        # 发送错误通知
                        try:
                            from web.app import socketio
                            socketio.emit('conversion_error', {
                                'session_id': session_id,
                                'error': session_info['error']
                            })
                        except Exception as socket_error:
                            app.logger.warning(f"WebSocket发送失败: {socket_error}")
                    
                    app.logger.info(f"转换完成: {session_id} - {session_info['status']}")
                    
                except Exception as e:
                    app.logger.error(f"后台转换失败: {e}\n{traceback.format_exc()}")
                    session_info['status'] = 'error'
                    session_info['error'] = str(e)
                    session_info['message'] = f'转换失败: {str(e)}'
                    session_info['progress'] = 0
                    
                    # 发送错误通知
                    try:
                        from web.app import socketio
                        socketio.emit('conversion_error', {
                            'session_id': session_id,
                            'error': str(e)
                        })
                    except Exception as socket_error:
                        app.logger.warning(f"WebSocket发送失败: {socket_error}")
        
        # 启动后台线程
        thread = threading.Thread(target=background_convert)
        thread.daemon = True
        thread.start()
        
        # 立即返回响应，不等待转换完成
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '转换已开始'
        })
        
    except Exception as e:
        current_app.logger.error(f"转换失败: {e}\n{traceback.format_exc()}")
        if session_id in sessions:
            sessions[session_id]['status'] = 'error'
            sessions[session_id]['error'] = str(e)
            sessions[session_id]['message'] = f'转换失败: {str(e)}'
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/result/<session_id>', methods=['GET'])
@bp.route('/process/result/<session_id>', methods=['GET'])
def get_result(session_id):
    """
    获取转换详细结果
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON响应
    """
    try:
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session_info = sessions[session_id]
        
        # 检查转换是否完成
        if session_info.get('status') != 'completed':
            return jsonify({
                'success': False,
                'error': '转换尚未完成'
            }), 400
        
        result = session_info.get('result', {})
        
        # 提取各层结果用于展示
        layers_result = {}
        for layer_name, layer_data in result.get('layers', {}).items():
            layers_result[layer_name] = layer_data
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': session_info.get('filename'),
            'result': result,
            'layers': layers_result,
            'output_dir': session_info.get('output_dir'),
            'start_time': result.get('start_time'),
            'end_time': result.get('end_time'),
            'success': result.get('success', False)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取结果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/layer/<session_id>/<layer_name>', methods=['GET'])
def get_layer_result(session_id, layer_name):
    """
    获取特定层的处理结果
    
    Args:
        session_id: 会话ID
        layer_name: 层名称 (layer1, layer2, layer3, layer4)
        
    Returns:
        JSON响应
    """
    try:
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session_info = sessions[session_id]
        
        # 检查转换是否完成
        if session_info.get('status') != 'completed':
            return jsonify({
                'success': False,
                'error': '转换尚未完成'
            }), 400
        
        result = session_info.get('result', {})
        layers = result.get('layers', {})
        
        if layer_name not in layers:
            return jsonify({
                'success': False,
                'error': f'层 {layer_name} 不存在'
            }), 404
        
        layer_result = layers[layer_name]
        
        # 根据不同层返回不同的详细信息
        if layer_name == 'layer1':
            # 预处理层：返回Markdown内容
            return jsonify({
                'success': True,
                'layer_name': layer_name,
                'layer_title': '预处理层',
                'file_type': layer_result.get('file_type'),
                'markdown_length': len(layer_result.get('markdown', '')),
                'markdown': layer_result.get('markdown', ''),
                'statistics': layer_result.get('statistics', {})
            })
        
        elif layer_name == 'layer2':
            # 语义分析层：返回分块结果
            chunks = layer_result.get('chunks', [])
            return jsonify({
                'success': True,
                'layer_name': layer_name,
                'layer_title': '语义分析层',
                'total_chunks': len(chunks),
                'chunks': chunks[:10],  # 只返回前10个块作为预览
                'statistics': layer_result.get('statistics', {}),
                'has_more': len(chunks) > 10
            })
        
        elif layer_name == 'layer3':
            # DITA转换层：返回转换结果
            return jsonify({
                'success': True,
                'layer_name': layer_name,
                'layer_title': 'DITA转换层',
                'total': layer_result.get('total', 0),
                'success': layer_result.get('success', 0),
                'failed': layer_result.get('failed', 0),
                'success_rate': layer_result.get('success_rate', 0)
            })
        
        elif layer_name == 'layer4':
            # 质量保证层：返回质量评估结果
            return jsonify({
                'success': True,
                'layer_name': layer_name,
                'layer_title': '质量保证层',
                'total': layer_result.get('total', 0),
                'success': layer_result.get('success', 0),
                'failed': layer_result.get('failed', 0),
                'success_rate': layer_result.get('success_rate', 0),
                'avg_quality_score': layer_result.get('avg_quality_score', 0),
                'summary': layer_result.get('summary', {})
            })
        
        else:
            return jsonify({
                'success': False,
                'error': f'未知的层名称: {layer_name}'
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"获取层结果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/status/<session_id>', methods=['GET'])
@bp.route('/process/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """
    获取转换状态
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON响应
    """
    try:
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session_info = sessions[session_id]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': session_info.get('status', 'unknown'),
            'progress': session_info.get('progress', 0),
            'message': session_info.get('message', ''),
            'filename': session_info.get('filename', ''),
            'file_size': session_info.get('file_size', 0),
            'upload_time': session_info.get('upload_time', ''),
            'error': session_info.get('error', '')
        })
        
    except Exception as e:
        current_app.logger.error(f"获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/download/<session_id>', methods=['GET'])
@bp.route('/download/result/<session_id>', methods=['GET'])
def download_result(session_id):
    """
    下载转换结果
    
    Args:
        session_id: 会话ID
        
    Returns:
        文件下载
    """
    try:
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session_info = sessions[session_id]
        
        # 检查转换是否完成
        if session_info.get('status') != 'completed':
            return jsonify({
                'success': False,
                'error': '转换尚未完成'
            }), 400
        
        # 获取输出文件路径
        output_path = session_info.get('output_path')
        
        if not output_path or not Path(output_path).exists():
            return jsonify({
                'success': False,
                'error': '输出文件不存在'
            }), 404
        
        # 发送文件
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"converted_{session_info['filename']}.zip"
        )
        
    except Exception as e:
        current_app.logger.error(f"下载失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/sessions', methods=['GET'])
def get_sessions():
    """
    获取所有会话
    
    Returns:
        JSON响应
    """
    try:
        session_list = []
        for session_id, info in sessions.items():
            session_list.append({
                'session_id': session_id,
                'filename': info.get('filename'),
                'status': info.get('status'),
                'upload_time': info.get('upload_time'),
                'file_size': info.get('file_size'),
                'progress': info.get('progress', 0)
            })
        
        # 按上传时间倒序排序
        session_list.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': session_list,
            'total': len(session_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取会话列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    删除会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON响应
    """
    try:
        if session_id not in sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session_info = sessions[session_id]
        
        # 删除上传的文件
        file_path = Path(session_info.get('file_path', ''))
        if file_path.exists():
            file_path.unlink()
            current_app.logger.info(f"删除文件: {file_path}")
        
        # 删除输出文件
        output_path = Path(session_info.get('output_path', ''))
        if output_path.exists():
            if output_path.is_dir():
                shutil.rmtree(output_path)
            else:
                output_path.unlink()
            current_app.logger.info(f"删除输出: {output_path}")
        
        # 删除会话
        del sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': '会话已删除'
        })
        
    except Exception as e:
        current_app.logger.error(f"删除会话失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查
    
    Returns:
        JSON响应
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'sessions_count': len(sessions)
    })

# 错误处理
@bp.errorhandler(413)
def too_large(e):
    """处理文件过大错误"""
    return jsonify({
        'success': False,
        'error': '文件大小超过限制（最大50MB）'
    }), 413

@bp.errorhandler(500)
def internal_error(e):
    """处理内部错误"""
    current_app.logger.error(f"内部错误: {e}")
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500