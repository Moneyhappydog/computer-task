# ===================================================================
# Conda 环境安装脚本 (PowerShell)
# 用于设置 DITA 转换器项目的 conda 环境
# ===================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始设置 Conda 环境" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查 conda 是否已安装
Write-Host "`n[1/8] 检查 Conda 安装..." -ForegroundColor Yellow
try {
    $condaVersion = conda --version
    Write-Host "✓ Conda 已安装: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: 未找到 Conda，请先安装 Anaconda 或 Miniconda" -ForegroundColor Red
    exit 1
}

# 初始化 conda for PowerShell（如果需要）
Write-Host "`n[2/8] 初始化 Conda for PowerShell..." -ForegroundColor Yellow
conda init powershell | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 警告: Conda PowerShell 初始化可能失败，但继续执行..." -ForegroundColor Yellow
}

# 创建 conda 环境（如果不存在）
Write-Host "`n[3/8] 创建/检查 Conda 环境 'venv'..." -ForegroundColor Yellow
$envExists = conda env list | Select-String -Pattern "^\s*venv\s"
if ($envExists) {
    Write-Host "✓ 环境 'venv' 已存在，跳过创建" -ForegroundColor Green
} else {
    Write-Host "创建新环境 'venv' (Python 3.10)..." -ForegroundColor Yellow
    conda create -n venv python=3.10 -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 错误: 创建环境失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 环境创建成功" -ForegroundColor Green
}

# 获取 conda 环境路径
Write-Host "`n[4/8] 获取环境路径..." -ForegroundColor Yellow
$condaInfo = conda info --envs | Select-String -Pattern "^\s*venv\s" | ForEach-Object { $_.Line }
if ($condaInfo -match '\S+\s+(\S+)') {
    $envPath = $matches[1]
    Write-Host "✓ 环境路径: $envPath" -ForegroundColor Green
} else {
    # 尝试默认路径
    $condaBase = conda info --base
    $envPath = Join-Path $condaBase "envs\venv"
    Write-Host "✓ 使用默认路径: $envPath" -ForegroundColor Green
}

# 获取 Python 和 pip 路径
$pythonExe = Join-Path $envPath "python.exe"
$pipExe = Join-Path $envPath "Scripts\pip.exe"

# 安装 conda 包
Write-Host "`n[5/8] 安装 Conda 包..." -ForegroundColor Yellow
Write-Host "安装 tesseract..." -ForegroundColor Yellow
conda install -n venv -c conda-forge tesseract -y
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 警告: tesseract 安装可能失败" -ForegroundColor Yellow
}

Write-Host "安装 pandoc..." -ForegroundColor Yellow
conda install -n venv -c conda-forge pandoc -y
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 警告: pandoc 安装可能失败" -ForegroundColor Yellow
}

Write-Host "安装 poppler..." -ForegroundColor Yellow
conda install -n venv -c conda-forge poppler -y
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 警告: poppler 安装可能失败" -ForegroundColor Yellow
}

Write-Host "✓ Conda 包安装完成" -ForegroundColor Green

# 升级 pip
Write-Host "`n[6/8] 升级 pip..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 错误: pip 升级失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ pip 升级成功" -ForegroundColor Green

# 安装 Python 依赖
Write-Host "`n[7/8] 安装 Python 依赖包（这可能需要一些时间）..." -ForegroundColor Yellow
& $pipExe install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 错误: 依赖安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python 依赖安装完成" -ForegroundColor Green

# 下载 spaCy 模型
Write-Host "`n[8/8] 下载 spaCy 模型..." -ForegroundColor Yellow
Write-Host "下载英文模型 (en_core_web_sm)..." -ForegroundColor Yellow
& $pythonExe -m spacy download en_core_web_sm
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 警告: 英文模型下载失败" -ForegroundColor Yellow
}

Write-Host "下载中文模型 (zh_core_web_sm)..." -ForegroundColor Yellow
& $pythonExe -m spacy download zh_core_web_sm
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 警告: 中文模型下载失败" -ForegroundColor Yellow
}

Write-Host "✓ spaCy 模型下载完成" -ForegroundColor Green

# 完成
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✓ Conda 环境设置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n使用以下命令激活环境:" -ForegroundColor Yellow
Write-Host "  conda activate venv" -ForegroundColor White
Write-Host "`n然后可以运行:" -ForegroundColor Yellow
Write-Host "  python run_web.py" -ForegroundColor White
Write-Host "`n"

