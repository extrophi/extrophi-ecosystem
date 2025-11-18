# CCW Orchestrator Instructions

<<<<<<< HEAD
You are the Claude Code Web orchestrator. Your job is to spawn sub-agents and coordinate work across the BrainDump v3.1 codebase.

## Your Capabilities
- You have access to the full GitHub repo
- You can spawn multiple parallel sub-agents
- You have $750 credits to burn by Tuesday
- Each sub-agent you spawn uses these credits (NOT local Max Plan credits)

## Immediate Tasks to Spawn

### Agent 1: Rust Backend Fixes
**Task**: Fix compilation errors in src-tauri/
- Fix `src-tauri/src/commands.rs`
- Fix `src-tauri/src/services/claude_api.rs`
- Fix `src-tauri/src/services/openai_api.rs`
- Run `cargo check --all-features` and fix all errors

### Agent 2: Frontend Validation
**Task**: Validate all Svelte components compile
- Run `npm run check`
- Fix any TypeScript errors in `src/`
- Ensure all imports resolve correctly

### Agent 3: Integration Testing
**Task**: Test full application flow
- Test provider persistence (OpenAI vs Claude)
- Test chat routing to correct backend
- Test session CRUD operations
- Test audio playback

### Agent 4: CI/CD Pipeline Monitoring
**Task**: Monitor PR #22 CI status
- Check all 5 jobs pass (rust-check macOS, rust-check Ubuntu, frontend, build, security)
- Fix any failing checks
- Push fixes to branch `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`

### Agent 5: Database Migration Testing
**Task**: Verify migrations V1 through V8
- Test schema upgrades work
- Test data integrity maintained
- Verify no breaking changes

## Coordination Pattern

1. **Read this file** - Get your instructions
2. **Spawn agents** - Create parallel sub-agents for each task above
3. **Collect results** - Wait for each agent to complete
4. **Push to repo** - Commit all fixes to the branch
5. **Report back** - Create `docs/agents/CCW_REPORT.md` with results

## Git Workflow

```bash
git pull origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
# Make changes
git add -A
git commit -m "fix: [Agent description of fix]"
git push origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
```

## Success Criteria

- [ ] All Rust compilation errors fixed
- [ ] Frontend builds with no errors
- [ ] CI pipeline passes all checks
- [ ] PR #22 ready for merge
- [ ] All 14 features from v3.1 working

## Priority

BURN THOSE $750 CREDITS! Spawn as many agents as needed. Do the actual coding work. Local Claude Code instances should NOT be doing this - YOU are the orchestrator, YOU spawn the sub-agents, YOU burn the credits.

**START NOW. SPAWN AGENTS IMMEDIATELY.**
=======
**COPY EVERYTHING BELOW INTO CLAUDE CODE WEB**

---

Clone https://github.com/Iamcodio/IAC-032-unified-scraper.git

Read these 4 files in .claude/agents/:
- twitter-scraper.md
- reddit-scraper.md
- queue-system.md
- vector-store.md

Each file contains complete Python code in markdown code blocks.

YOUR JOB: Extract the code from those files and write the actual Python modules.

Use the Task tool to spawn 4 sub-agents IN PARALLEL (one message, 4 tool calls):

## Agent 1: Twitter Scraper
```
Read .claude/agents/twitter-scraper.md
Extract the Python code from the code block
Write to: backend/scrapers/adapters/twitter.py
```

## Agent 2: Reddit Scraper
```
Read .claude/agents/reddit-scraper.md
Extract the Python code from the code block
Write to: backend/scrapers/adapters/reddit.py
```

## Agent 3: Queue System
```
Read .claude/agents/queue-system.md
Extract the Python code from the code blocks
Write to:
- backend/queue/__init__.py
- backend/queue/celery_app.py
- backend/queue/tasks.py
```

## Agent 4: Vector Store
```
Read .claude/agents/vector-store.md
Extract the Python code from the code blocks
Write to:
- backend/vector/__init__.py
- backend/vector/chromadb_client.py
- backend/vector/embeddings.py
```

## CRITICAL REQUIREMENTS:
- Container networking: postgres, redis, chromadb (NOT localhost)
- Import from backend.scrapers.base (already exists)
- All code is in the .claude/agents/*.md files - just extract and write it

## After all 4 agents complete:

Update backend/pyproject.toml dependencies:
```toml
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "pgvector>=0.2.0",
    "pydantic>=2.0.0",
    "redis>=5.0.0",
    "playwright>=1.40.0",
    "praw>=7.7.0",
    "celery>=5.3.0",
    "chromadb>=0.4.0",
    "openai>=1.0.0",
]
```

Then commit and push:
```bash
git add -A
git commit -m "feat: Add Twitter, Reddit, Queue, Vector modules (CCW parallel agents)"
git push origin main
```

GO NOW.
>>>>>>> iac032/main
