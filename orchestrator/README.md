# Orchestrator Module

Service orchestration and health monitoring for the Extrophi Ecosystem.

## Overview

The Orchestrator module coordinates communication between the three main services:
- **Writer** (port 8000) - BrainDump v3.0 voice journaling app
- **Research** (port 8001) - IAC-032 unified scraper
- **Backend** (port 8002) - IAC-011 sovereign backend

## Features

### Health Monitoring (CHI Agent)
- **Automatic health checks** every 30 seconds
- **Circuit breaker pattern** to prevent hammering unhealthy services
- **Concurrent service checks** for all 3 services
- **Uptime tracking** with success/failure statistics
- **Detailed status reporting** via REST API

### Circuit Breaker
The health monitoring system implements a circuit breaker pattern:
- **Closed**: Normal operation, health checks proceed
- **Open**: Service consistently failing, checks suspended for 60 seconds
- **Half-Open**: Testing if service recovered after timeout

Default thresholds:
- Open circuit after **5 consecutive failures**
- Close circuit after **2 consecutive successes**
- Timeout: **60 seconds**

## Installation

### Using UV (recommended)

```bash
cd orchestrator
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

uv pip install -e .
```

### Using pip

```bash
cd orchestrator
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

### Start the Orchestrator

```bash
# From orchestrator directory
python -m orchestrator.main

# Or using uvicorn directly
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8003 --reload
```

The service will start on **http://localhost:8003**

### API Endpoints

#### `GET /`
Root endpoint with service information
```json
{
  "service": "Orchestrator",
  "version": "0.1.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "health_status": "/health/status"
  }
}
```

#### `GET /health`
Basic health check for the orchestrator service itself
```json
{
  "status": "ok",
  "service": "orchestrator"
}
```

#### `GET /health/status`
Detailed health status of all monitored services
```json
{
  "timestamp": "2025-11-18T12:00:00.000000",
  "services": {
    "writer": {
      "health": "healthy",
      "last_check": "2025-11-18T12:00:00.000000",
      "response_time_ms": 45.2,
      "error_message": null,
      "consecutive_failures": 0,
      "total_checks": 120,
      "successful_checks": 118,
      "uptime_percentage": 98.33,
      "circuit_breaker_state": "closed"
    },
    "research": { ... },
    "backend": { ... }
  },
  "overall_health": "healthy"
}
```

**Health States:**
- `healthy` - Service responding normally
- `unhealthy` - Service unreachable or errors
- `unknown` - Not yet checked
- `circuit_open` - Circuit breaker activated

**Overall Health:**
- `healthy` - All services healthy
- `degraded` - Some services healthy, some unhealthy
- `unhealthy` - No services healthy

#### `POST /health/trigger`
Manually trigger an immediate health check of all services
```json
{
  "timestamp": "2025-11-18T12:00:00.000000",
  "services": { ... }
}
```

## Configuration

### Environment Variables

Create a `.env` file in the orchestrator directory:

```bash
# Service URLs (defaults shown)
WRITER_URL=http://localhost:8000/health
RESEARCH_URL=http://localhost:8001/health
BACKEND_URL=http://localhost:8002/health

# Health check settings
HEALTH_CHECK_INTERVAL=30  # seconds
HEALTH_CHECK_TIMEOUT=5    # seconds
CIRCUIT_BREAKER_THRESHOLD=5  # failures before opening
```

### Customizing Health Checker

```python
from orchestrator.monitoring.health_checker import HealthChecker

health_checker = HealthChecker(
    check_interval=30,      # Check every 30 seconds
    timeout=5.0,           # 5 second request timeout
    failure_threshold=5    # Open circuit after 5 failures
)

# Start monitoring
health_checker.start()

# Get current status
status = health_checker.get_status()

# Stop monitoring
await health_checker.stop()
```

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=orchestrator --cov-report=html

# Watch mode
pytest-watch
```

### Code Quality

```bash
# Format code
black orchestrator/
isort orchestrator/

# Lint
ruff orchestrator/

# Type check
mypy orchestrator/
```

## Architecture

### Health Monitoring Flow

```
┌─────────────────┐
│  FastAPI App    │
│  (Port 8003)    │
└────────┬────────┘
         │
         │ Lifespan Events
         │
         ▼
┌─────────────────┐
│ HealthChecker   │◄─── Background Task (30s interval)
│                 │
│ ┌─────────────┐ │
│ │Circuit      │ │     Check Writer:8000
│ │Breakers     │ │────►Check Research:8001
│ │(3 services) │ │     Check Backend:8002
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │Status Store │ │
│ │(in-memory)  │ │
│ └─────────────┘ │
└─────────────────┘
```

### Circuit Breaker State Machine

```
     ┌──────┐
     │Closed│◄──────────────┐
     └───┬──┘               │
         │                  │
         │ 5 failures       │ 2 successes
         │                  │
         ▼                  │
     ┌──────┐          ┌────┴────┐
     │ Open │─────────►│Half-Open│
     └──────┘          └─────────┘
      60s timeout
```

## Testing Strategy

### Unit Tests
- Circuit breaker logic
- Health check success/failure scenarios
- Status calculation
- Uptime percentage calculation

### Integration Tests
- FastAPI endpoint responses
- Background task lifecycle
- Concurrent service checks
- Error handling

### Coverage Goal
- **Target**: 80%+ code coverage
- **Current**: Run `pytest --cov` to check

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY orchestrator/ /app/orchestrator/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Systemd Service

```ini
[Unit]
Description=Orchestrator Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/extrophi-ecosystem/orchestrator
Environment="PATH=/opt/extrophi-ecosystem/orchestrator/.venv/bin"
ExecStart=/opt/extrophi-ecosystem/orchestrator/.venv/bin/uvicorn orchestrator.main:app --host 0.0.0.0 --port 8003
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring

### Metrics
The `/health/status` endpoint provides:
- Response time per service
- Uptime percentage
- Total/successful check counts
- Circuit breaker states

### Logging
Health check events are logged:
- Service health changes
- Circuit breaker state transitions
- Connection errors
- Timeouts

## Troubleshooting

### Issue: All services showing "circuit_open"
**Cause**: Services are down or unreachable
**Solution**:
1. Check if Writer, Research, and Backend services are running
2. Verify port numbers (8000, 8001, 8002)
3. Wait 60 seconds for circuit breaker to enter half-open state

### Issue: High response times
**Cause**: Services under load or network issues
**Solution**:
1. Check service logs for performance issues
2. Consider increasing timeout value
3. Monitor overall system resources

### Issue: Inconsistent health status
**Cause**: Services starting/stopping or network instability
**Solution**:
1. Check service logs
2. Verify network connectivity
3. Ensure services have `/health` endpoints

## Related Documentation

- [Technical Proposal](/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md)
- [Writer Module](/writer/README.md)
- [Research Module](/research/README.md)
- [Backend Module](/backend/README.md)

## License

Part of the IAC-033 Extrophi Ecosystem project.
