# Windows Server Setup Guide

Quick guide for setting up the Telegram bot on Windows Server.

## Prerequisites

1. **Windows Server** (2016, 2019, 2022) or Windows 10/11 Pro
2. **Docker Desktop for Windows** installed
3. **Git for Windows** installed

## Step 1: Install Required Software

### Install Docker Desktop

1. Download from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Run the installer
3. Restart your computer
4. Start Docker Desktop
5. Wait for Docker to be ready (whale icon in system tray)

### Install Git for Windows

1. Download from [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer (use default settings)
3. Git will be available in PowerShell

## Step 2: Clone the Repository

Open **PowerShell** (as Administrator):

```powershell
# Navigate to where you want the bot
cd C:\

# Clone the repository
git clone https://github.com/vj1701-dot/vjdytd-bot.git
cd vjdytd-bot
```

## Step 3: Get Required Credentials

Before running setup, gather these:

### 3.1 Telegram Bot Token
1. Open Telegram
2. Search for [@BotFather](https://t.me/BotFather)
3. Send `/newbot`
4. Follow instructions
5. **Copy the bot token**

### 3.2 Telegram API Credentials
1. Go to [my.telegram.org](https://my.telegram.org)
2. Login with your phone
3. Click "API Development Tools"
4. Create an app
5. **Copy `api_id` and `api_hash`**

### 3.3 Your Telegram User ID
1. Open Telegram
2. Search for [@userinfobot](https://t.me/userinfobot)
3. Send `/start`
4. **Copy your user ID**

### 3.4 (Optional) My.JDownloader Account
1. Go to [my.jdownloader.org](https://my.jdownloader.org)
2. Create free account
3. **Copy email and password**

## Step 4: Run Setup

In PowerShell (in the bot directory):

```powershell
.\setup.ps1
```

The script will ask for:
- ✅ Telegram Bot Token
- ✅ Telegram API ID & Hash
- ✅ Your Telegram User ID
- ✅ Enable Local Bot API? → **Yes** (for 2GB uploads)
- ❓ Set up JDownloader? → **Yes** if you have account
- ❓ GoFile token? → **No** (just press Enter)
- ❓ Start now? → **Yes**

## Step 5: Verify It's Running

```powershell
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f telegram-bot

# Press Ctrl+C to exit logs
```

## Common Commands

### Start the bot
```powershell
docker-compose up -d
```

### Stop the bot
```powershell
docker-compose down
```

### View logs
```powershell
docker-compose logs -f telegram-bot
```

### Update the bot
```powershell
.\update.ps1
```

### Restart a service
```powershell
docker-compose restart telegram-bot
```

### Check status
```powershell
docker-compose ps
```

## Troubleshooting

### Docker not starting

1. Enable Hyper-V:
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   ```

2. Enable WSL 2 (Windows Subsystem for Linux):
   ```powershell
   wsl --install
   ```

3. Restart computer

### Bot not responding

```powershell
# Check if running
docker-compose ps

# View errors
docker-compose logs telegram-bot

# Restart
docker-compose restart telegram-bot
```

### Can't download files

```powershell
# Check FastAPI service
docker-compose logs fastapi-service

# Restart it
docker-compose restart fastapi-service
```

### Out of disk space

```powershell
# Check disk usage
docker system df

# Clean up
docker system prune -a

# Restart cleanup worker
docker-compose restart cleanup-worker
```

## Firewall Configuration

If using Windows Firewall, you may need to allow Docker:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "Docker Desktop" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 6379,8000,5800
```

## Performance Tips

### For Better Performance:

1. **Use SSD** for downloads directory
2. **Allocate more resources** to Docker:
   - Open Docker Desktop
   - Settings → Resources
   - Increase CPU and Memory

3. **Disable Windows Defender** for downloads folder:
   ```powershell
   Add-MpPreference -ExclusionPath "C:\vjdytd-bot\downloads"
   ```

## Scheduled Tasks (Optional)

### Auto-start bot on system boot:

1. Open **Task Scheduler**
2. Create Basic Task
3. Name: "Telegram Bot Startup"
4. Trigger: "When the computer starts"
5. Action: "Start a program"
6. Program: `powershell.exe`
7. Arguments: `-File "C:\vjdytd-bot\start-bot.ps1"`

Create `start-bot.ps1`:
```powershell
cd C:\vjdytd-bot
docker-compose up -d
```

## Backup

### Backup your configuration:

```powershell
# Create backup directory
mkdir C:\bot-backups

# Backup .env
Copy-Item .env C:\bot-backups\.env-backup-$(Get-Date -Format 'yyyyMMdd').txt

# Backup database
docker-compose exec -T telegram-bot cat /app/data/bot_data.db > C:\bot-backups\bot_data-$(Get-Date -Format 'yyyyMMdd').db
```

## Getting Help

- Check [README.md](README.md)
- Check [QUICKSTART.md](QUICKSTART.md)
- Check [COMMANDS.md](COMMANDS.md)
- Open issue on [GitHub](https://github.com/vj1701-dot/vjdytd-bot/issues)

## Differences from Linux

| Feature | Linux | Windows |
|---------|-------|---------|
| Setup script | `./setup.sh` | `.\setup.ps1` |
| Update script | `./update.sh` | `.\update.ps1` |
| Path separator | `/` | `\` |
| Line endings | LF | CRLF (handled by Git) |
| Permissions | `chmod +x` | Not needed |

Everything else works the same! 🎉

## Next Steps

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Try downloading a YouTube URL

Enjoy! 🤖
