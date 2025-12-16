# Layer 1 无Ground Truth评估指南

## 🎯 解决方案

当你只有PDF文件，没有Ground Truth时，可以使用**无需Ground Truth的评估指标**来评估提取质量。

## 📊 评估维度

### 1. 文档结构完整性（Structure Completeness）
**无需对比，直接分析提取结果中包含的结构元素**

检查项：
- ✅ 是否有标题（H1-H6）
- ✅ 标题层级分布是否合理
- ✅ 是否有段落内容
- ✅ 是否有列表（有序/无序）
- ✅ 是否有表格
- ✅ 是否有图片引用
- ✅ 是否有代码块
- ✅ 是否有公式

**得分计算**：根据包含的元素类型计算结构丰富度（0-100分）

### 2. 标题层级合理性（Heading Hierarchy）
**检查标题结构是否符合文档规范**

检查项：
- ✅ H1是否唯一（通常文档只有一个标题）
- ✅ 标题层级是否连续（H1→H2，不跳级到H3）
- ✅ 标题层级是否过深（超过H4可能过度嵌套）
- ✅ 标题分布是否均匀

**得分计算**：根据违规数量扣分（100分起评）

### 3. 提取质量检测（Quality Detection）
**自动检测常见的提取问题**

检查项：
- ❌ 空行比例过高（>50%，可能是布局问题）
- ❌ 单行过长（>300字符，可能是表格或分栏问题）
- ❌ 大量数字行（可能是页码未过滤）
- ❌ 重复内容（>10%，可能是多栏重复提取）
- ❌ 连续标题（中间无内容，可能是内容遗漏）
- ❌ 标题下内容过少（平均<3行，可能有遗漏）

**得分计算**：根据问题严重程度扣分

### 4. PDF完整性对比（Completeness Comparison）
**如果提供原PDF，可进行字符数对比**

对比项：
- 📊 PDF总页数 vs Markdown行数
- 📊 PDF字符数 vs Markdown字符数
- 📊 提取比例（应在70%-130%之间）

**评判标准**：
- 比例 < 70%：可能有内容遗漏
- 比例 70%-130%：正常范围
- 比例 > 130%：可能有重复内容

### 5. 综合得分计算

```
综合得分 = (结构完整性 + 标题合理性 + 提取质量 + PDF完整性) / 4
```

---

## 🚀 快速开始

### 方法1：快速检查单个PDF

```bash
conda activate pdf_dita
python test_layer1_evaluation_no_gt.py --quick-check your_paper.pdf
```

**优点**：一条命令完成提取+评估  
**适合**：快速测试、临时评估

### 方法2：评估已有Layer 1输出

```bash
# 先运行Layer 1处理
python test_layer1.py --pdf your_paper.pdf

# 再进行评估
python test_layer1_evaluation_no_gt.py \
  --layer1-output data/output/your_paper/layer1 \
  --pdf your_paper.pdf
```

**优点**：可复用已有输出，节省时间  
**适合**：正式实验、多次评估

### 方法3：批量评估

```bash
# 评估整个目录下的所有PDF
python test_layer1_evaluation_no_gt.py --batch data/input/
```

**优点**：一次评估多个文件，生成对比表格  
**适合**：论文实验、批量测试

---

## 📋 输出示例

### 评估报告示例

```
======================================================================
Layer 1 评估报告（无Ground Truth）
======================================================================

🎯 综合得分: 87.50 / 100

1️⃣  文档结构完整性
   结构丰富度: 85/100
   ✅ 标题: 23个 (层级: [1, 2, 3])
   ✅ 段落: 156个
   ✅ 列表: 45项
   ✅ 表格: 3个
   ✅ 图片: 8张
   ⚪ 代码块: 0个

2️⃣  标题层级结构
   层级合理性: 95/100
   标题总数: 23
   层级分布: {1: 1, 2: 8, 3: 14}
   ⚠️  发现问题:
      - 标题 "Related Work" 从H2跳到H4（跳级）

3️⃣  提取质量
   质量分数: 85/100
   ⚠️  警告:
      - 有3行内容过长(>300字符)，可能是表格或分栏未正确处理
      - 检测到12行可疑内容（页码、页眉页脚等）

4️⃣  PDF对比
   PDF页数: 12
   PDF字符数: 25678
   Markdown字符数: 24532
   提取比例: 95.5%
   完整性得分: 95/100

5️⃣  处理信息
   提取方法: marker
   页数: 12
   图片数: 8

======================================================================
```

### JSON结果示例

```json
{
  "evaluation_type": "no_ground_truth",
  "overall_score": 87.50,
  "structure": {
    "has_headings": true,
    "heading_count": 23,
    "heading_levels": [1, 2, 3],
    "has_paragraphs": true,
    "paragraph_count": 156,
    "structure_richness_score": 85
  },
  "heading_hierarchy": {
    "valid": false,
    "score": 95,
    "issues": ["标题 'Related Work' 从H2跳到H4（跳级）"]
  },
  "quality": {
    "quality_score": 85,
    "issues": [],
    "warnings": [
      "有3行内容过长(>300字符)",
      "检测到12行可疑内容"
    ]
  },
  "pdf_comparison": {
    "pdf_pages": 12,
    "char_ratio": 0.955,
    "completeness_score": 95
  }
}
```

