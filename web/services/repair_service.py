"""
DITA包修复服务
处理手动修改后的DITA ZIP包：验证、链接化、构建
"""
import json
import re
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import subprocess
import uuid

logger = logging.getLogger(__name__)

# 导入现有模块
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.layer4_quality_assurance import QAManager


class DitaPackageRepairService:
    """DITA包修复服务"""
    
    # References文件名常量
    REFERENCES_DITA_FILENAME = "014_reference_References.dita"
    REF_INDEX_FILENAME = "ref_index.json"
    
    def __init__(
        self,
        output_base_dir: Path,
        max_zip_size_mb: int = 200,
        max_jobs_to_keep: int = 10
    ):
        """
        初始化修复服务
        
        Args:
            output_base_dir: 输出基础目录（data/output）
            max_zip_size_mb: 最大ZIP大小（MB）
            max_jobs_to_keep: 最多保留的job数量（用于清理）
        """
        self.output_base_dir = Path(output_base_dir)
        self.max_zip_size_bytes = max_zip_size_mb * 1024 * 1024
        self.max_jobs_to_keep = max_jobs_to_keep
        
        # 初始化QA管理器（不启用AI修复，用户是手动修改的）
        self.qa_manager = QAManager(
            use_dita_ot=False,  # 手动调用
            use_ai_repair=False,  # Option C默认不启用AI修复
            max_iterations=1
        )
        
        logger.info(f"✅ DITA包修复服务初始化完成")
    
    def process_package(
        self,
        zip_file_path: Path,
        doc_name: str,
        linkify_citations: bool = False,
        build_dita_ot: bool = False
    ) -> Dict[str, Any]:
        """
        处理DITA包
        
        Args:
            zip_file_path: 上传的ZIP文件路径
            doc_name: 文档名称
            linkify_citations: 是否执行引文链接化
            build_dita_ot: 是否执行DITA-OT构建
            
        Returns:
            处理结果字典
        """
        job_id = str(uuid.uuid4())
        logger.info(f"🔧 开始处理DITA包: {doc_name} (job_id: {job_id})")
        
        # 创建job目录
        job_dir = self.output_base_dir / doc_name / "repair" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        workdir = job_dir / "workdir"
        workdir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = job_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'job_id': job_id,
            'doc_name': doc_name,
            'start_time': datetime.now().isoformat(),
            'success': False,
            'errors': [],
            'warnings': [],
            'dita_files': [],
            'ref_index': None,
            'validation': {},
            'dita_ot_build': {},
            'output_zip': None
        }
        
        try:
            # 1. 检查ZIP大小
            zip_size = zip_file_path.stat().st_size
            if zip_size > self.max_zip_size_bytes:
                raise ValueError(
                    f"ZIP文件过大: {zip_size / 1024 / 1024:.2f}MB, "
                    f"最大允许: {self.max_zip_size_bytes / 1024 / 1024:.2f}MB"
                )
            
            # 2. 保存输入ZIP
            input_zip_path = job_dir / "input.zip"
            shutil.copy2(zip_file_path, input_zip_path)
            logger.info(f"✅ 输入ZIP已保存: {input_zip_path}")
            
            # 3. 安全解压ZIP
            logger.info("📦 解压ZIP文件...")
            dita_files, resources = self._safe_extract_zip(
                zip_file_path, 
                workdir,
                logs_dir
            )
            
            if not dita_files:
                result['errors'].append("ZIP中未找到任何.dita文件")
                raise ValueError("ZIP中未找到任何.dita文件")
            
            # 保存文件路径时，统一使用正斜杠（URL兼容）
            result['dita_files'] = [str(f.relative_to(workdir)).replace('\\', '/') for f in dita_files]
            logger.info(f"✅ 解压完成: {len(dita_files)} 个DITA文件")
            
            # 4. 检查References文件结构
            references_file = workdir / self.REFERENCES_DITA_FILENAME
            if references_file.exists():
                logger.info("📚 检查References文件结构...")
                ref_check_result = self._check_references_structure(references_file)
                if not ref_check_result['valid']:
                    result['errors'].extend(ref_check_result['errors'])
                    raise ValueError(f"References文件结构检查失败: {ref_check_result['errors']}")
                logger.info("✅ References文件结构检查通过")
            
            # 5. 可选：更新/重建ref_index.json
            ref_index = None
            ref_index_path = workdir / self.REF_INDEX_FILENAME
            if references_file.exists():
                logger.info("📋 生成/更新ref_index.json...")
                ref_index = self._generate_ref_index(references_file, ref_index_path)
                result['ref_index'] = {
                    'count': len(ref_index),
                    'range': f"1-{max(int(k) for k in ref_index.keys() if k.isdigit())}" if ref_index else "0-0"
                }
                logger.info(f"✅ ref_index.json已生成: {len(ref_index)} 个引用")
            
            # 6. 可选：正文引文链接化
            linkified_count = 0
            missing_refs = []
            if linkify_citations:
                if not ref_index:
                    result['warnings'].append("无法执行链接化：ref_index.json不存在")
                else:
                    logger.info("🔗 执行引文链接化...")
                    linkified_count, missing_refs = self._linkify_citations(
                        workdir,
                        dita_files,
                        ref_index,
                        logs_dir
                    )
                    result['linkify'] = {
                        'count': linkified_count,
                        'missing_refs': missing_refs
                    }
                    logger.info(f"✅ 链接化完成: {linkified_count} 个引用，{len(missing_refs)} 个缺失引用")
            
            # 7. 运行QA（复用Layer4）
            logger.info("✅ 运行质量保证检查...")
            qa_results = self._run_qa_checks(workdir, dita_files, logs_dir)
            result['validation'] = qa_results
            logger.info(f"✅ QA检查完成: {qa_results.get('total_errors', 0)} 个错误")
            
            # 8. 可选：DITA-OT构建
            build_result = {}
            if build_dita_ot:
                logger.info("🔨 执行DITA-OT构建...")
                build_result = self._run_dita_ot_build(workdir, logs_dir)
                result['dita_ot_build'] = build_result
                if build_result.get('success'):
                    logger.info("✅ DITA-OT构建完成")
                else:
                    logger.warning(f"⚠️ DITA-OT构建失败: {build_result.get('error')}")
            
            # 9. 打包输出
            logger.info("📦 打包输出ZIP...")
            output_zip_path = job_dir / "output.zip"
            self._package_output(workdir, output_zip_path, logs_dir, job_dir)
            result['output_zip'] = str(output_zip_path.relative_to(self.output_base_dir))
            logger.info(f"✅ 输出ZIP已生成: {output_zip_path}")
            
            # 10. 生成repair_result.json
            result['end_time'] = datetime.now().isoformat()
            result['success'] = True
            result_file = job_dir / "repair_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ DITA包处理完成: {job_id}")
            
        except Exception as e:
            logger.error(f"❌ 处理失败: {e}", exc_info=True)
            result['errors'].append(str(e))
            result['end_time'] = datetime.now().isoformat()
            result['success'] = False
            
            # 保存失败结果
            result_file = job_dir / "repair_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        finally:
            # 清理旧job（可选）
            # self._cleanup_old_jobs(doc_name)
            pass
        
        return result
    
    def _safe_extract_zip(
        self,
        zip_path: Path,
        extract_to: Path,
        logs_dir: Path
    ) -> Tuple[List[Path], List[Path]]:
        """
        安全解压ZIP文件（防止Zip Slip攻击）
        
        Args:
            zip_path: ZIP文件路径
            extract_to: 解压目标目录
            logs_dir: 日志目录
            
        Returns:
            (dita_files列表, resources列表)
        """
        dita_files = []
        resources = []
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for member in zipf.namelist():
                # 防止路径遍历攻击（Zip Slip）
                # 规范化路径，检查是否包含..或绝对路径
                member_path = Path(member)
                if '..' in member_path.parts or member_path.is_absolute():
                    logger.warning(f"⚠️ 跳过可疑路径: {member}")
                    continue
                
                # 构建安全的目标路径
                target_path = extract_to / member_path
                
                # 确保目标路径在extract_to目录内（二次检查）
                try:
                    target_path.resolve().relative_to(extract_to.resolve())
                except ValueError:
                    logger.warning(f"⚠️ 跳过路径遍历尝试: {member}")
                    continue
                
                # 提取文件
                zipf.extract(member, extract_to)
                
                # 分类文件
                if member_path.suffix == '.dita':
                    dita_files.append(target_path)
                elif member_path.parent.name in ['images', 'formulas']:
                    resources.append(target_path)
        
        return dita_files, resources
    
    def _check_references_structure(self, references_file: Path) -> Dict[str, Any]:
        """
        检查References文件结构
        
        Args:
            references_file: References DITA文件路径
            
        Returns:
            检查结果字典
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            with open(references_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查必需结构
            if '<topic id="refs">' not in content and '<topic id=\'refs\'>' not in content:
                result['valid'] = False
                result['errors'].append('缺少 <topic id="refs">')
            
            if '<title>References</title>' not in content:
                result['warnings'].append('缺少 <title>References</title>')
            
            if '<ol>' not in content:
                result['valid'] = False
                result['errors'].append('缺少 <ol> 标签')
            
            # 检查li数量
            li_matches = re.findall(r'<li\s+id=["\']ref(\d+)["\']', content)
            li_count = len(li_matches)
            if li_count == 0:
                result['valid'] = False
                result['errors'].append('没有找到任何 <li id="ref\\d+"> 条目')
            
            # 严禁<table>标签
            if re.search(r'<table\b', content, re.IGNORECASE):
                result['valid'] = False
                result['errors'].append('References文件中包含 <table> 标签（不允许）')
        
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'读取文件失败: {str(e)}')
        
        return result
    
    def _generate_ref_index(
        self,
        references_file: Path,
        ref_index_path: Path
    ) -> Dict[str, str]:
        """
        从References文件生成ref_index.json
        
        Args:
            references_file: References DITA文件路径
            ref_index_path: ref_index.json输出路径
            
        Returns:
            ref_index字典 {citation_number: ref_id}
        """
        ref_index = {}
        
        try:
            with open(references_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 匹配 <li id="refN">
            matches = re.findall(r'<li\s+id=["\']ref(\d+)["\']', content)
            for num_str in matches:
                num = int(num_str)
                ref_index[str(num)] = f"ref{num}"
            
            # 保存ref_index.json
            with open(ref_index_path, 'w', encoding='utf-8') as f:
                json.dump(ref_index, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 生成ref_index.json: {len(ref_index)} 个引用")
        
        except Exception as e:
            logger.error(f"❌ 生成ref_index.json失败: {e}")
        
        return ref_index
    
    def _linkify_citations(
        self,
        workdir: Path,
        dita_files: List[Path],
        ref_index: Dict[str, str],
        logs_dir: Path
    ) -> Tuple[int, List[str]]:
        """
        链接化正文中的引文
        
        Args:
            workdir: 工作目录
            dita_files: DITA文件列表
            ref_index: 引用索引字典
            logs_dir: 日志目录
            
        Returns:
            (链接化数量, 缺失引用列表)
        """
        total_count = 0
        missing_refs = []
        
        # 排除References文件本身
        target_files = [
            f for f in dita_files
            if f.name != self.REFERENCES_DITA_FILENAME
        ]
        
        for dita_file in target_files:
            try:
                count, missing = self._linkify_citations_in_dita(
                    dita_file,
                    ref_index
                )
                total_count += count
                missing_refs.extend(missing)
            except Exception as e:
                logger.error(f"❌ 链接化文件失败 {dita_file.name}: {e}")
        
        return total_count, list(set(missing_refs))
    
    def _linkify_citations_in_dita(
        self,
        dita_file: Path,
        ref_index: Dict[str, str]
    ) -> Tuple[int, List[str]]:
        """
        在单个DITA文件中链接化引文
        
        保护策略：
        - 保护math块（<codeblock outputclass="math">, <equation-inline>）
        - 保护代码块（<codeblock>）
        - 保护已有的<xref>标签
        - 保护URL（http://, https://）
        
        Args:
            dita_file: DITA文件路径
            ref_index: 引用索引字典 {citation_number: ref_id}
            
        Returns:
            (链接化数量, 缺失引用列表)
        """
        with open(dita_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        linkified_count = 0
        missing_refs = []
        
        # 1. 保护特定区域（用占位符替换）
        protected_regions = {}
        placeholder_counter = 0
        
        def protect_region(match):
            nonlocal placeholder_counter
            placeholder = f'__PROTECTED_REGION_{placeholder_counter}__'
            protected_regions[placeholder] = match.group(0)
            placeholder_counter += 1
            return placeholder
        
        # 保护math块
        content = re.sub(
            r'<codeblock[^>]*outputclass=["\']math["\'][^>]*>.*?</codeblock>',
            protect_region,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # 保护行内公式
        content = re.sub(
            r'<equation-inline>.*?</equation-inline>',
            protect_region,
            content,
            flags=re.DOTALL
        )
        
        # 保护代码块（非math）
        content = re.sub(
            r'<codeblock[^>]*>.*?</codeblock>',
            protect_region,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # 保护已有的xref标签
        content = re.sub(
            r'<xref[^>]*>.*?</xref>',
            protect_region,
            content,
            flags=re.DOTALL
        )
        
        # 保护URL（简单匹配，避免误替换）
        # 匹配 http:// 或 https:// 开头的URL（直到空格、引号或XML标签）
        content = re.sub(
            r'https?://[^\s<>"\']+',
            protect_region,
            content
        )
        
        # 2. 替换引文 [n] -> <xref href="014_reference_References.dita#refs/refn">[n]</xref>
        def replace_citation(match):
            nonlocal linkified_count
            citation_num = match.group(1)
            
            if citation_num in ref_index:
                ref_id = ref_index[citation_num]
                xref_tag = f'<xref href="{self.REFERENCES_DITA_FILENAME}#refs/{ref_id}">[{citation_num}]</xref>'
                linkified_count += 1
                return xref_tag
            else:
                missing_refs.append(citation_num)
                return match.group(0)  # 保持原样
        
        # 匹配 [n] 格式的引文（不在保护区域内）
        content = re.sub(r'\[(\d+)\]', replace_citation, content)
        
        # 3. 恢复保护区域
        for placeholder, original_text in protected_regions.items():
            content = content.replace(placeholder, original_text)
        
        # 4. 如果内容有变化，写回文件
        if content != original_content:
            with open(dita_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return linkified_count, missing_refs
    
    def _run_qa_checks(
        self,
        workdir: Path,
        dita_files: List[Path],
        logs_dir: Path
    ) -> Dict[str, Any]:
        """
        运行QA检查（复用Layer4）
        
        Args:
            workdir: 工作目录
            dita_files: DITA文件列表
            logs_dir: 日志目录
            
        Returns:
            QA结果字典
        """
        qa_results = {
            'total': len(dita_files),
            'success': 0,
            'failed': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'errors': []
        }
        
        # 准备QA文档列表
        qa_documents = []
        for dita_file in dita_files:
            try:
                with open(dita_file, 'r', encoding='utf-8') as f:
                    dita_xml = f.read()
                
                # 尝试识别内容类型（简单启发式）
                content_type = "Concept"  # 默认
                if '<task' in dita_xml.lower() or '<taskbody>' in dita_xml:
                    content_type = "Task"
                elif '<reference' in dita_xml.lower() or '<refbody>' in dita_xml:
                    content_type = "Reference"
                elif '<concept' in dita_xml.lower() or '<conbody>' in dita_xml:
                    content_type = "Concept"
                
                qa_documents.append({
                    'xml': dita_xml,
                    'type': content_type,
                    'metadata': {
                        'filename': dita_file.name,
                        'title': dita_file.stem
                    }
                })
            except Exception as e:
                logger.error(f"❌ 读取DITA文件失败 {dita_file.name}: {e}")
                qa_results['failed'] += 1
        
        # 运行QA（使用QAManager.process_batch）
        try:
            # 准备QA文档（转换为QAManager期望的格式）
            qa_docs_for_manager = []
            for doc in qa_documents:
                qa_docs_for_manager.append({
                    'xml': doc['xml'],
                    'type': doc['type'],
                    'metadata': doc['metadata']
                })
            
            # 调用QAManager.process_batch（但配置为不启用AI修复）
            if qa_docs_for_manager:
                # 创建临时输出目录（QAManager需要output_dir参数）
                qa_output_dir = workdir / "qa_output"
                qa_output_dir.mkdir(exist_ok=True)
                
                # 运行QA（批量处理）
                # 注意：由于Option C不启用AI修复，QAManager配置为use_ai_repair=False
                batch_result = self.qa_manager.process_batch(
                    qa_docs_for_manager,
                    output_dir=qa_output_dir
                )
                
                # 汇总结果
                qa_results['total'] = batch_result.get('total', len(qa_docs_for_manager))
                qa_results['success'] = batch_result.get('success', 0)
                qa_results['failed'] = batch_result.get('failed', 0)
                
                # 收集错误和警告
                for result_item in batch_result.get('results', []):
                    filename = result_item.get('filename') or result_item.get('metadata', {}).get('filename', 'unknown')
                    
                    if not result_item.get('success', False):
                        qa_results['failed'] += 1
                        error_msg = result_item.get('error', '未知错误')
                        qa_results['total_errors'] += 1
                        qa_results['errors'].append({
                            'filename': filename,
                            'error': error_msg
                        })
                    else:
                        qa_results['success'] += 1
                        # 收集quality_report中的错误和警告
                        if result_item.get('quality_report'):
                            qr = result_item['quality_report']
                            qa_results['total_errors'] += len(qr.get('errors', []))
                            qa_results['total_warnings'] += len(qr.get('warnings', []))
            else:
                logger.warning("⚠️ 没有可处理的QA文档")
        
        except Exception as e:
            logger.error(f"❌ QA检查失败: {e}", exc_info=True)
            qa_results['errors'].append({'general_error': str(e)})
            qa_results['failed'] = len(qa_documents)
        
        return qa_results
    
    def _run_dita_ot_build(
        self,
        workdir: Path,
        logs_dir: Path
    ) -> Dict[str, Any]:
        """
        运行DITA-OT构建
        
        Args:
            workdir: 工作目录
            logs_dir: 日志目录
            
        Returns:
            构建结果字典
        """
        result = {
            'success': False,
            'exit_code': -1,
            'log_file': None,
            'error': None
        }
        
        import os
        
        # 检查DITA-OT是否可用
        dita_ot_path = project_root / "dita-ot" / "dita-ot-4.3.5" / "bin" / "dita"
        if not dita_ot_path.exists():
            # 尝试环境变量
            dita_ot_path = Path(os.environ.get('DITA_OT_HOME', '')) / "bin" / "dita"
            if not dita_ot_path.exists():
                result['error'] = "DITA-OT未找到，请设置DITA_OT_HOME环境变量"
                return result
        
        log_file = logs_dir / "ditaot_build.log"
        
        try:
            # 查找map文件或第一个dita文件作为输入
            map_files = list(workdir.glob("*.ditamap"))
            if map_files:
                input_file = map_files[0]
            else:
                dita_files = list(workdir.glob("*.dita"))
                if dita_files:
                    input_file = dita_files[0]
                else:
                    result['error'] = "未找到输入文件（.ditamap或.dita）"
                    return result
            
            output_dir = workdir / "build"
            output_dir.mkdir(exist_ok=True)
            
            # 执行DITA-OT构建
            cmd = [
                str(dita_ot_path),
                f"-i={input_file}",
                f"-o={output_dir}",
                "-f=html5"
            ]
            
            with open(log_file, 'w', encoding='utf-8') as log_f:
                process = subprocess.run(
                    cmd,
                    cwd=str(workdir),
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    timeout=600  # 10分钟超时
                )
            
            result['exit_code'] = process.returncode
            result['log_file'] = str(log_file.relative_to(self.output_base_dir))
            result['success'] = (process.returncode == 0)
            
            if not result['success']:
                result['error'] = f"DITA-OT构建失败，退出码: {process.returncode}"
        
        except subprocess.TimeoutExpired:
            result['error'] = "DITA-OT构建超时（超过10分钟）"
        except Exception as e:
            result['error'] = f"DITA-OT构建异常: {str(e)}"
        
        return result
    
    def _package_output(
        self,
        workdir: Path,
        output_zip_path: Path,
        logs_dir: Path,
        job_dir: Path
    ) -> None:
        """
        打包输出ZIP
        
        Args:
            workdir: 工作目录
            output_zip_path: 输出ZIP路径
            logs_dir: 日志目录
            job_dir: job目录
        """
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加所有DITA文件
            for dita_file in workdir.glob("*.dita"):
                zipf.write(dita_file, dita_file.name)
            
            # 添加ref_index.json（如果存在）
            ref_index_file = workdir / self.REF_INDEX_FILENAME
            if ref_index_file.exists():
                zipf.write(ref_index_file, ref_index_file.name)
            
            # 添加资源目录（images, formulas等）
            for resource_dir in ['images', 'formulas']:
                resource_path = workdir / resource_dir
                if resource_path.exists() and resource_path.is_dir():
                    for file_path in resource_path.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(workdir)
                            zipf.write(file_path, str(arcname))
            
            # 添加build目录（如果存在）
            build_dir = workdir / "build"
            if build_dir.exists() and build_dir.is_dir():
                for file_path in build_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(workdir)
                        zipf.write(file_path, str(arcname))
            
            # 添加repair_result.json
            result_file = job_dir / "repair_result.json"
            if result_file.exists():
                zipf.write(result_file, "repair_result.json")
        
        logger.info(f"✅ 输出ZIP已打包: {output_zip_path}")

