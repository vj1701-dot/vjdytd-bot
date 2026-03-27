# Deployment Guide

This guide provides detailed step-by-step instructions for deploying the Telegram Video/Audio Downloader Bot to various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Production Server Deployment](#production-server-deployment)
3. [VPS Deployment (Ubuntu/Debian)](#vps-deployment)
4. [Docker Compose Setup](#docker-compose-setup)
5. [Configuration](#configuration)
6. [Maintenance](#maintenance)

---

## Local Development

### Prerequisites

- Docker and Docker Compose installed
- Telegram Bot Token
- Telegram API credentials
- JDownloader account

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vjdytd-bot
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

5. **Test the bot**
   - Open Telegram
   - Search for your bot
   - Send `/start`
   - As admin, you should be auto-approved

---

## Production Server Deployment

### Server Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 50GB+ (depending on download volume)
- **CPU**: 2+ cores recommended
- **Network**: Good bandwidth for downloads/uploads

### Initial Server Setup

1. **Update system**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Docker**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   docker-compose --version
   ```

4. **Set up firewall** (optional but recommended)
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

---

## VPS Deployment

### Step 1: Prepare VPS

1. **SSH into your VPS**
   ```bash
   ssh user@your-vps-ip
   ```

2. **Create application directory**
   ```bash
   mkdir -p ~/vjdytd-bot
   cd ~/vjdytd-bot
   ```

### Step 2: Transfer Files

**Option A: Using Git (Recommended)**
```bash
git clone <your-repository-url> .
```

**Option B: Using SCP**
```bash
# From your local machine
scp -r /path/to/vjdytd-bot user@vps-ip:~/vjdytd-bot
```

### Step 3: Configure Environment

1. **Create .env file**
   ```bash
   cp .env.example .env
   nano .env
   ```

2. **Set production values**
   ```env
   # Telegram Configuration
   TELEGRAM_BOT_TOKEN=your_production_token
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash

   # Admin Configuration
   ADMIN_IDS=your_telegram_id
   AUTO_APPROVE=false

   # JDownloader
   JDOWNLOADER_EMAIL=your_email
   JDOWNLOADER_PASSWORD=your_secure_password

   # Optional but recommended
   GOFILE_API_TOKEN=your_gofile_token

   # Performance tuning for production
   MAX_CONCURRENT_DOWNLOADS_PER_USER=3
   GLOBAL_RATE_LIMIT=15
   FILE_RETENTION_HOURS=24
   CLEANUP_INTERVAL_MINUTES=30
   ```

### Step 4: Start Services

1. **Build and start containers**
   ```bash
   docker-compose up -d --build
   ```

2. **Verify services are running**
   ```bash
   docker-compose ps
   ```

3. **Check logs**
   ```bash
   docker-compose logs -f telegram-bot
   ```

### Step 5: Set Up JDownloader

1. **Access JDownloader UI**
   - Open `http://your-vps-ip:5800` in browser
   - Login with your My.JDownloader credentials
   - Configure download settings

2. **Connect to My.JDownloader**
   - The JDownloader container should auto-connect
   - Verify in My.JDownloader web interface

---

## Docker Compose Setup

### Service Architecture

```
┌─────────────────┐
│  Telegram Bot   │ ─┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌─────────────┐
│  FastAPI API    │ ─┼───→│    Redis    │
└─────────────────┘  │    └─────────────┘
                     │
┌─────────────────┐  │
│ Cleanup Worker  │ ─┘
└─────────────────┘
         │
         ↓
┌─────────────────┐
│  JDownloader    │
└─────────────────┘
```

### Container Management

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Stop all services**
   ```bash
   docker-compose stop
   ```

3. **Restart a service**
   ```bash
   docker-compose restart telegram-bot
   ```

4. **View logs**
   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f telegram-bot

   # Last 100 lines
   docker-compose logs --tail=100 telegram-bot
   ```

5. **Update services**
   ```bash
   git pull
   docker-compose down
   docker-compose up -d --build
   ```

6. **Clean up**
   ```bash
   # Stop and remove containers
   docker-compose down

   # Remove volumes (WARNING: deletes data)
   docker-compose down -v
   ```

---

## Configuration

### Environment Variables Explained

#### Required Variables

```env
# Get from @BotFather
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Get from https://my.telegram.org
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef

# Your Telegram user ID (get from @userinfobot)
ADMIN_IDS=123456789,987654321

# My.JDownloader credentials
JDOWNLOADER_EMAIL=your@email.com
JDOWNLOADER_PASSWORD=your_password
```

#### Optional Variables

```env
# Auto-approve new users (default: false)
AUTO_APPROVE=false

# Maximum file size for Telegram upload (2GB)
MAX_FILE_SIZE_TELEGRAM=2147483648

# Minimum file size to process (50MB)
MIN_FILE_SIZE=52428800

# File retention period in hours
FILE_RETENTION_HOURS=48

# Max concurrent downloads per user
MAX_CONCURRENT_DOWNLOADS_PER_USER=2

# Global concurrent download limit
GLOBAL_RATE_LIMIT=10

# Cleanup worker run interval
CLEANUP_INTERVAL_MINUTES=60

# Logging level
LOG_LEVEL=INFO

# GoFile API token for better upload limits
GOFILE_API_TOKEN=your_token_here
```

### Advanced Configuration

#### Using PostgreSQL Instead of SQLite

1. **Add PostgreSQL to docker-compose.yml**
   ```yaml
   postgres:
     image: postgres:15-alpine
     environment:
       POSTGRES_DB: botdb
       POSTGRES_USER: botuser
       POSTGRES_PASSWORD: securepassword
     volumes:
       - postgres_data:/var/lib/postgresql/data
   ```

2. **Update .env**
   ```env
   DATABASE_URL=postgresql://botuser:securepassword@postgres:5432/botdb
   ```

#### Using Local Telegram Bot API

For uploads >50MB, use local Bot API server:

1. **Uncomment in docker-compose.yml**
   ```yaml
   telegram-bot-api:
     image: aiogram/telegram-bot-api:latest
     # ... rest of config
   ```

2. **Update .env**
   ```env
   USE_LOCAL_BOT_API=true
   LOCAL_BOT_API_URL=http://telegram-bot-api:8081
   ```

---

## Maintenance

### Regular Tasks

#### Daily
- Monitor disk space
  ```bash
  df -h
  du -sh downloads/
  ```

#### Weekly
- Check logs for errors
  ```bash
  docker-compose logs --tail=1000 | grep -i error
  ```

- Review user activity
  ```bash
  docker-compose exec telegram-bot python -c "
  from shared.database import get_db_session
  from shared.models import User
  db = get_db_session()
  print(f'Total users: {db.query(User).count()}')
  db.close()
  "
  ```

#### Monthly
- Update Docker images
  ```bash
  docker-compose pull
  docker-compose up -d
  ```

- Backup database
  ```bash
  docker-compose exec telegram-bot cp /app/data/bot_data.db /downloads/backup_$(date +%Y%m%d).db
  ```

### Backup Strategy

#### Automated Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T telegram-bot cat /app/data/bot_data.db > "$BACKUP_DIR/bot_data_$DATE.db"

# Backup .env
cp .env "$BACKUP_DIR/env_$DATE.backup"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Make executable and add to crontab:
```bash
chmod +x backup.sh
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Monitoring

#### Check Service Health

```bash
# Check if services are running
docker-compose ps

# Check resource usage
docker stats

# Check disk usage
docker system df

# Check FastAPI health
curl http://localhost:8000/api/health
```

#### Log Monitoring

Set up log rotation in docker-compose.yml:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Troubleshooting

#### Bot Not Responding
```bash
# Check container status
docker-compose ps telegram-bot

# View logs
docker-compose logs --tail=100 telegram-bot

# Restart bot
docker-compose restart telegram-bot

# Check if token is valid
docker-compose exec telegram-bot python -c "
from aiogram import Bot
import asyncio
bot = Bot(token='YOUR_TOKEN')
info = asyncio.run(bot.get_me())
print(info)
"
```

#### Downloads Not Working
```bash
# Check JDownloader connection
docker-compose logs jdownloader

# Check FastAPI service
docker-compose logs fastapi-service
curl http://localhost:8000/api/health

# Check yt-dlp
docker-compose exec fastapi-service yt-dlp --version
```

#### Disk Space Issues
```bash
# Check space
df -h

# Clean up old downloads manually
find downloads/ -type f -mtime +2 -delete

# Force cleanup run
docker-compose restart cleanup-worker

# Clear Docker cache
docker system prune -a
```

### Security Hardening

1. **Use secrets management**
   - Use Docker secrets instead of .env for production

2. **Regular updates**
   ```bash
   # Update base images monthly
   docker-compose pull
   docker-compose up -d
   ```

3. **Monitor access**
   - Check admin actions regularly
   - Review banned users

4. **Secure the server**
   - Use SSH keys only
   - Disable root login
   - Enable firewall
   - Use fail2ban

---

## Scaling

### Horizontal Scaling

For high load, scale specific services:

```bash
# Scale bot instances
docker-compose up -d --scale telegram-bot=3

# Scale FastAPI workers
# Update docker-compose.yml:
fastapi-service:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Load Balancing

Use nginx as reverse proxy:

```nginx
upstream fastapi {
    server localhost:8000;
    server localhost:8001;
}

server {
    listen 80;
    location /api {
        proxy_pass http://fastapi;
    }
}
```

---

## Migration

### Moving to New Server

1. **On old server**
   ```bash
   # Backup
   docker-compose exec -T telegram-bot cat /app/data/bot_data.db > bot_data.db
   tar czf downloads-backup.tar.gz downloads/
   ```

2. **Transfer to new server**
   ```bash
   scp bot_data.db user@new-server:~/
   scp downloads-backup.tar.gz user@new-server:~/
   scp .env user@new-server:~/vjdytd-bot/
   ```

3. **On new server**
   ```bash
   cd ~/vjdytd-bot
   mkdir -p data downloads
   mv ~/bot_data.db data/
   tar xzf ~/downloads-backup.tar.gz
   docker-compose up -d
   ```

---

## Support

For issues during deployment:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `.env` values
3. Test connectivity: `docker-compose exec telegram-bot ping redis`
4. Review documentation: [README.md](README.md)
