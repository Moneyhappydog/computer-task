# 安装依赖并运行块级公式检测

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "块级公式检测 - 安装依赖并运行" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境
if (-not $env:VIRTUAL_ENV) {
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# 检查 PyMuPDF 是否已安装
Write-Host "检查 PyMuPDF..." -ForegroundColor Yellow
$checkResult = python -c "import fitz; print('OK')" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyMuPDF 未安装，正在安装..." -ForegroundColor Yellow
    pip install "PyMuPDF>=1.23.0"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装失败！" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ PyMuPDF 安装成功" -ForegroundColor Green
} else {
    Write-Host "✓ PyMuPDF 已安装" -ForegroundColor Green
}

Write-Host ""
Write-Host "正在运行块级公式检测..." -ForegroundColor Green
Write-Host ""

# 运行检测
python run_block_formula.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan



