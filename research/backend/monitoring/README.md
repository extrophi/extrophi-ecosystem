# Scraper Health Monitoring System

**Author**: PSI-2 Agent
**Issue**: #83 - Scraper health monitoring
**Dependencies**: IOTA #39

## Overview

The Scraper Health Monitoring System provides real-time tracking and alerting for all platform scrapers (Twitter, YouTube, Reddit, Web). It monitors success rates, tracks errors, calculates uptime, and triggers alerts when scrapers fail or performance degrades.

## Features

### ✅ Success Rate Tracking
- Track success/failure rates per platform
- Configurable time windows (1-168 hours)
- Average response time monitoring

### 🚨 Error Tracking
- Categorized error types:
  - HTTP errors (4xx, 5xx)
  - Rate limits (429)
  - Timeouts
  - Parse errors
  - Authentication errors
  - Network errors
- Error breakdown statistics
- Latest occurrence timestamps

### ⏰ Uptime Monitoring
- Last successful scrape timestamp per platform
- Consecutive failure tracking
- All-time uptime percentage
- Health status indicators:
  - **Healthy**: Success rate > 80%, no consecutive failures
  - **Degraded**: Success rate 50-80%
  - **Warning**: 3+ consecutive failures
  - **Critical**: 5+ consecutive failures OR success rate < 50%

### 📊 Dashboard Summary
- Overall system health (worst status across platforms)
- 24-hour statistics (attempts, successes, failures)
- Average success rate across all platforms
- Per-platform health status

## Installation

### 1. Database Setup

Run the health monitoring schema migration:

```bash
cd research/backend
source .venv/bin/activate

# Connect to PostgreSQL
psql -d research_db -f db/schema_health_metrics.sql
```

This creates:
- `scraper_health_metrics` table - Individual scrape attempt records
- `scraper_uptime` table - Platform uptime tracking
- Health monitoring functions
- Indexes for performance

### 2. Verify Installation

Check tables were created:

```bash
psql -d research_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'scraper%' ORDER BY tablename;"
```

Expected output:
```
       tablename
-----------------------
 scraper_health_metrics
 scraper_uptime
```

### 3. Start API Server

The monitoring routes are automatically included in the main API:

```bash
cd research/backend
uvicorn main:app --reload --port 8000
```

## API Endpoints

All monitoring endpoints are under `/api/monitoring`:

### Dashboard Summary
```http
GET /api/monitoring/dashboard
```

Returns comprehensive dashboard with all platforms and 24-hour statistics.

**Response**:
```json
{
  "overall_status": "healthy",
  "platforms": [
    {
      "platform": "twitter",
      "status": "healthy",
      "success_rate": 95.5,
      "last_success_at": "2025-11-18T12:00:00",
      "consecutive_failures": 0,
      "uptime_percentage": 98.2,
      "avg_response_time_ms": 250
    }
  ],
  "total_attempts_24h": 1000,
  "total_successes_24h": 950,
  "total_failures_24h": 50,
  "avg_success_rate": 95.0,
  "timestamp": "2025-11-18T12:30:00"
}
```

### Platform Health
```http
GET /api/monitoring/health/{platform}?time_window_hours=24
```

Get detailed health status for a specific platform.

**Parameters**:
- `platform`: `twitter` | `youtube` | `reddit` | `web`
- `time_window_hours`: Time window for metrics (1-168 hours, default 24)

**Example**:
```bash
curl http://localhost:8000/api/monitoring/health/twitter?time_window_hours=24
```

**Response**:
```json
{
  "platform": "twitter",
  "status": "healthy",
  "success_rate": 95.5,
  "total_attempts": 100,
  "successful_attempts": 96,
  "failed_attempts": 4,
  "avg_response_time_ms": 250,
  "last_success_at": "2025-11-18T12:00:00",
  "last_failure_at": "2025-11-18T10:30:00",
  "consecutive_failures": 0,
  "uptime_percentage": 98.2,
  "time_window_hours": 24
}
```

### All Platforms Health
```http
GET /api/monitoring/health?time_window_hours=24
```

Get health status for all platforms.

### Error Breakdown
```http
GET /api/monitoring/errors/{platform}?time_window_hours=24
```

Get breakdown of errors by type for a platform.

**Response**:
```json
[
  {
    "error_type": "rate_limit",
    "error_count": 15,
    "percentage": 60.0,
    "latest_occurrence": "2025-11-18T11:45:00"
  },
  {
    "error_type": "timeout",
    "error_count": 10,
    "percentage": 40.0,
    "latest_occurrence": "2025-11-18T11:30:00"
  }
]
```

