# CCW Orchestrator Instructions

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
