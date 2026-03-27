import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Add shared module to path
sys.path.append('/app/shared')

from config import config
from bot.middleware import AuthMiddleware
from bot.handlers import (
    register_user_handlers,
    register_admin_handlers,
    register_download_handlers
)

from database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(dp: Dispatcher):
    """Execute on startup"""
    logger.info("Bot is starting...")

    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    # Create necessary directories
    os.makedirs(config.download_path, exist_ok=True)
    os.makedirs(config.temp_path, exist_ok=True)
    os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
    os.makedirs('/app/data', exist_ok=True)

    logger.info("Bot started successfully!")
    logger.info(f"Admins: {config.admin_ids}")
    logger.info(f"Auto-approve: {config.auto_approve}")


async def on_shutdown(dp: Dispatcher):
    """Execute on shutdown"""
    logger.info("Bot is shutting down...")

    # Close bot session
    await dp.storage.close()
    await dp.storage.wait_closed()

    logger.info("Bot stopped")


def main():
    """Main function"""
    logger.info("Initializing bot...")

    # Create bot instance
    if config.use_local_bot_api:
        bot = Bot(token=config.bot_token, server=config.local_bot_api_url)
        logger.info(f"Using local bot API: {config.local_bot_api_url}")
    else:
        bot = Bot(token=config.bot_token)
        logger.info("Using official Telegram Bot API")

    # Create dispatcher
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Setup middleware
    dp.middleware.setup(AuthMiddleware())
    logger.info("Middleware configured")

    # Register handlers
    register_user_handlers(dp)
    register_admin_handlers(dp)
    register_download_handlers(dp)
    logger.info("Handlers registered")

    # Start bot
    try:
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