### Uptime Statistics
```http
GET /api/monitoring/uptime/{platform}
```

Get all-time uptime statistics for a platform.

```http
GET /api/monitoring/uptime
```

Get all-time uptime statistics for all platforms.

### Recent Metrics
```http
GET /api/monitoring/metrics?platform={platform}&limit=100&time_window_hours=24
```

Get individual scrape attempt records.

**Parameters**:
- `platform`: Filter by platform (optional)
- `limit`: Maximum records (1-1000, default 100)
- `time_window_hours`: Time window (1-168 hours, default 24)

### Reset Statistics (Admin)
```http
POST /api/monitoring/reset/{platform}
```

⚠️ **WARNING**: Clears all health statistics for a platform. Use with caution!

## Usage in Code

### Recording Scrape Success

```python
from db import get_db_manager
from monitoring import ScraperHealthMonitor

db_manager = get_db_manager()
monitor = ScraperHealthMonitor(db_manager)

# After successful scrape
await monitor.record_success(
    platform="twitter",
    items_scraped=10,
    response_time_ms=250,
    metadata={"username": "@example"}
)
```

### Recording Scrape Failure

```python
from monitoring import ScraperHealthMonitor, ErrorType

# After failed scrape
await monitor.record_failure(
    platform="twitter",
    error_type=ErrorType.RATE_LIMIT,
    error_message="Rate limit exceeded: 429 Too Many Requests",
    http_status_code=429,
    response_time_ms=100
)
```

### Recording Timeout

```python
# After timeout
await monitor.record_timeout(
    platform="youtube",
    timeout_seconds=30,
    metadata={"video_id": "abc123"}
)
```

### Getting Platform Health

```python
# Get health status
health = await monitor.get_platform_health("twitter", time_window_hours=24)

print(f"Status: {health['status']}")
print(f"Success Rate: {health['success_rate']}%")
print(f"Consecutive Failures: {health['consecutive_failures']}")
```

### Getting Dashboard Summary

```python
# Get complete dashboard
dashboard = await monitor.get_dashboard_summary()

print(f"Overall Status: {dashboard['overall_status']}")
print(f"24h Success Rate: {dashboard['avg_success_rate']}%")

for platform in dashboard['platforms']:
    print(f"{platform['platform']}: {platform['status']}")
```

## Alert Thresholds

Default alert thresholds (configurable in `ScraperHealthMonitor`):

```python
alert_thresholds = {
    "consecutive_failures": 3,      # Alert after 3 consecutive failures
    "success_rate_warning": 80.0,   # Warning if success rate < 80%
    "success_rate_critical": 50.0,  # Critical if success rate < 50%
}
```

### Alert Behavior

Alerts are logged to the application logger:

- **Warning**: `consecutive_failures >= 3` OR `success_rate < 80%`
- **Critical**: `consecutive_failures >= 5` OR `success_rate < 50%`

Example alert messages:

```
⚠️  WARNING: twitter scraper uptime degraded: 75.5%
🚨 ALERT: youtube scraper has 3 consecutive failures!
🚨 ALERT: reddit scraper uptime critically low: 45.2%
```

## Integration with Scrapers

To integrate monitoring into your scraper:

```python
from backend.scrapers.base import BaseScraper
from monitoring import ScraperHealthMonitor, ErrorType
import time

class MyPlatformScraper(BaseScraper):
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.monitor = ScraperHealthMonitor(db_manager)

    async def extract(self, target: str, limit: int = 20):
        start_time = time.time()

        try:
            # Perform scraping
            results = await self._scrape_content(target, limit)

            # Record success
            response_time_ms = int((time.time() - start_time) * 1000)
            await self.monitor.record_success(
                platform="myplatform",
                items_scraped=len(results),
                response_time_ms=response_time_ms
            )

            return results

        except RateLimitError as e:
            # Record rate limit error
            await self.monitor.record_failure(
                platform="myplatform",
                error_type=ErrorType.RATE_LIMIT,
                error_message=str(e),
                http_status_code=429
            )
            raise

        except TimeoutError as e:
            # Record timeout
            await self.monitor.record_timeout(
                platform="myplatform",
                timeout_seconds=30
            )
            raise

        except Exception as e:
            # Record generic error
            await self.monitor.record_failure(
                platform="myplatform",
                error_type=ErrorType.UNKNOWN,
                error_message=str(e)
            )
            raise
```

## Database Schema

### `scraper_health_metrics` Table

