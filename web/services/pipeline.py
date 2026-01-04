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
        self.layer3 = DITAConverter(use_ai=True, max_fix_iterations=3)
        self.layer4 = QAManager(use_dita_ot=False, use_ai_repair=True, max_iterations=3)
        
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
            
            # 添加置信度信息
            layer1_result['confidence'] = layer1_result.get('confidence', 0.8)
            
            self._update_progress(progress_callback, 'layer1', 100, {
                'message': '✅ 预处理完成',
                'markdown_length': len(markdown_content),
                'file_type': layer1_result.get('file_type', 'unknown'),
                'confidence': layer1_result.get('confidence', 0.0)
            })
            
            # ========== Layer 2: 语义分析 ==========
            self._update_progress(progress_callback, 'layer2', 0, {
                'message': '开始语义分析，文本分块...'
            })
            
            layer2_result = self.layer2.analyze(markdown_content)
            result['layers']['layer2'] = layer2_result
            
            chunks = layer2_result['chunks']
            
            # 确定文档类型（使用最主要的类型）
            type_dist = layer2_result['statistics']['type_distribution']
            if type_dist:
                primary_type = max(type_dist.items(), key=lambda x: x[1])[0]
            else:
                primary_type = "Concept"  # 默认类型
            
            # 如果没有chunks，使用原始内容作为单个chunk
            if not chunks:
                chunks = [{
                    'id': 'single_chunk',
                    'content': markdown_content,
                    'title': layer2_result.get('title', 'Untitled Document'),
                    'type': primary_type,
                    'classification': {'type': primary_type, 'confidence': 0.8}
                }]
            else:
                # 确保每个chunk都有type字段
                for chunk in chunks:
                    if 'type' not in chunk and 'classification' in chunk:
                        chunk['type'] = chunk['classification']['type']
                    elif 'type' not in chunk:
                        chunk['type'] = primary_type
            
            self._update_progress(progress_callback, 'layer2', 100, {
                'message': '✅ 语义分析完成',
                'total_chunks': len(chunks),
                'type_distribution': layer2_result['statistics'].get('type_distribution', {}),
                'overall_avg_confidence': layer2_result['statistics'].get('overall_avg_confidence', 0.0)
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
                    'type': chunk['classification']['type'],
                    'metadata': {
                        'confidence': chunk['classification']['confidence'],
                        'chunk_id': chunk['id']
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
                'success_count': layer3_result['success'],
                'total': layer3_result['total'],
                'failed': layer3_result['failed'],
                'success_rate': layer3_result['success_rate']
            })
            
            # ========== Layer 4: 质量保证 ==========
            self._update_progress(progress_callback, 'layer4', 0, {
                'message': '开始质量保证，验证DITA文档...'
            })
            
            # 准备QA数据
            qa_documents = []
            layer3_output_dir = output_dir / 'dita_drafts'
            
            for i, conv_result in enumerate(layer3_result['results'], 1):
                if not conv_result['success']:
                    continue
                
                # 获取文档路径
                content_type = conv_result['content_type']
                title = conv_result['title']
                safe_title = "".join(c if c.isalnum() else '_' for c in title)[:50]
                filename = f"{i:03d}_{content_type.lower()}_{safe_title}.dita"
                dita_file_path = layer3_output_dir / filename
                
                # 读取DITA文件
                try:
                    with open(dita_file_path, 'r', encoding='utf-8') as f:
                        dita_xml = f.read()
                except Exception as e:
                    logger.error(f"❌ 读取DITA文件失败: {e}")
                    continue
                
                qa_documents.append({
                    'xml': dita_xml,
                    'type': content_type,
                    'metadata': {
                        'layer1_confidence': layer1_result.get('confidence', 0.0),
                        'layer2_confidence': layer2_result['statistics']['overall_avg_confidence'],
                        'layer3_iterations': conv_result['metadata']['iterations'],
                        'title': title,
                        'filename': filename
                    }
                })
            
            if qa_documents:
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
                    'avg_quality': layer4_result['summary']['quality_scores']['avg_overall_quality'],
                    'total': layer4_result['total'],
                    'success': layer4_result['success'],
                    'failed': layer4_result['failed']
                })
            else:
                # 没有可处理的DITA文档
                self._update_progress(progress_callback, 'layer4', 100, {
                    'message': '✅ 质量保证完成 (无DITA文档可处理)',
                    'avg_quality': 0.0,
                    'total': 0,
                    'success': 0,
                    'failed': 0
                })
                
                result['layers']['layer4'] = {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'success_rate': 0.0,
                    'avg_quality_score': 0.0
                }
            
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