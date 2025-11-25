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
    处理文档（后台线程）- 调用四层模型
    
    Args:
        app: Flask 应用实例
        session_id: 会话ID
    """
    # ✅ 在后台线程中创建应用上下文
    with app.app_context():
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        
        if not session:
            logger.error(f"❌ 会话不存在: {session_id}")
            return
        
        try:
            # 获取文件路径
            input_file = Path(session['file_path'])
            
            # 创建输出目录
            output_folder = Path(app.config['OUTPUT_FOLDER'])  # ← 使用 app.config
            output_dir = output_folder / session_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
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
            
            # 详细输出推送函数
            def push_layer_output(stage, output_data, step_name=""):
                """推送每层的详细输出到前端"""
                data = {
                    'session_id': session_id,
                    'stage': stage,
                    'type': 'layer_output',
                    'step_name': step_name,
                    'output': output_data,
                    'timestamp': time.time()
                }
                
                # WebSocket推送详细输出 - 使用线程安全的方式
                try:
                    socketio.emit('layer_output', data, namespace='/process')
                except Exception as ws_error:
                    logger.warning(f"WebSocket推送失败: {ws_error}")
                logger.info(f"📋 {stage} 输出: {step_name}")
            
            # ========== Layer 1: 结构提取 ==========
            push_progress('layer1', 0, '开始提取文档结构...')
            
            # 导入Layer 1模块
            from src.layer1_preprocessing.file_router import FileRouter
            
            push_layer_output('layer1', {
                'step': 'initialization',
                'message': '初始化文档路由器...',
                'details': '正在检测文件类型并选择合适的处理器'
            }, '文档路由初始化')
            
            # 文件路由
            router = FileRouter(str(input_file))
            file_type = router.detect_file_type()
            
            push_layer_output('layer1', {
                'step': 'file_detection',
                'message': f'检测到文件类型: {file_type}',
                'details': f'文件: {input_file.name}',
                'file_type': file_type,
                'file_size': input_file.stat().st_size
            }, '文件类型检测')
            
            push_progress('layer1', 20, f'检测到{file_type}文件，开始预处理...')
            
            # 根据文件类型选择处理器
            if file_type == 'word':
                from src.layer1_preprocessing.word_processor import WordProcessor
                processor = WordProcessor(str(input_file))
                
                push_layer_output('layer1', {
                    'step': 'processor_selection',
                    'message': '选择Word处理器',
                    'details': '使用WordProcessor处理.docx文件'
                }, '处理器选择')
                
            elif file_type == 'pdf':
                from src.layer1_preprocessing.pdf_processor import PDFProcessor
                processor = PDFProcessor(str(input_file))
                
                push_layer_output('layer1', {
                    'step': 'processor_selection', 
                    'message': '选择PDF处理器',
                    'details': '使用PDFProcessor处理.pdf文件，可能需要OCR'
                }, '处理器选择')
                
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            push_progress('layer1', 40, '正在提取文档结构...')
            
            # 执行结构提取
            structure_result = processor.extract_structure()
            
            push_layer_output('layer1', {
                'step': 'structure_extraction',
                'message': '文档结构提取完成',
                'details': f'提取了 {len(structure_result.get("elements", []))} 个结构元素',
                'elements_count': len(structure_result.get("elements", [])),
                'elements_preview': structure_result.get("elements", [])[:5]  # 前5个元素作为预览
            }, '结构提取结果')
            
            push_progress('layer1', 80, '正在保存结构化数据...')
            
            # 保存结构化数据
            import json
            structure_file = output_dir / 'layer1' / 'structure.json'
            structure_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(structure_file, 'w', encoding='utf-8') as f:
                json.dump(structure_result, f, ensure_ascii=False, indent=2)
            
            push_layer_output('layer1', {
                'step': 'save_results',
                'message': '结构化数据已保存',
                'details': f'保存到: {structure_file}',
                'file_path': str(structure_file)
            }, '保存结果')
            
            push_progress('layer1', 100, f'结构提取完成，识别 {len(structure_result.get("elements", []))} 个元素')
            
            # ========== Layer 2: 内容提取 ==========
            push_progress('layer2', 0, '开始提取内容...')
            
            # 导入Layer 2模块
            from src.layer2_semantic.document_analyzer import DocumentAnalyzer
            
            push_layer_output('layer2', {
                'step': 'initialization',
                'message': '初始化文档分析器...',
                'details': '正在准备语义分析和内容分类工具'
            }, '文档分析器初始化')
            
            push_progress('layer2', 20, '正在进行语义分析...')
            
            # 创建文档分析器
            analyzer = DocumentAnalyzer()
            
            push_layer_output('layer2', {
                'step': 'analyzer_ready',
                'message': '文档分析器已就绪',
                'details': '开始对文档结构进行语义分析'
            }, '分析器准备')
            
            # 执行语义分析
            content_result = analyzer.analyze_content(structure_result)
            
            push_layer_output('layer2', {
                'step': 'semantic_analysis',
                'message': '语义分析完成',
                'details': f'分析了 {len(content_result.get("content_blocks", []))} 个内容块',
                'content_blocks_count': len(content_result.get("content_blocks", [])),
                'content_preview': content_result.get("content_blocks", [])[:3]  # 前3个内容块作为预览
            }, '语义分析结果')
            
            push_progress('layer2', 60, '正在进行内容分类...')
            
            # 内容分类
            classified_content = analyzer.classify_content(content_result)
            
            push_layer_output('layer2', {
                'step': 'content_classification',
                'message': '内容分类完成',
                'details': f'分类结果: {classified_content.get("classification_summary", {})}',
                'classification_summary': classified_content.get("classification_summary", {}),
                'classified_types': list(set([block.get("type", "unknown") for block in classified_content.get("content_blocks", [])]))
            }, '内容分类结果')
            
            push_progress('layer2', 80, '正在保存内容分析结果...')
            
            # 保存内容分析结果
            content_file = output_dir / 'layer2' / 'content_analysis.json'
            content_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(classified_content, f, ensure_ascii=False, indent=2)
            
            push_layer_output('layer2', {
                'step': 'save_results',
                'message': '内容分析结果已保存',
                'details': f'保存到: {content_file}',
                'file_path': str(content_file)
            }, '保存结果')
            
            # 更新content_result为分类后的结果
            content_result = classified_content
            push_progress('layer2', 100, f'内容提取完成，处理 {len(content_result.get("content_blocks", []))} 项内容')
            
            # ========== Layer 3: DITA转换 ==========
            push_progress('layer3', 0, '开始DITA转换...')
            
            # 导入Layer 3模块
            from src.layer3_dita_conversion.converter import DITAConverter
            
            push_layer_output('layer3', {
                'step': 'initialization',
                'message': '初始化DITA转换器...',
                'details': '正在准备DITA XML生成工具和模板引擎'
            }, 'DITA转换器初始化')
            
            push_progress('layer3', 20, '正在选择DITA模板...')
            
            # 创建DITA转换器
            converter = DITAConverter()
            
            push_layer_output('layer3', {
                'step': 'converter_ready',
                'message': 'DITA转换器已就绪',
                'details': '开始将内容转换为DITA格式'
            }, '转换器准备')
            
            # 执行DITA转换
            dita_result = converter.convert_to_dita(structure_result, content_result)
            
            push_layer_output('layer3', {
                'step': 'dita_conversion',
                'message': 'DITA转换完成',
                'details': f'生成了 {len(dita_result.get("dita_files", []))} 个DITA文件',
                'dita_files_count': len(dita_result.get("dita_files", [])),
                'dita_files': dita_result.get("dita_files", []),
                'dita_types': list(set([file.get("type", "topic") for file in dita_result.get("dita_files", [])]))
            }, 'DITA转换结果')
            
            push_progress('layer3', 60, '正在进行XML验证...')
            
            # XML验证
            validation_result = converter.validate_dita(dita_result)
            
            push_layer_output('layer3', {
                'step': 'xml_validation',
                'message': 'XML验证完成',
                'details': f'验证结果: {validation_result.get("validation_status", "unknown")}',
                'validation_status': validation_result.get("validation_status", "unknown"),
                'validation_errors': validation_result.get("errors", []),
                'validation_warnings': validation_result.get("warnings", [])
            }, 'XML验证结果')
            
            push_progress('layer3', 80, '正在保存DITA文件...')
            
            # 保存DITA文件
            dita_dir = output_dir / 'layer3' / 'dita_files'
            dita_dir.mkdir(parents=True, exist_ok=True)
            
            for dita_file in dita_result.get("dita_files", []):
                file_path = dita_dir / dita_file["filename"]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(dita_file["content"])
            
            push_layer_output('layer3', {
                'step': 'save_results',
                'message': 'DITA文件已保存',
                'details': f'保存到: {dita_dir}',
                'files_saved': len(dita_result.get("dita_files", [])),
                'save_path': str(dita_dir)
            }, '保存结果')
            
            # 更新relationship_result为DITA转换结果
            relationship_result = dita_result
            push_progress('layer3', 100, f'DITA转换完成，生成 {len(dita_result.get("dita_files", []))} 个文件')
            
            # ========== Layer 4: 质量保证 ==========
            push_progress('layer4', 0, '开始质量保证检查...')
            
            # 导入Layer 4模块
            from src.layer4_quality_assurance.qa_manager import QAManager
            
            push_layer_output('layer4', {
                'step': 'initialization',
                'message': '初始化质量保证管理器...',
                'details': '正在准备QA检查工具和智能修复器'
            }, 'QA管理器初始化')
            
            push_progress('layer4', 20, '正在进行质量检查...')
            
            # 创建QA管理器
            qa_manager = QAManager()
            
            push_layer_output('layer4', {
                'step': 'qa_manager_ready',
                'message': 'QA管理器已就绪',
                'details': '开始对DITA文件进行质量检查'
            }, 'QA管理器准备')
            
            # 执行质量检查
            qa_result = qa_manager.run_quality_check(relationship_result)
            
            push_layer_output('layer4', {
                'step': 'quality_check',
                'message': '质量检查完成',
                'details': f'检查了 {len(qa_result.get("checked_files", []))} 个文件',
                'checked_files_count': len(qa_result.get("checked_files", [])),
                'issues_found': len(qa_result.get("issues", [])),
                'issues_summary': qa_result.get("issues_summary", {})
            }, '质量检查结果')
            
            push_progress('layer4', 50, '正在进行智能修复...')
            
            # 智能修复
            if qa_result.get("issues", []):
                repair_result = qa_manager.intelligent_repair(qa_result)
                
                push_layer_output('layer4', {
                    'step': 'intelligent_repair',
                    'message': '智能修复完成',
                    'details': f'修复了 {len(repair_result.get("repaired_issues", []))} 个问题',
                    'repaired_issues_count': len(repair_result.get("repaired_issues", [])),
                    'repair_summary': repair_result.get("repair_summary", {})
                }, '智能修复结果')
            else:
                push_layer_output('layer4', {
                    'step': 'intelligent_repair',
                    'message': '无需修复',
                    'details': '未发现质量问题，跳过修复步骤'
                }, '智能修复跳过')
            
            push_progress('layer4', 70, '正在生成质量报告...')
            
            # 生成质量报告
            quality_report = qa_manager.generate_quality_report(qa_result)
            
            push_layer_output('layer4', {
                'step': 'quality_report',
                'message': '质量报告生成完成',
                'details': f'报告包含 {quality_report.get("total_checks", 0)} 项检查',
                'quality_score': quality_report.get("quality_score", 0),
                'report_summary': quality_report.get("summary", {})
            }, '质量报告生成')
            
            push_progress('layer4', 80, '正在保存最终结果...')
            
            # 保存质量报告和最终结果
            qa_dir = output_dir / 'layer4' / 'quality_assurance'
            qa_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存质量报告
            report_file = qa_dir / 'quality_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(quality_report, f, ensure_ascii=False, indent=2)
            
            # 复制最终DITA文件到输出目录
            final_output_dir = output_dir / 'final_output'
            final_output_dir.mkdir(parents=True, exist_ok=True)
            
            import shutil
            dita_source_dir = output_dir / 'layer3' / 'dita_files'
            if dita_source_dir.exists():
                for file_path in dita_source_dir.glob('*.xml'):
                    shutil.copy2(file_path, final_output_dir)
            
            final_result = {
                'quality_report': quality_report,
                'output_files': [f.name for f in final_output_dir.glob('*.xml')],
                'final_output_dir': str(final_output_dir),
                'quality_score': quality_report.get("quality_score", 0)
            }
            
            push_layer_output('layer4', {
                'step': 'save_results',
                'message': '最终结果已保存',
                'details': f'质量报告: {report_file}, 最终输出: {final_output_dir}',
                'report_file': str(report_file),
                'final_output_path': str(final_output_dir),
                'final_files_count': len(final_result.get("output_files", []))
            }, '保存最终结果')
            
            push_progress('layer4', 100, f'质量保证完成，质量评分: {quality_report.get("quality_score", 0)}/100')
            
            # ========== 完成 ==========
            result = {
                'success': True,
                'layers': {
                    'layer1': {
                        'name': '结构提取',
                        'elements_count': len(structure_result.get("elements", [])),
                        'file_type': structure_result.get("file_type", "unknown")
                    },
                    'layer2': {
                        'name': '内容分析',
                        'content_blocks_count': len(content_result.get("content_blocks", [])),
                        'classified_types': list(set([block.get("type", "unknown") for block in content_result.get("content_blocks", [])]))
                    },
                    'layer3': {
                        'name': 'DITA转换',
                        'dita_files_count': len(relationship_result.get("dita_files", [])),
                        'dita_types': list(set([file.get("type", "topic") for file in relationship_result.get("dita_files", [])]))
                    },
                    'layer4': {
                        'name': '质量保证',
                        'quality_score': final_result.get("quality_score", 0),
                        'issues_found': len(qa_result.get("issues", [])),
                        'final_files_count': len(final_result.get("output_files", []))
                    }
                },
                'output_files': final_result.get("output_files", []),
                'final_output_dir': final_result.get("final_output_dir"),
                'statistics': {
                    'total_elements': len(structure_result.get("elements", [])),
                    'total_content_blocks': len(content_result.get("content_blocks", [])),
                    'total_dita_files': len(relationship_result.get("dita_files", [])),
                    'final_output_files': len(final_result.get("output_files", [])),
                    'quality_score': final_result.get("quality_score", 0)
                }
            }
            
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