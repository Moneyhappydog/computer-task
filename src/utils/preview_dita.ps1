# DITA预览脚本 - 将DITA文件转换为HTML并在浏览器中打开
param(
    [string]$InputDir = "data\output\2023CVPR-CoMFormer\layer3",
    [string]$OutputDir = "data\output\2023CVPR-CoMFormer\preview",
    [switch]$OpenBrowser = $false
)

Write-Host "开始转换DITA文件为HTML..." -ForegroundColor Cyan

# 获取所有DITA文件
$ditaFiles = Get-ChildItem -Path $InputDir -Filter "*.dita"

if ($ditaFiles.Count -eq 0) {
    Write-Host "未找到DITA文件" -ForegroundColor Red
    exit 1
}

Write-Host "找到 $($ditaFiles.Count) 个DITA文件" -ForegroundColor Green

# 切换到DITA-OT目录
Push-Location "dita-ot\dita-ot-4.3.5"

try {
    foreach ($file in $ditaFiles) {
        Write-Host "   转换: $($file.Name)..." -NoNewline
        
        $inputPath = "..\..\$InputDir\$($file.Name)"
        
        # 执行转换（静默模式）
        $result = & .\bin\dita --input=$inputPath --format=html5 --output="..\..\$OutputDir" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " OK" -ForegroundColor Green
        } else {
            Write-Host " FAIL" -ForegroundColor Red
        }
    }
    
    Write-Host "" -ForegroundColor Green
    Write-Host "转换完成!" -ForegroundColor Green
    Write-Host "输出目录: $OutputDir\layer3\" -ForegroundColor Cyan
    
    # 如果指定了OpenBrowser参数，在浏览器中打开第一个HTML文件
    if ($OpenBrowser) {
        Pop-Location
        $firstHtml = Get-ChildItem -Path "$OutputDir\layer3" -Filter "*.html" | Select-Object -First 1
        if ($firstHtml) {
            Write-Host "在浏览器中打开预览..." -ForegroundColor Cyan
            Start-Process $firstHtml.FullName
        }
    } else {
        Pop-Location
        Write-Host ""
        Write-Host "提示: 使用 -OpenBrowser 参数可自动在浏览器中打开预览" -ForegroundColor Yellow
        Write-Host "例如: .\preview_dita.ps1 -OpenBrowser" -ForegroundColor Yellow
    }
    
} catch {
    Pop-Location
    Write-Host ""
    Write-Host "转换失败: $_" -ForegroundColor Red
    exit 1
}
