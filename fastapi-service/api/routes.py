from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import logging
import os
import yt_dlp
import asyncio

import sys
sys.path.append('/app/shared')

from services.jdownloader import jdownloader_service
from models import DownloadJob, JobStatus
from database import get_db_session
from redis_client import redis_client
from utils import get_download_path, get_temp_path, format_file_size

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["downloads"])


class DownloadRequest(BaseModel):
    job_id: str
    user_id: int
    url: str
    format_type: str = "video"
    quality: str = "best"


class FormatRequest(BaseModel):
    url: str


class StatusRequest(BaseModel):
    job_id: str


@router.post("/download")
async def initiate_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Initiate a download"""
    logger.info(f"Received download request for job {request.job_id}")

    # Add download task to background
    background_tasks.add_task(process_download, request)

    return {
        "success": True,
        "job_id": request.job_id,
        "message": "Download initiated"
    }


@router.post("/formats")
async def get_formats(request: FormatRequest):
    """Get available formats for a URL using yt-dlp"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)

            formats = info.get('formats', [])
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            # Format the response
            format_list = []
            for fmt in formats:
                format_list.append({
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'quality': fmt.get('format_note'),
                    'filesize': fmt.get('filesize'),
                    'tbr': fmt.get('tbr'),
                    'resolution': fmt.get('resolution'),
                })

            return {
                "success": True,
                "title": title,
                "duration": duration,
                "formats": format_list[:20]  # Limit to 20 formats
            }

    except Exception as e:
        logger.error(f"Failed to get formats: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{job_id}")
async def get_download_status(job_id: str):
    """Get download status for a job"""
    db = get_db_session()

    try:
        job = db.query(DownloadJob).filter(DownloadJob.job_id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "success": True,
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "file_name": job.file_name,
            "file_size": job.file_size,
            "error": job.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    jd_status = "connected" if jdownloader_service.is_connected() else "disconnected"

    return {
        "status": "healthy",
        "jdownloader": jd_status,
        "redis": redis_client.ping()
    }


# Background task to process downloads
async def process_download(request: DownloadRequest):
    """Process download using yt-dlp (fallback) or JDownloader"""
    db = get_db_session()

    try:
        # Get job from database
        job = db.query(DownloadJob).filter(DownloadJob.job_id == request.job_id).first()

        if not job:
            logger.error(f"Job {request.job_id} not found")
            return

        # Update status
        job.status = JobStatus.DOWNLOADING
        db.commit()

        # Set up download path
        download_dir = get_temp_path(request.job_id)

        # Try JDownloader first
        jd_result = jdownloader_service.add_links([request.url], download_dir)

        if jd_result.get("success"):
            logger.info(f"Download initiated via JDownloader for job {request.job_id}")
            # Monitor JDownloader progress in a separate task
            await monitor_jdownloader_download(request.job_id, db)

        else:
            logger.warning(f"JDownloader failed, falling back to yt-dlp for job {request.job_id}")
            # Fallback to yt-dlp
            await download_with_ytdlp(request, job, download_dir, db)

    except Exception as e:
        logger.error(f"Download processing failed for job {request.job_id}: {e}")

        # Update job status
        job = db.query(DownloadJob).filter(DownloadJob.job_id == request.job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            db.commit()

    finally:
        db.close()
        # Remove from active jobs
        redis_client.remove_user_job(request.user_id, request.job_id)


async def download_with_ytdlp(request: DownloadRequest, job: DownloadJob, download_dir: str, db):
    """Download using yt-dlp"""

    def progress_hook(d):
        """Progress callback for yt-dlp"""
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip('%')
                progress = float(percent)

                # Update progress in Redis and DB
                redis_client.set_progress(request.job_id, progress)

                job.progress = progress
                db.commit()

            except Exception as e:
                logger.error(f"Progress hook error: {e}")

        elif d['status'] == 'finished':
            logger.info(f"Download finished for job {request.job_id}")

    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if request.format_type == 'video' else 'bestaudio/best',
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': False,
    }

    if request.format_type == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)

            # Get downloaded file info
            filename = ydl.prepare_filename(info)
            if request.format_type == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0

            # Update job
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.file_name = os.path.basename(filename)
            job.file_path = filename
            job.file_size = file_size
            job.title = info.get('title')
            job.duration = info.get('duration')
            db.commit()

            logger.info(f"Download completed for job {request.job_id}")

            # Notify user via bot (would need to implement this)
            # For now, just log
            logger.info(f"File ready: {filename} ({format_file_size(file_size)})")

    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.commit()


async def monitor_jdownloader_download(job_id: str, db):
    """Monitor JDownloader download progress"""
    # This is a simplified version - you'd need to implement proper monitoring
    # based on JDownloader's package tracking
    pass
