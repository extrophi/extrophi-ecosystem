# Orchestrator Module

API Gateway for coordinating Writer, Research, and Backend modules in the Extrophi Ecosystem.

## Features

- **Request Routing**: Routes requests to appropriate services
  - `/api/enrich` → Research module (port 8001)
  - `/api/publish` → Backend module (port 8002)
- **Health Monitoring**: Continuous health monitoring with circuit breaker pattern
  - Background health checks every 30 seconds
  - Circuit breaker for fault tolerance
  - Service uptime tracking
  - Detailed status reporting via `/health/status` endpoint
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

### Health Status (Detailed Monitoring)
```
GET /health/status
```
Returns detailed health status from the continuous monitoring system, updated every 30 seconds.

Response example:
```json
{
  "overall": "healthy",
  "timestamp": "2025-11-18T12:00:00",
  "services": {
    "writer": {
      "name": "writer",
      "url": "http://localhost:8000",
      "status": "healthy",
      "last_check": "2025-11-18T12:00:00",
      "response_time_ms": 150.5,
      "error": null,
      "circuit_state": "closed",
      "consecutive_failures": 0,
      "uptime_percentage": 99.5,
      "details": {}
    },
    "research": { "..." },
    "backend": { "..." }
  },
  "monitoring": {
    "check_interval": 30,
    "running": true
  }
}
```

### Service-Specific Health Status
```
GET /health/status/{service_name}
```
Returns detailed health status for a specific service (writer, research, or backend).

Available services:
- `/health/status/writer`
- `/health/status/research`
- `/health/status/backend`

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

### PHI Agent (API Gateway)
✅ Routes to all 3 modules (Writer, Research, Backend)
✅ Health endpoint aggregates status from all services
✅ Timeout works (30s)
✅ Retry works (3x)
✅ Tests pass
✅ CORS configured

### CHI Agent (Health Monitoring)
✅ Background monitoring runs every 30 seconds
✅ Checks all 3 services (Writer, Research, Backend)
✅ Stores status with uptime tracking
✅ `/health/status` endpoint works
✅ Circuit breaker pattern implemented
✅ Tests pass (25 health checker tests + 30 integration tests)

## Dependencies

- FastAPI >= 0.104.0
- uvicorn >= 0.24.0
- httpx >= 0.25.0 (for async HTTP client with retry)
- pydantic >= 2.5.0

## Health Monitoring System

The orchestrator includes a sophisticated health monitoring system built on the circuit breaker pattern for fault tolerance.

### Circuit Breaker Pattern

The circuit breaker prevents cascading failures by monitoring service health and temporarily blocking requests to unhealthy services.

**States:**
- **CLOSED**: Normal operation, requests allowed
- **OPEN**: Too many failures detected, requests blocked
- **HALF_OPEN**: Testing if service has recovered

**Configuration:**
- `failure_threshold`: 3 consecutive failures → OPEN
- `timeout`: 60 seconds before attempting recovery
- `success_threshold`: 2 consecutive successes → CLOSED

### Background Monitoring

The health checker runs as a background task that:
1. Checks all services every 30 seconds
2. Records response times and success/failure
3. Updates circuit breaker states
4. Calculates uptime percentages (last 100 checks)
5. Stores detailed status for each service

### Monitoring Data

Each service health status includes:
- **Status**: healthy, unhealthy, degraded, unknown
- **Last Check**: Timestamp of last health check
- **Response Time**: Milliseconds for health check
- **Circuit State**: Current circuit breaker state
- **Consecutive Failures**: Count of failures in a row
- **Uptime Percentage**: Success rate over recent checks
- **Error Details**: Specific error message if unhealthy

## Related Documentation

- [Technical Proposal](/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md)
- [PHI Agent Prompt](/.github/prompts/orchestrator/phi.md)
- [CHI Agent Prompt](/.github/prompts/orchestrator/chi.md)
