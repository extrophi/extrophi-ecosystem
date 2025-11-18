# Service Registry - Dynamic Service Discovery

Consul-based service registry for automatic service registration, discovery, and health monitoring across the Extrophi ecosystem.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Consul Service Registry                  │
│                    (localhost:8500/ui)                       │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    Register/              Register/           Register/
    Discover               Discover            Discover
         │                    │                    │
┌────────┴────────┐  ┌───────┴────────┐  ┌────────┴────────┐
│   Backend API   │  │  Research API   │  │ Orchestrator API │
│   (port 8002)   │  │   (port 8001)   │  │   (port 8003)    │
└─────────────────┘  └─────────────────┘  └──────────────────┘
```

### Components

1. **ServiceRegistry** - Core registration and discovery logic
   - Register services with health checks
   - Discover services by name or tag
   - Load balance across multiple instances
   - Auto-deregister unhealthy services

2. **ServiceDiscoveryClient** - HTTP client with auto-discovery
   - Automatically resolve service names to URLs
   - Make cross-service HTTP calls
   - Retry logic with exponential backoff
   - Convenience methods (get, post, put, delete, patch)

3. **Consul** - Service registry backend
   - Distributed key-value store
   - Health checking (HTTP endpoints)
   - Service catalog with tags and metadata
   - Web UI for monitoring

## Quick Start

### 1. Start Consul and Services

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Verify Consul is running
curl http://localhost:8500/v1/status/leader

# Check Consul UI
open http://localhost:8500/ui
```

### 2. Register a Service

```python
from orchestrator.registry import ServiceRegistry

# Initialize registry
registry = ServiceRegistry(host="localhost", port=8500)

# Register service
service_id = registry.register_service(
    name="backend-api",
    address="localhost",
    port=8000,
    tags=["api", "backend"],
    health_check_interval="10s",
)

print(f"Service registered: {service_id}")
# Output: Service registered: backend-api-localhost-8000
```

### 3. Discover Services

```python
# Get service URL (with load balancing)
url = registry.get_service_url("backend-api")
print(url)  # http://localhost:8000

# Discover all instances
instances = registry.discover_service("backend-api")
for instance in instances:
    print(f"{instance['address']}:{instance['port']}")

# List all services
all_services = registry.discover_all_services()
print(all_services)
# {'backend-api': ['api', 'backend'], 'research-api': ['api', 'research']}
```

### 4. Make Cross-Service Calls

```python
from orchestrator.registry import ServiceRegistry, ServiceDiscoveryClient

# Initialize
registry = ServiceRegistry()
client = ServiceDiscoveryClient(registry)

# Make requests (service name instead of URL)
response = await client.get("backend-api", "/health")
print(response.json())  # {'status': 'healthy'}

# POST with JSON body
response = await client.post(
    "backend-api",
    "/api/publish",
    json={"title": "Test Card", "content": "Hello world"}
)
print(response.status_code)  # 201

# PUT, DELETE, PATCH also supported
await client.put("backend-api", "/api/cards/123", json={...})
await client.delete("backend-api", "/api/cards/123")
await client.patch("backend-api", "/api/cards/123", json={...})
```

## Integration with FastAPI

### Auto-Registration on Startup

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from orchestrator.registry import ServiceRegistry
import os

