from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import os

import sys
sys.path.append('/app/shared')

from models import User, UserStatus, DownloadJob, JobStatus
from database import get_db_session

logger = logging.getLogger(__name__)


async def cmd_start(message: types.Message, user_status: UserStatus, is_admin: bool, new_user: bool = False):
    """Handle /start command"""

    if new_user:
        # New user notification to admins
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

            # Create inline keyboard for quick approval
            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_user:{message.from_user.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_user:{message.from_user.id}"),
                InlineKeyboardButton("🚫 Ban", callback_data=f"ban_user:{message.from_user.id}"),
            )

            notification = (
                f"🔔 New user request:\n\n"
                f"ID: {message.from_user.id}\n"
                f"Name: {message.from_user.first_name} {message.from_user.last_name or ''}\n"
                f"Username: @{message.from_user.username if message.from_user.username else 'N/A'}\n"
            )

            for admin_id in admin_ids:
                try:
                    await message.bot.send_message(admin_id, notification, reply_markup=keyboard)
                except Exception as e:
                    logger.warning(f"Could not notify admin {admin_id}: {e}")

        return  # Don't show start message to pending users

    if user_status == UserStatus.PENDING:
        await message.answer(
            "⏳ Your account is pending approval.\n"
            "An admin will review your request shortly."
        )
        return

    welcome_text = (
        "👋 Welcome to the Video/Audio Downloader Bot!\n\n"
        "I can help you download videos and audio from various platforms.\n\n"
        "📝 Available commands:\n"
        "/help - Show help message\n"
        "/download <url> - Download video/audio\n"
        "/audio <url> - Download audio only\n"
        "/video <url> - Download video\n"
        "/status - Check your active downloads\n"
        "/queue - View download queue\n"
        "/cancel <job_id> - Cancel a download\n\n"
    )

    if is_admin:
        welcome_text += (
            "👑 Admin commands:\n"
            "/pending - View pending users\n"
            "/approve <user_id> - Approve a user\n"
            "/reject <user_id> - Reject a user\n"
            "/ban <user_id> - Ban a user\n"
            "/users - List all approved users\n"
            "/banned - List banned users\n"
            "/remove <user_id> - Remove a user\n\n"
        )

    welcome_text += "Just send me a URL to get started!"

    await message.answer(welcome_text)


async def cmd_help(message: types.Message, is_admin: bool):
    """Handle /help command"""
    help_text = (
        "📖 Bot Help\n\n"
        "🎬 Download Commands:\n"
        "/download <url> - Download video/audio (best quality)\n"
        "/audio <url> - Download audio only\n"
        "/video <url> - Download video with audio\n\n"
        "📊 Status Commands:\n"
        "/status - Check your active downloads\n"
        "/queue - View your download queue\n"
        "/list - List your recent downloads\n\n"
        "🔧 Control Commands:\n"
        "/cancel <job_id> - Cancel a download\n"
        "/retry <job_id> - Retry a failed download\n\n"
        "ℹ️ Information Commands:\n"
        "/formats <url> - Show available formats\n"
        "/quality - Set default quality preference\n\n"
        "📏 File Size Limits:\n"
        "• Files up to 2GB: Uploaded to Telegram\n"
        "• Files over 2GB: Provided as external link\n\n"
    )

    if is_admin:
        help_text += (
            "\n👑 Admin Commands:\n"
            "/pending - View pending user requests\n"
            "/approve <user_id> - Approve a user\n"
            "/reject <user_id> - Reject a user\n"
            "/ban <user_id> - Ban a user\n"
            "/users - List all approved users\n"
            "/banned - List banned users\n"
            "/remove <user_id> - Remove a user from database\n"
        )

    await message.answer(help_text)


async def cmd_status(message: types.Message):
    """Show user's active downloads"""
    db = get_db_session()
    try:
        jobs = db.query(DownloadJob).filter(
            DownloadJob.user_id == message.from_user.id,
            DownloadJob.status.in_([JobStatus.QUEUED, JobStatus.DOWNLOADING, JobStatus.PROCESSING, JobStatus.UPLOADING])
        ).all()

        if not jobs:
            await message.answer("You have no active downloads.")
            return

        text = "📊 Your Active Downloads:\n\n"
        for job in jobs:
            status_emoji = {
                JobStatus.QUEUED: "⏳",
                JobStatus.DOWNLOADING: "⬇️",
                JobStatus.PROCESSING: "⚙️",
                JobStatus.UPLOADING: "⬆️",
            }.get(job.status, "❓")

            text += (
                f"{status_emoji} {job.status.value.upper()}\n"
                f"Job ID: {job.job_id[:8]}...\n"
                f"Title: {job.title or 'Fetching...'}\n"
                f"Progress: {job.progress:.1f}%\n"
                f"Started: {job.created_at.strftime('%H:%M:%S')}\n\n"
            )

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        await message.answer("❌ Error retrieving status.")
    finally:
        db.close()


async def cmd_queue(message: types.Message):
    """Show user's download queue"""
    db = get_db_session()
    try:
        jobs = db.query(DownloadJob).filter(
            DownloadJob.user_id == message.from_user.id,
            DownloadJob.status == JobStatus.QUEUED
        ).order_by(DownloadJob.created_at).all()

        if not jobs:
            await message.answer("Your download queue is empty.")
            return

        text = f"📋 Download Queue ({len(jobs)} items):\n\n"
        for idx, job in enumerate(jobs, 1):
            text += (
                f"{idx}. {job.title or job.url[:50]}\n"
                f"   Job ID: {job.job_id[:8]}...\n"
                f"   Queued: {job.created_at.strftime('%H:%M:%S')}\n\n"
            )

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        await message.answer("❌ Error retrieving queue.")
    finally:
        db.close()


async def cmd_list(message: types.Message):
    """List user's recent downloads"""
    db = get_db_session()
    try:
        jobs = db.query(DownloadJob).filter(
            DownloadJob.user_id == message.from_user.id,
            DownloadJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED])
        ).order_by(DownloadJob.completed_at.desc()).limit(10).all()

        if not jobs:
            await message.answer("You have no recent downloads.")
            return

        text = "📜 Recent Downloads:\n\n"
        for job in jobs:
            status_emoji = "✅" if job.status == JobStatus.COMPLETED else "❌"
            text += (
                f"{status_emoji} {job.title or job.url[:40]}\n"
                f"   Job ID: {job.job_id[:8]}...\n"
                f"   Completed: {job.completed_at.strftime('%Y-%m-%d %H:%M') if job.completed_at else 'N/A'}\n"
            )

            if job.status == JobStatus.COMPLETED:
                if job.external_link:
                    text += f"   Link: {job.external_link}\n"
                text += f"   Size: {job.file_size / (1024**3):.2f} GB\n" if job.file_size else ""

            text += "\n"

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error listing downloads: {e}")
        await message.answer("❌ Error retrieving downloads.")
    finally:
        db.close()


async def handle_unknown_command(message: types.Message):
    """Handle unknown commands"""
    await message.answer(
        "❓ Unknown command. Use /help to see available commands."
    )


def register_user_handlers(dp: Dispatcher):
    """Register user command handlers"""
    dp.register_message_handler(cmd_start, Command("start"))
    dp.register_message_handler(cmd_help, Command("help"))
    dp.register_message_handler(cmd_status, Command("status"))
    dp.register_message_handler(cmd_queue, Command("queue"))
    dp.register_message_handler(cmd_list, Command("list"))
