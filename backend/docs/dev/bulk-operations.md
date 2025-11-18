# Bulk Operations API

## Overview

The Bulk Operations API provides endpoints for importing, exporting, and deleting large batches of cards asynchronously using Celery task queues. This allows for efficient handling of operations involving 1000+ cards without blocking the API.

## Features

- **Bulk Import**: Import up to 10,000 cards per request with auto-publishing
- **Bulk Export**: Export cards to JSON, Markdown, or CSV formats
- **Bulk Delete**: Delete up to 10,000 cards (soft or hard delete)
- **Async Processing**: All operations use Celery for background processing
- **Progress Tracking**: Check operation status and progress in real-time
- **$EXTROPY Rewards**: Automatically award tokens for published cards

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Client    │────▶│ FastAPI App  │────▶│   Redis    │
└─────────────┘     └──────────────┘     └────────────┘
                           │                    │
                           │                    ▼
                           │              ┌────────────┐
                           │              │   Celery   │
                           │              │   Worker   │
                           │              └────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────────────────────┐
                    │      PostgreSQL Database     │
                    └──────────────────────────────┘
```

### Components

1. **API Routes** (`backend/api/routes/bulk.py`)
   - REST endpoints for bulk operations
   - Request validation and authentication
   - Task initiation and status checking

2. **Celery Tasks** (`backend/tasks/bulk_operations.py`)
   - Async task implementations
   - Database operations
   - Progress reporting

3. **Task Queue** (Redis + Celery)
   - Task broker and result backend
   - Task routing and execution
   - Result storage

## API Endpoints

### 1. Bulk Import

**Endpoint**: `POST /bulk/import`

**Description**: Import multiple cards asynchronously with auto-publishing.

**Request Body**:
```json
{
  "cards": [
    {
      "title": "How to Build Momentum",
      "body": "The key to building momentum is...",
      "category": "BUSINESS",
      "privacy_level": "BUSINESS",
      "tags": ["business", "growth"],
      "source_platform": "twitter",
      "source_url": "https://twitter.com/user/status/123",
      "metadata": {}
    }
  ],
  "publish_business": true,
  "publish_ideas": true
}
```

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "Bulk import initiated for 1000 cards",
  "estimated_duration_seconds": 100,
  "check_status_url": "/bulk/status/550e8400-e29b-41d4-a716-446655440000"
}
```

**Features**:
- Import up to 10,000 cards per request
- Auto-publish cards with BUSINESS or IDEAS privacy levels
- Award 1 $EXTROPY token per published card
- Detailed error reporting for failed imports

### 2. Bulk Export

**Endpoint**: `POST /bulk/export`

**Description**: Export cards to JSON, Markdown, or CSV format.

**Request Body**:
```json
{
  "card_ids": null,
  "privacy_levels": ["BUSINESS", "IDEAS"],
  "categories": null,
  "published_only": false,
  "format": "json",
  "include_metadata": true
}
```

**Formats**:
- `json`: Structured JSON array
- `markdown`: Concatenated markdown files
- `csv`: Tabular CSV format

**Response**:
```json
{
  "task_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "PENDING",
  "message": "Bulk export initiated in json format",
  "estimated_duration_seconds": 30,
  "check_status_url": "/bulk/status/6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```

### 3. Bulk Delete

**Endpoint**: `POST /bulk/delete`

**Description**: Delete multiple cards (soft or hard delete).

**Request Body**:
```json
{
  "card_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "soft_delete": true
}
```

**Delete Types**:
- **Soft Delete** (default): Marks cards as deleted in metadata, keeps data
- **Hard Delete**: Permanently removes cards from database

**Response**:
```json
{
  "task_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "PENDING",
  "message": "Bulk delete initiated for 100 cards",
  "estimated_duration_seconds": 2,
  "check_status_url": "/bulk/status/7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

### 4. Check Status

**Endpoint**: `GET /bulk/status/{task_id}`

**Description**: Check the status and progress of a bulk operation.

**Response (In Progress)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "STARTED",
  "progress": {
    "current": 500,
    "total": 1000,
    "percent": 50
  }
}
```

**Response (Completed)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "cards_imported": 1000,
    "cards_failed": 0,
    "cards_published": 800,
    "extropy_earned": "800.00000000",
    "errors": [],
    "duration_seconds": 45.2
  },
  "completed_at": "2025-11-18T12:34:56Z"
}
```

**Task States**:
- `PENDING`: Task is waiting to be executed
- `STARTED`: Task is currently running
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed with an error
- `RETRY`: Task failed but is being retried

### 5. Health Check

**Endpoint**: `GET /bulk/health`

**Description**: Check the health of the bulk operations service.

**Response**:
```json
{
  "status": "healthy",
  "service": "bulk-operations",
  "version": "1.0.0",
  "celery_workers": "healthy",
  "worker_count": 2
}
```

## Usage Examples

### Python Client

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Bulk Import
cards_data = [
    {
        "title": f"Card {i}",
        "body": f"Content {i}",
        "category": "BUSINESS",
        "privacy_level": "BUSINESS",
        "tags": ["test"]
    }
    for i in range(1000)
]

response = requests.post(
    f"{API_URL}/bulk/import",
    json={
        "cards": cards_data,
        "publish_business": True,
        "publish_ideas": True
    },
    headers=headers
)

task_id = response.json()["task_id"]

# Check Status
import time

while True:
    status_response = requests.get(
        f"{API_URL}/bulk/status/{task_id}",
        headers=headers
    )

    status_data = status_response.json()

    if status_data["status"] == "SUCCESS":
        print("Import completed!")
        print(status_data["result"])
        break
    elif status_data["status"] == "FAILURE":
        print("Import failed!")
        print(status_data["error"])
        break
    else:
        print(f"Progress: {status_data.get('progress', {})}")
        time.sleep(5)
```

