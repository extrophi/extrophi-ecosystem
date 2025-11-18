## Agent: OMICRON (Backend Module)
**Duration:** 1 hour  
**Branch:** `backend`  
**Dependencies:** None (parallel)

### Task
Design PostgreSQL schema

### Tables
1. cards - User cards
2. users - Accounts + $EXTROPY
3. attributions - Citations
4. extropy_ledger - Transactions
5. sync_state - Sync status

### CRITICAL
✅ DECIMAL for money (NOT float)  
✅ Database transactions  
✅ No negative balances  
✅ Foreign keys

### Technical Reference
- `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`

### Deliverables
- `backend/db/schema.sql`
- All 5 tables
- Constraints + indexes
- Triggers
- Migration script

### Success Criteria
✅ Schema creates  
✅ Constraints work  
✅ Triggers prevent negatives  
✅ Tests pass

**Update this issue when complete.**
