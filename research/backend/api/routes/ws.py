"""
WebSocket API routes for real-time scraping updates.

Endpoints:
- /ws/scraping - Global scraping updates (all jobs)
- /ws/scraping/{job_id} - Job-specific updates
- /ws/stats - Platform statistics stream
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import asyncio
import logging

from websocket.scraping_updates import scraping_ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/scraping")
async def websocket_scraping_global(websocket: WebSocket):
    """
    WebSocket endpoint for global scraping updates.

    Broadcasts all scraping events from all jobs:
    - Progress updates
    - Item previews
    - Job completions
    - Errors

    Example client code:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/scraping');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Update:', data.type, data.data);
    };
    ```
    """
    await scraping_ws_manager.connect(websocket)

    try:
        # Keep connection alive and listen for client messages (optional)
        while True:
            # Wait for any messages from client (ping/pong, etc.)
            data = await websocket.receive_text()

            # Optional: Handle client commands
            # For now, just echo back to confirm connection
            await websocket.send_json({
                "type": "pong",
                "message": "Connection alive"
            })

    except WebSocketDisconnect:
        scraping_ws_manager.disconnect(websocket)
        logger.info("Client disconnected from global scraping stream")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        scraping_ws_manager.disconnect(websocket)


@router.websocket("/scraping/{job_id}")
async def websocket_scraping_job(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for job-specific scraping updates.

    Subscribe to updates for a specific scraping job.

    Args:
        job_id: Scraping job UUID

    Broadcasts:
    - Progress updates for this job only
    - Item previews
    - Completion/error events

    Example:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/scraping/abc-123');
    ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        if (update.type === 'progress') {
            console.log(`Progress: ${update.data.items_scraped} items`);
        }
    };
    ```
    """
    await scraping_ws_manager.connect(websocket, job_id=job_id)

    try:
        while True:
            data = await websocket.receive_text()

            # Echo confirmation
            await websocket.send_json({
                "type": "pong",
                "job_id": job_id,
                "message": "Subscribed to job updates"
            })

    except WebSocketDisconnect:
        scraping_ws_manager.disconnect(websocket)
        logger.info(f"Client disconnected from job {job_id} stream")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        scraping_ws_manager.disconnect(websocket)


@router.websocket("/stats")
async def websocket_platform_stats(
    websocket: WebSocket,
    interval: int = Query(default=5, ge=1, le=60)
):
    """
    WebSocket endpoint for periodic platform statistics.

    Streams aggregated platform stats at specified interval.

    Query params:
        interval: Update interval in seconds (1-60, default 5)

    Broadcasts:
    - Platform breakdown (items per platform)
    - Success/error rates
    - Average processing times

    Example:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/stats?interval=3');
    ws.onmessage = (event) => {
        const stats = JSON.parse(event.data);
        console.log('Platform stats:', stats.data.platform_stats);
    };
    ```
    """
    await scraping_ws_manager.connect(websocket)

    try:
        while True:
            # Send platform stats at specified interval
            stats = await scraping_ws_manager.get_platform_stats()
            active_jobs = await scraping_ws_manager.get_active_jobs()

            await websocket.send_json({
                "type": "stats",
                "data": {
                    "platform_stats": stats,
                    "active_jobs_count": len(active_jobs),
                    "active_jobs": active_jobs,
                },
                "interval_seconds": interval
            })

            # Wait for next update
            await asyncio.sleep(interval)

    except WebSocketDisconnect:
        scraping_ws_manager.disconnect(websocket)
        logger.info("Client disconnected from stats stream")
    except Exception as e:
        logger.error(f"WebSocket stats error: {e}")
        scraping_ws_manager.disconnect(websocket)


@router.get("/scraping/status")
async def get_websocket_status():
    """
    REST endpoint to check WebSocket manager status.

    Returns:
        - Active connections count
        - Active jobs count
        - Platform statistics
    """
    return {
        "active_connections": len(scraping_ws_manager.active_connections),
        "active_jobs": len(scraping_ws_manager.active_jobs),
        "job_subscriptions": len(scraping_ws_manager.job_subscriptions),
        "platform_stats": await scraping_ws_manager.get_platform_stats(),
    }