Stores individual scrape attempt records:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `platform` | VARCHAR(50) | Platform name (twitter, youtube, reddit, web) |
| `scrape_attempt_id` | UUID | Reference to scrape_jobs.id if applicable |
| `status` | VARCHAR(20) | success, error, rate_limited, timeout |
| `error_type` | VARCHAR(50) | http_error, rate_limit, timeout, parse_error, auth_error |
| `error_message` | TEXT | Human-readable error message |
| `http_status_code` | INTEGER | HTTP status code if applicable |
| `response_time_ms` | INTEGER | Response time in milliseconds |
| `items_scraped` | INTEGER | Number of items successfully scraped |
| `timestamp` | TIMESTAMP | Timestamp of attempt |
| `metadata` | JSONB | Additional context |

### `scraper_uptime` Table

Tracks uptime statistics per platform:

| Column | Type | Description |
|--------|------|-------------|
| `platform` | VARCHAR(50) | Primary key |
| `last_success_at` | TIMESTAMP | Last successful scrape timestamp |
| `last_failure_at` | TIMESTAMP | Last failed scrape timestamp |
| `consecutive_failures` | INTEGER | Number of consecutive failures |
| `total_attempts` | INTEGER | Total scrape attempts all-time |
| `total_successes` | INTEGER | Total successful scrapes all-time |
| `total_failures` | INTEGER | Total failed scrapes all-time |
| `uptime_percentage` | FLOAT | Uptime percentage (calculated) |
| `created_at` | TIMESTAMP | Created timestamp |
| `updated_at` | TIMESTAMP | Updated timestamp |

## Testing

### Manual Testing

1. **Test Dashboard Endpoint**:
```bash
curl http://localhost:8000/api/monitoring/dashboard | jq
```

2. **Test Platform Health**:
```bash
curl http://localhost:8000/api/monitoring/health/twitter | jq
```

3. **Record Test Metrics**:
```python
from db import get_db_manager
from monitoring import ScraperHealthMonitor, ErrorType

db_manager = get_db_manager()
await db_manager.connect()

monitor = ScraperHealthMonitor(db_manager)

# Record some test data
for i in range(10):
    await monitor.record_success("twitter", items_scraped=5, response_time_ms=200)

for i in range(2):
    await monitor.record_failure("twitter", ErrorType.RATE_LIMIT, "Test failure")

# Check health
health = await monitor.get_platform_health("twitter")
print(health)
```

4. **View Recent Metrics**:
```bash
curl "http://localhost:8000/api/monitoring/metrics?platform=twitter&limit=20" | jq
```

### Automated Tests

Create tests in `research/backend/tests/test_monitoring.py`:

```python
import pytest
from monitoring import ScraperHealthMonitor, ErrorType

@pytest.mark.asyncio
async def test_record_success(db_manager):
    monitor = ScraperHealthMonitor(db_manager)

    metric_id = await monitor.record_success(
        platform="twitter",
        items_scraped=10,
        response_time_ms=250
    )

    assert metric_id is not None

@pytest.mark.asyncio
async def test_get_platform_health(db_manager):
    monitor = ScraperHealthMonitor(db_manager)

    health = await monitor.get_platform_health("twitter")

    assert health["platform"] == "twitter"
    assert health["status"] in ["healthy", "degraded", "warning", "critical"]
    assert 0.0 <= health["success_rate"] <= 100.0
```

## Troubleshooting

### Issue: "Table scraper_health_metrics does not exist"

**Solution**: Run the schema migration:
```bash
psql -d research_db -f db/schema_health_metrics.sql
```

### Issue: "Platform not initialized"

**Solution**: The `scraper_uptime` table should be auto-populated with all platforms. Verify:
```sql
SELECT * FROM scraper_uptime;
```

If empty, run the schema migration again.

### Issue: "No metrics showing in dashboard"

**Solution**: No scrape attempts have been recorded yet. Record some test data:
```python
from monitoring import ScraperHealthMonitor
monitor = ScraperHealthMonitor(db_manager)
await monitor.record_success("twitter", items_scraped=1)
```

## Future Enhancements

Potential improvements for future iterations:

- [ ] Webhook alerts (Slack, Discord, email)
- [ ] Prometheus metrics export
- [ ] Grafana dashboard templates
- [ ] Auto-scaling based on health metrics
- [ ] Predictive failure detection using ML
- [ ] Circuit breaker pattern integration
- [ ] Health-based scraper rotation

## Support

For issues or questions:
- GitHub Issue: #83
- Documentation: `/research/docs/pm/`
- Code: `/research/backend/monitoring/`

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
**Agent**: PSI-2
