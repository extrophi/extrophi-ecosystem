# Scraping Dashboard Frontend

Real-time scraping dashboard with WebSocket updates.

## Components

### 1. Svelte Component (`ScrapingDashboard.svelte`)

Production-ready Svelte 5 component with runes syntax.

**Features**:
- Real-time WebSocket updates
- Auto-reconnection on disconnect
- Job-specific or global view
- Platform statistics
- Live content previews
- Progress tracking

**Usage**:
```svelte
<script>
import ScrapingDashboard from './ScrapingDashboard.svelte';

let currentJobId = $state(null);
</script>

<ScrapingDashboard
    apiUrl="ws://localhost:8000"
    bind:jobId={currentJobId}
    autoConnect={true}
/>
```

### 2. Standalone Demo (`dashboard.html`)

Self-contained HTML file for testing and demos.

**Features**:
- No build step required
- Works in any modern browser
- WebSocket connection controls
- Test scraping job trigger
- Live updates display

**Usage**:
```bash
# Serve with Python
python3 -m http.server 8080

# Open http://localhost:8080/dashboard.html
```

## Quick Start

### 1. Start Backend Server

```bash
cd research/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. Open Dashboard

**Option A: Standalone HTML**
```bash
cd research/frontend
python3 -m http.server 8080
# Open http://localhost:8080/dashboard.html
```

**Option B: Integrate Svelte Component**
```bash
# Copy ScrapingDashboard.svelte to your Svelte project
# Import and use as shown above
```

### 3. Trigger Scraping Jobs

**Via Dashboard UI**:
- Click "Trigger Test Scrape" button

**Via API**:
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/test",
    "platform": "web"
  }'
```

### 4. Watch Live Updates

You should see:
- Progress bars updating in real-time
- Item previews as they're scraped
- Success/error counts
- Platform breakdown
- Job completion events

## WebSocket Endpoints

### Global Updates
```
ws://localhost:8000/ws/scraping
```
All scraping events from all jobs.

### Job-Specific Updates
```
ws://localhost:8000/ws/scraping/{job_id}
```
Updates for a specific job only.

### Platform Statistics
```
ws://localhost:8000/ws/stats?interval=5
```
Periodic stats updates (default 5s interval).

## Message Types

The dashboard receives these message types:

1. **`initial_state`** - Current state on connect
2. **`progress`** - Scraping progress updates
3. **`item_preview`** - Newly scraped items
4. **`job_complete`** - Job finished
5. **`job_error`** - Job failed
6. **`stats`** - Platform statistics

See [WEBSOCKET_API.md](../docs/WEBSOCKET_API.md) for complete API documentation.

## Customization

### Change API URL

**Svelte**:
```svelte
<ScrapingDashboard apiUrl="ws://api.example.com" />
```

**HTML**:
Edit the input field in the dashboard or modify:
```javascript
document.getElementById('apiUrl').value = 'ws://api.example.com';
```

### Subscribe to Specific Job

**Svelte**:
```svelte
<ScrapingDashboard jobId="abc-123-def-456" />
```

**HTML**:
Change WebSocket endpoint:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scraping/abc-123-def-456');
```

## Browser Compatibility

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- IE11: ❌ Not supported (no WebSocket)

## Troubleshooting

### Connection Refused

**Symptom**: "WebSocket connection failed"

**Fix**:
1. Ensure backend is running: `uvicorn main:app --port 8000`
2. Check URL matches backend port
3. Verify CORS settings allow frontend origin

### No Updates

**Symptom**: Connected but no messages

**Fix**:
1. Trigger a scraping job via API or UI button
2. Check backend logs for errors
3. Open browser console for WebSocket messages

### CORS Errors

**Symptom**: "Access-Control-Allow-Origin" error

**Fix**: Add frontend URL to `main.py` CORS config:
```python
allow_origins=[
    "http://localhost:8080",  # Add your frontend URL
    ...
]
```

## Development

### Svelte Component Development

If you want to modify the Svelte component:

1. Install dependencies:
```bash
npm install svelte@5
```

2. Use in your Svelte project
3. Build for production:
```bash
npm run build
```

### HTML Demo Development

Edit `dashboard.html` directly - no build step needed!

## Performance

- Handles 100+ concurrent WebSocket connections
- ~2 updates per second per job
- Auto-cleanup of disconnected clients
- Memory-efficient message broadcasting

## Future Features

- [ ] Job pause/resume controls
- [ ] Historical job playback
- [ ] Export data to CSV/JSON
- [ ] Advanced filtering (by platform, status)
- [ ] Dark mode toggle
- [ ] Multi-dashboard views (grid layout)

## License

Part of Extrophi Ecosystem monorepo.
