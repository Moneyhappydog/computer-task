@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
echo ========================================
echo 开始手动安装依赖
echo ========================================
echo.

set ENV_PATH=D:\anaconda\envs\venv
set PYTHON_EXE=%ENV_PATH%\python.exe
set PIP_EXE=%ENV_PATH%\Scripts\pip.exe

echo [1/6] 升级 pip...
"%PYTHON_EXE%" -m pip install --upgrade pip
if !errorlevel! neq 0 (
    echo [WARNING] pip 升级可能失败，但继续执行...
)
echo.
echo 按任意键继续安装 conda 包...
pause >nul
echo.

echo [2/6] 安装 conda 包 - tesseract...
conda install -n venv -c conda-forge tesseract -y
if !errorlevel! neq 0 (
    echo [WARNING] tesseract 安装可能失败，但继续执行...
)
echo.
echo tesseract 安装完成，继续下一个...
timeout /t 2 >nul
echo.

echo [3/6] 安装 conda 包 - pandoc...
conda install -n venv -c conda-forge pandoc -y
if !errorlevel! neq 0 (
    echo [WARNING] pandoc 安装可能失败，但继续执行...
)
echo.
echo pandoc 安装完成，继续下一个...
timeout /t 2 >nul
echo.

echo [4/6] 安装 conda 包 - poppler...
conda install -n venv -c conda-forge poppler -y
if !errorlevel! neq 0 (
    echo [WARNING] poppler 安装可能失败，但继续执行...
)
echo.
echo poppler 安装完成，继续安装 Python 依赖...
timeout /t 2 >nul
echo.

echo [5/6] 安装 Python 依赖包（这可能需要 10-15 分钟）...
echo 开始安装，请耐心等待...
"%PIP_EXE%" install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Python 依赖安装失败
    echo 请检查错误信息
    pause
    exit /b 1
)
echo.
echo Python 依赖安装完成！
echo.

echo [6/6] 下载 spaCy 模型...
echo 下载英文模型...
"%PYTHON_EXE%" -m spacy download en_core_web_sm
if !errorlevel! neq 0 (
    echo [WARNING] 英文模型下载失败，但继续执行...
)
echo.

echo 下载中文模型...
"%PYTHON_EXE%" -m spacy download zh_core_web_sm
if !errorlevel! neq 0 (
    echo [WARNING] 中文模型下载失败，但继续执行...
)
echo.

echo ========================================
echo 安装完成！
echo ========================================
pause




