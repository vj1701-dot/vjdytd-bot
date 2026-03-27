import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta

# Add shared module to path
sys.path.append('/app/shared')

from database import get_db_session, init_db
from models import DownloadJob, FileCache, JobStatus
from utils import cleanup_job_files, is_expired

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/cleanup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def cleanup_expired_files():
    """Clean up expired download files"""
    logger.info("Starting cleanup of expired files...")

    db = get_db_session()
    cleaned_count = 0

    try:
        # Get expired jobs
        now = datetime.utcnow()
        expired_jobs = db.query(DownloadJob).filter(
            DownloadJob.expires_at <= now,
            DownloadJob.file_path.isnot(None)
        ).all()

        logger.info(f"Found {len(expired_jobs)} expired jobs")

        for job in expired_jobs:
            try:
                # Clean up files
                if cleanup_job_files(job.job_id):
                    logger.info(f"Cleaned up files for job {job.job_id}")

                    # Update job record (remove file path)
                    job.file_path = None
                    db.commit()

                    cleaned_count += 1

            except Exception as e:
                logger.error(f"Failed to cleanup job {job.job_id}: {e}")

        logger.info(f"Cleanup completed. Cleaned {cleaned_count} jobs.")

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    finally:
        db.close()


def cleanup_expired_cache():
    """Clean up expired cache entries"""
    logger.info("Starting cleanup of expired cache...")

    db = get_db_session()
    cleaned_count = 0

    try:
        # Get expired cache entries
        now = datetime.utcnow()
        expired_cache = db.query(FileCache).filter(
            FileCache.expires_at <= now
        ).all()

        logger.info(f"Found {len(expired_cache)} expired cache entries")

        for cache in expired_cache:
            try:
                # Check if file exists and delete it
                if os.path.exists(cache.file_path):
                    os.remove(cache.file_path)
                    logger.info(f"Deleted cached file: {cache.file_path}")

                # Delete cache entry
                db.delete(cache)
                db.commit()

                cleaned_count += 1

            except Exception as e:
                logger.error(f"Failed to cleanup cache entry {cache.id}: {e}")

        logger.info(f"Cache cleanup completed. Cleaned {cleaned_count} entries.")

    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
    finally:
        db.close()


def cleanup_failed_jobs():
    """Clean up old failed jobs (older than 7 days)"""
    logger.info("Starting cleanup of old failed jobs...")

    db = get_db_session()
    cleaned_count = 0

    try:
        # Get old failed jobs (older than 7 days)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_failed_jobs = db.query(DownloadJob).filter(
            DownloadJob.status == JobStatus.FAILED,
            DownloadJob.created_at <= cutoff_date
        ).all()

        logger.info(f"Found {len(old_failed_jobs)} old failed jobs")

        for job in old_failed_jobs:
            try:
                # Clean up any remaining files
                cleanup_job_files(job.job_id)

                # Delete job record
                db.delete(job)
                db.commit()

                cleaned_count += 1

            except Exception as e:
                logger.error(f"Failed to cleanup failed job {job.job_id}: {e}")

        logger.info(f"Failed jobs cleanup completed. Cleaned {cleaned_count} jobs.")

    except Exception as e:
        logger.error(f"Failed jobs cleanup error: {e}")
    finally:
        db.close()


def cleanup_orphaned_files():
    """Clean up orphaned files in downloads directory"""
    logger.info("Starting cleanup of orphaned files...")

    download_path = os.getenv("DOWNLOAD_PATH", "/downloads")
    temp_path = os.getenv("TEMP_PATH", "/downloads/temp")

    cleaned_count = 0

    try:
        # Get all job directories
        if os.path.exists(download_path):
            for item in os.listdir(download_path):
                item_path = os.path.join(download_path, item)

                if os.path.isdir(item_path) and item != "temp":
                    # Check if this job exists in database
                    db = get_db_session()
                    try:
                        job = db.query(DownloadJob).filter(
                            DownloadJob.job_id == item
                        ).first()

                        if not job:
                            # Orphaned directory - delete it
                            import shutil
                            shutil.rmtree(item_path)
                            logger.info(f"Deleted orphaned directory: {item_path}")
                            cleaned_count += 1

                    except Exception as e:
                        logger.error(f"Error checking job {item}: {e}")
                    finally:
                        db.close()

        logger.info(f"Orphaned files cleanup completed. Cleaned {cleaned_count} directories.")

    except Exception as e:
        logger.error(f"Orphaned files cleanup error: {e}")


def run_all_cleanup_tasks():
    """Run all cleanup tasks"""
    logger.info("=" * 50)
    logger.info("Starting scheduled cleanup run")
    logger.info("=" * 50)

    cleanup_expired_files()
    cleanup_expired_cache()
    cleanup_failed_jobs()
    cleanup_orphaned_files()

    logger.info("=" * 50)
    logger.info("Cleanup run completed")
    logger.info("=" * 50)


def main():
    """Main worker function"""
    logger.info("Cleanup worker starting...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    # Get cleanup interval from environment (default 60 minutes)
    cleanup_interval_minutes = int(os.getenv("CLEANUP_INTERVAL_MINUTES", 60))

    logger.info(f"Cleanup interval: {cleanup_interval_minutes} minutes")

    # Schedule cleanup tasks
    schedule.every(cleanup_interval_minutes).minutes.do(run_all_cleanup_tasks)

    # Run immediately on startup
    run_all_cleanup_tasks()

    # Run scheduler
    logger.info("Cleanup worker running. Waiting for scheduled tasks...")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Cleanup worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Cleanup worker error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
