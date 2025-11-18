## Agent: KAPPA (Research Module)
**Duration:** 2 hours  
**Branch:** `research`  
**Dependencies:** None (parallel)

### Task
Set up PostgreSQL + pgvector

### Technical Reference
- `/docs/pm/research/TECHNICAL-PROPOSAL-RESEARCH.md`

### Deliverables
- `research/backend/db/schema.sql`
- PostgreSQL created
- pgvector enabled
- Connection module
- CRUD operations
- Vector similarity search

### Schema
```sql
CREATE EXTENSION vector;
CREATE TABLE contents (
  id UUID PRIMARY KEY,
  embedding vector(1536),
  ...
);
```

### Success Criteria
✅ Database created  
✅ pgvector enabled  
✅ Vector search works  
✅ Tests pass

**Update this issue when complete.**