### cURL Examples

**Bulk Import**:
```bash
curl -X POST http://localhost:8000/bulk/import \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "cards": [
      {
        "title": "Test Card",
        "body": "Content",
        "category": "BUSINESS",
        "privacy_level": "BUSINESS",
        "tags": []
      }
    ],
    "publish_business": true,
    "publish_ideas": true
  }'
```

**Bulk Export**:
```bash
curl -X POST http://localhost:8000/bulk/export \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "privacy_levels": ["BUSINESS", "IDEAS"],
    "include_metadata": true
  }'
```

**Check Status**:
```bash
curl http://localhost:8000/bulk/status/{task_id} \
  -H "Authorization: Bearer your-api-key"
```

## Performance Characteristics

### Throughput

| Operation | Cards/Second | 1000 Cards | 10000 Cards |
|-----------|--------------|------------|-------------|
| Import    | ~10          | ~100s      | ~1000s      |
| Export    | ~20          | ~50s       | ~500s       |
| Delete    | ~50          | ~20s       | ~200s       |

*Note: Actual performance depends on database configuration, network latency, and server resources.*

### Optimizations

1. **Batch Commits**: Database commits every 100 cards to balance transaction size and performance
2. **Progress Updates**: Status updates every 100 cards to avoid excessive Redis writes
3. **Connection Pooling**: SQLAlchemy connection pooling for efficient database access
4. **Async Processing**: Celery workers handle multiple tasks concurrently

## Error Handling

### Common Errors

1. **Empty Request**:
   - Status: 400 Bad Request
   - Message: "No cards provided for import"

2. **Too Many Items**:
   - Status: 400 Bad Request
   - Message: "Maximum 10,000 cards per import operation"

3. **Invalid Format**:
   - Status: 400 Bad Request
   - Message: "Invalid format. Must be one of: json, markdown, csv"

4. **Authentication Failure**:
   - Status: 401 Unauthorized
   - Message: "Invalid or missing API key"

5. **Task Failure**:
   - Status: 200 OK (task endpoint)
   - Task Status: FAILURE
   - Error details in response

### Error Recovery

- Failed tasks automatically retry up to 3 times with exponential backoff
- Individual card failures don't stop batch processing
- Detailed error logs for each failed card in task result
- Partial results returned even if some operations fail

## Deployment

### Requirements

1. **Redis** (task broker and result backend)
2. **PostgreSQL** (data storage)
3. **Celery Worker** (task processing)
4. **FastAPI** (API server)

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: unified_scraper
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: scraper_pass

  redis:
    image: redis:7-alpine

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://scraper:scraper_pass@postgres:5432/unified_scraper
      REDIS_URL: redis://redis:6379/0

  celery_worker:
    build: .
    command: celery -A backend.queue.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://scraper:scraper_pass@postgres:5432/unified_scraper
      REDIS_URL: redis://redis:6379/0
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL (usually same as REDIS_URL)
- `CELERY_RESULT_BACKEND`: Result backend URL (usually same as REDIS_URL)

## Testing

### Unit Tests

```bash
pytest backend/tests/test_bulk_operations.py -v
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
pytest backend/tests/test_bulk_operations.py --integration -v
```

### Load Testing

```bash
# Import 10,000 cards
python scripts/load_test_bulk_import.py --cards 10000

# Export all cards
python scripts/load_test_bulk_export.py --format json
```

## Monitoring

### Celery Flower

Monitor Celery tasks in real-time:

```bash
celery -A backend.queue.celery_app flower --port=5555
```

Access dashboard at http://localhost:5555

### Metrics to Monitor

- Task queue length
- Task execution time
- Worker availability
- Database connection pool usage
- Redis memory usage
- Error rate per task type

## Security Considerations

1. **Authentication**: All endpoints require valid API key
2. **Authorization**: Users can only access their own cards
3. **Rate Limiting**: Enforce rate limits to prevent abuse
4. **Input Validation**: Strict validation of all input data
5. **SQL Injection**: Use parameterized queries via SQLAlchemy ORM
6. **Task Timeouts**: Hard timeout at 1 hour, soft timeout at 55 minutes

## Future Enhancements

1. **Streaming Export**: Stream large exports instead of loading all into memory
2. **Webhook Notifications**: Notify client when task completes
3. **Scheduled Operations**: Schedule bulk operations for later execution
4. **Duplicate Detection**: Detect and skip duplicate cards during import
5. **Incremental Imports**: Resume failed imports from last successful position
6. **Compression**: Compress export data for large datasets
7. **Parallel Processing**: Split large batches across multiple workers

## Related Documentation

- [API Authentication](./authentication.md)
- [Database Schema](./database-schema.md)
- [$EXTROPY Token System](./extropy-tokens.md)
- [Card Publishing](./card-publishing.md)
- [Celery Task Queue](./celery-setup.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/extrophi/extrophi-ecosystem/issues
- Documentation: https://docs.extrophi.ai
- API Docs: http://localhost:8000/docs (when running locally)