---

## 💡 实验设计建议

### 场景1：对比不同提取方法

```bash
# 测试Marker方法
python test_layer1.py --pdf paper.pdf  # 默认使用Marker
python test_layer1_evaluation_no_gt.py \
  --layer1-output data/output/paper/layer1 \
  --pdf paper.pdf

# 对比PyMuPDF方法（需要修改代码）
# 然后同样评估
```

**对比指标**：
- 结构完整性（哪个方法识别的元素更多）
- 标题层级（哪个方法层级更准确）
- 提取比例（哪个方法提取更完整）

### 场景2：测试不同类型文档

准备测试集：
- 📄 单栏PDF（简单布局）
- 📄 双栏PDF（学术论文）
- 📄 扫描PDF（需要OCR）
- 📄 混合文档（包含大量图表）

批量评估：
```bash
python test_layer1_evaluation_no_gt.py --batch test_dataset/
```

**分析维度**：
- 哪种文档类型得分最高
- 哪种文档类型问题最多
- 不同类型的平均得分差异

### 场景3：10份文献的标准测试集

```bash
# 1. 准备10份代表性文献
mkdir data/input/golden_set/
# 复制10份PDF到这个目录

# 2. 批量处理
for f in data/input/golden_set/*.pdf; do
  python test_layer1.py --pdf "$f"
done

# 3. 批量评估
python test_layer1_evaluation_no_gt.py --batch data/input/golden_set/

# 4. 分析结果
# 会生成一个汇总表格，显示每份文献的得分
```

**实验报告可包含**：
- 平均得分
- 得分分布（最高/最低/中位数）
- 常见问题统计
- 结构丰富度对比

---

## 📈 评分标准建议

基于综合得分给出质量评级：

| 得分范围 | 质量等级 | 说明 | 后续处理建议 |
|---------|---------|------|------------|
| 90-100 | 优秀 | 提取质量很好，结构完整 | 可直接用于后续处理 |
| 75-89 | 良好 | 提取基本正确，有小问题 | 检查警告项，考虑人工校对 |
| 60-74 | 一般 | 有明显问题，但可用 | 需要人工审查和修正 |
| < 60 | 较差 | 提取质量不佳 | 尝试其他方法或手动处理 |

---

## 🔍 问题诊断

### 如果结构完整性得分低（<70）

**可能原因**：
- PDF是图片扫描件（未开启OCR）
- PDF使用特殊编码
- 文档布局复杂

**解决方案**：
```python
# 确保开启OCR
processor = PDFProcessor(use_marker=True, use_ocr=True)
```

### 如果标题层级得分低（<80）

**可能原因**：
- 原文档标题层级不规范
- 标题样式未正确识别
- 多栏布局导致顺序错乱

**解决方案**：
- 检查原PDF的标题样式
- 考虑手动调整Markdown标题层级
- 使用后处理脚本修正

### 如果提取质量得分低（<70）

**可能原因**：
- 页眉页脚未过滤
- 双栏内容重复提取
- 表格格式错乱

**解决方案**：
- 检查suspicious_lines（可疑行）
- 使用后处理脚本清理
- 尝试不同的提取参数

### 如果PDF对比比例异常

**比例 < 70%**：
- 检查是否有大段内容在图片中
- 检查是否有嵌入的子文档
- 考虑提高OCR质量

**比例 > 130%**：
- 检查是否有重复段落
- 检查双栏是否重复提取
- 检查表格是否被重复处理

---

## 🛠️ 高级用法

### 自定义评分权重

修改 `evaluate_layer1_without_gt` 中的权重：

```python
# 默认：各项平均
results['overall_score'] = sum(scores) / len(scores)

# 自定义：更重视结构完整性
results['overall_score'] = (
    structure_score * 0.4 +
    heading_score * 0.3 +
    quality_score * 0.2 +
    completeness_score * 0.1
)
```

### 导出Excel报告

```python
import pandas as pd

# 批量评估后，收集所有结果
results = []
for eval_file in Path('data/output').rglob('layer1_evaluation_no_gt.json'):
    with open(eval_file) as f:
        data = json.load(f)
        results.append({
            'file': eval_file.parent.parent.name,
            'score': data['overall_score'],
            'structure': data['structure']['structure_richness_score'],
            'heading': data['heading_hierarchy']['score'],
            'quality': data['quality']['quality_score']
        })

df = pd.DataFrame(results)
df.to_excel('evaluation_summary.xlsx', index=False)
```

---

## 📚 相关文件

- `src/evaluation/layer1_metrics_no_gt.py` - 核心评估实现
- `test_layer1_evaluation_no_gt.py` - 评估脚本
- `test_layer1.py` - Layer 1处理脚本

---

## ✨ 总结

**无Ground Truth评估的优势**：
1. ✅ 无需准备参考数据
2. ✅ 可自动化批量评估
3. ✅ 能发现常见提取问题
4. ✅ 适合实际应用场景

**局限性**：
1. ⚠️ 无法评估文本准确性（CER/WER）
2. ⚠️ 无法检测语义错误
3. ⚠️ 依赖启发式规则

**建议组合使用**：
- 开发阶段：准备少量Ground Truth，使用精确评估
- 测试阶段：使用无GT评估快速筛查
- 生产阶段：使用无GT评估+抽样人工检查
