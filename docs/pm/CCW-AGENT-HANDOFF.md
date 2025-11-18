# CCW Agent Handoff - Wave 1 Execution

**Status**: ✅ READY FOR CCW SPAWNING
**Date**: 2025-11-18
**Infrastructure Phase**: COMPLETE
**Next Phase**: CCW Agent Execution

---

## Quick Start - Spawn First Agent Now

**ALPHA Agent (#33)** - Writer Module - Astro Documentation Setup

1. Open CCW: https://claude.ai/code
2. Navigate to issue: https://github.com/extrophi/extrophi-ecosystem/issues/33
3. CCW reads prompt: `.github/prompts/writer/alpha.md`
4. Expected duration: 45 minutes
5. Dependencies: None (foundational task)

**CCW will automatically**:
- Checkout `writer` branch
- Read GitHub issue #33
- Execute task from `.github/prompts/writer/alpha.md`
- Run tests locally
- Commit and push to `writer` branch
- Trigger GitHub Actions CI
- Update issue with results
- Close issue on success

---

## GitHub Repository

**URL**: https://github.com/extrophi/extrophi-ecosystem
**Issues Dashboard**: https://github.com/extrophi/extrophi-ecosystem/issues
**Wave 1 Filter**: `is:issue is:open label:wave:1`
**Actions Dashboard**: https://github.com/extrophi/extrophi-ecosystem/actions

---

## How to Spawn CCW Agents

### Step 1: Open CCW Browser Tab

1. Navigate to: https://claude.ai/code
2. Open a new CCW tab for each agent
3. Point CCW to GitHub issue URL

### Step 2: CCW Agent Spawning Workflow

For each issue, spawn ONE CCW agent:

1. **Open CCW tab** → https://claude.ai/code
2. **Paste GitHub issue URL** → `https://github.com/extrophi/extrophi-ecosystem/issues/{number}`
3. **CCW automatically**:
   - Reads issue description
   - Locates prompt file: `.github/prompts/{module}/{agent}.md`
   - Checks out appropriate branch (`writer`, `research`, `backend`, `orchestrator`)
   - Executes task autonomously
   - Commits with standardized message
   - Pushes to module branch
   - Triggers GitHub Actions CI/CD
   - Updates issue with success/failure
   - Closes issue on completion

### Step 3: ROOT CCL Monitoring

**ROOT CCL (you)** monitors via:
- GitHub issue comments
- GitHub Actions status
- Issue labels (wave:1, module:writer, etc.)
- Direct CCW agent updates

---

## Recommended Execution Order

### Phase 1: Foundation (Parallel Execution)

Start with ALPHA-tier tasks (lowest risk, no dependencies):

| Agent | Issue | Module | Duration | Dependencies | Risk |
|-------|-------|--------|----------|--------------|------|
| **ALPHA** | #33 | Writer | 45 min | None | ✅ LOW |
| **THETA** | #37 | Research | 1 hour | None | ✅ LOW |
| **OMICRON** | #41 | Backend | 1 hour | None | ✅ LOW |
| **PHI** | #42 | Orchestrator | 2 hours | None | ⚠️ MEDIUM |

**Recommendation**: Spawn all 4 in parallel to maximize throughput.

### Phase 2: Dependent Tasks (Sequential or Gated)

Execute after Phase 1 completes:

| Agent | Issue | Module | Duration | Dependencies | Risk |
|-------|-------|--------|----------|--------------|------|
| **BETA** | #34 | Writer | 1 hour | ALPHA (#33) | ✅ LOW |
| **DELTA** | #35 | Writer | 2 hours | ALPHA, BETA | ⚠️ HIGH |
| **ETA** | #36 | Writer | 45 min | None (parallel) | ✅ LOW |
| **KAPPA** | #38 | Research | 1.5 hours | THETA (#37) | ⚠️ MEDIUM |
| **IOTA** | #39 | Research | 2 hours | THETA, KAPPA | ⚠️ MEDIUM |
| **NU** | #40 | Research | 1 hour | IOTA (#39) | ✅ LOW |
| **CHI** | #43 | Orchestrator | 1.5 hours | PHI (#42) | ⚠️ MEDIUM |

---

## Expected CCW Agent Workflow

### Agent Execution Pattern

```
┌─────────────────────────────────────────────────────────────┐
│ CCW Agent spawned via claude.ai/code                        │
│ ↓                                                            │
│ Reads GitHub issue #{number}                                │
│ ↓                                                            │
│ Locates .github/prompts/{module}/{agent}.md                 │
│ ↓                                                            │
│ Checks out {module} branch                                  │
│ ↓                                                            │
│ Executes task (code, test, document)                        │
│ ↓                                                            │
│ Runs local verification (npm test, cargo test, pytest)      │
│ ↓                                                            │
│ Commits with standardized message format                    │
│ ↓                                                            │
│ Pushes to {module} branch                                   │
│ ↓                                                            │
│ GitHub Actions triggers ({module}-ci.yml)                   │
│ ↓                                                            │
│ CI passes ✅ or fails ❌                                    │
│ ↓                                                            │
│ Agent updates issue with success/failure comment            │
│ ↓                                                            │
│ Agent closes issue if complete, or escalates if blocked     │
└─────────────────────────────────────────────────────────────┘
```

### Success Criteria per Agent

Each agent is considered **DONE** when:
- ✅ Task implementation complete (code written)
- ✅ Local tests pass (`npm test` / `cargo test` / `pytest`)
- ✅ GitHub Actions CI passes (workflow runs green)
- ✅ Commit follows format from prompt file
- ✅ Issue updated with completion comment
- ✅ Issue closed with success label

### Escalation to ROOT CCL

Agents should **escalate to ROOT CCL** when:
- 🚨 CI fails after 2 retry attempts
- 🚨 Dependency missing (another agent's work needed)
- 🚨 Scope ambiguity (task requirements unclear)
- 🚨 Technical blocker (external service down, API unavailable)

**ROOT CCL monitors via**:
- GitHub issue comments
- GitHub Actions failure notifications
- Direct CCW agent status updates

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         ROOT CCL                            │
│              (You - Coordination & Monitoring)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Monitors issues, Actions, coordinates
                      │
        ┌─────────────┼─────────────┬─────────────┬───────────┐
        ▼             ▼             ▼             ▼           ▼
   ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐
   │ WRITER  │  │ RESEARCH │  │ BACKEND │  │ ORCHESTRATOR │
   │ Branch  │  │ Branch   │  │ Branch  │  │ Branch       │
   └────┬────┘  └────┬─────┘  └────┬────┘  └──────┬───────┘
        │            │             │              │
        │            │             │              │
   ┌────▼─────┐ ┌───▼──────┐ ┌────▼─────┐  ┌─────▼──────┐
   │ ALPHA    │ │ THETA    │ │ OMICRON  │  │ PHI        │
   │ BETA     │ │ KAPPA    │ │          │  │ CHI        │
   │ DELTA    │ │ IOTA     │ │          │  │            │
   │ ETA      │ │ NU       │ │          │  │            │
   └──────────┘ └──────────┘ └──────────┘  └────────────┘
        │            │             │              │
        ▼            ▼             ▼              ▼
   ┌────────────────────────────────────────────────────┐
   │         GitHub Actions (CI/CD per branch)          │
   │  writer-ci.yml | research-ci.yml | backend-ci.yml  │
   │              orchestrator-ci.yml                   │
   └────────────────────────────────────────────────────┘
```

---

## Infrastructure Verification Checklist

### ✅ Complete Infrastructure

| Component | Count | Status | Location |
|-----------|-------|--------|----------|
| **GitHub Issues** | 11 | ✅ Created | https://github.com/extrophi/extrophi-ecosystem/issues |
| **Prompt Files** | 11 | ✅ Deployed | `.github/prompts/{module}/{agent}.md` |
| **CI Workflows** | 4 | ✅ Active | `.github/workflows/{module}-ci.yml` |
| **Module Branches** | 4 | ✅ Ready | `writer`, `research`, `backend`, `orchestrator` |
| **Handoff Doc** | 1 | ✅ Current | `docs/pm/CCW-AGENT-HANDOFF.md` |

### Prompt Files Inventory

**Writer Module** (4 agents):
- `.github/prompts/writer/alpha.md` - Astro documentation setup
- `.github/prompts/writer/beta.md` - Component library
- `.github/prompts/writer/delta.md` - API integration
- `.github/prompts/writer/eta.md` - Testing suite

**Research Module** (4 agents):
- `.github/prompts/research/theta.md` - FastAPI skeleton
- `.github/prompts/research/kappa.md` - Scraper adapters
- `.github/prompts/research/iota.md` - RAG integration
- `.github/prompts/research/nu.md` - Analysis pipeline

**Backend Module** (1 agent):
- `.github/prompts/backend/omicron.md` - PostgreSQL schema

**Orchestrator Module** (2 agents):
- `.github/prompts/orchestrator/phi.md` - API Gateway
- `.github/prompts/orchestrator/chi.md` - Admin dashboard

### GitHub Actions Workflows

- `writer-ci.yml` - Writer module CI (npm, cargo, tests)
- `research-ci.yml` - Research module CI (pytest, linting)
- `backend-ci.yml` - Backend module CI (pytest, database tests)
- `orchestrator-ci.yml` - Orchestrator module CI (npm, API tests)

---

## ROOT CCL Monitoring Commands

### Check Issue Status
```bash
gh issue list --state open --label wave:1
```

### Check Recent Commits (All Branches)
```bash
git log --oneline --graph --all --branches
```

### Check GitHub Actions Status
```bash
gh run list --limit 10
```

### Check Specific Workflow Run
```bash
gh run view {run-id}
```

### Re-run Failed Workflow
```bash
gh run rerun {run-id}
```

### View Issue Details
```bash
gh issue view {issue-number}
```

### Monitor Real-Time Actions
```bash
gh run watch
```

---

## Wave 1 Completion Criteria

**All 11 agents DONE** when:
- ✅ All issues #33-#43 closed
- ✅ All GitHub Actions passing (4 module branches)
- ✅ All 11 commits pushed to respective branches
- ✅ ROOT CCL reviewed all implementations
- ✅ No blocking errors or escalations
- ✅ Ready for Wave 2 agent spawning

---

## Execution Timeline Estimates

### Sequential Execution
- **Total Duration**: ~18-24 hours (one agent at a time)
- **Completion Date**: 3-4 days

### Parallel Execution (Recommended)
- **Phase 1** (4 agents): 2 hours (ALPHA, THETA, OMICRON, PHI in parallel)
- **Phase 2** (7 agents): 4-6 hours (batched by dependencies)
- **Total Duration**: 6-8 hours
- **Completion Date**: 1 day

### Optimal Strategy
1. Spawn all 4 Phase 1 agents immediately (parallel)
2. Monitor via GitHub Actions dashboard
3. As Phase 1 agents complete, spawn Phase 2 agents
4. Keep 3-4 agents running in parallel at all times
5. ROOT CCL handles escalations and coordination

---

## Common Scenarios & Troubleshooting

### Scenario 1: CI Fails on First Push

**Agent Response**:
1. Read CI logs from GitHub Actions
2. Fix error locally
3. Re-run tests
4. Commit fix
5. Push again
6. If fails again (2nd time), escalate to ROOT CCL

**ROOT CCL Response**:
1. Review CI logs
2. Identify systemic issue (env var, dependency, etc.)
3. Fix infrastructure issue
4. Notify agent to retry
5. Update other agents to avoid same issue

### Scenario 2: Dependency Not Ready

**Example**: BETA agent (#34) needs ALPHA (#33) to complete first.

**Agent Response**:
1. Check if ALPHA issue is closed
2. If not closed, add comment to #34: "Waiting for #33 to complete"
3. Label issue: `status:blocked`
4. Wait for ROOT CCL to notify when unblocked

**ROOT CCL Response**:
1. Monitor dependency graph
2. When ALPHA closes #33, comment on #34: "Unblocked - ready to execute"
3. BETA agent resumes work

### Scenario 3: Scope Ambiguity

**Agent Response**:
1. Add comment to issue: "Need clarification on [specific question]"
2. Label issue: `status:needs-clarification`
3. Wait for ROOT CCL response

**ROOT CCL Response**:
1. Review question
2. Provide clarification in issue comment
3. Update prompt file if needed
4. Remove `status:needs-clarification` label
5. Agent resumes work

---

## Next Actions for PM (ROOT CCL)

### Immediate Actions (Now)

1. **Verify GitHub Access**
   ```bash
   gh auth status
   # Should show: extrophi/extrophi-ecosystem
   ```

2. **Open First CCW Tab for ALPHA #33**
   - URL: https://claude.ai/code
   - Issue: https://github.com/extrophi/extrophi-ecosystem/issues/33
   - Expected duration: 45 minutes

3. **Monitor ALPHA Progress**
   - Watch GitHub Actions: https://github.com/extrophi/extrophi-ecosystem/actions
   - Check issue comments for updates
   - Verify commit pushed to `writer` branch

4. **Spawn THETA #37 in Parallel** (independent of ALPHA)
   - URL: https://claude.ai/code
   - Issue: https://github.com/extrophi/extrophi-ecosystem/issues/37
   - Expected duration: 1 hour

5. **Spawn OMICRON #41 in Parallel** (independent)
   - URL: https://claude.ai/code
   - Issue: https://github.com/extrophi/extrophi-ecosystem/issues/41
   - Expected duration: 1 hour

6. **Spawn PHI #42 in Parallel** (independent)
   - URL: https://claude.ai/code
   - Issue: https://github.com/extrophi/extrophi-ecosystem/issues/42
   - Expected duration: 2 hours

### Ongoing Monitoring

- Check GitHub Actions dashboard every 30 minutes
- Respond to escalations within 15 minutes
- Update this handoff doc with lessons learned
- Track completion rate and estimated finish time

---

## Summary

### ✅ Infrastructure Ready
- 4 git branches configured (`writer`, `research`, `backend`, `orchestrator`)
- 11 GitHub issues created (#33-#43)
- 4 GitHub Actions workflows deployed
- 11 prompt files available in `.github/prompts/`

### ✅ CCW Agent System Online
- Agents can read tasks from GitHub issues
- Agents can access prompt files via `.github/prompts/`
- Agents can push to isolated module branches
- CI/CD validates all changes automatically

### ✅ ROOT CCL Monitoring Active
- Issue tracker: https://github.com/extrophi/extrophi-ecosystem/issues
- Actions dashboard: https://github.com/extrophi/extrophi-ecosystem/actions
- Escalation protocol defined
- Handoff documentation complete

---

## 🚀 Ready to Spawn Wave 1 Agents

**Recommended first agent**: ALPHA #33 (Writer - Astro setup)
**Start URL**: https://github.com/extrophi/extrophi-ecosystem/issues/33
**Expected Wave 1 completion**: 6-8 hours (parallel execution)

---

**Infrastructure Setup Duration**: 2 hours
**Wave 1 Estimated Duration**: 18-24 hours (sequential) / 6-8 hours (parallel)
**Total Issues**: 11
**Total Agents**: 11

**Status**: ✅ **PHASE 1 COMPLETE - READY FOR CCW SPAWNING**

---

**Last Updated**: 2025-11-18
**Phase**: Infrastructure Complete → CCW Execution
**Next Milestone**: Wave 1 completion (all 11 issues closed)
