# Layer 1 评估指标使用指南

本指南介绍如何使用 Layer 1 的评判标准进行实验评估。

## 📊 评判指标

### 1. 文本提取精度

#### 字符错误率 (CER - Character Error Rate)
- **定义**: 基于Levenshtein编辑距离，计算提取文本与参考文本之间的字符级差异
- **公式**: `CER = 编辑距离 / 参考文本字符数`
- **范围**: 0-1（越小越好，0表示完美匹配）
- **适用场景**: 
  - 评估OCR识别准确度
  - 评估PDF文本提取完整性
  - 检测文本提取中的字符遗漏或错误

#### 词错误率 (WER - Word Error Rate)
- **定义**: 词级别的编辑距离，支持中英文混合文本
- **公式**: `WER = 词级编辑距离 / 参考文本词数`
- **范围**: 0-1（越小越好，0表示完美匹配）
- **适用场景**:
  - 评估语义单元的保留程度
  - 对比不同提取方法的效果
  - 评估Word文档转换质量

### 2. 标题层级准确率

#### 多维度指标
- **召回率 (Recall)**: 检测到的标题 / 实际标题数
- **精确率 (Precision)**: 正确的标题 / 检测到的标题数
- **F1分数**: 综合评价指标
- **层级准确率**: 标题层级（H1/H2/H3）是否正确
- **完全匹配率**: 文本+层级都正确的比例

---

## 🚀 快速开始

### 步骤1: 安装依赖
```bash
conda activate pdf_dita
pip install python-Levenshtein
```

### 步骤2: 运行演示
```bash
python test_layer1_evaluation.py --demo
```

这将展示：
- CER/WER的计算示例
- 标题层级准确率的计算示例
- 不同场景下的评估结果

---

## 📝 准备 Ground Truth 数据

### 方法1: 从Markdown自动提取（推荐）

如果你已有高质量的Markdown文件（如手工整理的文档）：

```bash
python prepare_ground_truth.py \
  --from-markdown docs/reference.md \
  --output data/ground_truth/reference.gt.json
```

### 方法2: 手动创建

```bash
# 创建模板
python prepare_ground_truth.py \
  --create-template data/ground_truth/template.json

# 编辑模板文件，填写：
# - source_document: 原始文档路径
# - text: 参考文本（从PDF手动复制或使用其他工具提取）
# - headings: 标题列表（可选，系统会自动提取）
```

**Ground Truth JSON格式**:
```json
{
  "source_document": "path/to/original.pdf",
  "text": "完整的参考文本内容...",
  "headings": [
    {
      "level": 1,
      "text": "Introduction",
      "line_number": 1
    },
    {
      "level": 2,
      "text": "Background",
      "line_number": 5
    }
  ],
  "notes": "可选的备注信息"
}
```

### 方法3: 验证Ground Truth

```bash
python prepare_ground_truth.py \
  --validate data/ground_truth/reference.gt.json
```

---

## 🧪 运行评估

### 完整流程

```bash
# 1. 运行Layer 1处理（生成输出）
python test_layer1.py --pdf path/to/test.pdf

# 2. 进行评估（假设输出在 data/output/test/layer1）
python test_layer1_evaluation.py \
  --layer1-output data/output/test/layer1 \
  --ground-truth data/ground_truth/test.gt.json
```

### 输出示例

```
======================================================================
📊 Layer 1 评估结果
======================================================================

1️⃣  文本提取精度:
  字符错误率 (CER): 0.0234 (越小越好，0表示完美)
  词错误率 (WER):   0.0156 (越小越好，0表示完美)
  参考文本长度: 15234 字符
  提取文本长度: 15189 字符
  长度比例: 99.70%

2️⃣  标题层级准确率:
  召回率 (Recall):    95.00%
  精确率 (Precision): 97.00%
  F1分数:             96.00%
  层级准确率:         92.50%
  完全匹配率:         90.00%
  参考标题数: 20
  提取标题数: 19

🎯 综合得分: 94.20 / 100

💾 评估结果已保存: data/output/test/layer1/layer1_evaluation.json
```

---

## 📊 批量评估

如果你有多个测试文档：

```bash
# 创建批量评估脚本
for file in data/input/*.pdf; do
  filename=$(basename "$file" .pdf)
  
  # 处理
  python test_layer1.py --pdf "$file"
  
  # 评估
  python test_layer1_evaluation.py \
    --layer1-output "data/output/${filename}/layer1" \
    --ground-truth "data/ground_truth/${filename}.gt.json"
done
```

