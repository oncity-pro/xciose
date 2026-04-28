param(
    [switch]$SkipMigrations = $false,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "  ONCITY-Django"
Write-Host "========================================"
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    Write-Host "Error: Python not found" -ForegroundColor Red
    exit 1
}
$pythonVersion = & $pythonCmd.Source --version
Write-Host "Python: $pythonVersion" -ForegroundColor Green
Write-Host ""

Write-Host "Check MySQL..."
$mysqlRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("localhost", 3306)
    $tcp.Close()
    $mysqlRunning = $true
} catch {
    $mysqlRunning = $false
}

if (-not $mysqlRunning) {
    Write-Host "Warning: MySQL not running" -ForegroundColor Red
    $continue = Read-Host "Continue? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
} else {
    Write-Host "MySQL OK" -ForegroundColor Green
}
Write-Host ""

$venvPath = Join-Path $PSScriptRoot "venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating venv..."
    & $pythonCmd.Source -m venv $venvPath
    Write-Host "Done"
    Write-Host ""
}

Write-Host "Install deps..."
$venvPip = Join-Path $venvPath "Scripts\pip.exe"
& $venvPip install --upgrade pip | Out-Null
& $venvPip install -r (Join-Path $PSScriptRoot "requirements.txt") | Out-Null
Write-Host "Done"
Write-Host ""

$envFile = Join-Path $PSScriptRoot ".env"
$envExample = Join-Path $PSScriptRoot ".env.example"
if (-not (Test-Path $envFile)) {
    Write-Host "Creating .env..."
    Copy-Item $envExample $envFile
    Write-Host "Done"
    Read-Host "Press Enter"
}

if (-not $SkipMigrations) {
    Write-Host "Migrating..."
    & $venvPython (Join-Path $PSScriptRoot "manage.py") migrate
    Write-Host "Done"
    Write-Host ""
} else {
    Write-Host "Skip migrations"
    Write-Host ""
}

Write-Host "Start server on port $Port"
