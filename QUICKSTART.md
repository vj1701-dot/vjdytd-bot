# Quick Start Guide

Get your bot running in 5 minutes! ⚡

## Prerequisites

You only need:
- A server (VPS, home server, etc.) running Linux
- Docker installed
- A Telegram account

## Step 1: Install Docker

If you don't have Docker installed:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add your user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER
newgrp docker
```

## Step 2: Get the Bot

```bash
# Clone the repository
git clone https://github.com/vj1701-dot/vjdytd-bot.git
cd vjdytd-bot

# Make setup script executable
chmod +x setup.sh update.sh
```

## Step 3: Get Required Credentials

### 3.1 Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name and username
4. **Copy the bot token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 3.2 Get Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Click on "API Development Tools"
4. Create an app (any name/description)
5. **Copy the `api_id` and `api_hash`**

### 3.3 Get Your Telegram User ID

1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Send `/start`
3. **Copy your user ID** (a number like: `123456789`)

## Step 4: Run Setup

```bash
./setup.sh
```

The script will ask you for:

**Required:**
- ✅ Telegram Bot Token (from step 3.1)
- ✅ Telegram API ID (from step 3.2)
- ✅ Telegram API Hash (from step 3.2)
- ✅ Your Telegram User ID (from step 3.3)

**Optional (you can skip these):**
- ❌ Auto-approve users → Recommended: **No**
- ❌ JDownloader setup → Recommended: **No** (yt-dlp works great!)
- ❌ GoFile API token → Recommended: **No** (works without token)

Just press Enter to use defaults for performance settings.

The script will:
1. Create your `.env` configuration file
2. Ask if you want to start the bot immediately
3. Start all services if you say yes

## Step 5: Test Your Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. You should see a welcome message!
5. Try sending a YouTube URL

## Common Commands

```bash
# View logs (see what's happening)
docker-compose logs -f telegram-bot

# Stop the bot
docker-compose down

# Start the bot
docker-compose up -d

# Update to latest version
./update.sh

# Restart a specific service
docker-compose restart telegram-bot

# Check if services are running
docker-compose ps
```

## Troubleshooting

### Bot doesn't respond

```bash
# Check if bot is running
docker-compose ps

# View logs
docker-compose logs telegram-bot

# Restart the bot
docker-compose restart telegram-bot
```

### Can't download videos

```bash
# Check FastAPI service logs
docker-compose logs fastapi-service

# Make sure yt-dlp is working
docker-compose exec fastapi-service yt-dlp --version
```

### Out of disk space

```bash
# Check disk usage
df -h

# Clean up old downloads (files are auto-deleted after 48h)
docker-compose restart cleanup-worker

# Or manually clean
docker system prune -a
```

## What's Next?

- **Add more admins**: Edit `.env` and add more user IDs to `ADMIN_IDS=123,456,789`
- **Change settings**: Edit `.env` and run `docker-compose restart`
- **View all commands**: Send `/help` to your bot
- **Monitor usage**: Check logs with `docker-compose logs -f`

## Advanced Features (Optional)

### Want to use JDownloader?

1. Create account at [my.jdownloader.org](https://my.jdownloader.org)
2. Run `./setup.sh` again and choose "Yes" for JDownloader
3. Or manually edit `.env` and add:
   ```
   JDOWNLOADER_EMAIL=your@email.com
   JDOWNLOADER_PASSWORD=yourpassword
   ```
4. Restart: `docker-compose restart`

### Want better external upload limits?

1. Create account at [gofile.io](https://gofile.io)
2. Get your API token from account settings
3. Add to `.env`: `GOFILE_API_TOKEN=your_token`
4. Restart: `docker-compose restart`

### Want to use PostgreSQL instead of SQLite?

1. Add to `docker-compose.yml`:
   ```yaml
   postgres:
     image: postgres:15-alpine
     environment:
       POSTGRES_DB: botdb
       POSTGRES_USER: botuser
       POSTGRES_PASSWORD: changeme
     volumes:
       - postgres_data:/var/lib/postgresql/data
   ```
2. Update `.env`: `DATABASE_URL=postgresql://botuser:changeme@postgres:5432/botdb`
3. Restart: `docker-compose down && docker-compose up -d`

## Need Help?

- Check the full [README.md](README.md)
- Check the [DEPLOYMENT.md](DEPLOYMENT.md) for advanced setup
- Open an issue on [GitHub](https://github.com/vj1701-dot/vjdytd-bot/issues)

## Summary

That's it! You now have a fully functional Telegram download bot that:
- ✅ Downloads videos and audio from YouTube and other platforms
- ✅ Handles files up to 2GB via Telegram
- ✅ Uploads larger files to GoFile
- ✅ Automatically cleans up after 48 hours
- ✅ Has admin controls for user management
- ✅ Caches files to save bandwidth

Enjoy! 🎉
