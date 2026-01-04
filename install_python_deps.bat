@echo off
echo ========================================
echo 安装 Python 依赖包
echo ========================================
echo.
echo 注意：这个过程可能需要 10-15 分钟，请耐心等待
echo 会显示安装进度，请不要关闭窗口
echo.
pause

D:\anaconda\envs\venv\Scripts\pip.exe install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Python 依赖包安装完成！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 安装过程中出现错误，请检查上面的错误信息
    echo ========================================
)

pause




