# 手动安装命令脚本
# 使用完整路径，无需激活环境

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始手动安装依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ENV_PATH = "D:\anaconda\envs\venv"
$PYTHON_EXE = "$ENV_PATH\python.exe"
$PIP_EXE = "$ENV_PATH\Scripts\pip.exe"

Write-Host "`n[1/5] 升级 pip..." -ForegroundColor Yellow
& $PYTHON_EXE -m pip install --upgrade pip

Write-Host "`n[2/5] 安装 conda 包 - tesseract..." -ForegroundColor Yellow
conda install -n venv -c conda-forge tesseract -y

Write-Host "`n[3/5] 安装 conda 包 - pandoc..." -ForegroundColor Yellow
conda install -n venv -c conda-forge pandoc -y

Write-Host "`n[4/5] 安装 conda 包 - poppler..." -ForegroundColor Yellow
conda install -n venv -c conda-forge poppler -y

Write-Host "`n[5/5] 安装 Python 依赖包（这可能需要 10-15 分钟）..." -ForegroundColor Yellow
& $PIP_EXE install -r requirements.txt

Write-Host "`n[6/6] 下载 spaCy 模型..." -ForegroundColor Yellow
Write-Host "下载英文模型..." -ForegroundColor Yellow
& $PYTHON_EXE -m spacy download en_core_web_sm

Write-Host "下载中文模型..." -ForegroundColor Yellow
& $PYTHON_EXE -m spacy download zh_core_web_sm

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n注意：如果 conda activate 不工作，请重新打开 PowerShell 窗口" -ForegroundColor Yellow
Write-Host "或者使用完整路径: D:\anaconda\envs\venv\python.exe" -ForegroundColor Yellow


