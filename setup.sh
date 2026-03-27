#!/bin/bash

# Telegram Video/Audio Downloader Bot - Easy Setup Script
# This script will guide you through the setup process

set -e

echo "================================================"
echo "  Telegram Video/Audio Downloader Bot Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if .env already exists
if [ -f .env ]; then
    print_warning ".env file already exists!"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled. Existing .env file kept."
        exit 0
    fi
    mv .env .env.backup
    print_info "Backed up existing .env to .env.backup"
fi

echo ""
print_info "Let's set up your bot! I'll ask you a few questions..."
echo ""

# Function to read input with default value
read_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        eval $var_name="${input:-$default}"
    else
        read -p "$prompt: " input
        eval $var_name="$input"
    fi
}

# ===== REQUIRED CONFIGURATION =====
echo -e "${GREEN}=== Required Configuration ===${NC}"
echo ""

# Telegram Bot Token
print_info "Get your bot token from https://t.me/BotFather"
read_with_default "Enter your Telegram Bot Token" "" "BOT_TOKEN"

# Telegram API credentials
echo ""
print_info "Get API credentials from https://my.telegram.org/apps"
read_with_default "Enter your Telegram API ID" "" "API_ID"
read_with_default "Enter your Telegram API Hash" "" "API_HASH"

# Admin ID
echo ""
print_info "Get your Telegram User ID from https://t.me/userinfobot"
read_with_default "Enter your Telegram User ID (admin)" "" "ADMIN_ID"

# ===== OPTIONAL CONFIGURATION =====
echo ""
echo -e "${YELLOW}=== Optional Configuration ===${NC}"
echo ""

# Auto-approve users
print_info "Auto-approve: Automatically approve new users (not recommended)"
read -p "Enable auto-approve? (y/n) [n]: " -n 1 -r AUTO_APPROVE_INPUT
echo
if [[ $AUTO_APPROVE_INPUT =~ ^[Yy]$ ]]; then
    AUTO_APPROVE="true"
else
    AUTO_APPROVE="false"
fi

# JDownloader setup
echo ""
print_info "JDownloader: Optional download engine (yt-dlp will be used as fallback)"
print_warning "Note: Requires My.JDownloader account from https://my.jdownloader.org"
read -p "Do you want to set up JDownloader? (y/n) [n]: " -n 1 -r SETUP_JDOWNLOADER
echo

if [[ $SETUP_JDOWNLOADER =~ ^[Yy]$ ]]; then
    echo ""
    print_info "Enter your My.JDownloader credentials (create account at https://my.jdownloader.org)"
    read_with_default "JDownloader Email" "" "JDOWNLOADER_EMAIL"
    read -s -p "JDownloader Password: " JDOWNLOADER_PASSWORD
    echo ""
    read_with_default "JDownloader Device Name" "TelegramBot" "JDOWNLOADER_DEVICE"
else
    JDOWNLOADER_EMAIL=""
    JDOWNLOADER_PASSWORD=""
    JDOWNLOADER_DEVICE="TelegramBot"
fi

# GoFile API Token
echo ""
print_info "GoFile: Used for files >2GB (works without API token, token gives better limits)"
read -p "Do you have a GoFile API token? (y/n) [n]: " -n 1 -r HAS_GOFILE_TOKEN
echo

if [[ $HAS_GOFILE_TOKEN =~ ^[Yy]$ ]]; then
    read_with_default "GoFile API Token" "" "GOFILE_TOKEN"
else
    GOFILE_TOKEN=""
fi

# Local Telegram Bot API
echo ""
echo -e "${GREEN}=== Large File Upload Settings ===${NC}"
print_info "Choose how to handle large files:"
echo ""
echo "Option 1: Official Telegram API (default)"
echo "  - Files up to 50MB → Uploaded to Telegram"
echo "  - Files 50MB-2GB → Uploaded to GoFile (external service)"
echo "  - Files >2GB → Uploaded to GoFile"
echo ""
echo "Option 2: Local Telegram Bot API (recommended for better Telegram integration)"
echo "  - Files up to 2GB → Uploaded to Telegram ✅"
echo "  - Files >2GB → Uploaded to GoFile"
echo "  - Requires additional Docker container"
echo ""
read -p "Enable Local Telegram Bot API for 2GB Telegram uploads? (y/n) [y]: " -n 1 -r USE_LOCAL_API
echo

