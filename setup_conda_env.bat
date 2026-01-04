@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
echo ========================================
echo 开始设置 Conda 环境
echo ========================================
echo.

REM 检查 conda 是否已安装
echo Step 1/8: 检查 Conda 安装...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Conda，请先安装 Anaconda 或 Miniconda
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('conda --version 2^>nul') do set CONDA_VERSION=%%i
echo [OK] Conda 已安装: %CONDA_VERSION%
echo.

REM 初始化 conda for PowerShell（如果需要）
echo Step 2/8: 初始化 Conda for PowerShell...
conda init powershell >nul 2>&1
echo [OK] 初始化完成
echo.

REM 创建 conda 环境（如果不存在）
echo Step 3/8: 创建/检查 Conda 环境 'venv'...
conda env list | findstr /R "^[ ]*venv[ ]" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 环境 'venv' 已存在，跳过创建
) else (
    echo 创建新环境 'venv' (Python 3.10)...
    conda create -n venv python=3.10 -y
    if %errorlevel% neq 0 (
        echo [ERROR] 创建环境失败
        pause
        exit /b 1
    )
    echo [OK] 环境创建成功
)
echo.

REM 获取 conda 环境路径
echo Step 4/8: 获取环境路径...
for /f "tokens=*" %%i in ('conda info --base') do set CONDA_BASE=%%i
set ENV_PATH=%CONDA_BASE%\envs\venv
set PYTHON_EXE=%ENV_PATH%\python.exe
set PIP_EXE=%ENV_PATH%\Scripts\pip.exe
echo [OK] 环境路径: %ENV_PATH%
echo.

REM 安装 conda 包
echo Step 5/8: 安装 Conda 包...
echo 安装 tesseract...
conda install -n venv -c conda-forge tesseract -y
if %errorlevel% neq 0 (
    echo [WARNING] tesseract 安装可能失败
)

echo 安装 pandoc...
conda install -n venv -c conda-forge pandoc -y
if %errorlevel% neq 0 (
    echo [WARNING] pandoc 安装可能失败
)

echo 安装 poppler...
conda install -n venv -c conda-forge poppler -y
if %errorlevel% neq 0 (
    echo [WARNING] poppler 安装可能失败
)

echo [OK] Conda 包安装完成
echo.

REM 升级 pip
echo Step 6/8: 升级 pip...
"%PYTHON_EXE%" -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERROR] pip 升级失败
    pause
    exit /b 1
)
echo [OK] pip 升级成功
echo.

REM 安装 Python 依赖
echo Step 7/8: 安装 Python 依赖包（这可能需要一些时间）...
"%PIP_EXE%" install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)
echo [OK] Python 依赖安装完成
echo.

REM 下载 spaCy 模型
echo Step 8/8: 下载 spaCy 模型...
echo 下载英文模型 (en_core_web_sm)...
"%PYTHON_EXE%" -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo [WARNING] 英文模型下载失败
)

echo 下载中文模型 (zh_core_web_sm)...
"%PYTHON_EXE%" -m spacy download zh_core_web_sm
if %errorlevel% neq 0 (
    echo [WARNING] 中文模型下载失败
)

echo [OK] spaCy 模型下载完成
echo.

REM 完成
echo ========================================
echo [OK] Conda 环境设置完成！
echo ========================================
echo.
echo 使用以下命令激活环境:
echo   conda activate venv
echo.
echo 然后可以运行:
echo   python run_web.py
echo.
pause