# Global registry instance
registry = None
service_id = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Register on startup, deregister on shutdown."""
    global registry, service_id

    # Startup - Register with Consul
    consul_host = os.getenv("CONSUL_HOST", "localhost")
    consul_port = int(os.getenv("CONSUL_PORT", "8500"))

    registry = ServiceRegistry(host=consul_host, port=consul_port)

    service_id = registry.register_service(
        name=os.getenv("SERVICE_NAME", "backend-api"),
        address=os.getenv("SERVICE_ADDRESS", "localhost"),
        port=int(os.getenv("SERVICE_PORT", "8000")),
        tags=os.getenv("SERVICE_TAGS", "api").split(","),
        health_check_interval="10s",
    )

    print(f"✓ Registered with Consul: {service_id}")

    yield

    # Shutdown - Deregister from Consul
    if registry and service_id:
        registry.deregister_service(service_id)
        print(f"✓ Deregistered from Consul: {service_id}")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    """Health check endpoint (required for Consul)."""
    return {"status": "healthy"}
```

### Environment Variables

Configure service registration via environment variables:

```bash
# Consul connection
CONSUL_HOST=localhost
CONSUL_PORT=8500

# Service identity
SERVICE_NAME=backend-api
SERVICE_ADDRESS=localhost
SERVICE_PORT=8000
SERVICE_TAGS=api,backend,publish
```

## Health Checks

Consul automatically polls the `/health` endpoint every 10 seconds:

```
┌─────────┐         GET /health         ┌──────────┐
│ Consul  │ ─────────────────────────► │ Backend  │
│         │ ◄───────────────────────── │   API    │
└─────────┘    200 OK {"status": "healthy"}  └──────────┘
```

If a service fails 3 consecutive health checks (30s), it is automatically deregistered.

### Custom Health Check

```python
@app.get("/health")
async def health():
    """Health check with dependency validation."""
    # Check database
    try:
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Check Redis
    try:
        await redis.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    overall_status = "healthy" if all([
        db_status == "healthy",
        redis_status == "healthy",
    ]) else "unhealthy"

    return {
        "status": overall_status,
        "components": {
            "database": db_status,
            "cache": redis_status,
        }
    }
```

## Load Balancing

When multiple instances of a service are registered, `get_service_url()` randomly selects one:

```python
# Register 3 instances
registry.register_service("backend-api", "host1", 8000)
registry.register_service("backend-api", "host2", 8000)
registry.register_service("backend-api", "host3", 8000)

# Calls are distributed randomly
for i in range(10):
    url = registry.get_service_url("backend-api")
    print(url)
    # http://host1:8000
    # http://host3:8000
    # http://host2:8000
    # http://host1:8000
    # ... (random distribution)
```

## Error Handling

### Service Not Found

```python
url = registry.get_service_url("nonexistent-service")
# Returns: None

# Discovery client raises ValueError
await client.get("nonexistent-service", "/health")
# Raises: ValueError: Service 'nonexistent-service' not found in registry
```

### Network Errors with Retry

```python
# ServiceDiscoveryClient automatically retries on network errors
client = ServiceDiscoveryClient(
    registry,
    timeout=10.0,
    max_retries=3,
    retry_delay=1.0,
)

# Retries on:
# - TimeoutException (3 attempts, 1s delay between)
# - RequestError (network failures)
# - HTTPStatusError (5xx errors only, not 4xx)

response = await client.get("backend-api", "/slow-endpoint")
# If first attempt times out, automatically retries up to 3 times
```

## Consul UI

Monitor services at http://localhost:8500/ui:

- **Services** - View all registered services and their health
- **Nodes** - View Consul cluster nodes
- **Key/Value** - Store configuration (not used yet)
- **Intentions** - Service mesh access control (advanced)

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest orchestrator/tests/test_service_registry.py -v

# Run with coverage
pytest orchestrator/tests/test_service_registry.py --cov=orchestrator.registry --cov-report=html

# Open coverage report
open htmlcov/index.html
```

Test coverage: **29 tests** covering:
- Service registration (4 tests)
- Service deregistration (2 tests)
- Service discovery (5 tests)
- URL and health checks (5 tests)
- Discovery client (7 tests)
- Error handling (6 tests)

## Production Deployment

### Docker Compose (Recommended)

```bash
# Start all services with Consul
docker-compose up -d

# View logs
docker-compose logs -f consul backend research

# Scale a service
docker-compose up -d --scale backend=3

# Verify registration
curl http://localhost:8500/v1/catalog/service/backend-api
```

### Manual Deployment

1. **Install Consul**:
   ```bash
   # macOS
   brew install consul

   # Ubuntu
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install consul
   ```

2. **Start Consul**:
   ```bash
   # Development mode (single node)
   consul agent -dev -ui -client=0.0.0.0

   # Production mode (3-5 nodes recommended)
   consul agent -server -bootstrap-expect=3 -data-dir=/var/consul -ui -client=0.0.0.0
   ```

3. **Configure Services**:
   ```bash
   # Export environment variables
   export CONSUL_HOST=localhost
   export CONSUL_PORT=8500
   export SERVICE_NAME=backend-api
   export SERVICE_PORT=8000

   # Start service (auto-registers via lifespan)
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

## Troubleshooting

### Service not registering

```bash
# Check Consul is running
curl http://localhost:8500/v1/status/leader

# Check service logs for registration errors
docker-compose logs backend | grep -i consul

# Verify health endpoint is accessible
curl http://localhost:8002/health
```

### Service shows unhealthy

```bash
# Check health endpoint
curl http://localhost:8002/health

# View Consul checks
curl http://localhost:8500/v1/health/checks/backend-api

# Check service logs
docker-compose logs backend
```

### Discovery client timeout

```bash
# Increase timeout
client = ServiceDiscoveryClient(registry, timeout=60.0)

# Check target service is healthy
curl http://localhost:8500/v1/health/service/backend-api?passing=true
```

## API Reference

### ServiceRegistry

- `register_service()` - Register a service with health check
- `deregister_service()` - Remove a service from registry
- `discover_service()` - Find all instances of a service
- `discover_all_services()` - List all registered services
- `get_service_url()` - Get URL for a service (with load balancing)
- `get_service_health()` - Check health of a specific instance
- `is_healthy()` - Verify Consul connection

### ServiceDiscoveryClient

- `call_service()` - Make HTTP request with auto-discovery
- `get()` - GET request
- `post()` - POST request
- `put()` - PUT request
- `delete()` - DELETE request
- `patch()` - PATCH request

## Next Steps

1. **Add ACL tokens** for production security
2. **Implement service mesh** with Consul Connect (mTLS)
3. **Add distributed tracing** with OpenTelemetry
4. **Implement circuit breakers** for fault tolerance
5. **Add rate limiting** per service

## References

- [Consul Documentation](https://www.consul.io/docs)
- [python-consul Library](https://python-consul.readthedocs.io/)
- [Service Discovery Patterns](https://microservices.io/patterns/service-registry.html)
- [Health Check Best Practices](https://www.consul.io/docs/discovery/checks)
