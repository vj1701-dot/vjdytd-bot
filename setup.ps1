# Telegram Video/Audio Downloader Bot - Windows Setup Script
# PowerShell script for Windows Server

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Telegram Video/Audio Downloader Bot Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env already exists
if (Test-Path .env) {
    Write-Host "[!] .env file already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "[i] Setup cancelled. Existing .env file kept." -ForegroundColor Blue
        exit 0
    }
    Move-Item .env .env.backup -Force
    Write-Host "[i] Backed up existing .env to .env.backup" -ForegroundColor Blue
}

Write-Host ""
Write-Host "[i] Let's set up your bot! I'll ask you a few questions..." -ForegroundColor Blue
Write-Host ""

# ===== REQUIRED CONFIGURATION =====
Write-Host "=== Required Configuration ===" -ForegroundColor Green
Write-Host ""

# Telegram Bot Token
Write-Host "[i] Get your bot token from https://t.me/BotFather" -ForegroundColor Blue
$BOT_TOKEN = Read-Host "Enter your Telegram Bot Token"

# Telegram API credentials
Write-Host ""
Write-Host "[i] Get API credentials from https://my.telegram.org/apps" -ForegroundColor Blue
$API_ID = Read-Host "Enter your Telegram API ID"
$API_HASH = Read-Host "Enter your Telegram API Hash"

# Admin ID
Write-Host ""
Write-Host "[i] Get your Telegram User ID from https://t.me/userinfobot" -ForegroundColor Blue
$ADMIN_ID = Read-Host "Enter your Telegram User ID (admin)"

# ===== OPTIONAL CONFIGURATION =====
Write-Host ""
Write-Host "=== Optional Configuration ===" -ForegroundColor Yellow
Write-Host ""

# Auto-approve users
Write-Host "[i] Auto-approve: Automatically approve new users (not recommended)" -ForegroundColor Blue
$autoApproveInput = Read-Host "Enable auto-approve? (y/n) [n]"
if ($autoApproveInput -eq "y") {
    $AUTO_APPROVE = "true"
} else {
    $AUTO_APPROVE = "false"
}

# JDownloader setup
Write-Host ""
Write-Host "[i] JDownloader: Optional download engine (yt-dlp will be used as fallback)" -ForegroundColor Blue
Write-Host "[!] Note: Requires My.JDownloader account from https://my.jdownloader.org" -ForegroundColor Yellow
$setupJDownloader = Read-Host "Do you want to set up JDownloader? (y/n) [n]"

if ($setupJDownloader -eq "y") {
    Write-Host ""
    Write-Host "[i] Enter your My.JDownloader credentials (create account at https://my.jdownloader.org)" -ForegroundColor Blue
    $JDOWNLOADER_EMAIL = Read-Host "JDownloader Email"
    $JDOWNLOADER_PASSWORD = Read-Host "JDownloader Password" -AsSecureString
    $JDOWNLOADER_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($JDOWNLOADER_PASSWORD))
    $JDOWNLOADER_DEVICE = Read-Host "JDownloader Device Name [TelegramBot]"
    if ([string]::IsNullOrWhiteSpace($JDOWNLOADER_DEVICE)) {
        $JDOWNLOADER_DEVICE = "TelegramBot"
    }
} else {
    $JDOWNLOADER_EMAIL = ""
    $JDOWNLOADER_PASSWORD = ""
    $JDOWNLOADER_DEVICE = "TelegramBot"
}

# GoFile API Token
Write-Host ""
Write-Host "[i] GoFile: Used for files >2GB (works without API token, token gives better limits)" -ForegroundColor Blue
$hasGoFileToken = Read-Host "Do you have a GoFile API token? (y/n) [n]"

if ($hasGoFileToken -eq "y") {
    $GOFILE_TOKEN = Read-Host "GoFile API Token"
} else {
    $GOFILE_TOKEN = ""
}

