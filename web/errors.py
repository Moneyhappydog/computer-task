"""
错误处理模块
"""
from flask import render_template, jsonify, request
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

def init_error_handlers(app):
    """
    初始化错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """处理400错误"""
        logger.warning(f"Bad request: {error}")
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': 'Bad Request',
                'message': str(error)
            }), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """处理404错误"""
        logger.warning(f"Page not found: {request.url}")
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': 'Not Found',
                'message': 'Resource not found'
            }), 404
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """处理413错误 - 文件过大"""
        logger.warning(f"File too large: {error}")
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': 'File Too Large',
                'message': '文件大小超过限制（最大50MB）'
            }), 413
        return render_template('errors/413.html', error=error), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        logger.error(f"Internal error: {error}", exc_info=True)
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': 'Internal Server Error',
                'message': 'An internal error occurred'
            }), 500
        return render_template('errors/500.html', error=error), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理未捕获的异常"""
        if isinstance(error, HTTPException):
            return error
        
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }), 500
        
        return render_template('errors/500.html', error=error), 500

def request_wants_json():
    """
    判断请求是否期望JSON响应
    
    Returns:
        bool: 是否期望JSON
    """
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json' and 
            request.accept_mimetypes[best] > request.accept_mimetypes['text/html']) or \
           request.path.startswith('/api/')