# Default to Yes if user just hits enter
if [[ -z $USE_LOCAL_API ]] || [[ $USE_LOCAL_API =~ ^[Yy]$ ]]; then
    USE_LOCAL_BOT_API="true"
    ENABLE_LOCAL_API_SERVICE=true
    print_success "Local Bot API enabled - files up to 2GB will go to Telegram!"
else
    USE_LOCAL_BOT_API="false"
    ENABLE_LOCAL_API_SERVICE=false
    print_info "Using official API - files over 50MB will go to GoFile"
fi

# ===== PERFORMANCE TUNING =====
echo ""
echo -e "${BLUE}=== Performance Settings ===${NC}"
echo ""

read_with_default "Max concurrent downloads per user" "2" "MAX_CONCURRENT"
read_with_default "File retention hours (auto-delete after)" "48" "RETENTION_HOURS"
read_with_default "Cleanup interval (minutes)" "60" "CLEANUP_INTERVAL"

# ===== CREATE .ENV FILE =====
echo ""
print_info "Creating .env file..."

cat > .env << EOF
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
EOF

print_success ".env file created successfully!"

# ===== DOCKER COMPOSE ADJUSTMENT =====
echo ""
print_info "Adjusting docker-compose.yml for your setup..."

if [[ $ENABLE_LOCAL_API_SERVICE == true ]]; then
    print_info "Enabling Local Telegram Bot API service..."
    # Uncomment the telegram-bot-api service in docker-compose.yml
    if command -v sed &> /dev/null; then
        # Create backup
        cp docker-compose.yml docker-compose.yml.backup

        # Uncomment telegram-bot-api service and its volume
        sed -i.bak '/# Optional: Local Telegram Bot API/,/# telegram_bot_api:/s/^  # /  /' docker-compose.yml
        sed -i.bak 's/^  # telegram_bot_api:/  telegram_bot_api:/' docker-compose.yml

        rm -f docker-compose.yml.bak
        print_success "Local Bot API service enabled in docker-compose.yml"
    else
        print_warning "sed not found - please manually uncomment telegram-bot-api in docker-compose.yml"
    fi
fi

if [[ ! $SETUP_JDOWNLOADER =~ ^[Yy]$ ]]; then
    print_info "Note: JDownloader service will run but yt-dlp will be used as primary downloader"
fi

print_success "Configuration complete!"

# ===== SUMMARY =====
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Setup Complete! 🎉${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Configuration saved to .env"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the bot:"
echo -e "   ${BLUE}docker-compose up -d${NC}"
echo ""
echo "2. View logs:"
echo -e "   ${BLUE}docker-compose logs -f telegram-bot${NC}"
echo ""
echo "3. Stop the bot:"
echo -e "   ${BLUE}docker-compose down${NC}"
echo ""
echo "4. Update the bot (pull latest code):"
echo -e "   ${BLUE}git pull && docker-compose down && docker-compose up -d --build${NC}"
echo ""

# Ask if user wants to start now
read -p "Do you want to start the bot now? (y/n): " -n 1 -r START_NOW
echo
if [[ $START_NOW =~ ^[Yy]$ ]]; then
    echo ""
    print_info "Starting bot services..."

    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
        echo ""
        print_success "Bot started successfully!"
        echo ""
        print_info "Checking service status..."
        sleep 3
        docker-compose ps
        echo ""
        print_info "View logs with: docker-compose logs -f"
    else
        print_error "docker-compose not found. Please install Docker and Docker Compose first."
        echo ""
        echo "Install instructions:"
        echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
        echo "  Then: sudo apt install docker-compose"
    fi
else
    echo ""
    print_info "You can start the bot later with: docker-compose up -d"
fi

echo ""
print_success "All done! Enjoy your bot! 🤖"
echo ""
