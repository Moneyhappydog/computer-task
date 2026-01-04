# 启动 DITA Converter Web Server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动 DITA Converter Web Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonExe = "D:\anaconda\envs\venv\python.exe"

# 检查 Python 是否存在
if (Test-Path $pythonExe) {
    Write-Host "启动服务器..." -ForegroundColor Yellow
    Write-Host "访问地址: http://127.0.0.1:5000" -ForegroundColor Green
    Write-Host ""
    & $pythonExe run_web.py
} else {
    Write-Host "错误: 找不到 Python 环境" -ForegroundColor Red
    Write-Host "请检查环境路径: $pythonExe" -ForegroundColor Yellow
    pause
}




