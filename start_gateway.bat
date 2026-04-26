@echo off
chcp 65001 >nul
cd /d "%~dp0"
title QuantaMind Gateway
echo.
echo  ============================================================
echo   QuantaMind Gateway
echo   首次启动可能要 1~2 分钟加载依赖，窗口会暂时只有几行日志。
echo   看到 "Uvicorn running on http://0.0.0.0:18789" 后再打开浏览器。
echo   浏览器地址必须是:  http://127.0.0.1:18789
echo   不要关闭本窗口（关闭即停止服务）。
echo   如需启用飞书卡片图片: 复制 .quantamind.local.env.example 为 .quantamind.local.env 后填写配置。
echo  ============================================================
echo.

py -3 run_gateway.py
if errorlevel 1 python run_gateway.py
if errorlevel 1 (
  echo.
  echo 无法启动。请在本目录打开 CMD 执行:  pip install -r requirements.txt
  pause
  exit /b 1
)
