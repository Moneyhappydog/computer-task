# DITA Converter - PDF/Word 到 DITA XML 转换器

一个基于AI的多层架构文档转换系统，将PDF和Word文档智能转换为符合DITA标准的XML文档。

## 📋 项目概述

DITA Converter 是一个四层处理架构的文档转换系统：

- **Layer 1: 预处理层** - PDF/Word解析、OCR、图像/表格/公式提取
- **Layer 2: 语义分析层** - AI驱动的文档内容分类（Concept/Task/Reference）
- **Layer 3: DITA转换层** - 生成符合DITA标准的XML文档
- **Layer 4: 质量保证层** - DITA验证、错误修复和优化

## ✨ 主要特性

- 🤖 **AI驱动** - 使用大语言模型进行智能内容分析和转换
- 📄 **多格式支持** - 支持PDF、Word（DOCX）文档
- 🔍 **智能提取** - 自动提取图像、表格、公式和参考文献
- 🎯 **结构化输出** - 生成符合DITA 1.3标准的XML文档
- 🌐 **Web界面** - 友好的Web用户界面，实时查看处理进度
- 🔄 **实时预览** - 支持各层结果文件的实时预览和下载

## 🛠️ 系统要求

### Python 环境
- **Python**: >= 3.10, < 3.13
- **推荐**: Python 3.11

### 系统依赖

#### Windows
- **Tesseract OCR**: 用于OCR文字识别
- **Poppler**: 用于PDF转图像（pdf2image）
- **Pandoc**: 用于Word文档转换（可选）

#### Linux/Mac
- **Tesseract OCR**: `sudo apt-get install tesseract-ocr` (Ubuntu) / `brew install tesseract` (Mac)
- **Poppler**: `sudo apt-get install poppler-utils` (Ubuntu) / `brew install poppler` (Mac)
- **Pandoc**: `sudo apt-get install pandoc` (Ubuntu) / `brew install pandoc` (Mac)

### DITA-OT (可选)
- DITA Open Toolkit 4.3.5（用于Layer 4的DITA验证）
- 下载地址：https://www.dita-ot.org/download
- 解压到项目 `dita-ot/dita-ot-4.3.5/` 目录

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd computer-task
```

### 2. 创建虚拟环境

**使用 venv (推荐)**:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**使用 conda**:
```bash
conda create -n dita-converter python=3.11
conda activate dita-converter
```

### 3. 安装Python依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

**重要提示**：安装过程可能需要较长时间，因为需要下载深度学习模型和依赖包。

### 4. 安装spaCy语言模型

```bash
# 英文模型（必需）
python -m spacy download en_core_web_sm

# 中文模型（如果需要处理中文文档）
python -m spacy download zh_core_web_sm
```

### 5. 安装系统依赖

#### Windows (使用 conda)
```bash
conda install -c conda-forge tesseract -y
conda install -c conda-forge poppler -y
conda install -c conda-forge pandoc -y
```

#### Linux
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils pandoc
```

#### Mac
```bash
brew install tesseract poppler pandoc
```

### 6. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# AI API配置（必需）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=qwen-plus
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Anthropic API配置（可选）
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 工具路径配置（可选，如果系统找不到命令则设置）
TESSERACT_CMD=tesseract
POPPLER_PATH=C:\path\to\poppler\bin  # Windows示例
DITA_OT_DIR=dita-ot/dita-ot-4.3.5

# 目录配置（可选）
INPUT_DIR=data/input
OUTPUT_DIR=data/output
LOG_DIR=logs

# 处理配置（可选）
MAX_WORKERS=4
CHUNK_SIZE=2000
OCR_LANG=chi_sim+eng
LOG_LEVEL=INFO
```

**重要**：必须配置 `OPENAI_API_KEY` 才能使用AI功能。项目默认使用阿里云通义千问API，也可以配置OpenAI或Claude API。

## 🚀 运行项目

### 启动Web服务

```bash
python run_web.py
```

或者指定参数：

```bash
python run_web.py --host 127.0.0.1 --port 5000 --env development --debug
```

参数说明：
- `--host`: 服务器地址（默认: 127.0.0.1）
- `--port`: 服务器端口（默认: 5000）
- `--env`: 运行环境，可选 development/production/testing（默认: development）
- `--debug`: 启用调试模式
- `--log-level`: 日志级别，可选 DEBUG/INFO/WARNING/ERROR/CRITICAL（默认: INFO）

### 访问Web界面

启动成功后，在浏览器中打开：
```
http://127.0.0.1:5000
```

## 📁 项目结构

```
computer-task/
├── src/                          # 源代码
│   ├── layer1_preprocessing/     # Layer 1: 预处理层
│   │   ├── pdf_processor.py      # PDF处理器
│   │   ├── formula_extractor.py  # 公式提取器
│   │   ├── table_extractor.py    # 表格提取器
│   │   └── ...
│   ├── layer2_semantic/          # Layer 2: 语义分析层
│   │   ├── document_analyzer.py  # 文档分析器
│   │   └── ...
│   ├── layer3_dita_conversion/   # Layer 3: DITA转换层
│   │   ├── dita_converter.py     # DITA转换器
│   │   └── ...
│   ├── layer4_quality_assurance/ # Layer 4: 质量保证层
│   │   ├── qa_manager.py         # 质量保证管理器
│   │   └── ...
│   └── utils/                    # 工具模块
├── web/                          # Web应用
│   ├── app.py                    # Flask应用主文件
│   ├── routes/                   # 路由模块
│   ├── services/                 # 服务模块
│   ├── static/                   # 静态资源
│   └── templates/                # HTML模板
├── data/                         # 数据目录
│   ├── input/                    # 输入文件目录
│   └── output/                   # 输出文件目录
├── dita-ot/                      # DITA-OT工具包（可选）
├── logs/                         # 日志目录
├── requirements.txt              # Python依赖列表
├── run_web.py                    # Web服务启动脚本
└── README.md                     # 项目说明文档
```

## 🔧 配置说明

### API密钥配置

项目支持多种AI服务提供商：

1. **阿里云通义千问**（默认）
   - 需要配置 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`
   - 推荐模型：`qwen-plus`、`qwen-max`