---

## 🔍 对比评估结果

可以使用提供的对比工具：

```bash
python prepare_ground_truth.py \
  --compare \
  --layer1-output data/output/test/layer1 \
  --ground-truth data/ground_truth/test.gt.json
```

这将显示：
- 文本长度差异
- 标题数量对比
- 标题内容对比（并排显示）

---

## 💡 实验建议

### 1. 准备测试集

建议准备10-20份不同类型的文档作为标准测试集（Golden Set）：
- **操作手册** (Task为主)
- **API文档** (Reference为主)
- **概念说明** (Concept为主)
- **学术论文** (混合类型)
- **双栏PDF** (测试布局处理)
- **扫描PDF** (测试OCR能力)

### 2. 评估维度

| 文档类型 | 关注指标 | 预期阈值 |
|---------|---------|---------|
| 电子PDF | CER < 0.02, WER < 0.05 | 高精度 |
| 扫描PDF | CER < 0.10, WER < 0.15 | 中等精度 |
| 双栏布局 | 标题F1 > 0.90 | 结构准确 |
| Word文档 | CER < 0.01, 标题F1 > 0.95 | 接近完美 |

### 3. 对比实验

可以测试不同配置的效果：
- Marker vs PyMuPDF
- 启用OCR vs 不启用OCR
- 不同的OCR语言设置

---

## 📈 结果分析

### 查看JSON结果

```python
import json

with open('data/output/test/layer1/layer1_evaluation.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print(f"CER: {results['text_extraction']['cer']:.4f}")
print(f"WER: {results['text_extraction']['wer']:.4f}")
print(f"标题F1: {results['heading_accuracy']['f1_score']:.2%}")
print(f"综合得分: {results['overall_score']:.2f}/100")
```

### 综合得分计算

```
综合得分 = 文本提取得分 × 0.7 + 标题准确率得分 × 0.3

其中:
- 文本提取得分 = (1 - CER) × 50 + (1 - WER) × 50
- 标题准确率得分 = F1 Score × 100
```

---

## 🛠️ 高级用法

### 自定义阈值

在代码中调整 `calculate_heading_accuracy` 的 `level_tolerance` 参数：

```python
# 允许1级层级偏差
metrics = calculate_heading_accuracy(
    ref_headings,
    ext_headings,
    level_tolerance=1
)
```

### 导出评估报告

```python
from src.evaluation.layer1_metrics import evaluate_layer1

result = evaluate_layer1(reference_text, extracted_text)

# 生成Markdown报告
with open('report.md', 'w', encoding='utf-8') as f:
    f.write(f"# Layer 1 评估报告\n\n")
    f.write(f"## 文本提取精度\n")
    f.write(f"- CER: {result['text_extraction']['cer']:.4f}\n")
    f.write(f"- WER: {result['text_extraction']['wer']:.4f}\n\n")
    f.write(f"## 标题准确率\n")
    f.write(f"- F1分数: {result['heading_accuracy']['f1_score']:.2%}\n")
```

---

## ❓ 常见问题

### Q1: 没有Ground Truth怎么办？
如果无法准备Ground Truth，可以：
1. 只评估标题提取（无需参考文本）
2. 使用人工抽样评估（评估部分样本）
3. 使用相对比较（对比不同方法的输出）

### Q2: CER很高是什么原因？
可能原因：
- OCR识别错误（扫描文档）
- PDF编码问题（特殊字符）
- 表格提取错误
- 公式转换失败

### Q3: 标题层级错误怎么处理？
检查：
- Markdown生成逻辑
- PDF原文的标题样式
- 是否有嵌套标题混淆

---

## 📚 相关文件

- `src/evaluation/layer1_metrics.py` - 评估指标实现
- `test_layer1_evaluation.py` - 评估测试脚本
- `prepare_ground_truth.py` - Ground Truth准备工具
- `test_layer1.py` - Layer 1处理脚本

---

## 🔗 下一步

完成Layer 1评估后，可以继续：
- [Layer 2评估指南](LAYER2_EVALUATION.md) - 语义分类准确率
- [Layer 3评估指南](LAYER3_EVALUATION.md) - DITA验证通过率
- [端到端评估](E2E_EVALUATION.md) - 完整流程评估