# Local Telegram Bot API
Write-Host ""
Write-Host "=== Large File Upload Settings ===" -ForegroundColor Green
Write-Host "[i] Choose how to handle large files:" -ForegroundColor Blue
Write-Host ""
Write-Host "Option 1: Official Telegram API (default)"
Write-Host "  - Files up to 50MB -> Uploaded to Telegram"
Write-Host "  - Files 50MB-2GB -> Uploaded to GoFile (external service)"
Write-Host "  - Files >2GB -> Uploaded to GoFile"
Write-Host ""
Write-Host "Option 2: Local Telegram Bot API (recommended for better Telegram integration)"
Write-Host "  - Files up to 2GB -> Uploaded to Telegram ✓" -ForegroundColor Green
Write-Host "  - Files >2GB -> Uploaded to GoFile"
Write-Host "  - Requires additional Docker container"
Write-Host ""
$useLocalAPI = Read-Host "Enable Local Telegram Bot API for 2GB Telegram uploads? (y/n) [y]"

if ([string]::IsNullOrWhiteSpace($useLocalAPI) -or $useLocalAPI -eq "y") {
    $USE_LOCAL_BOT_API = "true"
    $ENABLE_LOCAL_API_SERVICE = $true
    Write-Host "[✓] Local Bot API enabled - files up to 2GB will go to Telegram!" -ForegroundColor Green
} else {
    $USE_LOCAL_BOT_API = "false"
    $ENABLE_LOCAL_API_SERVICE = $false
    Write-Host "[i] Using official API - files over 50MB will go to GoFile" -ForegroundColor Blue
}

# ===== PERFORMANCE TUNING =====
Write-Host ""
Write-Host "=== Performance Settings ===" -ForegroundColor Cyan
Write-Host ""

$MAX_CONCURRENT = Read-Host "Max concurrent downloads per user [2]"
if ([string]::IsNullOrWhiteSpace($MAX_CONCURRENT)) { $MAX_CONCURRENT = "2" }

$RETENTION_HOURS = Read-Host "File retention hours (auto-delete after) [48]"
if ([string]::IsNullOrWhiteSpace($RETENTION_HOURS)) { $RETENTION_HOURS = "48" }

$CLEANUP_INTERVAL = Read-Host "Cleanup interval (minutes) [60]"
if ([string]::IsNullOrWhiteSpace($CLEANUP_INTERVAL)) { $CLEANUP_INTERVAL = "60" }

# ===== CREATE .ENV FILE =====
Write-Host ""
Write-Host "[i] Creating .env file..." -ForegroundColor Blue

$envContent = @"
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_API_ID=$API_ID
TELEGRAM_API_HASH=$API_HASH

# Admin Configuration
ADMIN_IDS=$ADMIN_ID
AUTO_APPROVE=$AUTO_APPROVE

# Redis Configuration (default settings work out-of-box)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Database Configuration
DATABASE_URL=sqlite:///./data/bot_data.db

# JDownloader Configuration
JDOWNLOADER_EMAIL=$JDOWNLOADER_EMAIL
JDOWNLOADER_PASSWORD=$JDOWNLOADER_PASSWORD
JDOWNLOADER_DEVICE_NAME=$JDOWNLOADER_DEVICE

# FastAPI Service
FASTAPI_HOST=fastapi-service
FASTAPI_PORT=8000

# File Handling
MAX_FILE_SIZE_TELEGRAM=2147483648
MIN_FILE_SIZE=52428800
DOWNLOAD_PATH=/downloads
TEMP_PATH=/downloads/temp
FILE_RETENTION_HOURS=$RETENTION_HOURS

# External Upload Services
GOFILE_API_TOKEN=$GOFILE_TOKEN
UPLOAD_FALLBACK_ENABLED=true

# Rate Limiting
MAX_CONCURRENT_DOWNLOADS_PER_USER=$MAX_CONCURRENT
GLOBAL_RATE_LIMIT=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=/logs/bot.log

