# WebSocket API Documentation

## Overview

The scraping dashboard provides real-time updates via WebSocket connections. This enables live monitoring of scraping progress, content previews, success/error counts, and platform statistics.

## WebSocket Endpoints

### 1. Global Scraping Updates

```
ws://localhost:8000/ws/scraping
```

Broadcasts all scraping events from all jobs.

**Use case**: Dashboard showing all active scraping operations

**Example (JavaScript)**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scraping');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Update:', message.type, message.data);
};
```

### 2. Job-Specific Updates

```
ws://localhost:8000/ws/scraping/{job_id}
```

Subscribe to updates for a specific scraping job.

**Use case**: Monitoring a single scraping job

**Example**:
```javascript
const jobId = 'abc-123-def-456';
const ws = new WebSocket(`ws://localhost:8000/ws/scraping/${jobId}`);

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    if (update.type === 'progress') {
        console.log(`Progress: ${update.data.items_scraped} items`);
    }
};
```

### 3. Platform Statistics Stream

```
ws://localhost:8000/ws/stats?interval=5
```

Periodic platform statistics updates.

**Query Parameters**:
- `interval`: Update interval in seconds (1-60, default: 5)

**Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stats?interval=3');

ws.onmessage = (event) => {
    const stats = JSON.parse(event.data);
    console.log('Platform stats:', stats.data.platform_stats);
};
```

## Message Types

### 1. `initial_state`

Sent immediately upon connection with current state.

```json
{
    "type": "initial_state",
    "data": {
        "active_jobs": {
            "job-id-1": {
                "job_id": "job-id-1",
                "platform": "twitter",
                "status": "processing",
                "items_scraped": 15,
                "items_total": 20,
                "success_count": 14,
                "error_count": 1,
                "started_at": "2025-11-18T19:30:00Z",
                "elapsed_seconds": 7.5
            }
        },
        "platform_stats": {
            "twitter": {
                "platform": "twitter",
                "total_items": 15,
                "success_count": 14,
                "error_count": 1,
                "avg_processing_time": 0.5
            }
        }
    },
    "timestamp": "2025-11-18T19:30:00Z"
}
```

### 2. `progress`

Scraping progress update.

```json
{
    "type": "progress",
    "data": {
        "job_id": "abc-123",
        "platform": "youtube",
        "status": "processing",
        "items_scraped": 8,
        "items_total": 20,
        "success_count": 7,
        "error_count": 1,
        "current_item": {
            "id": "video_8",
            "title": "Productivity Tips",
            "channel": "Creator 2"
        },
        "started_at": "2025-11-18T19:30:00Z",
        "elapsed_seconds": 4.2
    },
    "timestamp": "2025-11-18T19:30:04Z"
}
```

### 3. `item_preview`

Preview of newly scraped item.

```json
{
    "type": "item_preview",
    "data": {
        "job_id": "abc-123",
        "platform": "twitter",
        "item": {
            "id": "tweet_5",
            "author": "@user2",
            "text": "This is a tweet about productivity...",
            "likes": 185,
            "retweets": 65,
            "timestamp": "2025-11-18T19:30:05Z",
            "url": "https://twitter.com/user2/status/1000005"
        }
    },
    "timestamp": "2025-11-18T19:30:05Z"
}
```

### 4. `job_complete`

Job completion event.

```json
{
    "type": "job_complete",
    "data": {
        "job_id": "abc-123",
        "platform": "reddit",
        "total_items": 20,
        "success_count": 18,
        "error_count": 2,
        "elapsed_seconds": 10.5
    },
    "timestamp": "2025-11-18T19:30:10Z"
}
```

### 5. `job_error`

Job error event.

```json
{
    "type": "job_error",
    "data": {
        "job_id": "abc-123",
        "platform": "twitter",
        "error_message": "Rate limit exceeded. Retry after 60s."
    },
    "timestamp": "2025-11-18T19:30:15Z"
}
```

### 6. `stats`

Periodic platform statistics (from `/ws/stats` endpoint).

```json
{
    "type": "stats",
    "data": {
        "platform_stats": {
            "twitter": {
                "platform": "twitter",
                "total_items": 150,
                "success_count": 145,
                "error_count": 5,
                "avg_processing_time": 0.48
            },
            "youtube": {
                "platform": "youtube",
                "total_items": 80,
                "success_count": 78,
                "error_count": 2,
                "avg_processing_time": 0.52
            }
        },
        "active_jobs_count": 2,
        "active_jobs": {
            "job-1": { /* job data */ },
            "job-2": { /* job data */ }
        }
    },
    "interval_seconds": 5
}
```

### 7. `pong`

Keepalive response (echo confirmation).

```json
{
    "type": "pong",
    "message": "Connection alive"
}
```

## REST Endpoints

### Check WebSocket Status

```
GET /ws/scraping/status
```

Returns current WebSocket manager status.

**Response**:
```json
{
    "active_connections": 3,
    "active_jobs": 2,
    "job_subscriptions": 1,
    "platform_stats": {
        "twitter": {
            "platform": "twitter",
            "total_items": 150,
            "success_count": 145,
            "error_count": 5,
            "avg_processing_time": 0.48
        }
    }
}
```

### Trigger Scraping Job

```
POST /api/scrape
```

Starts a new scraping job with WebSocket updates.

**Request**:
```json
{
    "url": "https://twitter.com/user/status/123",
    "platform": "twitter",
    "depth": 1,
    "extract_embeddings": true
}
```

