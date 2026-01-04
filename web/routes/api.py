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
                    from web.services.pipeline import get_pipeline
                    
                    # 创建输出目录
                    output_dir = Path(app.config['OUTPUT_FOLDER']) / session_id
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 获取流水线单例
                    pipeline = get_pipeline()
                    
                    # 定义进度回调函数
                    def progress_callback(stage, progress, data):
                        """进度回调函数"""
                        session_info['current_stage'] = stage
                        session_info['stage_progress'] = progress
                        session_info['stage_data'] = data
                        
                        # 初始化layers信息
                        if 'layers' not in session_info:
                            session_info['layers'] = {
                                'layer1': {'status': 'pending', 'progress': 0, 'message': ''},
                                'layer2': {'status': 'pending', 'progress': 0, 'message': ''},
                                'layer3': {'status': 'pending', 'progress': 0, 'message': ''},
                                'layer4': {'status': 'pending', 'progress': 0, 'message': ''}
                            }
                        
                        # 更新当前层的进度信息
                        if stage in ['layer1', 'layer2', 'layer3', 'layer4']:
                            session_info['layers'][stage]['progress'] = progress
                            session_info['layers'][stage]['message'] = data.get('message', f'{stage} 处理中...')
                            session_info['layers'][stage]['status'] = 'completed' if progress == 100 else 'processing'
                            # 保存详细数据供前端使用
                            session_info['layers'][stage]['data'] = data
                        
                        # 计算总进度
                        stage_weights = {
                            'layer1': 20,
                            'layer2': 40,
                            'layer3': 70,
                            'layer4': 90,
                            'complete': 100
                        }
                        
                        if stage == 'error':
                            total_progress = 0
                        else:
                            base_progress = stage_weights.get(stage, 0)
                            if stage in stage_weights:
                                stage_index = list(stage_weights.keys()).index(stage)
                                prev_progress = list(stage_weights.values())[stage_index - 1] if stage_index > 0 else 0
                                stage_progress = progress / 100 * (base_progress - prev_progress)
                                total_progress = min(100, prev_progress + stage_progress)
                            else:
                                total_progress = base_progress
                        
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
                                'data': data,
                                'layers': session_info['layers']
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
                        # 使用实际的output_dir，文件保存在 output_dir/layer1, output_dir/layer2 等目录中
                        session_info['output_dir'] = str(output_dir)
                        
                        # 确保所有层都显示为100%完成
                        session_info['layers'] = {
                            'layer1': {'status': 'completed', 'progress': 100, 'message': '✅ 预处理完成'},
                            'layer2': {'status': 'completed', 'progress': 100, 'message': '✅ 语义分析完成'},
                            'layer3': {'status': 'completed', 'progress': 100, 'message': '✅ DITA转换完成'},
                            'layer4': {'status': 'completed', 'progress': 100, 'message': '✅ 质量保证完成'}
                        }
                        
                        # 发送完成通知
                        try:
                            from web.app import socketio
                            socketio.emit('conversion_complete', {
                                'session_id': session_id,
                                'output_dir': session_info['output_dir'],
                                'result': result,
                                'layers': session_info['layers']
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

@bp.route('/layer/<session_id>/<layer_name>/files', methods=['GET'])
def get_layer_files(session_id, layer_name):
    """
    获取指定层的文件列表
    
    Args:
        session_id: 会话ID
        layer_name: 层名称（layer1, layer2, layer3, layer4）
        
    Returns:
        JSON: 文件列表
    """
    try:
        if session_id not in sessions:
            return jsonify({'error': '会话不存在'}), 404
        
        session_info = sessions[session_id]
        
        from src.utils.config import Config
        filename = session_info.get('filename', '')
        doc_name = Path(filename).stem if filename else None
        
        # 根据层名称确定查找策略
        if layer_name in ['layer1', 'layer2']:
            # Layer1和Layer2在 {session_id}_{doc_name}/ 目录中
            output_dir = None
            if doc_name:
                possible_dirs = [
                    Config.OUTPUT_DIR / f"{session_id}_{doc_name}",  # session_id_doc_name格式（主要路径）
                    Config.OUTPUT_DIR / doc_name,  # doc_name格式（兼容性）
                ]
                for possible_dir in possible_dirs:
                    if possible_dir.exists():
                        output_dir = possible_dir
                        break
            layer_dir = output_dir / layer_name if output_dir else None
        elif layer_name == 'layer3':
            # Layer3的文件在 {session_id}/dita_drafts/ 目录中
            output_dir = None
            if 'output_dir' in session_info and session_info['output_dir']:
                output_dir = Path(session_info['output_dir'])
                if not output_dir.exists():
                    output_dir = None
            if output_dir is None:
                output_dir = Path(Config.OUTPUT_DIR) / session_id
            layer_dir = output_dir / 'dita_drafts' if output_dir.exists() else None
        elif layer_name == 'layer4':
            # Layer4的文件在 {session_id}/final_dita/ 目录中
            output_dir = None
            if 'output_dir' in session_info and session_info['output_dir']:
                output_dir = Path(session_info['output_dir'])
                if not output_dir.exists():
                    output_dir = None
            if output_dir is None:
                output_dir = Path(Config.OUTPUT_DIR) / session_id
            layer_dir = output_dir / 'final_dita' if output_dir.exists() else None
        else:
            layer_dir = None
        
        files = []
        
        if layer_dir and layer_dir.exists() and layer_dir.is_dir():
            for file_path in layer_dir.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(layer_dir)
                    files.append({
                        'name': file_path.name,
                        'path': str(rel_path).replace('\\', '/'),
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
                    })
        
        current_app.logger.debug(f"找到 {len(files)} 个文件在 {layer_dir} (layer={layer_name})")
        return jsonify({'success': True, 'files': files})
    
    except Exception as e:
        current_app.logger.error(f"获取文件列表失败: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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
        
        # 获取层进度信息
        layers_info = session_info.get('layers', {
            'layer1': {'status': 'pending', 'progress': 0, 'message': ''},
            'layer2': {'status': 'pending', 'progress': 0, 'message': ''},
            'layer3': {'status': 'pending', 'progress': 0, 'message': ''},
            'layer4': {'status': 'pending', 'progress': 0, 'message': ''}
        })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': session_info.get('status', 'unknown'),
            'progress': session_info.get('progress', 0),
            'message': session_info.get('message', ''),
            'filename': session_info.get('filename', ''),
            'file_size': session_info.get('file_size', 0),
            'upload_time': session_info.get('upload_time', ''),
            'error': session_info.get('error', ''),
            'layers': layers_info
        })
        
    except Exception as e:
        current_app.logger.error(f"获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/preview/<session_id>/<layer>/<path:filepath>', methods=['GET'])
def preview_layer_file(session_id, layer, filepath):
    """
    预览指定层的文件内容
    
    Args:
        session_id: 会话ID
        layer: 层名称（layer1, layer2, layer3, layer4）
        filepath: 文件相对路径
        
    Returns:
        文件内容（JSON格式，包含content和type）
    """
    try:
        if session_id not in sessions:
            return jsonify({'error': '会话不存在'}), 404
        
        session_info = sessions[session_id]
        
        from src.utils.config import Config
        filename = session_info.get('filename', '')
        doc_name = Path(filename).stem if filename else None
        
        # 根据层名称确定查找策略
        if layer in ['layer1', 'layer2']:
            # Layer1和Layer2在 {session_id}_{doc_name}/ 目录中
            output_dir = None
            if doc_name:
                possible_dirs = [
                    Config.OUTPUT_DIR / f"{session_id}_{doc_name}",  # session_id_doc_name格式（主要路径）
                    Config.OUTPUT_DIR / doc_name,  # doc_name格式（兼容性）
                ]
                for possible_dir in possible_dirs:
                    if possible_dir.exists():
                        output_dir = possible_dir
                        break
            if output_dir is None or not output_dir.exists():
                current_app.logger.error(f"找不到Layer{layer[-1]}输出目录: session_id={session_id}, doc_name={doc_name}")
                return jsonify({'error': '输出目录不存在'}), 404
            layer_dir = output_dir / layer
        elif layer == 'layer3':
            # Layer3的文件在 {session_id}/dita_drafts/ 目录中
            output_dir = None
            if 'output_dir' in session_info and session_info['output_dir']:
                output_dir = Path(session_info['output_dir'])
                if not output_dir.exists():
                    output_dir = None
            if output_dir is None:
                output_dir = Path(Config.OUTPUT_DIR) / session_id
            if not output_dir.exists():
                current_app.logger.error(f"找不到Layer3输出目录: session_id={session_id}")
                return jsonify({'error': '输出目录不存在'}), 404
            layer_dir = output_dir / 'dita_drafts'
        elif layer == 'layer4':
            # Layer4的文件在 {session_id}/final_dita/ 目录中
            output_dir = None
            if 'output_dir' in session_info and session_info['output_dir']:
                output_dir = Path(session_info['output_dir'])
                if not output_dir.exists():
                    output_dir = None
            if output_dir is None:
                output_dir = Path(Config.OUTPUT_DIR) / session_id
            if not output_dir.exists():
                current_app.logger.error(f"找不到Layer4输出目录: session_id={session_id}")
                return jsonify({'error': '输出目录不存在'}), 404
            layer_dir = output_dir / 'final_dita'
        else:
            current_app.logger.error(f"未知的层名称: {layer}")
            return jsonify({'error': '未知的层名称'}), 400
        
        # 规范化文件路径（URL中的路径使用正斜杠）
        normalized_filepath = filepath.replace('\\', '/')  # 统一为正斜杠
        # 构建文件路径（Path对象会自动处理路径分隔符）
        file_path = layer_dir / normalized_filepath
        
        # 安全检查：确保文件在输出目录内
        try:
            file_path.resolve().relative_to(output_dir.resolve())
        except ValueError:
            return jsonify({'error': '非法文件路径'}), 403
        
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': '文件不存在'}), 404
        
        # 读取文件内容
        file_ext = file_path.suffix.lower()
        file_type = 'text'
        
        # 根据文件类型确定内容类型
        if file_ext in ['.md', '.markdown']:
            file_type = 'markdown'
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_ext in ['.dita', '.xml']:
            file_type = 'xml'
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_ext == '.json':
            file_type = 'json'
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            file_type = 'image'
            # 对于图片，返回base64编码
            import base64
            with open(file_path, 'rb') as f:
                img_data = f.read()
                content = base64.b64encode(img_data).decode('utf-8')
                if file_ext == '.png':
                    mime_type = 'image/png'
                elif file_ext in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif file_ext == '.gif':
                    mime_type = 'image/gif'
                elif file_ext == '.svg':
                    mime_type = 'image/svg+xml'
                else:
                    mime_type = 'image/png'
        else:
            # 默认按文本处理
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                return jsonify({'error': '无法以文本方式预览此文件'}), 400
        
        return jsonify({
            'success': True,
            'filename': file_path.name,
            'filepath': filepath,
            'content': content,
            'type': file_type,
            'mime_type': mime_type if file_type == 'image' else None
        })
    
    except Exception as e:
        current_app.logger.error(f"预览文件失败: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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
    
@bp.route('/download/layer/<session_id>/<layer>', methods=['GET'])
def download_layer_result(session_id, layer):
    """
    下载指定层的转换结果
    
    Args:
        session_id: 会话ID
        layer: 层名称（如layer1, layer2, layer3, layer4）
        
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
        
        # 验证层名称
        if layer not in ['layer1', 'layer2', 'layer3', 'layer4']:
            return jsonify({
                'success': False,
                'error': '无效的层名称'
            }), 400
        
        # 获取主输出目录
        main_output_dir = Path(session_info.get('output_dir'))
        
        if not main_output_dir or not main_output_dir.exists():
            return jsonify({
                'success': False,
                'error': '输出目录不存在'
            }), 404
        
        # 创建临时ZIP文件
        import tempfile
        import zipfile
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            tmp_zip_path = tmp_file.name
        
        # 创建ZIP文件
        with zipfile.ZipFile(tmp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 尝试获取层特定的输出目录
            layer_output_dir = main_output_dir / layer
            
            if layer_output_dir.exists() and layer_output_dir.is_dir():
                # 如果层有专门的目录，压缩该目录下的所有文件
                for root, dirs, files in os.walk(layer_output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 相对路径从层目录开始
                        arcname = os.path.relpath(file_path, layer_output_dir)
                        zipf.write(file_path, arcname)
            else:
                # 如果没有层特定目录，检查会话中的层结果数据
                result = session_info.get('result', {})
                layers = result.get('layers', {})
                
                if layer in layers:
                    layer_data = layers[layer]
                    
                    # 根据不同层处理结果数据
                    if layer == 'layer1':
                        # 层1：预处理层，输出Markdown
                        markdown_content = layer_data.get('markdown', '')
                        if markdown_content:
                            # 创建临时Markdown文件
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as md_file:
                                md_file.write(markdown_content)
                                temp_md_path = md_file.name
                            
                            # 添加到ZIP
                            zipf.write(temp_md_path, f"{layer}_preprocessed.md")
                            
                            # 删除临时文件
                            os.unlink(temp_md_path)
                    
                    elif layer == 'layer2':
                        # 层2：语义分析层，输出分块结果
                        chunks = layer_data.get('chunks', [])
                        if chunks:
                            # 创建临时JSON文件存储分块
                            import json
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as json_file:
                                json.dump(chunks, json_file, ensure_ascii=False, indent=2)
                                temp_json_path = json_file.name
                            
                            # 添加到ZIP
                            zipf.write(temp_json_path, f"{layer}_chunks.json")
                            
                            # 删除临时文件
                            os.unlink(temp_json_path)
                    
                    elif layer == 'layer3':
                        # 层3：DITA转换层，可能有XML文件
                        # 检查是否有DITA文件
                        dita_files = list(main_output_dir.glob('*.dita')) + list(main_output_dir.glob('**/*.dita'))
                        for dita_file in dita_files:
                            arcname = os.path.relpath(dita_file, main_output_dir)
                            zipf.write(dita_file, arcname)
                    
                    elif layer == 'layer4':
                        # 层4：质量保证层，可能有报告文件
                        # 检查是否有质量报告文件
                        report_files = list(main_output_dir.glob('*quality*.json')) + list(main_output_dir.glob('*report*.json'))
                        for report_file in report_files:
                            arcname = os.path.relpath(report_file, main_output_dir)
                            zipf.write(report_file, arcname)
                
                # 如果没有找到任何文件或数据
                if zipf.namelist() == []:
                    # 创建一个空的说明文件
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as info_file:
                        info_file.write(f"层 {layer} 没有生成可下载的文件")
                        temp_info_path = info_file.name
                    
                    zipf.write(temp_info_path, "info.txt")
                    os.unlink(temp_info_path)
        
        # 发送ZIP文件
        response = send_file(
            tmp_zip_path,
            as_attachment=True,
            download_name=f"{layer}_result_{session_info['filename']}.zip",
            mimetype='application/zip'
        )
        
        # 删除临时文件
        @response.call_on_close
        def remove_temp_file():
            try:
                os.unlink(tmp_zip_path)
            except Exception as e:
                current_app.logger.error(f"删除临时文件失败: {e}")
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"下载层结果失败: {e}")
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