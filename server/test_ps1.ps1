param(
    [switch]$SkipMigrations = $false,
    [int]$Port = 8000
)

Write-Host "Test script loaded"

if (-not $SkipMigrations) {
    Write-Host "Would run migrations"
} else {
    Write-Host "Skip migrations"
}

Write-Host "Port: $Port"
