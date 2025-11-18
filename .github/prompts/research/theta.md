## Agent: THETA (Research Module)
**Duration:** 2 hours  
**Branch:** `research`  
**Dependencies:** None (parallel)

### Task
Create FastAPI skeleton with 3 endpoints

### Endpoints
1. POST /api/enrich - Card enrichment
2. POST /api/scrape - Trigger scraping
3. GET /health - Health check

### Technical Reference
- `/docs/pm/research/TECHNICAL-PROPOSAL-RESEARCH.md`
- `research/dev/fastapi/`

### Deliverables
- `research/backend/main.py`
- All 3 endpoints
- CORS for Writer
- Pydantic models
- Logging

### Success Criteria
✅ All endpoints respond  
✅ CORS configured  
✅ Pydantic validation  
✅ Health returns 200  
✅ Tests pass

**Update this issue when complete.**
