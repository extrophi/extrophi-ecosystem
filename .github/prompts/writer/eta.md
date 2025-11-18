## Agent: ETA (Writer Module)
**Duration:** 1 hour  
**Branch:** `writer`  
**Dependencies:** None (parallel)

### Task
Update SQLite schema for privacy_level, git_sha, published

### Technical Reference
- `/docs/pm/writer/TECHNICAL-PROPOSAL-WRITER.md` (lines 809-891)

### Deliverables
- `src-tauri/src/db/schema.sql` updated
- `src-tauri/src/db/migration.rs` created
- Migration tested
- Rust code updated

### Schema
```sql
privacy_level TEXT CHECK(privacy_level IN (
  'PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS'
)),
published INTEGER DEFAULT 0,
git_sha TEXT
```

### Success Criteria
✅ Migration runs successfully  
✅ Data preserved  
✅ New columns added  
✅ Indexes created  
✅ `cargo test` passes

**Update this issue when complete.**
