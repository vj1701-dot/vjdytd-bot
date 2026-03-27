# Telegram Video/Audio Downloader Bot - Windows Update Script
# PowerShell script for Windows Server

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Updating Telegram Downloader Bot" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "[!] .env file not found!" -ForegroundColor Red
    Write-Host "Please run .\setup.ps1 first to configure the bot." -ForegroundColor Yellow
    exit 1
}

# Pull latest code
Write-Host "[i] Pulling latest code from GitHub..." -ForegroundColor Blue
git pull

Write-Host "[+] Code updated!" -ForegroundColor Green

# Stop existing containers
Write-Host "[i] Stopping existing containers..." -ForegroundColor Blue
docker-compose down

Write-Host "[+] Containers stopped!" -ForegroundColor Green

# Rebuild and start
Write-Host "[i] Building and starting updated containers..." -ForegroundColor Blue
docker-compose up -d --build

Write-Host "[+] Bot updated and restarted!" -ForegroundColor Green

Write-Host ""
Write-Host "[i] Checking service status..." -ForegroundColor Blue
Start-Sleep -Seconds 3
docker-compose ps

Write-Host ""
Write-Host "[+] Update complete! 🎉" -ForegroundColor Green
Write-Host ""
Write-Host "[i] View logs with: docker-compose logs -f" -ForegroundColor Blue
Write-Host ""
