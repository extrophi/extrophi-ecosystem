# CORRECTED: 2-TIER ARCHITECTURE

**Deadline:** Wednesday 7:00 AM GMT (~29.5 hours)

## THE SYSTEM

**TIER 1: CCL (Claude Code Local) - 4 tmux windows**
- Dev leads / Quality gatekeepers
- Monitor, decide, review
- NO CODING (preserves Max Plan)
- Cost: $0 (monitoring is free)

**TIER 2: CCW (Claude Code Web) - 4 browser tabs**
- Orchestrators spawn sub-agents
- DO ALL CODING
- Cost: $700 total
- 30 sub-agents = cost of 1 CCL instance

## COMMUNICATION FLOW

```
Codio (Executive Decisions)
    ↓
CCL Dev Leads (Quality Control) ← Tmux, 4 windows
    ↓ [Reviews PRs, runs tests, approves/rejects]
GitHub Issues & PRs
    ↓ [Creates PRs, reports progress]
CCW Orchestrators ← Browser, 4 tabs
    ↓ [Spawns agents]
23 Sub-Agents (Parallel Workers)
```

## CODE QUALITY ENFORCED BY CCL

Every PR must have:
- ✅ All tests passing
- ✅ No silent failures
- ✅ Type safety
- ✅ Error handling
- ✅ Linting clean

If CCL rejects → CCW agent fixes → resubmit

## WHY THIS WORKS

- CCL catches bad code before merge
- CCW efficient ($700 for 30 agents)
- Max Plan preserved (CCL doesn't code)
- Fast decisions (CCL responds in minutes)
- Clear roles (brains vs hands)
