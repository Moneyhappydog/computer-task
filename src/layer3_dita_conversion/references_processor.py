"""
References处理模块 - 集成到Layer3 pipeline

本模块从Layer1的Markdown文件中提取References。
- 主要数据源：Layer1输出的Markdown文件（必需）
- 辅助数据源：Layer2输出的JSON文件（可选，仅用于辅助信息）

不直接访问PDF文件或其他原始文档。
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .references_extractor import ReferencesExtractor

logger = logging.getLogger(__name__)


class ReferencesProcessor:
    """References处理器 - 集成到Layer3 pipeline"""
    
    def __init__(self, linkify_citations: bool = True):
        """
        初始化References处理器
        
        Args:
            linkify_citations: 是否对正文中的引文进行链接化
        """
        self.extractor = ReferencesExtractor()
        self.linkify_citations = linkify_citations
        logger.info("✅ References处理器初始化完成")
    
    def process(
        self,
        layer3_output_dir: Path,
        markdown_path: Path,
        layer2_result_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        处理References：提取、生成DITA、链接化
        
        主要从Layer1的Markdown文件中提取References，Layer2 JSON仅作为可选的辅助信息。
        
        Args:
            layer3_output_dir: Layer3输出目录
            markdown_path: Layer1的Markdown文件路径（必需，主要数据源）
            layer2_result_path: Layer2结果JSON路径（可选，仅用于辅助信息）
            
        Returns:
            处理结果字典
        """
        logger.info("="*70)
        logger.info("📚 开始处理References")
        logger.info("="*70)
        
        # 1. 从Layer1 Markdown提取References（主要数据源）
        if not markdown_path or not markdown_path.exists():
            logger.error(f"❌ Layer1 Markdown文件不存在: {markdown_path}")
            return {
                'success': False,
                'error': f'Layer1 Markdown文件不存在: {markdown_path}',
                'warnings': ['必须提供Layer1 Markdown文件作为References提取的数据源']
            }
        
        logger.info(f"📄 从Layer1 Markdown提取References: {markdown_path}")
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # 检查是否存在ref_index.json（可能在之前的运行中已生成）
        ref_index_path = layer3_output_dir / "ref_index.json"
        ref_index_for_extraction = ref_index_path if ref_index_path.exists() else None
        
        extract_result = self.extractor.extract_from_markdown(
            markdown_content,
            ref_index_path=ref_index_for_extraction
        )
        
        if not extract_result['success']:
            logger.error("❌ References提取失败")
            return {
                'success': False,
                'error': 'References提取失败',
                'warnings': extract_result.get('warnings', [])
            }
        
        references = extract_result['references']
        statistics = extract_result['statistics']
        warnings = extract_result.get('warnings', [])
        
        # 2. 生成DITA文件（带重试机制）
        dita_filename = "014_reference_References.dita"
        dita_path = layer3_output_dir / dita_filename
        
        max_retries = 2
        generation_success = False
        validation_result = None
        
        for attempt in range(1, max_retries + 1):
            logger.info(f"🔄 生成DITA文件（尝试 {attempt}/{max_retries}）...")
            
            success = self.extractor.generate_dita(
                references=references,
                output_path=dita_path,
                topic_id="refs"
            )
            
            if not success:
                logger.error(f"❌ DITA文件生成失败（尝试 {attempt}/{max_retries}）")
                validation_result = {'valid': False, 'errors': ['文件生成失败']}
                continue
            
            # 3. 基本验证DITA文件（此时ref_index.json尚未生成）
            try:
                validation_result = self.extractor.validate_references_dita(
                    dita_path,
                    ref_index_path=None  # 第一次验证不使用ref_index，只做基本检查
                )
            except ValueError as e:
                # 验证失败，记录错误
                validation_result = {'valid': False, 'errors': [str(e)]}
                logger.warning(f"⚠️ 基本验证失败: {e}")
            
            if validation_result['valid']:
                generation_success = True
                logger.info(f"✅ DITA文件生成并验证成功（尝试 {attempt}/{max_retries}）")
                break
            else:
                logger.warning(f"⚠️ DITA文件验证失败（尝试 {attempt}/{max_retries}）: {validation_result['errors']}")
                if attempt < max_retries:
                    logger.info(f"   准备重试（清理并重新生成）...")
                    # 删除失败的DITA文件
                    if dita_path.exists():
                        dita_path.unlink()
                        logger.info(f"   已删除失败的DITA文件: {dita_path}")
        
        if not generation_success:
            logger.error("❌ DITA文件生成失败（达到最大重试次数）")
            return {
                'success': False,
                'error': 'DITA文件生成失败（验证未通过）',
                'validation_errors': validation_result.get('errors', []) if validation_result else ['未知错误']
            }
        
        # 4. 生成ref_index.json（在验证之前生成，以便后续验证可以使用）
        ref_index_path = layer3_output_dir / "ref_index.json"
        ref_index = {
            str(ref['number']): f"ref{ref['number']}"
            for ref in references
        }
        self.extractor.generate_ref_index(references, ref_index_path)
        
        # 5. 最终验证（使用刚生成的ref_index.json）
        try:
            final_validation = self.extractor.validate_references_dita(
                dita_path,
                ref_index_path=ref_index_path
            )
            validation_result = final_validation
        except ValueError as e:
            # 最终验证失败
            logger.error(f"❌ 最终验证失败: {e}")
            return {
                'success': False,
                'error': f'最终验证失败: {str(e)}',
                'validation_errors': [str(e)]
            }
        
        # 6. 链接化正文中的引文（可选）
        linkified_count = 0
        missing_refs_all = []
        
        if self.linkify_citations:
            logger.info("🔗 开始链接化正文中的引文")
            
            # 查找所有DITA文件（除了References文件本身）
            dita_files = [
                f for f in layer3_output_dir.glob("*.dita")
                if f.name != dita_filename
            ]
            
            for dita_file in dita_files:
                count, missing = self.extractor.linkify_citations_in_dita(
                    dita_file=dita_file,
                    ref_index=ref_index,
                    references_dita_filename=dita_filename
                )
                linkified_count += count
                missing_refs_all.extend(missing)
        
        # 7. 生成统计报告
        result = {
            'success': True,
            'dita_file': str(dita_path),
            'ref_index_file': str(ref_index_path),
            'statistics': {
                'total_references': statistics['total'],
                'min_number': statistics['min_number'],
                'max_number': statistics['max_number'],
                'missing_numbers': statistics['missing_numbers'],
                'linkified_count': linkified_count,
                'missing_refs_in_body': list(set(missing_refs_all))
            },
            'validation': validation_result,
            'warnings': warnings
        }
        
        # 输出统计信息
        logger.info("\n" + "="*70)
        logger.info("✅ References处理完成")
        logger.info("="*70)
        logger.info(f"   参考文献条目数: {statistics['total']}")
        logger.info(f"   编号范围: {statistics['min_number']}-{statistics['max_number']}")
        if statistics['missing_numbers']:
            logger.warning(f"   缺失编号: {statistics['missing_numbers']}")
        logger.info(f"   链接化引文数: {linkified_count}")
        if missing_refs_all:
            logger.warning(f"   正文中缺失的引用: {set(missing_refs_all)}")
        logger.info(f"   DITA文件: {dita_path}")
        logger.info(f"   验证结果: {'通过' if validation_result['valid'] else '失败'}")
        if validation_result['errors']:
            for error in validation_result['errors']:
                logger.error(f"   ❌ {error}")
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                logger.warning(f"   ⚠️ {warning}")
        logger.info("="*70)
        
        return result

