"""
手动修复DITA包路由 (Option C)
"""
from flask import Blueprint, request, jsonify, render_template, send_file, current_app
from pathlib import Path
import logging
import os

bp = Blueprint('repair', __name__)
logger = logging.getLogger(__name__)


@bp.route('/repair', methods=['GET'])
def repair_page():
    """
    渲染手动修复页面
    
    Returns:
        HTML页面
    """
    return render_template('repair.html')


@bp.route('/repair/process', methods=['POST'])
def repair_process():
    """
    处理手动修改后的DITA ZIP包
    
    Request:
        - file: ZIP文件（multipart/form-data）
        - linkify: 是否执行引文链接化（可选，默认false）
        - build: 是否执行DITA-OT构建（可选，默认false）
        - doc_name: 文档名称（可选，默认使用文件名）
    
    Returns:
        JSON: 处理结果
    """
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 获取选项
        linkify_citations = request.form.get('linkify', 'false').lower() == 'true'
        build_dita_ot = request.form.get('build', 'false').lower() == 'true'
        doc_name = request.form.get('doc_name', '').strip()
        
        # 如果没有提供doc_name，使用文件名（去掉扩展名）
        if not doc_name:
            doc_name = Path(file.filename).stem
        
        # 确保doc_name安全（只包含字母数字和下划线）
        doc_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in doc_name)
        
        # 保存上传文件到临时位置
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads')) / 'repair'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        import uuid
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_file_path = upload_dir / temp_filename
        
        file.save(str(temp_file_path))
        logger.info(f"📥 文件已上传: {temp_file_path}")
        
        # 初始化修复服务
        # 确保OUTPUT_FOLDER是绝对路径（相对于项目根目录）
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'data/output')
        if not Path(output_folder).is_absolute():
            # 获取项目根目录（web目录的父目录）
            project_root = Path(__file__).parent.parent.parent
            output_base_dir = project_root / output_folder
        else:
            output_base_dir = Path(output_folder)
        
        from web.services.repair_service import DitaPackageRepairService
        
        repair_service = DitaPackageRepairService(
            output_base_dir=output_base_dir
        )
        
        # 处理包
        result = repair_service.process_package(
            zip_file_path=temp_file_path,
            doc_name=doc_name,
            linkify_citations=linkify_citations,
            build_dita_ot=build_dita_ot
        )
        
        # 清理临时文件
        try:
            temp_file_path.unlink()
        except Exception as e:
            logger.warning(f"⚠️ 清理临时文件失败: {e}")
        
        # 返回结果
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"❌ 处理失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/repair/download/<doc_name>/<job_id>', methods=['GET'])
def repair_download(doc_name: str, job_id: str):
    """
    下载修复结果ZIP
    
    Args:
        doc_name: 文档名称
        job_id: job ID
        
    Returns:
        ZIP文件
    """
    try:
        # 确保OUTPUT_FOLDER是绝对路径
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'data/output')
        if not Path(output_folder).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            output_base_dir = project_root / output_folder
        else:
            output_base_dir = Path(output_folder)
        
        output_zip_path = output_base_dir / doc_name / "repair" / job_id / "output.zip"
        
        if not output_zip_path.exists():
            return jsonify({'error': '输出文件不存在'}), 404
        
        logger.info(f"📦 下载修复结果: {output_zip_path}")
        
        return send_file(
            str(output_zip_path),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"dita_repaired_{doc_name}_{job_id[:8]}.zip"
        )
    
    except Exception as e:
        logger.error(f"❌ 下载失败: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/repair/result/<doc_name>/<job_id>', methods=['GET'])
def repair_result(doc_name: str, job_id: str):
    """
    获取修复结果JSON
    
    Args:
        doc_name: 文档名称
        job_id: job ID
        
    Returns:
        JSON: 修复结果
    """
    try:
        # 确保OUTPUT_FOLDER是绝对路径
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'data/output')
        if not Path(output_folder).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            output_base_dir = project_root / output_folder
        else:
            output_base_dir = Path(output_folder)
        
        result_file = output_base_dir / doc_name / "repair" / job_id / "repair_result.json"
        
        if not result_file.exists():
            return jsonify({'error': '结果文件不存在'}), 404
        
        import json
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"❌ 读取结果失败: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/repair/preview/<doc_name>/<job_id>/<path:filepath>', methods=['GET'])
def repair_preview_file(doc_name: str, job_id: str, filepath: str):
    """
    预览修复结果中的文件
    
    Args:
        doc_name: 文档名称
        job_id: job ID
        filepath: 文件相对路径（相对于workdir）
        
    Returns:
        文件内容（JSON格式）
    """
    try:
        # 确保OUTPUT_FOLDER是绝对路径
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'data/output')
        if not Path(output_folder).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            output_base_dir = project_root / output_folder
        else:
            output_base_dir = Path(output_folder)
        
        # 构建文件路径（在workdir中）
        workdir = output_base_dir / doc_name / "repair" / job_id / "workdir"
        
        # 将URL路径中的正斜杠转换为适合当前操作系统的路径分隔符
        # Path对象会自动处理正斜杠，但为了确保一致性，我们规范化路径
        # URL中的路径使用正斜杠，Path对象会自动转换为系统路径分隔符
        normalized_filepath = filepath.replace('\\', '/')  # 统一为正斜杠（URL格式）
        # 使用Path对象构建路径，它会自动处理路径分隔符
        file_path = workdir / normalized_filepath
        
        # 安全检查：确保文件在workdir内
        try:
            file_path.resolve().relative_to(workdir.resolve())
        except ValueError:
            return jsonify({'error': '非法文件路径'}), 403
        
        if not file_path.exists() or not file_path.is_file():
            # 尝试列出workdir中的文件以便调试
            available_files = []
            if workdir.exists():
                try:
                    available_files = [str(f.relative_to(workdir)).replace('\\', '/') for f in workdir.rglob('*') if f.is_file()]
                except Exception:
                    pass
            
            logger.error(f"文件不存在: {file_path}, workdir: {workdir}, filepath: {filepath}, available: {available_files[:5]}")
            return jsonify({
                'error': f'文件不存在: {filepath}',
                'debug': {
                    'workdir': str(workdir),
                    'filepath': filepath,
                    'normalized_path': normalized_filepath,
                    'full_path': str(file_path),
                    'workdir_exists': workdir.exists(),
                    'available_files_sample': available_files[:10]  # 只返回前10个作为参考
                }
            }), 404
        
        # 读取文件内容
        file_ext = file_path.suffix.lower()
        file_type = 'text'
        mime_type = None
        
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
            'mime_type': mime_type
        })
    
    except Exception as e:
        logger.error(f"❌ 预览文件失败: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

