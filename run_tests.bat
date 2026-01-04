@echo off
echo ========================================
echo 运行 README 中的测试命令
echo ========================================
echo.

REM 获取当前项目路径
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo 当前项目目录: %PROJECT_DIR%
echo.

REM 检查环境是否激活
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python 未找到，请先激活 conda 环境
    echo 运行: conda activate venv
    pause
    exit /b 1
)

echo ========================================
echo [1/5] 测试 Layer 1 - PDF + Word
echo ========================================
python test_layer1.py --pdf uploads\2023CVPR-CoMFormer.pdf --word uploads\0d98a7bb-bb4c-4d9b-800b-83da29355828_sample.docx
if %errorlevel% neq 0 (
    echo [警告] Layer 1 测试失败
)
echo.
pause

echo ========================================
echo [2/5] 测试 Layer 1 - 仅 PDF
echo ========================================
python test_layer1.py --pdf "uploads\2023CVPR-CoMFormer.pdf"
if %errorlevel% neq 0 (
    echo [警告] Layer 1 PDF 测试失败
)
echo.
pause

echo ========================================
echo [3/5] 测试 Layer 2
echo ========================================
python test_layer2.py
if %errorlevel% neq 0 (
    echo [警告] Layer 2 测试失败
)
echo.
pause

echo ========================================
echo [4/5] 测试集成流程
echo ========================================
python test_integration.py "uploads\2023CVPR-CoMFormer.pdf" "uploads\0d98a7bb-bb4c-4d9b-800b-83da29355828_sample.docx"
if %errorlevel% neq 0 (
    echo [警告] 集成测试失败
)
echo.
pause

echo ========================================
echo [5/5] 启动 Web 服务器
echo ========================================
echo 服务器将在 http://127.0.0.1:5000 启动
echo 按 Ctrl+C 停止服务器
echo.
python run_web.py
pause




