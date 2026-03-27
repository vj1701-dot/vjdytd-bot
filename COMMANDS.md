# Quick Command Reference

Common commands you'll use to manage your bot.

## Setup & Deployment

```bash
# Initial setup (only once)
./setup.sh

# Update to latest version
./update.sh

# Or update manually
git pull && docker-compose down && docker-compose up -d --build
```

## Docker Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart telegram-bot

# Check service status
docker-compose ps

# View resource usage
docker stats
```

## Logs & Debugging

```bash
# View all logs (follow mode)
docker-compose logs -f

# View specific service logs
docker-compose logs -f telegram-bot
docker-compose logs -f fastapi-service
docker-compose logs -f cleanup-worker

# View last 100 lines
docker-compose logs --tail=100 telegram-bot

# View logs for errors only
docker-compose logs telegram-bot | grep -i error
```

## Maintenance

```bash
# Check disk space
df -h
du -sh downloads/

# Clean up Docker cache
docker system prune -a

# Force cleanup of old files
docker-compose restart cleanup-worker

# Backup database
docker-compose exec telegram-bot cp /app/data/bot_data.db /downloads/backup.db
```

## Configuration

```bash
# Edit configuration
nano .env

# After changing .env, restart services
docker-compose restart

# View current configuration (careful - shows secrets!)
cat .env
```

## Health Checks

```bash
# Check FastAPI health
curl http://localhost:8000/api/health

# Check Redis
docker-compose exec redis redis-cli ping

# Check if bot is running
docker-compose ps telegram-bot

# Test bot connection
docker-compose exec telegram-bot python -c "
from aiogram import Bot
import asyncio
import os
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
info = asyncio.run(bot.get_me())
print(f'Bot is running: @{info.username}')
"
```

## Troubleshooting

```bash
# Bot not responding?
docker-compose restart telegram-bot
docker-compose logs --tail=50 telegram-bot

# Downloads not working?
docker-compose logs --tail=50 fastapi-service

# Out of disk space?
docker system prune -a
docker-compose restart cleanup-worker

# Reset everything (WARNING: deletes all data)
docker-compose down -v
./setup.sh
```

## User Management (via Telegram)

Send these commands to your bot:

```
# Admin commands
/pending          - View pending users
/approve <id>     - Approve a user
/reject <id>      - Reject a user
/ban <id>         - Ban a user
/users            - List approved users
/banned           - List banned users
/remove <id>      - Remove user from database

# User commands
/start            - Start the bot
/help             - Show help
/download <url>   - Download video/audio
/audio <url>      - Download audio only
/video <url>      - Download video
/status           - Check active downloads
/queue            - View download queue
/cancel <id>      - Cancel a download
/list             - List recent downloads
```

## Server Commands

```bash
# Check server resources
free -h              # RAM usage
df -h                # Disk usage
top                  # CPU usage (press q to quit)

# Check if services are listening
netstat -tlnp | grep -E '6379|8000|5800'

# View all running containers
docker ps

# View all containers (including stopped)
docker ps -a
```

## Advanced

```bash
# Scale FastAPI service (more workers)
docker-compose up -d --scale fastapi-service=3

# Execute command in container
docker-compose exec telegram-bot bash

# Copy file from container
docker-compose cp telegram-bot:/app/data/bot_data.db ./backup.db

# Copy file to container
docker-compose cp config.txt telegram-bot:/app/

# View environment variables in container
docker-compose exec telegram-bot env | grep TELEGRAM
```

## Quick Reference Card

| Task | Command |
|------|---------|
| Setup bot | `./setup.sh` |
| Update bot | `./update.sh` |
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Restart | `docker-compose restart` |
| Logs | `docker-compose logs -f` |
| Status | `docker-compose ps` |
| Edit config | `nano .env` |
| Backup DB | `docker-compose exec telegram-bot cp /app/data/bot_data.db /downloads/backup.db` |

## Emergency Recovery

If something goes wrong:

```bash
# 1. Stop everything
docker-compose down

# 2. Backup your .env
cp .env .env.backup

# 3. Clean Docker
docker system prune -a

# 4. Pull latest code
git pull

# 5. Rebuild and start
docker-compose up -d --build

# 6. Check logs
docker-compose logs -f
```

## Getting Help

- Check logs first: `docker-compose logs -f`
- Check [QUICKSTART.md](QUICKSTART.md)
- Check [README.md](README.md)
- Check [DEPLOYMENT.md](DEPLOYMENT.md)
- Open issue on [GitHub](https://github.com/vj1701-dot/vjdytd-bot/issues)
