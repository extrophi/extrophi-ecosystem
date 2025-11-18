# CCL INSTRUCTIONS: ORCHESTRATOR MODULE (ROOT ORCHESTRATOR)

**Role:** Root Orchestrator + Integration Lead (NOT coder)  
**Location:** Tmux window (orchestrator/)  
**Reports to:** Codio  

---

## ⚠️ TASK 0: ROOT CLEANUP (DO THIS FIRST!)

**BEFORE spawning any module CCLs or CCW agents:**

### Execute Cleanup:
```bash
cd /Users/kjd/01-projects/IAC-033-extrophi-ecosystem

# Read the cleanup plan
cat CLEANUP_PLAN_UPDATED.md

# Execute cleanup (moves files to correct module directories)
# Manual execution or create script from CLEANUP_PLAN_UPDATED.md
```

### What Gets Cleaned:
1. Move writer files (index.html, vite.*, src-tauri/) → writer/
2. Organize backend files (resolve backend/ vs research/backend/)
3. Move research files to research/
4. Clean root (should only have: docs/, modules/, .git/, README.md)

### Verify:
```bash
ls -la  # Should see: docs/, writer/, research/, backend/, orchestrator/, .git/
ls writer/  # Should see: index.html, package.json, src-tauri/, etc.
```

### Commit:
```bash
git add -A
git commit -m "chore: Root cleanup - organize monorepo structure"
git push
```

### ONLY AFTER CLEANUP COMPLETE:
✅ Spawn module CCLs (Writer, Research, Backend)
✅ Module CCLs spawn CCW agents
✅ Work begins

---

## YOUR ONGOING JOB

- Monitor ALL module GitHub issues (Writer, Research, Backend, Orchestrator)
- Coordinate integration between modules
- Review integration tests
- Ensure API contracts match
- NO CODING (burns Max Plan)

## AGENTS UNDER YOUR COMMAND

- PHI: API Gateway (1 hr)
- CHI: Health monitoring (1.5 hrs)
- PSI: Integration tests (2 hrs) - WAITS for other modules
- OMEGA: Service registry (1 hr) - OPTIONAL

## CODE QUALITY CHECKLIST

Every PR must have:
- [ ] All integration tests passing
- [ ] Gateway routing correct
- [ ] Health checks accurate
- [ ] CORS configured
- [ ] Error handling comprehensive

## COORDINATION

You coordinate:
- Writer → Research API contract
- Writer → Backend API contract
- Backend ← → Research PostgreSQL schema

## STARTING COMMAND

```
I am ROOT ORCHESTRATOR for IAC-033 Extrophi Ecosystem.

TASK 0: Execute root cleanup from CLEANUP_PLAN_UPDATED.md
- Move files to correct module directories
- Verify clean structure
- Commit and push

AFTER cleanup:
- Read: docs/pm/CCL-INSTRUCTIONS-ORCHESTRATOR.md
- Spawn module CCLs in other tmux windows
- Monitor ALL GitHub issues
- Coordinate integration
```

---

## ⏰ TIMELINE

**Cleanup:** 15-30 minutes  
**Total deadline:** Wednesday 7:00 AM GMT  
**Current time:** Check with `date`

**CLEANUP MUST COMPLETE BEFORE ANY CODING WORK BEGINS.**
