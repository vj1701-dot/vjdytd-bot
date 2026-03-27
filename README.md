# Telegram Video/Audio Downloader Bot

A comprehensive, self-hosted Telegram bot that downloads videos and audio from various platforms using JDownloader and yt-dlp, with automatic file management and external upload support for large files.

## Features

### Core Features
- Download videos and audio from YouTube and other platforms
- User authorization system with admin approval workflow
- File caching to avoid duplicate downloads
- Automatic cleanup after 48 hours
- Support for files up to 2GB via Telegram
- Automatic external upload for files over 2GB (GoFile)
- Progress tracking and status updates
- Queue management with rate limiting

### Admin Features
- User approval/rejection/ban system
- Inline approval buttons for quick actions
- Multiple admin support
- User management commands
- Admin action logging

### Technical Features
- Modular Docker Compose architecture
- JDownloader integration with yt-dlp fallback
- Redis-based queue and state management
- SQLite database for persistence
- FastAPI service layer
- Automatic file cleanup worker
- Health check endpoints

## Architecture

```
telegram-bot/          # Telegram bot service (aiogram)
├── bot/
│   ├── handlers/      # Command handlers (user, admin, download)
│   ├── middleware/    # Authorization middleware
│   └── utils/         # Uploader and external upload utilities
├── config.py
└── main.py

fastapi-service/       # API wrapper service
├── api/
│   └── routes.py      # API endpoints
├── services/
│   └── jdownloader.py # JDownloader integration
└── main.py

worker/                # Cleanup worker
└── cleanup.py         # 48h TTL file cleanup

shared/                # Shared modules
├── models.py          # Database models
├── database.py        # Database connection
├── redis_client.py    # Redis client wrapper
└── utils.py           # Common utilities
```

## Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram API ID and Hash (from [my.telegram.org](https://my.telegram.org))
- JDownloader account (My.JDownloader)

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd vjdytd-bot
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
ADMIN_IDS=123456789,987654321  # Your Telegram user ID(s)

# JDownloader (My.JDownloader account)
JDOWNLOADER_EMAIL=your_email@example.com
JDOWNLOADER_PASSWORD=your_password
JDOWNLOADER_DEVICE_NAME=TelegramBot

# Optional - GoFile API token for better external uploads
GOFILE_API_TOKEN=your_gofile_token
```

### 3. Get your Telegram User ID

Send a message to [@userinfobot](https://t.me/userinfobot) to get your Telegram user ID and add it to `ADMIN_IDS` in `.env`.

### 4. Set up JDownloader

1. Create account at [my.jdownloader.org](https://my.jdownloader.org)
2. Install JDownloader on a server or local machine
3. Connect it to My.JDownloader using your account
4. Note the device name (default: computer name)

### 5. Start the services

```bash
docker-compose up -d
```

### 6. Check logs

```bash
# Bot logs
docker-compose logs -f telegram-bot

# API service logs
docker-compose logs -f fastapi-service

