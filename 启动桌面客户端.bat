@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   QuantaMind 量智大脑 - 正在启动（后台常驻 + 自恢复）…
echo.
start "" wscript.exe //B "%~dp0run_gateway_hidden.vbs"
timeout /t 10 /nobreak >nul
start http://127.0.0.1:18789
echo.
echo   Gateway 守护进程已在后台隐藏运行
echo   浏览器已打开 http://127.0.0.1:18789
echo   如需设置开机自启动，请运行 install_gateway_autostart.bat
echo.