# Optional: Local Telegram Bot API
USE_LOCAL_BOT_API=$USE_LOCAL_BOT_API
LOCAL_BOT_API_URL=http://telegram-bot-api:8081

# Optional: MTProto
USE_MTPROTO=false
MTPROTO_SESSION_STRING=

# Worker Configuration
CLEANUP_INTERVAL_MINUTES=$CLEANUP_INTERVAL
"@

$envContent | Out-File -FilePath .env -Encoding UTF8
Write-Host "[✓] .env file created successfully!" -ForegroundColor Green

# ===== DOCKER COMPOSE ADJUSTMENT =====
Write-Host ""
Write-Host "[i] Adjusting docker-compose.yml for your setup..." -ForegroundColor Blue

if ($ENABLE_LOCAL_API_SERVICE) {
    Write-Host "[i] Enabling Local Telegram Bot API service..." -ForegroundColor Blue

    # Create backup
    Copy-Item docker-compose.yml docker-compose.yml.backup

    # Read file content
    $content = Get-Content docker-compose.yml -Raw

    # Uncomment telegram-bot-api service - simple string replacement
    $content = $content -replace '(?m)^  # telegram-bot-api:', '  telegram-bot-api:'
    $content = $content -replace '(?m)^  #   image: aiogram', '    image: aiogram'
    $content = $content -replace '(?m)^  #   container_name', '    container_name'
    $content = $content -replace '(?m)^  #   restart', '    restart'
    $content = $content -replace '(?m)^  #   ports:', '    ports:'
    $content = $content -replace '(?m)^  #     - "8081', '      - "8081'
    $content = $content -replace '(?m)^  #   volumes:', '    volumes:'
    $content = $content -replace '(?m)^  #     - telegram', '      - telegram'
    $content = $content -replace '(?m)^  #   environment:', '    environment:'
    $content = $content -replace '(?m)^  #     - TELEGRAM', '      - TELEGRAM'
    $content = $content -replace '(?m)^  #   networks:', '    networks:'
    $content = $content -replace '(?m)^  #     - vjdytd', '      - vjdytd'
    $content = $content -replace '(?m)^  # telegram_bot_api:', '  telegram_bot_api:'

    # Write back
    $content | Out-File -FilePath docker-compose.yml -Encoding UTF8

    Write-Host "[✓] Local Bot API service enabled in docker-compose.yml" -ForegroundColor Green
}

if ($setupJDownloader -ne "y") {
    Write-Host "[i] Note: JDownloader service will run but yt-dlp will be used as primary downloader" -ForegroundColor Blue
}

Write-Host "[✓] Configuration complete!" -ForegroundColor Green

# ===== SUMMARY =====
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Setup Complete! 🎉" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration saved to .env"
Write-Host ""
Write-Host "Next steps:"
Write-Host ""
Write-Host "1. Start the bot:"
Write-Host "   docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. View logs:"
Write-Host "   docker-compose logs -f telegram-bot" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Stop the bot:"
Write-Host "   docker-compose down" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Update the bot (pull latest code):"
Write-Host "   .\update.ps1" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to start now
$startNow = Read-Host "Do you want to start the bot now? (y/n)"
if ($startNow -eq "y") {
    Write-Host ""
    Write-Host "[i] Starting bot services..." -ForegroundColor Blue

    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        docker-compose up -d
        Write-Host ""
        Write-Host "[✓] Bot started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "[i] Checking service status..." -ForegroundColor Blue
        Start-Sleep -Seconds 3
        docker-compose ps
        Write-Host ""
        Write-Host "[i] View logs with: docker-compose logs -f" -ForegroundColor Blue
    } else {
        Write-Host "[!] docker-compose not found. Please install Docker Desktop for Windows first." -ForegroundColor Red
        Write-Host ""
        Write-Host "Install from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[i] You can start the bot later with: docker-compose up -d" -ForegroundColor Blue
}

Write-Host ""
Write-Host "[✓] All done! Enjoy your bot! 🤖" -ForegroundColor Green
Write-Host ""
