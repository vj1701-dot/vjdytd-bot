from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Command
import logging
import httpx
import os

import sys
sys.path.append('/app/shared')

from models import DownloadJob, JobStatus, FileCache
from database import get_db_session
from redis_client import redis_client
from utils import (
    generate_job_id, hash_url, is_valid_url, format_file_size,
    calculate_expiry
)

logger = logging.getLogger(__name__)

FASTAPI_URL = f"http://{os.getenv('FASTAPI_HOST', 'fastapi-service')}:{os.getenv('FASTAPI_PORT', '8000')}"


async def handle_download(message: types.Message, format_type: str = "video", quality: str = "best"):
    """Handle download requests"""
    user_id = message.from_user.id

    # Get URL from command args or just from message text
    url = message.get_args()
    if not url:
        # Try to extract URL from message text
        text = message.text or ""
        words = text.split()
        if len(words) > 1:
            url = words[1]
        else:
            await message.answer(
                "❌ Please provide a URL.\n\n"
                "Usage: /download <url>"
            )
            return

    # Validate URL
    if not is_valid_url(url):
        await message.answer("❌ Invalid URL. Please provide a valid HTTP/HTTPS URL.")
        return

    # Check rate limit
    max_concurrent = int(os.getenv("MAX_CONCURRENT_DOWNLOADS_PER_USER", 2))
    if not redis_client.check_rate_limit(user_id, max_concurrent):
        await message.answer(
            f"⚠️ You have reached your concurrent download limit ({max_concurrent}).\n"
            "Please wait for your current downloads to complete."
        )
        return

    # Check cache
    url_hash_key = hash_url(url, format_type, quality)
    db = get_db_session()

    try:
        cached_file = db.query(FileCache).filter(FileCache.url_hash == url_hash_key).first()

        if cached_file and os.path.exists(cached_file.file_path):
            await message.answer(
                "✅ This file was already downloaded!\n"
                "Retrieving from cache..."
            )

            # Reuse cached file
            from bot.utils.uploader import upload_file
            await upload_file(
                message=message,
                file_path=cached_file.file_path,
                file_size=cached_file.file_size,
                title=cached_file.title,
                telegram_file_id=cached_file.telegram_file_id
            )

            # Update cache hit count
            cached_file.hit_count += 1
            db.commit()
            return

        # Create new download job
        job_id = generate_job_id()

        new_job = DownloadJob(
            job_id=job_id,
            user_id=user_id,
            url=url,
            url_hash=url_hash_key,
            format_type=format_type,
            quality=quality,
            status=JobStatus.QUEUED,
            expires_at=calculate_expiry(48)
        )

        db.add(new_job)
        db.commit()

        # Add to Redis queue
        job_data = {
            "job_id": job_id,
            "user_id": user_id,
            "url": url,
            "format_type": format_type,
            "quality": quality,
        }

        redis_client.enqueue_job("download_queue", job_data)
        redis_client.add_user_job(user_id, job_id)

        await message.answer(
            f"✅ Download added to queue!\n\n"
            f"Job ID: {job_id[:8]}...\n"
            f"Format: {format_type}\n"
            f"Quality: {quality}\n\n"
            "You'll be notified when the download is ready.\n"
            "Use /status to check progress."
        )

        # Trigger download via FastAPI
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{FASTAPI_URL}/api/download",
                    json=job_data
                )
        except Exception as e:
            logger.error(f"Failed to trigger download: {e}")

    except Exception as e:
        logger.error(f"Error creating download job: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_download(message: types.Message):
    """Handle /download command"""
    await handle_download(message, format_type="video", quality="best")


async def cmd_audio(message: types.Message):
    """Handle /audio command"""
    await handle_download(message, format_type="audio", quality="best")


async def cmd_video(message: types.Message):
    """Handle /video command"""
    await handle_download(message, format_type="video", quality="best")


async def cmd_cancel(message: types.Message):
    """Cancel a download job"""
    job_id_arg = message.get_args()

    if not job_id_arg:
        await message.answer("Usage: /cancel <job_id>")
        return

    db = get_db_session()
    try:
        # Find jobs that start with the provided ID (allows short IDs)
        job = db.query(DownloadJob).filter(
            DownloadJob.user_id == message.from_user.id,
            DownloadJob.job_id.like(f"{job_id_arg}%")
        ).first()

        if not job:
            await message.answer("❌ Job not found or you don't have permission to cancel it.")
            return

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            await message.answer(f"❌ Cannot cancel a job that is already {job.status.value}.")
            return

        # Update job status
        job.status = JobStatus.CANCELLED
        db.commit()

        # Remove from active jobs
        redis_client.remove_user_job(message.from_user.id, job.job_id)

        await message.answer(f"✅ Download cancelled: {job.job_id[:8]}...")

    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_retry(message: types.Message):
    """Retry a failed download"""
    job_id_arg = message.get_args()

    if not job_id_arg:
        await message.answer("Usage: /retry <job_id>")
        return

    db = get_db_session()
    try:
        job = db.query(DownloadJob).filter(
            DownloadJob.user_id == message.from_user.id,
            DownloadJob.job_id.like(f"{job_id_arg}%")
        ).first()

        if not job:
            await message.answer("❌ Job not found.")
            return

        if job.status != JobStatus.FAILED:
            await message.answer("❌ Only failed jobs can be retried.")
            return

        # Check rate limit
        max_concurrent = int(os.getenv("MAX_CONCURRENT_DOWNLOADS_PER_USER", 2))
        if not redis_client.check_rate_limit(message.from_user.id, max_concurrent):
            await message.answer(
                f"⚠️ You have reached your concurrent download limit ({max_concurrent}).\n"
                "Please wait for your current downloads to complete."
            )
            return

        # Reset job
        job.status = JobStatus.QUEUED
        job.progress = 0.0
        job.retry_count += 1
        job.error_message = None
        db.commit()

        # Re-add to queue
        job_data = {
            "job_id": job.job_id,
            "user_id": job.user_id,
            "url": job.url,
            "format_type": job.format_type,
            "quality": job.quality,
        }

        redis_client.enqueue_job("download_queue", job_data)
        redis_client.add_user_job(message.from_user.id, job.job_id)

        await message.answer(f"✅ Download queued for retry: {job.job_id[:8]}...")

        # Trigger download
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{FASTAPI_URL}/api/download",
                    json=job_data
                )
        except Exception as e:
            logger.error(f"Failed to trigger retry: {e}")

    except Exception as e:
        logger.error(f"Error retrying job: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_formats(message: types.Message):
    """Show available formats for a URL"""
    url = message.get_args()

    if not url or not is_valid_url(url):
        await message.answer("❌ Please provide a valid URL.\n\nUsage: /formats <url>")
        return

    await message.answer("🔍 Fetching available formats...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{FASTAPI_URL}/api/formats",
                json={"url": url}
            )

            if response.status_code == 200:
                data = response.json()
                formats = data.get("formats", [])

                if not formats:
                    await message.answer("❌ No formats found for this URL.")
                    return

                text = f"📋 Available formats:\n\n"
                text += f"Title: {data.get('title', 'Unknown')}\n"
                text += f"Duration: {data.get('duration', 'Unknown')}\n\n"

                # Show top 10 formats
                for fmt in formats[:10]:
                    text += (
                        f"Format: {fmt.get('format_id', 'N/A')}\n"
                        f"Quality: {fmt.get('quality', 'N/A')}\n"
                        f"Extension: {fmt.get('ext', 'N/A')}\n"
                        f"Size: {format_file_size(fmt.get('filesize', 0)) if fmt.get('filesize') else 'Unknown'}\n\n"
                    )

                await message.answer(text)
            else:
                await message.answer("❌ Failed to fetch formats.")

    except Exception as e:
        logger.error(f"Error fetching formats: {e}")
        await message.answer("❌ Error fetching formats. Please try again later.")


async def handle_direct_url(message: types.Message):
    """Handle direct URL messages (without command)"""
    text = message.text or ""

    if is_valid_url(text):
        await message.answer(
            "📥 URL detected! What would you like to do?\n\n"
            "Choose an option:",
            reply_markup=types.InlineKeyboardMarkup(row_width=2).add(
                types.InlineKeyboardButton("🎬 Download Video", callback_data=f"dl_video:{text}"),
                types.InlineKeyboardButton("🎵 Download Audio", callback_data=f"dl_audio:{text}"),
                types.InlineKeyboardButton("ℹ️ Show Formats", callback_data=f"dl_formats:{text}"),
            )
        )


async def handle_download_callback(callback_query: types.CallbackQuery):
    """Handle download callback buttons"""
    data = callback_query.data
    action, url = data.split(":", 1)

    if action == "dl_video":
        await callback_query.message.answer(f"⬇️ Downloading video from:\n{url}")
        # Create a temporary message object with the URL
        temp_msg = callback_query.message
        temp_msg.text = f"/download {url}"
        await handle_download(temp_msg, format_type="video", quality="best")

    elif action == "dl_audio":
        await callback_query.message.answer(f"🎵 Downloading audio from:\n{url}")
        temp_msg = callback_query.message
        temp_msg.text = f"/audio {url}"
        await handle_download(temp_msg, format_type="audio", quality="best")

    elif action == "dl_formats":
        temp_msg = callback_query.message
        temp_msg.text = f"/formats {url}"
        await cmd_formats(temp_msg)

    await callback_query.answer()


def register_download_handlers(dp: Dispatcher):
    """Register download command handlers"""
    dp.register_message_handler(cmd_download, Command("download"))
    dp.register_message_handler(cmd_audio, Command("audio"))
    dp.register_message_handler(cmd_video, Command("video"))
    dp.register_message_handler(cmd_cancel, Command("cancel"))
    dp.register_message_handler(cmd_retry, Command("retry"))
    dp.register_message_handler(cmd_formats, Command("formats"))

    # Handle direct URLs
    dp.register_message_handler(
        handle_direct_url,
        lambda message: message.text and is_valid_url(message.text)
    )

    # Callback handlers
    dp.register_callback_query_handler(
        handle_download_callback,
        lambda c: c.data and c.data.startswith(("dl_video:", "dl_audio:", "dl_formats:"))
    )
