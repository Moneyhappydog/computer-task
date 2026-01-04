@echo off
echo ========================================
echo 启动 DITA Converter Web Server
echo ========================================
echo.

REM 尝试激活环境，如果失败则使用完整路径
conda activate venv 2>nul
if %errorlevel% neq 0 (
    echo 使用完整路径启动...
    D:\anaconda\envs\venv\python.exe run_web.py
) else (
    echo 环境已激活，启动服务器...
    python run_web.py
)

pause




