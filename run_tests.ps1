# 运行 README 中的测试命令
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "运行 README 中的测试命令" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_DIR = $PSScriptRoot
Set-Location $PROJECT_DIR

Write-Host "当前项目目录: $PROJECT_DIR" -ForegroundColor Yellow
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] Python 未找到，请先激活 conda 环境" -ForegroundColor Red
    Write-Host "运行: conda activate venv" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[1/5] 测试 Layer 1 - PDF + Word" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
python test_layer1.py --pdf "uploads\2023CVPR-CoMFormer.pdf" --word "uploads\0d98a7bb-bb4c-4d9b-800b-83da29355828_sample.docx"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] Layer 1 测试失败" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "按 Enter 继续"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[2/5] 测试 Layer 1 - 仅 PDF" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
python test_layer1.py --pdf "uploads\2023CVPR-CoMFormer.pdf"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] Layer 1 PDF 测试失败" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "按 Enter 继续"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[3/5] 测试 Layer 2" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
python test_layer2.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] Layer 2 测试失败" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "按 Enter 继续"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[4/5] 测试集成流程" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
python test_integration.py "uploads\2023CVPR-CoMFormer.pdf" "uploads\0d98a7bb-bb4c-4d9b-800b-83da29355828_sample.docx"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] 集成测试失败" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "按 Enter 继续"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[5/5] 启动 Web 服务器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服务器将在 http://127.0.0.1:5000 启动" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""
python run_web.py




