from aiogram import types, Bot
from typing import Optional
import os
import logging

import sys
sys.path.append('/app/shared')

from utils import format_file_size, is_video_file, is_audio_file
from .external_upload import upload_to_external_service

logger = logging.getLogger(__name__)

MAX_TELEGRAM_SIZE = int(os.getenv("MAX_FILE_SIZE_TELEGRAM", 2147483648))  # 2GB


async def upload_file(
    message: types.Message,
    file_path: str,
    file_size: int,
    title: Optional[str] = None,
    duration: Optional[int] = None,
    thumbnail_path: Optional[str] = None,
    telegram_file_id: Optional[str] = None
) -> dict:
    """
    Upload file to Telegram or external service based on size

    Returns:
        dict with keys: success, telegram_file_id, external_link, external_provider
    """

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        await message.answer("❌ Error: Downloaded file not found.")
        return {"success": False}

    # If we have a cached telegram_file_id and file is under limit, reuse it
    if telegram_file_id and file_size <= MAX_TELEGRAM_SIZE:
        try:
            logger.info(f"Reusing cached file_id: {telegram_file_id}")
            # Determine file type
            if is_video_file(file_path):
                await message.answer_video(
                    telegram_file_id,
                    caption=f"✅ {title or 'Download complete'}\n\nSize: {format_file_size(file_size)}"
                )
            elif is_audio_file(file_path):
                await message.answer_audio(
                    telegram_file_id,
                    caption=f"✅ {title or 'Download complete'}\n\nSize: {format_file_size(file_size)}"
                )
            else:
                await message.answer_document(
                    telegram_file_id,
                    caption=f"✅ {title or 'Download complete'}\n\nSize: {format_file_size(file_size)}"
                )

            return {
                "success": True,
                "telegram_file_id": telegram_file_id,
                "external_link": None,
                "external_provider": None
            }
        except Exception as e:
            logger.warning(f"Failed to reuse file_id: {e}. Uploading fresh copy.")

    # Check file size
    if file_size > MAX_TELEGRAM_SIZE:
        logger.info(f"File too large for Telegram ({format_file_size(file_size)}). Using external upload.")
        return await upload_large_file(message, file_path, file_size, title)

    # Upload to Telegram
    try:
        return await upload_to_telegram(message, file_path, file_size, title, duration, thumbnail_path)
    except Exception as e:
        logger.error(f"Telegram upload failed: {e}")

        # Fallback to external upload
        if os.getenv("UPLOAD_FALLBACK_ENABLED", "true").lower() == "true":
            logger.info("Falling back to external upload")
            await message.answer("⚠️ Telegram upload failed. Uploading to external service...")
            return await upload_large_file(message, file_path, file_size, title)
        else:
            await message.answer("❌ Upload failed. Please try again later.")
            return {"success": False}


async def upload_to_telegram(
    message: types.Message,
    file_path: str,
    file_size: int,
    title: Optional[str] = None,
    duration: Optional[int] = None,
    thumbnail_path: Optional[str] = None
) -> dict:
    """Upload file to Telegram"""

    caption = f"✅ {title or 'Download complete'}\n\nSize: {format_file_size(file_size)}"

    if duration:
        caption += f"\nDuration: {duration // 60}:{duration % 60:02d}"

    try:
        with open(file_path, 'rb') as file:
            # Determine file type and upload accordingly
            if is_video_file(file_path):
                logger.info(f"Uploading video: {file_path}")

                sent_message = await message.answer_video(
                    types.InputFile(file),
                    caption=caption,
                    duration=duration,
                    supports_streaming=True
                )

                return {
                    "success": True,
                    "telegram_file_id": sent_message.video.file_id,
                    "external_link": None,
                    "external_provider": None
                }

            elif is_audio_file(file_path):
                logger.info(f"Uploading audio: {file_path}")

                sent_message = await message.answer_audio(
                    types.InputFile(file),
                    caption=caption,
                    duration=duration,
                    title=title
                )

                return {
                    "success": True,
                    "telegram_file_id": sent_message.audio.file_id,
                    "external_link": None,
                    "external_provider": None
                }

            else:
                logger.info(f"Uploading document: {file_path}")

                sent_message = await message.answer_document(
                    types.InputFile(file),
                    caption=caption
                )

                return {
                    "success": True,
                    "telegram_file_id": sent_message.document.file_id,
                    "external_link": None,
                    "external_provider": None
                }

    except Exception as e:
        logger.error(f"Telegram upload error: {e}")
        raise


async def upload_large_file(
    message: types.Message,
    file_path: str,
    file_size: int,
    title: Optional[str] = None
) -> dict:
    """Upload large file to external service"""

    await message.answer(
        f"📦 File is too large for Telegram ({format_file_size(file_size)}).\n"
        "Uploading to external service..."
    )

    try:
        result = await upload_to_external_service(file_path, file_size)

        if result["success"]:
            expiry_text = ""
            if result.get("expiry_date"):
                expiry_text = f"\n⏰ Link expires: {result['expiry_date']}"

            await message.answer(
                f"✅ {title or 'Upload complete'}!\n\n"
                f"📊 Size: {format_file_size(file_size)}\n"
                f"🔗 Download link:\n{result['link']}\n"
                f"{expiry_text}\n\n"
                f"Provider: {result['provider']}"
            )

            return {
                "success": True,
                "telegram_file_id": None,
                "external_link": result["link"],
                "external_provider": result["provider"],
                "external_expiry": result.get("expiry_date")
            }
        else:
            await message.answer(
                f"❌ External upload failed: {result.get('error', 'Unknown error')}"
            )
            return {"success": False}

    except Exception as e:
        logger.error(f"External upload error: {e}")
        await message.answer(f"❌ Upload failed: {str(e)}")
        return {"success": False}


async def send_progress_update(bot: Bot, chat_id: int, job_id: str, progress: float, status: str):
    """Send progress update to user"""
    try:
        progress_bar = create_progress_bar(progress)
        await bot.send_message(
            chat_id,
            f"📊 Download Progress\n\n"
            f"Job ID: {job_id[:8]}...\n"
            f"Status: {status}\n\n"
            f"{progress_bar} {progress:.1f}%"
        )
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")


def create_progress_bar(progress: float, length: int = 20) -> str:
    """Create a visual progress bar"""
    filled = int(length * progress / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"
