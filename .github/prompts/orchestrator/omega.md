# IAC-033 Extrophi Ecosystem - OMEGA Agent
## Service Registry for Dynamic Discovery

See full prompt in issue #73

**Repository**: https://github.com/extrophi/extrophi-ecosystem  
**Branch**: `claude/service-registry-omega`  
**Issue**: Closes #73  
**Duration**: 1 hour

## Quick Start

```bash
# Create branch
git checkout -b claude/service-registry-omega

# Install Consul client
pip install python-consul==1.1.0

# Create registry directory
mkdir -p orchestrator/registry
```

## Mission
Implement Consul-based service registry for dynamic service discovery across modules.

## Files to Create

1. **`orchestrator/registry/service_registry.py`** (200+ lines)
   - ServiceRegistry class
   - register_service()
   - deregister_service()
   - discover_service()
   - discover_all_services()
   - get_service_url()

2. **`orchestrator/registry/discovery_client.py`** (100+ lines)
   - ServiceDiscoveryClient
   - call_service() - HTTP client with auto-discovery

3. **`orchestrator/tests/test_service_registry.py`** (150+ lines)
   - Registration tests
   - Discovery tests
   - Load balancing tests
   - Mock Consul responses

4. **`docker-compose.yml`** (root)
   - Consul service (port 8500)
   - Backend service (auto-register)
   - Research service (auto-register)
   - Postgres + Redis

5. **`orchestrator/registry/README.md`**
   - Architecture diagram
   - Usage examples

## Key Features

### Auto-Registration
```python
# On startup
registry.register_service(
    name="backend-api",
    address="localhost",
    port=8000,
    tags=["api", "backend"],
    health_check_interval="10s"
)
```

### Service Discovery
```python
# Find service
url = registry.get_service_url("backend-api")
# Returns: "http://localhost:8000"

# Call discovered service
client = ServiceDiscoveryClient(registry)
response = await client.call_service(
    "backend-api",
    "/publish",
    method="POST",
    data={"title": "Test"}
)
```

### Health Checks
- Consul hits `/health` every 10s
- Unhealthy services auto-deregistered after 30s

## Docker Compose Structure

```yaml
services:
  consul:
    image: consul:1.17
    ports:
      - "8500:8500"  # UI + API
  
  backend:
    depends_on: [consul, postgres]
    environment:
      CONSUL_HOST: consul
      SERVICE_ADDRESS: backend
      SERVICE_PORT: 8000
  
  research:
    depends_on: [consul, postgres]
    environment:
      CONSUL_HOST: consul
```

## Update Files
- `backend/main.py` - Add lifespan for auto-registration
- `research/main.py` - Add lifespan for auto-registration
- `backend/pyproject.toml` - Add python-consul

## Success Criteria
- ✅ Consul UI at `localhost:8500`
- ✅ Services auto-register on startup
- ✅ Health checks every 10s
- ✅ Service discovery working
- ✅ Graceful deregistration
- ✅ Docker Compose working
- ✅ 15+ tests passing

**When complete**: Create PR "Wave 2 Phase 3: OMEGA - Service Registry"