2. **OpenAI**
   - 配置 `OPENAI_API_KEY`
   - 设置 `OPENAI_BASE_URL=https://api.openai.com/v1`
   - 推荐模型：`gpt-4o`、`gpt-4-turbo`

3. **Anthropic Claude**
   - 配置 `ANTHROPIC_API_KEY`
   - 推荐模型：`claude-3-5-sonnet-20241022`

### DITA-OT配置

如果需要使用Layer 4的DITA-OT验证功能：

1. 下载 DITA-OT 4.3.5：https://www.dita-ot.org/download
2. 解压到项目 `dita-ot/dita-ot-4.3.5/` 目录
3. 在 `.env` 中配置 `DITA_OT_DIR=dita-ot/dita-ot-4.3.5`

如果不配置DITA-OT，Layer 4将使用内置的XML验证器。

## 📖 使用指南

### 基本使用

1. **上传文档**
   - 在Web界面点击"上传文件"
   - 选择PDF或Word文档（支持.docx格式）
   - 点击"开始转换"

2. **查看进度**
   - Web界面会实时显示四个处理层的进度
   - 每个层完成后会显示相应的统计信息

3. **预览结果**
   - 每个层完成后，可以点击"预览"按钮查看结果文件
   - Layer 3和Layer 4支持多个文件的标签页预览

4. **下载结果**
   - 点击"下载"按钮下载各层的结果文件
   - 最终DITA文件在Layer 4的结果中

### 命令行使用（测试）

```bash
# 测试Layer 1
python test_layer1.py --pdf path/to/file.pdf

# 测试Layer 2
python test_layer2.py

# 测试完整流程
python test_integration.py path/to/file.pdf
```

## 🐛 常见问题

### 1. 安装依赖失败

**问题**：安装 `marker-pdf` 或其他包失败

**解决**：
- 确保Python版本 >= 3.10 且 < 3.13
- 升级pip：`pip install --upgrade pip`
- 如果遇到torch安装问题，先安装torch：`pip install torch --index-url https://download.pytorch.org/whl/cpu`

### 2. Tesseract未找到

**问题**：`pytesseract.pytesseract.TesseractNotFoundError`

**解决**：
- Windows: 确保Tesseract已安装并添加到PATH，或在`.env`中配置`TESSERACT_CMD`
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

### 3. Poppler未找到

**问题**：`pdf2image`无法转换PDF

**解决**：
- Windows: 确保Poppler已安装，或在`.env`中配置`POPPLER_PATH`
- Linux: `sudo apt-get install poppler-utils`
- Mac: `brew install poppler`

### 4. API调用失败

**问题**：AI功能无法使用

**解决**：
- 检查`.env`文件中的`OPENAI_API_KEY`是否配置正确
- 检查API服务是否可访问（网络连接）
- 查看日志文件`logs/web.log`获取详细错误信息

### 5. 内存不足

**问题**：处理大文件时内存溢出

**解决**：
- 减少`MAX_WORKERS`配置（默认4，可改为2）
- 分批处理大文件
- 确保系统有足够的内存（推荐8GB+）

## 📝 开发说明

### 代码风格

项目使用以下工具进行代码质量检查：

```bash
# 代码格式化
black src/ web/

# 代码风格检查
flake8 src/ web/

# 类型检查
mypy src/ web/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_layer1.py

# 生成测试覆盖率报告
pytest --cov=src tests/
```

## 📄 许可证

本项目采用 MIT 许可证。

```
MIT License

Copyright (c) 2024 Moneyhappydog

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

- **邮箱**: 3239143984@qq.com

如有任何问题或建议，请通过邮箱联系。

## 🙏 致谢

- [Marker PDF](https://github.com/VikParuchuri/marker) - PDF智能处理
- [DITA-OT](https://www.dita-ot.org/) - DITA Open Toolkit
- [spaCy](https://spacy.io/) - NLP处理库
- [Transformers](https://huggingface.co/transformers/) - 深度学习模型库

---

**注意**：首次运行时会自动下载所需的AI模型，可能需要较长时间。请确保网络连接正常。
