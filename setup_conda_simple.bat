@echo off
echo ========================================
echo 开始设置 Conda 环境
echo ========================================
echo.

echo Step 1: 检查 Conda...
conda --version
if %errorlevel% neq 0 (
    echo [ERROR] Conda 未安装
    pause
    exit /b 1
)
echo [OK] Conda 已安装
echo.

echo Step 2: 创建 conda 环境 venv (Python 3.10)...
conda create -n venv python=3.10 -y
if %errorlevel% neq 0 (
    echo [ERROR] 创建环境失败
    pause
    exit /b 1
)
echo [OK] 环境创建成功
echo.

echo Step 3: 安装 conda 包 - tesseract...
conda install -n venv -c conda-forge tesseract -y
echo.

echo Step 4: 安装 conda 包 - pandoc...
conda install -n venv -c conda-forge pandoc -y
echo.

echo Step 5: 安装 conda 包 - poppler...
conda install -n venv -c conda-forge poppler -y
echo.

echo Step 6: 获取环境路径...
for /f "tokens=*" %%i in ('conda info --base') do set CONDA_BASE=%%i
set ENV_PATH=%CONDA_BASE%\envs\venv
set PYTHON_EXE=%ENV_PATH%\python.exe
set PIP_EXE=%ENV_PATH%\Scripts\pip.exe
echo 环境路径: %ENV_PATH%
echo.

echo Step 7: 升级 pip...
"%PYTHON_EXE%" -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERROR] pip 升级失败
    pause
    exit /b 1
)
echo [OK] pip 升级成功
echo.

echo Step 8: 安装 Python 依赖包（这可能需要较长时间）...
"%PIP_EXE%" install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)
echo [OK] Python 依赖安装完成
echo.

echo Step 9: 下载 spaCy 英文模型...
"%PYTHON_EXE%" -m spacy download en_core_web_sm
echo.

echo Step 10: 下载 spaCy 中文模型...
"%PYTHON_EXE%" -m spacy download zh_core_web_sm
echo.

echo ========================================
echo [OK] Conda 环境设置完成！
echo ========================================
echo.
echo 使用以下命令激活环境:
echo   conda activate venv
echo.
pause


