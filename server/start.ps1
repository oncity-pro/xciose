# ONCITY-Django Backend One-Click Startup Script for PowerShell
# Usage: .\start.ps1 [-SkipMigrations] [-Port 8000]
param(
    [switch]$SkipMigrations = $false,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ONCITY-Django Backend Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    Write-Host "Error: Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
$pythonVersion = & $pythonCmd.Source --version
Write-Host "Python version: $pythonVersion" -ForegroundColor Green
Write-Host ""

# 2. Check MySQL
Write-Host "Checking MySQL status..." -ForegroundColor Yellow
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
    Write-Host "Warning: MySQL is not running on localhost:3306!" -ForegroundColor Red
    Write-Host "Please make sure MySQL service is started." -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
} else {
    Write-Host "MySQL is running" -ForegroundColor Green
}
Write-Host ""

# 3. Virtual environment paths
$venvPath = Join-Path $PSScriptRoot "venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $pythonCmd.Source -m venv $venvPath
    Write-Host "Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

# 4. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip 2>$null
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt") 2>$null
Write-Host "Dependencies installed" -ForegroundColor Green
Write-Host ""

# 5. Check .env
$envFile = Join-Path $PSScriptRoot ".env"
$envExample = Join-Path $PSScriptRoot ".env.example"
if (-not (Test-Path $envFile)) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
    Write-Host "Created .env, please check the configuration!" -ForegroundColor Red
    Read-Host "Press Enter to continue"
}

# 6. Run migrations
if (-not $SkipMigrations) {
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    & $venvPython (Join-Path $PSScriptRoot "manage.py") migrate
    Write-Host "Migrations complete" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Skipping migrations (-SkipMigrations)" -ForegroundColor Yellow
    Write-Host ""
}

# 7. Start server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Django Development Server" -ForegroundColor Cyan
Write-Host "  URL: http://127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "  Admin: http://127.0.0.1:$Port/admin/" -ForegroundColor Cyan
Write-Host "  API Health: http://127.0.0.1:$Port/api/health/" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& $venvPython (Join-Path $PSScriptRoot "manage.py") runserver "127.0.0.1:$Port"
