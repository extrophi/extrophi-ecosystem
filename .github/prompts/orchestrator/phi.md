## Agent: PHI (Orchestrator Module)
**Duration:** 1 hour  
**Branch:** `orchestrator`  
**Dependencies:** None (parallel)

### Task
Implement API Gateway

### Routing
- /api/enrich → Research (8001)
- /api/publish → Backend (8002)
- /health → Aggregate all

### Technical Reference
- `/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md`

### Deliverables
- `orchestrator/main.py`
- Request routing
- Timeout (30s)
- Retry (3x)
- CORS

### Success Criteria
✅ Routes to all 3 modules  
✅ Health aggregates  
✅ Timeout works  
✅ Retry works  
✅ Tests pass

**Update this issue when complete.**
