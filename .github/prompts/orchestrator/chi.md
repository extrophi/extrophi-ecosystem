## Agent: CHI (Orchestrator Module)
**Duration:** 1.5 hours  
**Branch:** `orchestrator`  
**Dependencies:** None (parallel)

### Task
Health monitoring every 30s

### Technical Reference
- `/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md`

### Deliverables
- `orchestrator/monitoring/health_checker.py`
- Async task (30s)
- Check Writer (8000)
- Check Research (8001)
- Check Backend (8002)
- /health/status endpoint
- Circuit breaker

### Success Criteria
✅ Runs every 30s  
✅ Checks all 3 services  
✅ Stores status  
✅ Endpoint works  
✅ Circuit breaker  
✅ Tests pass

**Update this issue when complete.**
