# Orchestrator Module

API Gateway for coordinating Writer, Research, and Backend modules in the Extrophi Ecosystem.

## Features

- **Request Routing**: Routes requests to appropriate services
  - `/api/enrich` → Research module (port 8001)
  - `/api/publish` → Backend module (port 8002)
- **Health Aggregation**: `/health` endpoint aggregates health from all modules
- **Timeout Handling**: 30-second timeout for all proxied requests
- **Retry Logic**: Automatic retry (3 attempts) on failure
- **CORS Support**: Fully configured CORS middleware

## Installation

```bash
# Using UV (recommended)
cd orchestrator
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

## Running the Service

```bash
# Development mode
uvicorn orchestrator.main:app --reload --port 8003

# Production mode
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8003 --workers 4
```

## API Endpoints

### Root
```
GET /
```
Returns API information and available services.

### Research Routing
```
GET/POST/PUT/DELETE/PATCH /api/enrich
```
Routes requests to Research module (port 8001).

### Backend Routing
```
GET/POST/PUT/DELETE/PATCH /api/publish
```
Routes requests to Backend module (port 8002).

### Health Check
```
GET /health
```
Aggregates health status from all modules (Writer, Research, Backend).

Response example:
```json
{
  "orchestrator": "healthy",
  "services": {
    "writer": {
      "status": "healthy",
      "details": {},
      "url": "http://localhost:8000"
    },
    "research": {
      "status": "healthy",
      "details": {},
      "url": "http://localhost:8001"
    },
    "backend": {
      "status": "healthy",
      "details": {},
      "url": "http://localhost:8002"
    }
  },
  "overall": "healthy"
}
```

## Configuration

Service endpoints are configured in `main.py`:

```python
SERVICES = {
    "writer": "http://localhost:8000",
    "research": "http://localhost:8001",
    "backend": "http://localhost:8002",
}
```

Timeout and retry settings:
```python
REQUEST_TIMEOUT = 30.0  # 30 seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 1 second between retries
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=orchestrator --cov-report=term-missing

# Run specific test file
pytest tests/test_orchestrator.py

# Run specific test
pytest tests/test_orchestrator.py::TestRoutingToResearch::test_route_to_research_get
```

## Architecture

The Orchestrator acts as an API Gateway that:

1. **Routes requests** to the appropriate module based on path
2. **Aggregates health** from all modules for monitoring
3. **Handles failures** with automatic retry and timeout logic
4. **Provides CORS** support for frontend applications

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       v
┌─────────────────┐
│  Orchestrator   │ (port 8003)
│   API Gateway   │
└────────┬────────┘
         │
    ┌────┼────┐
    │    │    │
    v    v    v
┌────┐ ┌──────┐ ┌────────┐
│Writer│ │Research│ │Backend │
│:8000 │ │:8001   │ │:8002   │
└────┘ ┌──────┘ └────────┘
```

## Success Criteria

✅ Routes to all 3 modules (Writer, Research, Backend)
✅ Health endpoint aggregates status from all services
✅ Timeout works (30s)
✅ Retry works (3x)
✅ Tests pass
✅ CORS configured

## Dependencies

- FastAPI >= 0.104.0
- uvicorn >= 0.24.0
- httpx >= 0.25.0 (for async HTTP client with retry)
- pydantic >= 2.5.0

## Related Documentation

- [Technical Proposal](/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md)
- [PHI Agent Prompt](/.github/prompts/orchestrator/phi.md)
