# Setup Checklist

Before running `./setup.sh`, gather these credentials:

## ✅ Required

### 1. Telegram Bot Token
- Go to [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot`
- Follow the instructions
- **Copy your bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Telegram API Credentials
- Go to [my.telegram.org](https://my.telegram.org)
- Login with your phone number
- Click "API Development Tools"
- Create an app (name: anything you want)
- **Copy `api_id`** (number like: `12345678`)
- **Copy `api_hash`** (string like: `0123456789abcdef0123456789abcdef`)

### 3. Your Telegram User ID
- Open Telegram
- Search for [@userinfobot](https://t.me/userinfobot)
- Send `/start`
- **Copy your ID** (number like: `123456789`)

---

## ⭐ Recommended

### 4. My.JDownloader Account
**For better download support and premium link sites**

- Go to [my.jdownloader.org](https://my.jdownloader.org)
- Click "Register"
- Create a free account
- **Copy your email and password**

---

## ❓ Optional (Not Needed)

### 5. GoFile API Token
**For better upload limits on files >2GB**

- Go to [gofile.io](https://gofile.io)
- Create account (optional)
- Get API token from account settings
- **Note: Bot works fine WITHOUT this!**

---

## 📋 Setup Answers

When you run `./setup.sh`, answer these questions:

| Question | Recommended Answer | Notes |
|----------|-------------------|-------|
| Telegram Bot Token | ✅ Paste your token | From @BotFather |
| Telegram API ID | ✅ Paste your api_id | From my.telegram.org |
| Telegram API Hash | ✅ Paste your api_hash | From my.telegram.org |
| Admin User ID | ✅ Paste your user ID | From @userinfobot |
| Enable Local Bot API? | **YES** | Upload files up to 2GB to Telegram |
| Auto-approve users? | **NO** | For security |
| Set up JDownloader? | **YES** if you have account | Better downloads |
| JDownloader Email | ✅ Your My.JDownloader email | If enabled |
| JDownloader Password | ✅ Your My.JDownloader password | If enabled |
| GoFile API Token? | **NO** (press Enter) | Not needed |
| Max concurrent downloads | **2** (press Enter) | Default is fine |
| File retention hours | **48** (press Enter) | Default is fine |
| Cleanup interval | **60** (press Enter) | Default is fine |
| Start bot now? | **YES** | Launch immediately |

---

## 🚀 Ready to Go?

Once you have gathered:
- ✅ Bot Token
- ✅ API ID & Hash
- ✅ Your User ID
- ✅ (Optional) JDownloader credentials

Run:
```bash
./setup.sh
```

The script will ask for everything in order and set up your bot automatically!

---

## 💡 What Happens During Setup

1. Script asks for your credentials
2. Creates `.env` configuration file
3. Enables Local Bot API (for 2GB uploads)
4. Configures JDownloader (if you want it)
5. Starts all Docker containers
6. Shows you the logs

**Total time: ~2-3 minutes**

---

## 🆘 Need Help?

- Read [QUICKSTART.md](QUICKSTART.md) for detailed instructions
- Read [README.md](README.md) for full documentation
- Open an issue on [GitHub](https://github.com/vj1701-dot/vjdytd-bot/issues)
