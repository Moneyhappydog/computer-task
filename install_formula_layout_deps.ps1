# 安装公式版面解析模块的依赖
# PowerShell 脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装 PDF 版面解析模块依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在虚拟环境中
$inVenv = $env:VIRTUAL_ENV -ne $null
if (-not $inVenv) {
    Write-Host "警告: 未检测到虚拟环境" -ForegroundColor Yellow
    Write-Host "建议先激活虚拟环境: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "是否继续安装到系统Python? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "已取消安装" -ForegroundColor Red
        exit
    }
}

# 选项1: 只安装 PyMuPDF（快速，推荐用于测试版面解析）
Write-Host "选项 1: 只安装 PyMuPDF（快速）" -ForegroundColor Green
Write-Host "选项 2: 安装完整依赖（从 requirements.txt）" -ForegroundColor Green
Write-Host ""
$choice = Read-Host "请选择 (1 或 2, 默认: 1)"

if ($choice -eq "2") {
    Write-Host ""
    Write-Host "正在安装完整依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ 完整依赖安装成功！" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ 依赖安装失败，请检查错误信息" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "正在安装 PyMuPDF..." -ForegroundColor Yellow
    pip install "PyMuPDF>=1.23.0"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ PyMuPDF 安装成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "现在可以运行版面解析模块了：" -ForegroundColor Cyan
        Write-Host '  python src\layer1_preprocessing\formula_layout.py "data\input\2023CVPR-CoMFormer.pdf"' -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "❌ PyMuPDF 安装失败，请检查错误信息" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan



