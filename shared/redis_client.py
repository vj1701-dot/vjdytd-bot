import redis
import json
import os
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for queue and state management"""

    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password if self.password else None,
            decode_responses=True,
        )

    def ping(self) -> bool:
        """Check if Redis is available"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    # Queue operations
    def enqueue_job(self, queue_name: str, job_data: Dict[str, Any]) -> bool:
        """Add a job to the queue"""
        try:
            self.client.rpush(queue_name, json.dumps(job_data))
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False

    def dequeue_job(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Get a job from the queue (blocking)"""
        try:
            result = self.client.blpop(queue_name, timeout=timeout)
            if result:
                _, job_data = result
                return json.loads(job_data)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    def get_queue_length(self, queue_name: str) -> int:
        """Get the number of jobs in queue"""
        try:
            return self.client.llen(queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0

    # State management
    def set_job_state(self, job_id: str, state: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set job state"""
        try:
            key = f"job:{job_id}"
            self.client.set(key, json.dumps(state))
            if ttl:
                self.client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set job state: {e}")
            return False

    def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job state"""
        try:
            key = f"job:{job_id}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get job state: {e}")
            return None

    def delete_job_state(self, job_id: str) -> bool:
        """Delete job state"""
        try:
            key = f"job:{job_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete job state: {e}")
            return False

    # Progress tracking
    def set_progress(self, job_id: str, progress: float) -> bool:
        """Set job progress (0-100)"""
        try:
            key = f"progress:{job_id}"
            self.client.set(key, progress, ex=3600)  # 1 hour TTL
            return True
        except Exception as e:
            logger.error(f"Failed to set progress: {e}")
            return False

    def get_progress(self, job_id: str) -> Optional[float]:
        """Get job progress"""
        try:
            key = f"progress:{job_id}"
            progress = self.client.get(key)
            if progress:
                return float(progress)
            return None
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return None

    # User rate limiting
    def check_rate_limit(self, user_id: int, max_concurrent: int = 2) -> bool:
        """Check if user has reached their concurrent download limit"""
        try:
            key = f"user:{user_id}:active"
            count = self.client.scard(key)
            return count < max_concurrent
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False

    def add_user_job(self, user_id: int, job_id: str) -> bool:
        """Add job to user's active jobs"""
        try:
            key = f"user:{user_id}:active"
            self.client.sadd(key, job_id)
            self.client.expire(key, 86400)  # 24 hours
            return True
        except Exception as e:
            logger.error(f"Failed to add user job: {e}")
            return False

    def remove_user_job(self, user_id: int, job_id: str) -> bool:
        """Remove job from user's active jobs"""
        try:
            key = f"user:{user_id}:active"
            self.client.srem(key, job_id)
            return True
        except Exception as e:
            logger.error(f"Failed to remove user job: {e}")
            return False

    def get_user_active_jobs(self, user_id: int) -> list:
        """Get user's active job IDs"""
        try:
            key = f"user:{user_id}:active"
            return list(self.client.smembers(key))
        except Exception as e:
            logger.error(f"Failed to get user active jobs: {e}")
            return []

    # Cache operations
    def set_cache(self, key: str, value: Any, ttl: int) -> bool:
        """Set cache value"""
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None


# Global instance
redis_client = RedisClient()
