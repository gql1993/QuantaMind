# Redis 3.x -> 5.0.14.1 升级脚本
# 需以管理员身份运行

$RedisDir = "C:\Program Files\Redis"
$BackupDir = "$env:TEMP\redis-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$ZipUrl = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"
$ZipPath = "$env:TEMP\Redis-x64-5.0.14.1.zip"

Write-Host "=== Redis 升级到 5.0.14.1 ===" -ForegroundColor Cyan

# 1. 停止 Redis 服务
Write-Host "`n[1/5] 停止 Redis 服务..." -ForegroundColor Yellow
Stop-Service -Name Redis -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
if ((Get-Service Redis).Status -eq 'Running') {
    Write-Host "无法停止服务，请手动以管理员运行" -ForegroundColor Red
    exit 1
}
Write-Host "  已停止" -ForegroundColor Green

# 2. 备份配置
Write-Host "`n[2/5] 备份配置文件到 $BackupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item "$RedisDir\redis.windows-service.conf" $BackupDir -Force
Copy-Item "$RedisDir\redis.windows.conf" $BackupDir -Force
Write-Host "  已备份" -ForegroundColor Green

# 3. 下载 Redis 5.0.14.1
Write-Host "`n[3/5] 下载 Redis 5.0.14.1..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
} catch {
    Write-Host "下载失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host "  已下载" -ForegroundColor Green

# 4. 解压并替换可执行文件
Write-Host "`n[4/5] 解压并替换可执行文件..." -ForegroundColor Yellow
$ExtractDir = "$env:TEMP\Redis-5.0.14.1"
Remove-Item $ExtractDir -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

# Redis 5.0 解压后目录结构可能是 Redis-x64-5.0.14.1 或直接文件
$SrcDir = Get-ChildItem $ExtractDir -Directory | Select-Object -First 1
if (-not $SrcDir) { $SrcDir = $ExtractDir } else { $SrcDir = $SrcDir.FullName }

$FilesToReplace = @("redis-server.exe", "redis-cli.exe", "redis-benchmark.exe", "redis-check-aof.exe")
# 5.0 用 redis-check-rdb 替代 redis-check-dump
if (Test-Path "$SrcDir\redis-check-rdb.exe") {
    $FilesToReplace += "redis-check-rdb.exe"
} elseif (Test-Path "$SrcDir\redis-check-dump.exe") {
    $FilesToReplace += "redis-check-dump.exe"
}

foreach ($f in $FilesToReplace) {
    $src = Join-Path $SrcDir $f
    if (Test-Path $src) {
        Copy-Item $src $RedisDir -Force
        Write-Host "  已替换 $f" -ForegroundColor Gray
    }
}
# 删除旧的 redis-check-dump（5.0 使用 redis-check-rdb）
if (Test-Path "$RedisDir\redis-check-dump.exe") {
    Remove-Item "$RedisDir\redis-check-dump.exe" -Force
}
Write-Host "  替换完成" -ForegroundColor Green

# 5. 启动 Redis 服务
Write-Host "`n[5/5] 启动 Redis 服务..." -ForegroundColor Yellow
Start-Service -Name Redis
Start-Sleep -Seconds 2

# 验证
$svc = Get-Service Redis
if ($svc.Status -eq 'Running') {
    Write-Host "  Redis 服务已启动" -ForegroundColor Green
} else {
    Write-Host "  服务未运行，状态: $($svc.Status)" -ForegroundColor Red
}

# 测试连接
Start-Sleep -Seconds 1
try {
    $r = & "C:\Program Files\Redis\redis-cli.exe" ping 2>&1
    if ($r -match "PONG") {
        $ver = & "C:\Program Files\Redis\redis-cli.exe" INFO server 2>&1 | Select-String "redis_version"
        Write-Host "`n=== 升级成功 ===" -ForegroundColor Green
        Write-Host $ver
    } else {
        Write-Host "`nRedis 响应异常: $r" -ForegroundColor Yellow
    }
} catch {
    Write-Host "验证失败: $_" -ForegroundColor Yellow
}

Write-Host "`n备份目录: $BackupDir" -ForegroundColor Gray
Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
Remove-Item $ExtractDir -Recurse -Force -ErrorAction SilentlyContinue
