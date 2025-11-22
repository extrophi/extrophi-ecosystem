"""Simple Redis job queue (no Celery)."""

import json
import os
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import redis


class RedisQueue:
    """Simple Redis-based job queue using pub/sub pattern."""

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.queue_name = "scraper_jobs"

    def enqueue(self, job_id: str, platform: str, target: str, limit: int = 20) -> bool:
        """
        Add a job to the queue.

        Args:
            job_id: UUID of the job
            platform: Platform to scrape (twitter, youtube, reddit, web)
            target: Platform-specific identifier
            limit: Max items to scrape

        Returns:
            True if job was enqueued successfully
        """
        try:
            job_data = {
                "job_id": job_id,
                "platform": platform,
                "target": target,
                "limit": limit,
                "enqueued_at": datetime.utcnow().isoformat(),
            }
            # Push to Redis list (FIFO queue)
            self.redis_client.rpush(self.queue_name, json.dumps(job_data))
            return True
        except Exception as e:
            print(f"Failed to enqueue job: {e}")
            return False

    def dequeue(self) -> Optional[dict[str, Any]]:
        """
        Get next job from the queue.

        Returns:
            Job data dict or None if queue is empty
        """
        try:
            # Pop from Redis list (blocking with 1 second timeout)
            result = self.redis_client.blpop(self.queue_name, timeout=1)
            if result:
                _, job_json = result
                return json.loads(job_json)
            return None
        except Exception as e:
            print(f"Failed to dequeue job: {e}")
            return None

    def get_queue_length(self) -> int:
        """Get number of pending jobs in queue."""
        try:
            return self.redis_client.llen(self.queue_name)
        except Exception:
            return 0

    def health_check(self) -> bool:
        """Check Redis connection."""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

    def set_job_status(
        self, job_id: str, status: str, error: Optional[str] = None
    ) -> bool:
        """
        Update job status in Redis.

        Args:
            job_id: UUID of the job
            status: New status (pending, processing, completed, failed)
            error: Optional error message

        Returns:
            True if status was updated
        """
        try:
            status_key = f"job_status:{job_id}"
            status_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
            if error:
                status_data["error"] = error

            # Set with 24 hour expiration
            self.redis_client.setex(
                status_key, 86400, json.dumps(status_data)  # 24 hours
            )
            return True
        except Exception as e:
            print(f"Failed to set job status: {e}")
            return False

    def get_job_status(self, job_id: str) -> Optional[dict[str, Any]]:
        """
        Get job status from Redis.

        Args:
            job_id: UUID of the job

        Returns:
            Status data dict or None if not found
        """
        try:
            status_key = f"job_status:{job_id}"
            status_json = self.redis_client.get(status_key)
            if status_json:
                return json.loads(status_json)
            return None
        except Exception as e:
            print(f"Failed to get job status: {e}")
            return None


# Global queue instance
_queue_instance: Optional[RedisQueue] = None


def get_queue() -> RedisQueue:
    """Get or create global queue instance."""
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = RedisQueue()
    return _queue_instance
