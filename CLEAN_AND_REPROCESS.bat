@echo off
chcp 65001 >nul
echo ========================================
echo 清理旧输出并准备重新处理PDF
echo ========================================
echo.
echo 当前操作将删除以下目录:
echo   data\output\2023CVPR-CoMFormer
echo.
echo 请确认您已经备份了需要保留的数据！
echo.
pause

echo.
echo 正在删除旧输出目录...
if exist "data\output\2023CVPR-CoMFormer" (
    rmdir /s /q "data\output\2023CVPR-CoMFormer"
    echo [OK] 已删除旧输出目录
) else (
    echo [INFO] 输出目录不存在，无需删除
)

echo.
echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 下一步操作:
echo   1. 通过Web界面上传新的PDF文件: data\input\2023CVPR-CoMFormer.pdf
echo   2. 开始转换处理
echo.
pause

