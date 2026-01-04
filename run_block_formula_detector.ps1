# 运行块级公式检测模块 - PowerShell 脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "块级公式检测模块测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pdfPath = "data\input\2023CVPR-CoMFormer.pdf"

if ($args.Count -gt 0) {
    $pdfPath = $args[0]
}

Write-Host "PDF文件: $pdfPath" -ForegroundColor Yellow
Write-Host ""

# 检查文件是否存在
if (-not (Test-Path $pdfPath)) {
    Write-Host "错误: PDF文件不存在: $pdfPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "可用的PDF文件:" -ForegroundColor Yellow
    Get-ChildItem -Path . -Recurse -Filter "*.pdf" | Where-Object { $_.FullName -notlike "*dita-ot*" } | ForEach-Object {
        Write-Host "  - $($_.FullName)" -ForegroundColor Gray
    }
    exit 1
}

Write-Host "正在运行块级公式检测..." -ForegroundColor Green
Write-Host ""

# 运行测试脚本
python test_block_formula_detector.py $pdfPath

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "运行出错，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan



