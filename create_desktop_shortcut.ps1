# 在桌面创建 QuantaMind 客户端快捷方式，双击即可打开 QuantaMind 桌面软件
# 运行方式: PowerShell -ExecutionPolicy Bypass -File "E:\work\QuantaMind\create_desktop_shortcut.ps1"
$Desktop = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop "QuantaMind Client.lnk"

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Write-Error "未找到 python，请先安装 Python 并加入 PATH"
    exit 1
}
$pythonw = $python -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path $pythonw)) { $pythonw = $python }

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $pythonw
$Shortcut.Arguments = 'E:\work\QuantaMind\run_desktop_client.py'
$Shortcut.WorkingDirectory = 'E:\work\QuantaMind'
$Shortcut.Description = "QuantaMind Client"
$Shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null

Write-Host "Done: $ShortcutPath"
Write-Host "Double-click to launch QuantaMind client. Start Gateway first: python run_gateway.py"
