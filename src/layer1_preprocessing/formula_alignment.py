"""
公式与 Markdown / DITA 文本对齐与回写模块
将OCR得到的LaTeX公式回写到Markdown/DITA文档中
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Dict
from pathlib import Path
import json
import re
from difflib import SequenceMatcher

# 导入FormulaOCRResult（如果存在）
try:
    from .formula_ocr import FormulaOCRResult
except ImportError:
    import sys
    import importlib.util
    
    current_file = Path(__file__)
    formula_ocr_path = current_file.parent / "formula_ocr.py"
    
    if formula_ocr_path.exists():
        spec = importlib.util.spec_from_file_location("formula_ocr", formula_ocr_path)
        formula_ocr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(formula_ocr)
        FormulaOCRResult = formula_ocr.FormulaOCRResult
    else:
        # 如果导入失败，定义基本结构
        @dataclass
        class FormulaOCRResult:
            formula_id: str
            formula_type: str
            page_number: int
            block_index: Optional[int]
            line_index: Optional[int]
            span_indices: Optional[List[int]]
            bbox: Tuple[float, float, float, float]
            image_path: str
            latex: str
            ocr_confidence: Optional[float]
            detector_score: Optional[float]
            source_text: Optional[str]


@dataclass
class ReplacementLog:
    """替换日志"""
    formula_id: str
    formula_type: str
    before: str
    after: str
    success: bool
    reason: str = ""


class FormulaAligner:
    """公式对齐与回写器"""
    
    def __init__(
        self,
        formula_results: List[FormulaOCRResult],
    ):
        """
        初始化公式对齐器
        
        Args:
            formula_results: 公式OCR结果列表
        """
        self.formula_results = formula_results
        self.replacement_logs: List[ReplacementLog] = []
    
    @classmethod
    def from_json(cls, json_path: str) -> "FormulaAligner":
        """
        从JSON文件加载FormulaOCRResult列表，并构造FormulaAligner
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            FormulaAligner实例
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 从JSON中提取formulas列表
        if isinstance(data, dict):
            formulas_data = data.get('formulas', [])
        elif isinstance(data, list):
            formulas_data = data
        else:
            raise ValueError(f"无法解析JSON格式: {json_path}")
        
        # 转换为FormulaOCRResult对象
        formula_results = []
        for f_data in formulas_data:
            # 处理bbox（可能是list，需要转为tuple）
            bbox = f_data.get('bbox')
            if isinstance(bbox, list):
                bbox = tuple(bbox)
            
            formula = FormulaOCRResult(
                formula_id=f_data.get('formula_id', ''),
                formula_type=f_data.get('formula_type', ''),
                page_number=f_data.get('page_number', 0),
                block_index=f_data.get('block_index'),
                line_index=f_data.get('line_index'),
                span_indices=f_data.get('span_indices'),
                bbox=bbox,
                image_path=f_data.get('image_path', ''),
                latex=f_data.get('latex', ''),
                ocr_confidence=f_data.get('ocr_confidence'),
                detector_score=f_data.get('detector_score'),
                source_text=f_data.get('source_text'),
            )
            formula_results.append(formula)
        
        return cls(formula_results)
    
    def align_markdown(
        self,
        markdown_text: str,
        block_prefix: str = "$$",
        block_suffix: str = "$$",
        inline_prefix: str = "$",
        inline_suffix: str = "$",
        min_source_len: int = 3,
    ) -> str:
        """
        输入原始markdown文本和公式结果，
        返回已经插入/替换LaTeX公式后的markdown文本
        
        Args:
            markdown_text: 原始Markdown文本
            block_prefix: 块级公式前缀（默认"$$"）
            block_suffix: 块级公式后缀（默认"$$"）
            inline_prefix: 行内公式前缀（默认"$"）
            inline_suffix: 行内公式后缀（默认"$"）
            min_source_len: source_text的最小长度阈值（低于此值可能跳过）
            
        Returns:
            增强后的Markdown文本
        """
        self.replacement_logs = []
        
        # 分离块级公式和行内公式
        block_formulas = [f for f in self.formula_results if f.formula_type == "block"]
        inline_formulas = [f for f in self.formula_results if f.formula_type == "inline"]
        
        # 按page_number和detector_score排序（从前到后，高分优先）
        block_formulas.sort(key=lambda f: (f.page_number, -f.detector_score if f.detector_score else 0))
        inline_formulas.sort(key=lambda f: (f.page_number, f.line_index if f.line_index is not None else 0, -f.detector_score if f.detector_score else 0))
        
        # 第一轮：处理块级公式
        result_text = self._align_block_formulas(
            markdown_text,
            block_formulas,
            block_prefix,
            block_suffix,
            min_source_len
        )
        
        # 第二轮：处理行内公式
        result_text = self._align_inline_formulas(
            result_text,
            inline_formulas,
            inline_prefix,
            inline_suffix,
            min_source_len
        )
        
        return result_text
    
    def _align_block_formulas(
        self,
        markdown_text: str,
        block_formulas: List[FormulaOCRResult],
        block_prefix: str,
        block_suffix: str,
        min_source_len: int,
    ) -> str:
        """
        对齐块级公式
        
        Args:
            markdown_text: Markdown文本
            block_formulas: 块级公式列表
            block_prefix: 块级公式前缀
            block_suffix: 块级公式后缀
            min_source_len: 最小source_text长度
            
        Returns:
            处理后的Markdown文本
        """
        lines = markdown_text.splitlines(keepends=True)
        used_indices = set()  # 记录已使用的行索引，避免重复替换
        
        for formula in block_formulas:
            # 检查latex是否有效
            if not formula.latex or not formula.latex.strip():
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="block",
                    before="",
                    after="",
                    success=False,
                    reason="LaTeX为空"
                ))
                continue
            
            # 检查source_text
            source_text = formula.source_text
            if not source_text or len(source_text.strip()) < min_source_len:
                # 尝试在文末添加
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="block",
                    before="",
                    after=f"{block_prefix}\n{formula.latex}\n{block_suffix}",
                    success=False,
                    reason=f"source_text无效（长度={len(source_text) if source_text else 0}），未插入"
                ))
                continue
            
            # 在行中搜索匹配
            best_match_idx = None
            best_similarity = 0.0
            best_line = None
            
            for i, line in enumerate(lines):
                if i in used_indices:
                    continue
                
                # 计算相似度
                similarity = SequenceMatcher(None, source_text.lower(), line.lower()).ratio()
                
                # 如果包含source_text的子串，提高相似度
                if source_text.lower() in line.lower():
                    similarity = max(similarity, 0.8)
                
                if similarity > best_similarity and similarity > 0.3:  # 相似度阈值
                    best_similarity = similarity
                    best_match_idx = i
                    best_line = line
            
            if best_match_idx is not None:
                # 检查是否已经有$$包裹
                if block_prefix in best_line and block_suffix in best_line:
                    # 已有公式标记，跳过
                    self.replacement_logs.append(ReplacementLog(
                        formula_id=formula.formula_id,
                        formula_type="block",
                        before=best_line.strip(),
                        after=best_line.strip(),
                        success=False,
                        reason="已存在公式标记"
                    ))
                    continue
                
                # 替换或插入
                before = best_line.strip()
                after = f"{block_prefix}\n{formula.latex}\n{block_suffix}\n"
                
                # 如果原行看起来像公式文本，直接替换；否则在前后插入
                if best_similarity > 0.6:
                    lines[best_match_idx] = after
                else:
                    # 在行后插入
                    lines[best_match_idx] = best_line.rstrip() + "\n\n" + after
                
                used_indices.add(best_match_idx)
                
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="block",
                    before=before,
                    after=after.strip(),
                    success=True,
                    reason=f"相似度={best_similarity:.2f}"
                ))
            else:
                # 未找到匹配，记录日志
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="block",
                    before="",
                    after=f"{block_prefix}\n{formula.latex}\n{block_suffix}",
                    success=False,
                    reason="未找到匹配行"
                ))
        
        return ''.join(lines)
    
    def _align_inline_formulas(
        self,
        markdown_text: str,
        inline_formulas: List[FormulaOCRResult],
        inline_prefix: str,
        inline_suffix: str,
        min_source_len: int,
    ) -> str:
        """
        对齐行内公式
        
        Args:
            markdown_text: Markdown文本
            inline_formulas: 行内公式列表
            inline_prefix: 行内公式前缀
            inline_suffix: 行内公式后缀
            min_source_len: 最小source_text长度
            
        Returns:
            处理后的Markdown文本
        """
        result_text = markdown_text
        used_positions = []  # 记录已替换的位置，避免重复
        
        for formula in inline_formulas:
            # 检查latex是否有效
            if not formula.latex or not formula.latex.strip():
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="inline",
                    before="",
                    after="",
                    success=False,
                    reason="LaTeX为空"
                ))
                continue
            
            # 检查source_text
            source_text = formula.source_text
            if not source_text or len(source_text.strip()) < min_source_len:
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="inline",
                    before="",
                    after="",
                    success=False,
                    reason=f"source_text无效（长度={len(source_text) if source_text else 0}）"
                ))
                continue
            
            # 检查是否已经在$...$中
            if inline_prefix in source_text and inline_suffix in source_text:
                # 可能已经是公式，跳过
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="inline",
                    before=source_text,
                    after=source_text,
                    success=False,
                    reason="已包含公式标记"
                ))
                continue
            
            # 转义source_text用于正则匹配
            escaped_source = re.escape(source_text)
            
            # 查找所有匹配位置
            matches = list(re.finditer(escaped_source, result_text))
            
            if not matches:
                # 尝试模糊匹配：去除空格
                source_clean = re.sub(r'\s+', ' ', source_text.strip())
                escaped_clean = re.escape(source_clean)
                matches = list(re.finditer(escaped_clean, result_text))
            
            if not matches:
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="inline",
                    before=source_text,
                    after="",
                    success=False,
                    reason="未找到匹配文本"
                ))
                continue
            
            # 选择第一个未使用的位置
            replacement_made = False
            for match in matches:
                start, end = match.span()
                
                # 检查是否与已替换位置重叠
                overlap = False
                for used_start, used_end in used_positions:
                    if not (end <= used_start or start >= used_end):
                        overlap = True
                        break
                
                if overlap:
                    continue
                
                # 检查匹配位置前后是否已有$符号（避免重复包裹）
                before_char = result_text[max(0, start - 1)]
                after_char = result_text[min(len(result_text) - 1, end)]
                
                if before_char == inline_prefix or after_char == inline_suffix:
                    # 已有公式标记，跳过
                    self.replacement_logs.append(ReplacementLog(
                        formula_id=formula.formula_id,
                        formula_type="inline",
                        before=source_text,
                        after=source_text,
                        success=False,
                        reason="附近已有公式标记"
                    ))
                    continue
                
                # 执行替换
                before = result_text[start:end]
                after = f"{inline_prefix}{formula.latex}{inline_suffix}"
                
                result_text = result_text[:start] + after + result_text[end:]
                used_positions.append((start, start + len(after)))
                replacement_made = True
                
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="inline",
                    before=before,
                    after=after,
                    success=True,
                    reason="成功替换"
                ))
                break
            
            if not replacement_made:
                self.replacement_logs.append(ReplacementLog(
                    formula_id=formula.formula_id,
                    formula_type="inline",
                    before=source_text,
                    after="",
                    success=False,
                    reason="所有匹配位置已被使用"
                ))
        
        return result_text
    
    def align_dita(
        self,
        dita_text: str,
        block_tag: str = "codeblock",
        block_outputclass: str = "math",
        inline_tag: str = "ph",
        min_source_len: int = 3,
    ) -> str:
        """
        对齐DITA文本（可选功能）
        
        Args:
            dita_text: 原始DITA文本
            block_tag: 块级公式使用的标签（默认"codeblock"）
            block_outputclass: 块级公式的outputclass属性（默认"math"）
            inline_tag: 行内公式使用的标签（默认"ph"）
            min_source_len: 最小source_text长度
            
        Returns:
            处理后的DITA文本
        """
        # 分离块级公式和行内公式
        block_formulas = [f for f in self.formula_results if f.formula_type == "block"]
        inline_formulas = [f for f in self.formula_results if f.formula_type == "inline"]
        
        result_text = dita_text
        
        # 处理块级公式
        for formula in block_formulas:
            if not formula.latex or not formula.latex.strip():
                continue
            
            source_text = formula.source_text
            if not source_text or len(source_text.strip()) < min_source_len:
                continue
            
            # 在DITA中搜索并替换
            escaped_source = re.escape(source_text)
            match = re.search(escaped_source, result_text)
            
            if match:
                before = match.group(0)
                after = f'<{block_tag} outputclass="{block_outputclass}">{formula.latex}</{block_tag}>'
                result_text = result_text[:match.start()] + after + result_text[match.end():]
        
        # 处理行内公式
        for formula in inline_formulas:
            if not formula.latex or not formula.latex.strip():
                continue
            
            source_text = formula.source_text
            if not source_text or len(source_text.strip()) < min_source_len:
                continue
            
            # 在DITA中搜索并替换
            escaped_source = re.escape(source_text)
            match = re.search(escaped_source, result_text)
            
            if match:
                before = match.group(0)
                after = f'<{inline_tag}>{formula.latex}</{inline_tag}>'
                result_text = result_text[:match.start()] + after + result_text[match.end():]
        
        return result_text
    
    def get_replacement_stats(self) -> Dict:
        """
        获取替换统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.replacement_logs)
        successful = sum(1 for log in self.replacement_logs if log.success)
        failed = total - successful
        
        block_success = sum(1 for log in self.replacement_logs 
                           if log.success and log.formula_type == "block")
        inline_success = sum(1 for log in self.replacement_logs 
                            if log.success and log.formula_type == "inline")
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'block_success': block_success,
            'inline_success': inline_success,
            'success_rate': successful / total if total > 0 else 0.0
        }
    
    def print_replacement_logs(self, max_logs: int = 20):
        """
        打印替换日志
        
        Args:
            max_logs: 最多打印的日志数
        """
        print(f"\n替换日志（前{max_logs}个）:")
        print("=" * 70)
        
        for i, log in enumerate(self.replacement_logs[:max_logs], 1):
            status = "✓" if log.success else "✗"
            print(f"\n{status} {log.formula_id} ({log.formula_type}):")
            print(f"  原因: {log.reason}")
            if log.before:
                print(f"  替换前: {log.before[:60]!r}...")
            if log.after:
                print(f"  替换后: {log.after[:60]!r}...")
        
        if len(self.replacement_logs) > max_logs:
            print(f"\n... (还有 {len(self.replacement_logs) - max_logs} 条日志)")


# ============================================================================
# 命令行使用示例
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 3:
        print("用法: python formula_alignment.py <markdown_path> <ocr_json_path> [output_path]")
        print("示例: python formula_alignment.py layer1_markdown.txt formula_ocr_results.json")
        print("示例: python formula_alignment.py layer1_markdown.txt formula_ocr_results.json output.md")
        sys.exit(1)
    
    md_path = sys.argv[1]
    json_path = sys.argv[2]
    out_md_path = sys.argv[3] if len(sys.argv) > 3 else "markdown_with_formulas.md"
    
    try:
        print("=" * 70)
        print("公式对齐与回写")
        print("=" * 70)
        print(f"\nMarkdown文件: {md_path}")
        print(f"OCR结果JSON: {json_path}")
        print(f"输出文件: {out_md_path}\n")
        
        # 读取markdown
        print("步骤1: 读取Markdown文件...")
        markdown_text = Path(md_path).read_text(encoding="utf-8")
        print(f"✓ 读取完成，共 {len(markdown_text)} 字符\n")
        
        # 读取OCR结果JSON
        print("步骤2: 加载OCR结果...")
        aligner = FormulaAligner.from_json(json_path)
        print(f"✓ 加载完成，共 {len(aligner.formula_results)} 个公式\n")
        
        # 对齐并回写
        print("步骤3: 对齐并回写公式...")
        new_markdown = aligner.align_markdown(markdown_text)
        print("✓ 处理完成\n")
        
        # 保存结果
        print("步骤4: 保存结果...")
        Path(out_md_path).write_text(new_markdown, encoding="utf-8")
        print(f"✓ 已保存到: {out_md_path}\n")
        
        # 显示统计信息
        stats = aligner.get_replacement_stats()
        print("=" * 70)
        print("替换统计")
        print("=" * 70)
        print(f"总公式数: {stats['total']}")
        print(f"成功替换: {stats['successful']} ({stats['success_rate']:.1%})")
        print(f"失败: {stats['failed']}")
        print(f"  块级公式成功: {stats['block_success']}")
        print(f"  行内公式成功: {stats['inline_success']}")
        
        # 显示部分日志
        aligner.print_replacement_logs(max_logs=10)
        
        print(f"\n{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



