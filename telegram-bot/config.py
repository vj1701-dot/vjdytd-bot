import os
from dataclasses import dataclass


@dataclass
class Config:
    """Bot configuration"""

    # Telegram
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash: str = os.getenv("TELEGRAM_API_HASH", "")

    # Admin
    admin_ids: list = None
    auto_approve: bool = os.getenv("AUTO_APPROVE", "false").lower() == "true"

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: str = os.getenv("REDIS_PASSWORD", None)

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/bot_data.db")

    # FastAPI
    fastapi_host: str = os.getenv("FASTAPI_HOST", "fastapi-service")
    fastapi_port: int = int(os.getenv("FASTAPI_PORT", 8000))

    # File handling
    max_file_size_telegram: int = int(os.getenv("MAX_FILE_SIZE_TELEGRAM", 2147483648))
    min_file_size: int = int(os.getenv("MIN_FILE_SIZE", 52428800))
    download_path: str = os.getenv("DOWNLOAD_PATH", "/downloads")
    temp_path: str = os.getenv("TEMP_PATH", "/downloads/temp")
    file_retention_hours: int = int(os.getenv("FILE_RETENTION_HOURS", 48))

    # Rate limiting
    max_concurrent_downloads_per_user: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS_PER_USER", 2))
    global_rate_limit: int = int(os.getenv("GLOBAL_RATE_LIMIT", 10))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "/logs/bot.log")

    # Optional: Local Bot API
    use_local_bot_api: bool = os.getenv("USE_LOCAL_BOT_API", "false").lower() == "true"
    local_bot_api_url: str = os.getenv("LOCAL_BOT_API_URL", "http://telegram-bot-api:8081")

    def __post_init__(self):
        """Process admin IDs"""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            self.admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        else:
            self.admin_ids = []

    def validate(self):
        """Validate configuration"""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        if not self.admin_ids:
            raise ValueError("At least one admin ID is required in ADMIN_IDS")

        return True


# Global config instance
config = Config()
