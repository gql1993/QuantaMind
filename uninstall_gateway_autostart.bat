@echo off
chcp 65001 >nul
echo.
echo   正在移除 QuantaMind Gateway 开机自启动任务...
echo.

schtasks /Delete /TN "QuantaMind Gateway" /F

if errorlevel 1 (
    echo.
    echo   未找到计划任务，或删除失败。
    echo.
    pause
    exit /b 1
)

echo.
echo   已移除。
echo.
pause
