"""
WebSocket manager for real-time scraping updates.

Provides live broadcasting of:
- Scraping progress (items processed, time elapsed)
- Content previews (as scraped)
- Success/error counts
- Platform breakdown
- Job status changes
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapingProgress:
    """Real-time scraping progress data."""
    job_id: str
    platform: str
    status: str  # "started", "processing", "completed", "failed"
    items_scraped: int
    items_total: Optional[int]
    success_count: int
    error_count: int
    current_item: Optional[Dict[str, Any]]  # Preview of current item being scraped
    started_at: str
    elapsed_seconds: float
    error_message: Optional[str] = None


@dataclass
class PlatformStats:
    """Platform-specific statistics."""
    platform: str
    total_items: int
    success_count: int
    error_count: int
    avg_processing_time: float


class ScrapingWebSocketManager:
    """
    Manages WebSocket connections for real-time scraping updates.

    Features:
    - Connection lifecycle management (connect/disconnect/broadcast)
    - Job-specific and global broadcasts
    - Progress tracking and aggregation
    - Platform statistics
    """

    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Set[WebSocket] = set()

        # Job-specific connections (clients subscribed to specific jobs)
        self.job_subscriptions: Dict[str, Set[WebSocket]] = {}

        # Active job tracking
        self.active_jobs: Dict[str, ScrapingProgress] = {}

        # Platform statistics
        self.platform_stats: Dict[str, PlatformStats] = {}

        logger.info("ScrapingWebSocketManager initialized")

    async def connect(self, websocket: WebSocket, job_id: Optional[str] = None):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            job_id: Optional job ID to subscribe to specific job updates
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        if job_id:
            if job_id not in self.job_subscriptions:
                self.job_subscriptions[job_id] = set()
            self.job_subscriptions[job_id].add(websocket)
            logger.info(f"WebSocket connected and subscribed to job {job_id}")
        else:
            logger.info("WebSocket connected (global)")

        # Send initial state
        await self._send_initial_state(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
        """
        self.active_connections.discard(websocket)

        # Remove from job subscriptions
        for job_id, subscribers in self.job_subscriptions.items():
            subscribers.discard(websocket)

        # Clean up empty subscription sets
        self.job_subscriptions = {
            job_id: subs for job_id, subs in self.job_subscriptions.items() if subs
        }

        logger.info("WebSocket disconnected")

    async def broadcast_progress(self, progress: ScrapingProgress):
        """
        Broadcast scraping progress to all relevant clients.

        Args:
            progress: ScrapingProgress dataclass with update info
        """
        message = {
            "type": "progress",
            "data": asdict(progress),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Update active jobs tracking
        self.active_jobs[progress.job_id] = progress

        # Update platform stats
        self._update_platform_stats(progress)

        # Broadcast to job-specific subscribers
        if progress.job_id in self.job_subscriptions:
            await self._broadcast_to_set(
                self.job_subscriptions[progress.job_id],
                message
            )

        # Broadcast to global subscribers (all connections)
        await self._broadcast_to_set(self.active_connections, message)

    async def broadcast_item_preview(
        self,
        job_id: str,
        platform: str,
        item: Dict[str, Any]
    ):
        """
        Broadcast a preview of a newly scraped item.

        Args:
            job_id: Job identifier
            platform: Platform name (twitter, youtube, reddit, web)
            item: Scraped item data (preview)
        """
        message = {
            "type": "item_preview",
            "data": {
                "job_id": job_id,
                "platform": platform,
                "item": item,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Broadcast to relevant subscribers
        if job_id in self.job_subscriptions:
            await self._broadcast_to_set(
                self.job_subscriptions[job_id],
                message
            )

        await self._broadcast_to_set(self.active_connections, message)

    async def broadcast_job_complete(
        self,
        job_id: str,
        platform: str,
        total_items: int,
        success_count: int,
        error_count: int,
        elapsed_seconds: float
    ):
        """
        Broadcast job completion event.

        Args:
            job_id: Job identifier
            platform: Platform name
            total_items: Total items scraped
            success_count: Successful items
            error_count: Failed items
            elapsed_seconds: Total processing time
        """
        message = {
            "type": "job_complete",
            "data": {
                "job_id": job_id,
                "platform": platform,
                "total_items": total_items,
                "success_count": success_count,
                "error_count": error_count,
                "elapsed_seconds": elapsed_seconds,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Remove from active jobs
        self.active_jobs.pop(job_id, None)

        # Broadcast
        if job_id in self.job_subscriptions:
            await self._broadcast_to_set(
                self.job_subscriptions[job_id],
                message
            )

        await self._broadcast_to_set(self.active_connections, message)

        # Clean up job subscriptions
        self.job_subscriptions.pop(job_id, None)

    async def broadcast_job_error(
        self,
        job_id: str,
        platform: str,
        error_message: str
    ):
        """
        Broadcast job error event.

        Args:
            job_id: Job identifier
            platform: Platform name
            error_message: Error description
        """
        message = {
            "type": "job_error",
            "data": {
                "job_id": job_id,
                "platform": platform,
                "error_message": error_message,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Update job status if tracked
        if job_id in self.active_jobs:
            self.active_jobs[job_id].status = "failed"
            self.active_jobs[job_id].error_message = error_message

        # Broadcast
        if job_id in self.job_subscriptions:
            await self._broadcast_to_set(
                self.job_subscriptions[job_id],
                message
            )

        await self._broadcast_to_set(self.active_connections, message)

    async def get_platform_stats(self) -> Dict[str, PlatformStats]:
        """
        Get current platform statistics.

        Returns:
            Dictionary of platform statistics
        """
        return {
            platform: asdict(stats)
            for platform, stats in self.platform_stats.items()
        }

    async def get_active_jobs(self) -> Dict[str, ScrapingProgress]:
        """
        Get currently active scraping jobs.

        Returns:
            Dictionary of active jobs
        """
        return {
            job_id: asdict(progress)
            for job_id, progress in self.active_jobs.items()
        }

    # Private methods

    async def _send_initial_state(self, websocket: WebSocket):
        """Send initial state to newly connected client."""
        try:
            # Send active jobs
            active_jobs_data = await self.get_active_jobs()
            await websocket.send_json({
                "type": "initial_state",
                "data": {
                    "active_jobs": active_jobs_data,
                    "platform_stats": await self.get_platform_stats(),
                },
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")

    async def _broadcast_to_set(self, connections: Set[WebSocket], message: dict):
        """
        Broadcast a message to a set of WebSocket connections.

        Args:
            connections: Set of WebSocket connections
            message: Message dictionary to broadcast
        """
        disconnected = set()

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
                logger.warning("WebSocket disconnected during broadcast")
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            self.disconnect(ws)

    def _update_platform_stats(self, progress: ScrapingProgress):
        """Update platform statistics based on progress."""
        platform = progress.platform

        if platform not in self.platform_stats:
            self.platform_stats[platform] = PlatformStats(
                platform=platform,
                total_items=0,
                success_count=0,
                error_count=0,
                avg_processing_time=0.0
            )

        stats = self.platform_stats[platform]
        stats.total_items = max(stats.total_items, progress.items_scraped)
        stats.success_count = progress.success_count
        stats.error_count = progress.error_count

        # Update average processing time
        if progress.items_scraped > 0:
            stats.avg_processing_time = (
                progress.elapsed_seconds / progress.items_scraped
            )


# Global singleton instance
scraping_ws_manager = ScrapingWebSocketManager()
