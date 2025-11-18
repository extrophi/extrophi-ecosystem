## Agent: OMEGA (Orchestrator Module)
**Duration:** 1 hour
**Branch:** `orchestrator`
**Dependencies:** PHI #42, CHI #43
**Priority:** OPTIONAL (defer if time-constrained)

### Task
Build service registry for dynamic service discovery (optional enhancement)

### Technical Reference
- `/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md`

### Deliverables
- `orchestrator/registry/service_registry.py`
- Service registration
- Service discovery
- Health-based routing
- Automatic failover

### Why Service Registry?
- Dynamic service discovery (no hardcoded ports)
- Load balancing (route to healthy instances)
- Automatic failover (if service down)
- Multi-instance support (scale horizontally)

### Implementation
```python
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class ServiceInstance:
    name: str  # "writer", "research", "backend"
    host: str  # "localhost"
    port: int  # 8000, 8001, 8002
    healthy: bool = True
    last_check: datetime = None
    metadata: dict = None

class ServiceRegistry:
    def __init__(self):
        self.services: dict[str, list[ServiceInstance]] = {}

    def register(
        self,
        name: str,
        host: str,
        port: int,
        metadata: dict = None
    ) -> ServiceInstance:
        """Register a service instance"""
        instance = ServiceInstance(
            name=name,
            host=host,
            port=port,
            metadata=metadata or {}
        )

        if name not in self.services:
            self.services[name] = []

        self.services[name].append(instance)
        return instance

    def get_instance(
        self,
        service_name: str,
        require_healthy: bool = True
    ) -> ServiceInstance | None:
        """Get service instance (load-balanced, round-robin)"""
        instances = self.services.get(service_name, [])

        if require_healthy:
            instances = [i for i in instances if i.healthy]

        if not instances:
            return None

        # Round-robin selection
        # (In production, use more sophisticated load balancing)
        return instances[0]

    def get_all_instances(self, service_name: str) -> list[ServiceInstance]:
        """Get all instances of a service"""
        return self.services.get(service_name, [])

    def mark_unhealthy(self, instance: ServiceInstance):
        """Mark instance as unhealthy"""
        instance.healthy = False
        instance.last_check = datetime.now()

    def mark_healthy(self, instance: ServiceInstance):
        """Mark instance as healthy"""
        instance.healthy = True
        instance.last_check = datetime.now()

# Integration with API Gateway (PHI)
registry = ServiceRegistry()

# Register services on startup
@app.on_event("startup")
async def register_services():
    registry.register("writer", "localhost", 8000)
    registry.register("research", "localhost", 8001)
    registry.register("backend", "localhost", 8002)

# Use registry in routing
@app.post("/api/enrich")
async def route_enrich(request: dict):
    # Get healthy research instance
    instance = registry.get_instance("research")

    if not instance:
        raise HTTPException(503, "Research service unavailable")

    # Forward request
    url = f"http://{instance.host}:{instance.port}/api/enrich"
    response = await http.post(url, json=request)

    return response.json()

# Health check updates registry
async def health_check_loop():
    while True:
        for service_name in ["writer", "research", "backend"]:
            instances = registry.get_all_instances(service_name)

            for instance in instances:
                try:
                    response = await http.get(
                        f"http://{instance.host}:{instance.port}/health",
                        timeout=2.0
                    )

                    if response.status_code == 200:
                        registry.mark_healthy(instance)
                    else:
                        registry.mark_unhealthy(instance)

                except Exception:
                    registry.mark_unhealthy(instance)

        await asyncio.sleep(30)  # Check every 30s
```

### Endpoints
```python
# Get registered services
GET /registry/services
→ {
    "writer": [{"host": "localhost", "port": 8000, "healthy": true}],
    "research": [{"host": "localhost", "port": 8001, "healthy": true}],
    "backend": [{"host": "localhost", "port": 8002, "healthy": true}]
  }

# Register new instance
POST /registry/register
{
  "name": "research",
  "host": "localhost",
  "port": 8003
}

# Deregister instance
DELETE /registry/deregister/{service_name}/{host}/{port}
```

### Success Criteria
✅ Service registration works
✅ Service discovery returns healthy instances
✅ Health checks update registry status
✅ Failover routes to healthy instance
✅ Multi-instance support works
✅ Tests pass

### Commit Message
```
feat(orchestrator): Add service registry (optional)

Implements dynamic service discovery:
- Service registration/deregistration
- Health-based instance selection
- Automatic failover
- Multi-instance support
- Round-robin load balancing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #61 when complete.**
