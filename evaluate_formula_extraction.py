#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公式提取效果评估工具
评估公式提取的质量，包括：
1. 提取完整性（数量统计）
2. OCR质量（LaTeX准确性）
3. 图片质量（清晰度、尺寸）
4. 提供改进建议
"""
from pathlib import Path
import json
import sys
from typing import Dict, List, Tuple
from PIL import Image
import re

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluate_formula_extraction")


class FormulaExtractionEvaluator:
    """公式提取效果评估器"""
    
    def __init__(self, formula_dir: Path):
        """
        初始化评估器
        
        Args:
            formula_dir: 公式目录路径（包含公式图片和formulas_latex.json）
        """
        self.formula_dir = Path(formula_dir)
        self.latex_file = self.formula_dir / "formulas_latex.json"
        
    def evaluate(self) -> Dict:
        """
        执行完整评估
        
        Returns:
            评估结果字典
        """
        print("=" * 80)
        print("[评估] 公式提取效果评估")
        print("=" * 80)
        
        results = {
            'extraction_stats': self._evaluate_extraction(),
            'ocr_quality': self._evaluate_ocr_quality(),
            'image_quality': self._evaluate_image_quality(),
            'overall_score': 0.0,
            'recommendations': []
        }
        
        # 计算总体评分
        results['overall_score'] = self._calculate_overall_score(results)
        
        # 生成改进建议
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _evaluate_extraction(self) -> Dict:
        """评估提取完整性"""
        print("\n[1/3] 评估提取完整性...")
        
        # 统计公式图片
        formula_images = list(self.formula_dir.glob("page*_formula*.png"))
        total_formulas = len(formula_images)
        
        # 按页面分组
        page_distribution = {}
        for img_path in formula_images:
            match = re.search(r'page(\d+)_formula', img_path.name)
            if match:
                page = int(match.group(1))
                page_distribution[page] = page_distribution.get(page, 0) + 1
        
        # 检查是否有LaTeX文件
        has_latex = self.latex_file.exists()
        latex_count = 0
        if has_latex:
            try:
                with open(self.latex_file, 'r', encoding='utf-8') as f:
                    latex_data = json.load(f)
                    latex_count = len([v for v in latex_data.values() if v.strip()])
            except Exception as e:
                logger.warning(f"读取LaTeX文件失败: {e}")
        
        stats = {
            'total_formulas': total_formulas,
            'pages_with_formulas': len(page_distribution),
            'page_distribution': page_distribution,
            'has_latex_file': has_latex,
            'latex_count': latex_count,
            'extraction_rate': latex_count / total_formulas if total_formulas > 0 else 0
        }
        
        print(f"  [OK] 总公式数: {stats['total_formulas']}")
        print(f"  [OK] 包含公式的页数: {stats['pages_with_formulas']}")
        print(f"  [OK] OCR转换数: {stats['latex_count']}")
        print(f"  [OK] 提取率: {stats['extraction_rate']:.1%}")
        
        return stats
    
    def _evaluate_ocr_quality(self) -> Dict:
        """评估OCR质量"""
        print("\n[2/3] 评估OCR质量...")
        
        if not self.latex_file.exists():
            return {
                'score': 0.0,
                'issues': ['LaTeX文件不存在'],
                'sample_count': 0
            }
        
        try:
            with open(self.latex_file, 'r', encoding='utf-8') as f:
                latex_data = json.load(f)
        except Exception as e:
            return {
                'score': 0.0,
                'issues': [f'无法读取LaTeX文件: {e}'],
                'sample_count': 0
            }
        
        issues = []
        quality_scores = []
        valid_count = 0
        empty_count = 0
        suspicious_count = 0
        
        for name, latex in latex_data.items():
            if not latex or not latex.strip():
                empty_count += 1
                continue
            
            valid_count += 1
            score = self._score_latex_quality(latex)
            quality_scores.append(score)
            
            # 检测可疑的LaTeX
            if self._is_suspicious_latex(latex):
                suspicious_count += 1
        
        avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        if empty_count > 0:
            issues.append(f"{empty_count} 个公式OCR失败（空结果）")
        if suspicious_count > 0:
            issues.append(f"{suspicious_count} 个公式OCR结果可疑（可能包含乱码）")
        if avg_score < 0.5:
            issues.append("OCR整体质量较低，建议检查pix2tex模型")
        
        result = {
            'score': avg_score,
            'valid_count': valid_count,
            'empty_count': empty_count,
            'suspicious_count': suspicious_count,
            'issues': issues,
            'sample_count': len(latex_data)
        }
        
        print(f"  [OK] 有效LaTeX数: {result['valid_count']}")
        print(f"  [OK] 空结果数: {result['empty_count']}")
        print(f"  [OK] 可疑结果数: {result['suspicious_count']}")
        print(f"  [OK] 平均质量分: {result['score']:.2f}/1.0")
        
        if issues:
            print(f"  [WARN] 问题:")
            for issue in issues:
                print(f"     - {issue}")
        
        return result
    
    def _evaluate_image_quality(self) -> Dict:
        """评估图片质量"""
        print("\n[3/3] 评估图片质量...")
        
        formula_images = list(self.formula_dir.glob("page*_formula*.png"))
        
        if not formula_images:
            return {
                'score': 0.0,
                'total_images': 0,
                'issues': ['未找到公式图片']
            }
        
        sizes = []
        issues = []
        
        for img_path in formula_images:
            try:
                img = Image.open(img_path)
                width, height = img.size
                sizes.append((width, height))
                
                # 检查图片是否过小
                if width < 50 or height < 20:
                    issues.append(f"{img_path.name}: 尺寸过小 ({width}x{height})")
                
            except Exception as e:
                issues.append(f"{img_path.name}: 无法读取 ({e})")
        
        avg_width = sum(w for w, h in sizes) / len(sizes) if sizes else 0
        avg_height = sum(h for w, h in sizes) / len(sizes) if sizes else 0
        
        # 质量评分：基于平均尺寸
        size_score = min(1.0, (avg_width * avg_height) / (200 * 50))
        
        result = {
            'score': size_score,
            'total_images': len(formula_images),
            'avg_width': avg_width,
            'avg_height': avg_height,
            'issues': issues
        }
        
        print(f"  [OK] 总图片数: {result['total_images']}")
        print(f"  [OK] 平均尺寸: {result['avg_width']:.0f}x{result['avg_height']:.0f}")
        print(f"  [OK] 质量评分: {result['score']:.2f}/1.0")
        
        if issues:
            print(f"  [WARN] 问题:")
            for issue in issues[:5]:  # 只显示前5个
                print(f"     - {issue}")
            if len(issues) > 5:
                print(f"     ... 还有 {len(issues) - 5} 个问题")
        
        return result
    
    def _score_latex_quality(self, latex: str) -> float:
        """
        评估单个LaTeX代码的质量
        
        Returns:
            0.0-1.0 之间的质量分数
        """
        if not latex or not latex.strip():
            return 0.0
        
        score = 1.0
        
        # 检查常见问题
        # 1. 乱码字符
        if re.search(r'[^\x00-\x7F\u0100-\uFFFF\\{}_^]', latex):
            score -= 0.3
        
        # 2. 过多的转义字符（可能是OCR错误）
        if latex.count('\\') > len(latex) * 0.3:
            score -= 0.2
        
        # 3. 重复字符（可能是OCR错误）
        if re.search(r'(.)\1{5,}', latex):
            score -= 0.2
        
        # 4. 不匹配的括号
        open_braces = latex.count('{')
        close_braces = latex.count('}')
        if abs(open_braces - close_braces) > 2:
            score -= 0.1
        
        # 5. 包含常见数学符号（加分）
        math_symbols = ['frac', 'sum', 'int', 'sqrt', 'exp', 'log', 'sin', 'cos']
        if any(symbol in latex for symbol in math_symbols):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _is_suspicious_latex(self, latex: str) -> bool:
        """判断LaTeX是否可疑（可能包含乱码）"""
        if not latex:
            return True
        
        # 检查乱码模式
        suspicious_patterns = [
            r'ï¿½',  # 常见乱码
            r'\\lnot\\lnot\\lnot',  # 重复的否定符号
            r'\\qquad\\qquad\\qquad',  # 过多的空白
            r'\\mathrm{~}\\mathrm{~}\\mathrm{~}',  # 重复的空白
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, latex):
                return True
        
        return False
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """计算总体评分"""
        extraction = results['extraction_stats']
        ocr = results['ocr_quality']
        image = results['image_quality']
        
        # 权重分配
        extraction_weight = 0.3
        ocr_weight = 0.5
        image_weight = 0.2
        
        extraction_score = extraction.get('extraction_rate', 0.0)
        ocr_score = ocr.get('score', 0.0)
        image_score = image.get('score', 0.0)
        
        overall = (
            extraction_score * extraction_weight +
            ocr_score * ocr_weight +
            image_score * image_weight
        )
        
        return overall
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        extraction = results['extraction_stats']
        ocr = results['ocr_quality']
        image = results['image_quality']
        
        # 提取完整性建议
        if extraction['total_formulas'] == 0:
            recommendations.append("[ERROR] 未提取到任何公式，请检查PDF是否包含公式")
        elif extraction['extraction_rate'] < 0.8:
            recommendations.append("[WARN] OCR转换率较低，建议检查pix2tex模型是否正确安装")
        
        # OCR质量建议
        if ocr['score'] < 0.5:
            recommendations.append("[WARN] OCR质量较低，建议：")
            recommendations.append("   1. 检查pix2tex模型版本和配置")
            recommendations.append("   2. 尝试调整公式提取的阈值参数")
            recommendations.append("   3. 考虑使用其他OCR工具（如Mathpix API）")
        
        if ocr['suspicious_count'] > 0:
            recommendations.append(f"[WARN] 发现 {ocr['suspicious_count']} 个可疑的OCR结果，建议人工检查")
        
        # 图片质量建议
        if image['avg_width'] < 100 or image['avg_height'] < 30:
            recommendations.append("[WARN] 公式图片尺寸较小，可能影响OCR效果")
            recommendations.append("   建议：调整min_formula_height和min_formula_width参数")
        
        # 总体建议
        if results['overall_score'] < 0.6:
            recommendations.append("[TIP] 总体质量较低，建议：")
            recommendations.append("   1. 检查公式提取参数（min_formula_height, min_formula_width）")
            recommendations.append("   2. 验证pix2tex模型是否正确加载")
            recommendations.append("   3. 考虑手动标注部分公式作为训练数据")
        
        if not recommendations:
            recommendations.append("[OK] 公式提取效果良好！")
        
        return recommendations
    
    def print_report(self, results: Dict):
        """打印评估报告"""
        print("\n" + "=" * 80)
        print("[报告] 评估报告")
        print("=" * 80)
        
        print(f"\n[评分] 总体评分: {results['overall_score']:.2f}/1.0")
        
        # 详细统计
        extraction = results['extraction_stats']
        print(f"\n[统计] 提取统计:")
        print(f"   总公式数: {extraction['total_formulas']}")
        print(f"   包含公式的页数: {extraction['pages_with_formulas']}")
        print(f"   OCR转换率: {extraction['extraction_rate']:.1%}")
        
        ocr = results['ocr_quality']
        print(f"\n[OCR] OCR质量:")
        print(f"   平均质量分: {ocr['score']:.2f}/1.0")
        print(f"   有效结果: {ocr['valid_count']}")
        print(f"   空结果: {ocr['empty_count']}")
        print(f"   可疑结果: {ocr['suspicious_count']}")
        
        image = results['image_quality']
        print(f"\n[图片] 图片质量:")
        print(f"   总图片数: {image['total_images']}")
        print(f"   平均尺寸: {image['avg_width']:.0f}x{image['avg_height']:.0f}")
        
        # 改进建议
        print(f"\n[建议] 改进建议:")
        for rec in results['recommendations']:
            print(f"   {rec}")
        
        print("\n" + "=" * 80)
        
        # 显示部分LaTeX示例
        if self.latex_file.exists():
            try:
                with open(self.latex_file, 'r', encoding='utf-8') as f:
                    latex_data = json.load(f)
                
                print("\n[示例] LaTeX示例（前3个）:")
                for i, (name, latex) in enumerate(list(latex_data.items())[:3]):
                    print(f"\n   [{i+1}] {name}:")
                    if latex:
                        # 截断过长的LaTeX
                        display_latex = latex[:100] + "..." if len(latex) > 100 else latex
                        print(f"      {display_latex}")
                        # 显示质量评分
                        score = self._score_latex_quality(latex)
                        status = "[GOOD]" if score > 0.7 else "[WARN]" if score > 0.4 else "[BAD]"
                        print(f"      质量: {status} {score:.2f}/1.0")
                    else:
                        print(f"      (空)")
            except Exception as e:
                print(f"   无法读取LaTeX示例: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='评估公式提取效果')
    parser.add_argument(
        'formula_dir',
        type=str,
        nargs='?',
        default='data/output/2023CVPR-CoMFormer/formulas',
        help='公式目录路径（默认: data/output/2023CVPR-CoMFormer/formulas）'
    )
    
    args = parser.parse_args()
    
    formula_dir = Path(args.formula_dir)
    
    if not formula_dir.exists():
        print(f"[ERROR] 公式目录不存在: {formula_dir}")
        print(f"   请先运行公式提取器")
        return 1
    
    # 执行评估
    evaluator = FormulaExtractionEvaluator(formula_dir)
    results = evaluator.evaluate()
    
    # 打印报告
    evaluator.print_report(results)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

