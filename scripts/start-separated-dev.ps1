param(
    [string]$BackendHost = "127.0.0.1",
    [string]$BackendPort = "18789",
    [string]$FrontendPort = "5173",
    [switch]$BuildFrontend
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$frontendDir = Join-Path $repoRoot "frontend"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    throw "frontend/package.json not found. Run this script from the QuantaMind repository."
}

if ($BuildFrontend) {
    Push-Location $frontendDir
    try {
        npm run build
    }
    finally {
        Pop-Location
    }
}

$backendCommand = @"
Set-Location '$repoRoot'
`$env:QUANTAMIND_API_HOST='$BackendHost'
`$env:QUANTAMIND_API_PORT='$BackendPort'
python -m backend.quantamind_api.app
"@

$frontendCommand = @"
Set-Location '$frontendDir'
`$env:VITE_API_BASE_URL=''
npm run dev -- --host 127.0.0.1 --port $FrontendPort
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "QuantaMind separated dev environment is starting..."
Write-Host "Backend:  http://$BackendHost`:$BackendPort"
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
