"""
处理流水线
协调四层架构的完整处理流程
"""
from pathlib import Path
from typing import Dict, Any, Callable
import logging
from datetime import datetime

from src.layer1_preprocessing import FileRouter
from src.layer2_semantic import DocumentAnalyzer
from src.layer3_dita_conversion import DITAConverter
from src.layer4_quality_assurance import QAManager

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """完整处理流水线"""
    
    def __init__(self):
        """初始化流水线"""
        logger.info("🔧 初始化处理流水线...")
        
        # 初始化四层
        self.layer1 = FileRouter()
        self.layer2 = DocumentAnalyzer(use_ai=True)
        self.layer3 = DITAConverter(use_ai=True)
        self.layer4 = QAManager(use_ai_repair=True)
        
        logger.info("✅ 处理流水线初始化完成")
    
    def process(
        self,
        input_file: Path,
        output_dir: Path,
        progress_callback: Callable[[str, int, Dict], None] = None
    ) -> Dict[str, Any]:
        """
        执行完整处理流程
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录
            progress_callback: 进度回调函数(stage, progress, data)
            
        Returns:
            处理结果
        """
        logger.info(f"🚀 开始处理: {input_file.name}")
        
        result = {
            'success': False,
            'input_file': str(input_file),
            'start_time': datetime.now().isoformat(),
            'layers': {},
            'final_output': None,
            'errors': []
        }
        
        try:
            # ========== Layer 1: 预处理 ==========
            self._update_progress(progress_callback, 'layer1', 0, {
                'message': '开始预处理，读取文件...'
            })
            
            layer1_result = self.layer1.process_file(input_file)
            result['layers']['layer1'] = layer1_result
            
            if not layer1_result['success']:
                raise Exception(f"Layer 1 失败: {layer1_result.get('error')}")
            
            markdown_content = layer1_result['markdown']
            
            self._update_progress(progress_callback, 'layer1', 100, {
                'message': '✅ 预处理完成',
                'markdown_length': len(markdown_content),
                'file_type': layer1_result['file_type']
            })
            
            # ========== Layer 2: 语义分析 ==========
            self._update_progress(progress_callback, 'layer2', 0, {
                'message': '开始语义分析，文本分块...'
            })
            
            layer2_result = self.layer2.analyze(markdown_content)
            result['layers']['layer2'] = layer2_result
            
            chunks = layer2_result['chunks']
            
            self._update_progress(progress_callback, 'layer2', 100, {
                'message': '✅ 语义分析完成',
                'total_chunks': len(chunks),
                'type_distribution': layer2_result['statistics']['type_distribution']
            })
            
            # ========== Layer 3: DITA转换 ==========
            self._update_progress(progress_callback, 'layer3', 0, {
                'message': f'开始DITA转换，处理 {len(chunks)} 个块...'
            })
            
            # 准备转换数据
            conversion_chunks = []
            for chunk in chunks:
                conversion_chunks.append({
                    'content': chunk['content'],
                    'title': chunk['title'],
                    'type': chunk['final_classification']['type'],
                    'metadata': {
                        'confidence': chunk['final_classification']['confidence'],
                        'chunk_id': chunk['chunk_id']
                    }
                })
            
            layer3_result = self.layer3.convert_batch(
                conversion_chunks,
                output_dir=output_dir / 'dita_drafts'
            )
            
            result['layers']['layer3'] = {
                'total': layer3_result['total'],
                'success': layer3_result['success'],
                'failed': layer3_result['failed'],
                'success_rate': layer3_result['success_rate']
            }
            
            self._update_progress(progress_callback, 'layer3', 100, {
                'message': f'✅ DITA转换完成 ({layer3_result["success"]}/{layer3_result["total"]})',
                'success_count': layer3_result['success']
            })
            
            # ========== Layer 4: 质量保证 ==========
            self._update_progress(progress_callback, 'layer4', 0, {
                'message': '开始质量保证，验证DITA文档...'
            })
            
            # 准备QA数据
            qa_documents = []
            for conv_result in layer3_result['results']:
                if conv_result['success']:
                    qa_documents.append({
                        'xml': conv_result['dita_xml'],
                        'type': conv_result['content_type'],
                        'metadata': conv_result.get('metadata', {})
                    })
            
            layer4_result = self.layer4.process_batch(
                qa_documents,
                output_dir=output_dir / 'final_dita'
            )
            
            result['layers']['layer4'] = {
                'total': layer4_result['total'],
                'success': layer4_result['success'],
                'failed': layer4_result['failed'],
                'success_rate': layer4_result['success_rate'],
                'avg_quality_score': layer4_result['summary']['quality_scores']['avg_overall_quality']
            }
            
            self._update_progress(progress_callback, 'layer4', 100, {
                'message': f'✅ 质量保证完成 ({layer4_result["success"]}/{layer4_result["total"]})',
                'avg_quality': layer4_result['summary']['quality_scores']['avg_overall_quality']
            })
            
            # ========== 完成 ==========
            result['success'] = True
            result['end_time'] = datetime.now().isoformat()
            result['final_output'] = str(output_dir / 'final_dita')
            
            self._update_progress(progress_callback, 'complete', 100, {
                'message': '🎉 所有处理完成！',
                'output_dir': str(output_dir / 'final_dita')
            })
            
            logger.info(f"✅ 处理完成: {input_file.name}")
            
        except Exception as e:
            logger.error(f"❌ 处理失败: {e}", exc_info=True)
            result['errors'].append(str(e))
            
            self._update_progress(progress_callback, 'error', 0, {
                'message': f'❌ 处理失败: {str(e)}'
            })
        
        return result
    
    def _update_progress(
        self,
        callback: Callable,
        stage: str,
        progress: int,
        data: Dict
    ):
        """更新进度"""
        if callback:
            callback(stage, progress, data)


# 全局单例
_pipeline = None

def get_pipeline() -> ProcessingPipeline:
    """获取流水线单例"""
    global _pipeline
    if _pipeline is None:
        _pipeline = ProcessingPipeline()
    return _pipeline