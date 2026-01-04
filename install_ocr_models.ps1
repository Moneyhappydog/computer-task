# 安装公式OCR模型依赖

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装公式OCR模型依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境
if (-not $env:VIRTUAL_ENV) {
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

Write-Host "可用的OCR模型:" -ForegroundColor Green
Write-Host "  1. pix2tex (推荐) - 专门的公式OCR"
Write-Host "  2. easyocr - 通用OCR（对公式效果一般）"
Write-Host ""

$choice = Read-Host "请选择要安装的模型 (1=pix2tex, 2=easyocr, 3=全部, 回车=跳过)"

if ($choice -eq "1" -or $choice -eq "3") {
    Write-Host "`n正在安装 pix2tex..." -ForegroundColor Yellow
    pip install pix2tex
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ pix2tex 安装成功" -ForegroundColor Green
    } else {
        Write-Host "✗ pix2tex 安装失败" -ForegroundColor Red
    }
}

if ($choice -eq "2" -or $choice -eq "3") {
    Write-Host "`n正在安装 easyocr..." -ForegroundColor Yellow
    pip install easyocr
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ easyocr 安装成功" -ForegroundColor Green
    } else {
        Write-Host "✗ easyocr 安装失败" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "安装完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n使用说明:" -ForegroundColor Green
Write-Host "  运行公式OCR: python run_formula_ocr.py"
Write-Host "  脚本会自动检测并使用已安装的OCR模型"



