#!/bin/bash

# Telegram Video/Audio Downloader Bot - Easy Update Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo ""
echo "================================================"
echo "  Updating Telegram Downloader Bot"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found!"
    echo "Please run ./setup.sh first to configure the bot."
    exit 1
fi

# Pull latest code
print_info "Pulling latest code from GitHub..."
git pull

print_success "Code updated!"

# Stop existing containers
print_info "Stopping existing containers..."
docker-compose down

print_success "Containers stopped!"

# Rebuild and start
print_info "Building and starting updated containers..."
docker-compose up -d --build

print_success "Bot updated and restarted!"

echo ""
print_info "Checking service status..."
sleep 3
docker-compose ps

echo ""
print_success "Update complete! 🎉"
echo ""
print_info "View logs with: docker-compose logs -f"
echo ""
