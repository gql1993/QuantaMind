@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   正在安装 QuantaMind Gateway 开机自启动任务...
echo.
set "TASK_NAME=QuantaMind Gateway"
set "VBS_PATH=%~dp0run_gateway_hidden.vbs"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$action = New-ScheduledTaskAction -Execute 'C:\Windows\System32\wscript.exe' -Argument ('//B ""' + '%VBS_PATH%' + '""');" ^
  "$trigger = New-ScheduledTaskTrigger -AtLogOn;" ^
  "Register-ScheduledTask -TaskName '%TASK_NAME%' -Action $action -Trigger $trigger -Description 'QuantaMind Gateway background auto-recovery' -User ($env:COMPUTERNAME + '\' + $env:USERNAME) -RunLevel Highest -Force"

if errorlevel 1 (
    echo.
    echo   安装失败，请尝试右键“以管理员身份运行”此脚本。
    echo.
    pause
    exit /b 1
)

echo.
echo   安装成功。
echo   登录 Windows 后，Gateway 会自动在后台启动并自恢复。
echo.
pause
