import hashlib
import uuid
import os
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def generate_job_id() -> str:
    """Generate a unique job ID"""
    return str(uuid.uuid4())


def hash_url(url: str, format_type: str = "video", quality: str = "best") -> str:
    """Generate a hash for URL + format + quality for caching"""
    combined = f"{url}:{format_type}:{quality}"
    return hashlib.sha256(combined.encode()).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def calculate_expiry(hours: int = 48) -> datetime:
    """Calculate expiry datetime"""
    return datetime.utcnow() + timedelta(hours=hours)


def is_expired(expiry_time: Optional[datetime]) -> bool:
    """Check if a datetime has expired"""
    if not expiry_time:
        return False
    return datetime.utcnow() > expiry_time


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Limit filename length
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    return filename


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def is_video_file(filename: str) -> bool:
    """Check if file is a video"""
    video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"]
    return get_file_extension(filename) in video_extensions


def is_audio_file(filename: str) -> bool:
    """Check if file is audio"""
    audio_extensions = [".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wav"]
    return get_file_extension(filename) in audio_extensions


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in HH:MM:SS"""
    if not seconds:
        return "Unknown"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def get_download_path(job_id: str, filename: str) -> str:
    """Get full download path for a job"""
    download_dir = os.getenv("DOWNLOAD_PATH", "/downloads")
    job_dir = os.path.join(download_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)
    return os.path.join(job_dir, sanitize_filename(filename))


def get_temp_path(job_id: str) -> str:
    """Get temporary download path for a job"""
    temp_dir = os.getenv("TEMP_PATH", "/downloads/temp")
    job_temp = os.path.join(temp_dir, job_id)
    os.makedirs(job_temp, exist_ok=True)
    return job_temp


def cleanup_job_files(job_id: str) -> bool:
    """Delete all files associated with a job"""
    try:
        download_dir = os.getenv("DOWNLOAD_PATH", "/downloads")
        job_dir = os.path.join(download_dir, job_id)

        if os.path.exists(job_dir):
            import shutil
            shutil.rmtree(job_dir)
            logger.info(f"Cleaned up files for job {job_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup job files: {e}")
        return False


def parse_telegram_user(user_obj) -> dict:
    """Parse Telegram user object to dict"""
    return {
        "telegram_id": user_obj.id,
        "username": user_obj.username,
        "first_name": user_obj.first_name,
        "last_name": user_obj.last_name,
    }


def is_valid_url(url: str) -> bool:
    """Basic URL validation"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None