# All services
docker-compose logs -f
```

## Usage

### User Commands

- `/start` - Start the bot and register
- `/help` - Show help message
- `/download <url>` - Download video/audio (best quality)
- `/audio <url>` - Download audio only
- `/video <url>` - Download video
- `/formats <url>` - Show available formats
- `/status` - Check active downloads
- `/queue` - View download queue
- `/list` - List recent downloads
- `/cancel <job_id>` - Cancel a download
- `/retry <job_id>` - Retry failed download

### Admin Commands

- `/pending` - View pending user requests
- `/approve <user_id>` - Approve a user
- `/reject <user_id>` - Reject a user
- `/ban <user_id>` - Ban a user
- `/users` - List all approved users
- `/banned` - List banned users
- `/remove <user_id>` - Remove user from database

### Direct URL Support

Simply send a URL to the bot and it will present you with download options via inline buttons.

## File Handling

### Size Constraints
- Minimum file size: 50MB (configurable)
- Maximum Telegram upload: 2GB
- Files over 2GB: Uploaded to external service (GoFile)

### Upload Strategy
1. Files ≤ 2GB: Upload to Telegram
2. Files > 2GB: Upload to GoFile and provide download link
3. Failed uploads: Automatic fallback to external service

### File Retention
- All downloads stored locally in `downloads/` directory
- Files automatically deleted after 48 hours
- Telegram copies remain intact
- Cache entries cleaned up with files

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | - | Yes |
| `TELEGRAM_API_ID` | API ID from my.telegram.org | - | Yes |
| `TELEGRAM_API_HASH` | API hash from my.telegram.org | - | Yes |
| `ADMIN_IDS` | Comma-separated admin user IDs | - | Yes |
| `AUTO_APPROVE` | Auto-approve new users | false | No |
| `JDOWNLOADER_EMAIL` | My.JDownloader email | - | Yes |
| `JDOWNLOADER_PASSWORD` | My.JDownloader password | - | Yes |
| `MAX_FILE_SIZE_TELEGRAM` | Max Telegram upload size (bytes) | 2147483648 | No |
| `FILE_RETENTION_HOURS` | File retention period | 48 | No |
| `MAX_CONCURRENT_DOWNLOADS_PER_USER` | Max concurrent downloads per user | 2 | No |
| `CLEANUP_INTERVAL_MINUTES` | Cleanup job interval | 60 | No |

### Rate Limiting
- Per-user concurrent downloads: 2 (configurable)
- Global rate limit: 10 downloads (configurable)

## Development

### Project Structure

```
vjdytd-bot/
├── docker-compose.yml       # Docker Compose configuration
├── .env                      # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── README.md                # This file
├── telegram-bot/            # Telegram bot service
├── fastapi-service/         # FastAPI wrapper service
├── worker/                  # Cleanup worker
├── shared/                  # Shared modules
├── downloads/               # Download storage
└── logs/                    # Log files
```

### Adding New Handlers

1. Create handler function in appropriate file under `telegram-bot/bot/handlers/`
2. Register handler in the handler's `register_*_handlers()` function
3. Handler receives `message` and middleware data (is_admin, user_status, etc.)

### Database Models

All models are defined in `shared/models.py`:
- `User` - User information and status
- `DownloadJob` - Download job tracking
- `FileCache` - File cache for duplicate detection
- `AdminAction` - Admin action logging

## Troubleshooting

### Bot not responding
```bash
# Check bot logs
docker-compose logs -f telegram-bot

# Restart bot
docker-compose restart telegram-bot
```

### JDownloader not working
```bash
# Check if JDownloader is connected
docker-compose exec fastapi-service curl http://localhost:8000/api/health

# Check JDownloader container
docker-compose logs jdownloader
```

### Files not cleaning up
```bash
# Check cleanup worker logs
docker-compose logs -f cleanup-worker

# Manually trigger cleanup (restart worker)
docker-compose restart cleanup-worker
```

### Database issues
```bash
# Access database
docker-compose exec telegram-bot python -c "from shared.database import *; init_db()"
```

## Security Best Practices

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use strong passwords** - For JDownloader account
3. **Limit admin access** - Only add trusted users to ADMIN_IDS
4. **Regular updates** - Keep Docker images and dependencies updated
5. **Monitor logs** - Check for suspicious activity
6. **Secure server** - Use firewall and proper access controls
7. **Backup database** - Regular backups of `bot_data.db`

## Deployment

### Production Deployment

1. **Use environment-specific configuration**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Set up reverse proxy** (Optional - for FastAPI dashboard)
   ```nginx
   location /api {
       proxy_pass http://localhost:8000;
   }
   ```

3. **Enable auto-restart**
   ```yaml
   # Already configured in docker-compose.yml
   restart: unless-stopped
   ```

4. **Set up monitoring**
   - Monitor container health
   - Check disk space (downloads directory)
   - Monitor logs for errors

5. **Backup strategy**
   ```bash
   # Backup database
   docker-compose exec telegram-bot cp /app/data/bot_data.db /downloads/backup_$(date +%Y%m%d).db
   ```

## Performance Optimization

### For High Load

1. **Increase worker limits**
   ```env
   MAX_CONCURRENT_DOWNLOADS_PER_USER=5
   GLOBAL_RATE_LIMIT=20
   ```

2. **Adjust cleanup frequency**
   ```env
   CLEANUP_INTERVAL_MINUTES=30
   FILE_RETENTION_HOURS=24
   ```

3. **Use PostgreSQL instead of SQLite**
   ```env
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   ```

4. **Scale services**
   ```bash
   docker-compose up -d --scale telegram-bot=2
   ```

## Future Improvements

- [ ] Support for more external upload services
- [ ] Web dashboard for monitoring
- [ ] User download history with search
- [ ] Download scheduling
- [ ] Subtitle download support
- [ ] Playlist support
- [ ] Quality presets per user
- [ ] Download statistics and analytics
- [ ] Multi-language support
- [ ] Download from private/password-protected videos

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for self-hosting purposes. Use responsibly and respect content creators' rights.

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs for error messages
- Open an issue on GitHub

## Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader
- [JDownloader](https://jdownloader.org/) - Download manager
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
