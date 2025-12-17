# 模型文件目录

## 公式检测模型

### arxivFormula_YOLOv8l.pt

**下载地址：**
- 直接下载：https://huggingface.co/LouiseBloch/ArxivFormulaYOLOv8/resolve/main/arxivFormula_YOLOv8l.pt
- 模型页面：https://huggingface.co/LouiseBloch/ArxivFormulaYOLOv8

**模型信息：**
- 类型：YOLOv8-Large
- 训练数据集：ArxivFormula
- 用途：检测 PDF 文档中的数学公式
- 大小：约 130 MB

**使用方法：**
1. 下载模型文件到此目录
2. 代码会自动检测并加载
3. 或手动指定：`FormulaExtractor(model_path='models/arxivFormula_YOLOv8l.pt')`

**下载命令（Windows PowerShell）：**
```powershell
# 使用 curl
curl -L -o models\arxivFormula_YOLOv8l.pt https://huggingface.co/LouiseBloch/ArxivFormulaYOLOv8/resolve/main/arxivFormula_YOLOv8l.pt

# 或使用 wget（如果已安装）
wget -O models\arxivFormula_YOLOv8l.pt https://huggingface.co/LouiseBloch/ArxivFormulaYOLOv8/resolve/main/arxivFormula_YOLOv8l.pt
```

**下载命令（使用镜像站，更快）：**
```powershell
curl -L -o models\arxivFormula_YOLOv8l.pt https://hf-mirror.com/LouiseBloch/ArxivFormulaYOLOv8/resolve/main/arxivFormula_YOLOv8l.pt
```

**Python 下载脚本：**
```python
import requests
from pathlib import Path

url = "https://hf-mirror.com/LouiseBloch/ArxivFormulaYOLOv8/resolve/main/arxivFormula_YOLOv8l.pt"
output_path = Path("models/arxivFormula_YOLOv8l.pt")

print("正在下载模型...")
response = requests.get(url, stream=True)
total_size = int(response.headers.get('content-length', 0))

with open(output_path, 'wb') as f:
    downloaded = 0
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
        downloaded += len(chunk)
        if total_size > 0:
            percent = (downloaded / total_size) * 100
            print(f"\r进度: {percent:.1f}%", end='')

print("\n下载完成！")
```