**Response**:
```json
{
    "job_id": "abc-123-def-456",
    "status": "started",
    "url": "https://twitter.com/user/status/123",
    "estimated_time_seconds": 10,
    "message": "Scraping job started. Connect to /ws/scraping/abc-123-def-456 for real-time updates."
}
```

## Frontend Integration

### Svelte Component

Use the provided `ScrapingDashboard.svelte` component:

```svelte
<script>
import ScrapingDashboard from './ScrapingDashboard.svelte';

let jobId = $state(null); // Optional: specific job ID
</script>

<ScrapingDashboard
    apiUrl="ws://localhost:8000"
    bind:jobId={jobId}
    autoConnect={true}
/>
```

### Standalone HTML

Open `dashboard.html` in a browser:

```bash
# Serve via Python HTTP server
cd research/frontend
python3 -m http.server 8080

# Open http://localhost:8080/dashboard.html
```

## Architecture

### Components

1. **WebSocket Manager** (`websocket/scraping_updates.py`)
   - Connection lifecycle management
   - Broadcasting to subscribers
   - Job and platform statistics tracking

2. **WebSocket Routes** (`api/routes/ws.py`)
   - FastAPI WebSocket endpoints
   - Client subscription management

3. **Scraping Service** (`scraping/service.py`)
   - Async scraping execution
   - Progress event emission
   - Mock item generation (for testing)

4. **Frontend Components**
   - `ScrapingDashboard.svelte` - Svelte 5 component
   - `dashboard.html` - Standalone HTML demo

### Data Flow

```
Scraping Job Started
        ↓
Scraping Service
        ↓
WebSocket Manager (broadcast)
        ↓
WebSocket Connections (subscribed clients)
        ↓
Frontend Dashboard Updates
```

## Testing

### 1. Start Backend Server

```bash
cd research/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. Open Dashboard

```bash
# Serve frontend
cd research/frontend
python3 -m http.server 8080

# Open browser: http://localhost:8080/dashboard.html
```

### 3. Trigger Scraping Job

**Option A: Via Dashboard UI**
- Click "Trigger Test Scrape" button

**Option B: Via curl**
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/test",
    "platform": "web",
    "depth": 1,
    "extract_embeddings": true
  }'
```

### 4. Observe Live Updates

You should see:
- Progress bar updating every 500ms
- Item previews appearing in real-time
- Success/error counts incrementing
- Platform statistics updating

## Performance Considerations

### Connection Limits

- No hard limit on WebSocket connections
- Each connection consumes ~10KB memory
- Tested with 100+ concurrent connections

### Message Frequency

- Progress updates: ~2 per second per job
- Item previews: 1 per scraped item
- Stats updates: Configurable interval (default 5s)

### Cleanup

- Disconnected clients automatically removed
- Completed jobs cleaned from memory
- Empty subscription sets pruned

## Error Handling

### Connection Errors

The frontend dashboard auto-reconnects after 3 seconds if connection is lost.

### Job Errors

Errors broadcast via `job_error` message type:
```json
{
    "type": "job_error",
    "data": {
        "job_id": "abc-123",
        "platform": "twitter",
        "error_message": "Rate limit exceeded"
    }
}
```

### Disconnection Cleanup

WebSocket manager automatically:
1. Removes disconnected clients from active connections
2. Cleans up job subscriptions
3. Logs disconnection events

## Future Enhancements

### Planned Features

1. **Authentication**
   - API key validation for WebSocket connections
   - User-specific job filtering

2. **Job Control**
   - Pause/resume scraping jobs
   - Cancel running jobs via WebSocket message

3. **Advanced Filtering**
   - Platform-specific subscriptions
   - Error-only streams
   - Custom event filtering

4. **Persistence**
   - Job history storage
   - Platform statistics aggregation
   - Historical playback

### Integration Points

1. **Celery Integration**
   - Replace mock scraping with actual Celery tasks
   - Emit progress from Celery workers

2. **Database Integration**
   - Store job progress in `scrape_jobs` table
   - Query historical data via REST API

3. **Real Scraper Adapters**
   - Replace mock items with actual scraper data
   - Platform-specific preview formatting

## Troubleshooting

### WebSocket Connection Refused

**Problem**: `WebSocket connection to 'ws://localhost:8000/ws/scraping' failed`

**Solution**:
1. Ensure backend server is running: `uvicorn main:app --port 8000`
2. Check CORS settings in `main.py`
3. Verify WebSocket routes are included: `app.include_router(ws_router)`

### No Updates Received

**Problem**: Connected but not receiving messages

**Solution**:
1. Trigger a scraping job: `POST /api/scrape`
2. Check server logs for errors
3. Verify `scraping_service` is imported in `main.py`

### CORS Errors

**Problem**: `Access-Control-Allow-Origin` error

**Solution**: Add your frontend URL to CORS origins in `main.py`:
```python
allow_origins=[
    "http://localhost:8080",  # Add this
    ...
]
```

## API Versioning

Current version: **1.0.0**

WebSocket API follows semantic versioning. Breaking changes will increment major version.

## Support

For issues or questions:
- GitHub Issues: https://github.com/extrophi/extrophi-ecosystem/issues
- Documentation: `/research/docs/WEBSOCKET_API.md`
- API Docs: http://localhost:8000/docs (FastAPI Swagger UI)
