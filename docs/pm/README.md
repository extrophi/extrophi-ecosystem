# Project Management Documentation

**Monorepo-level coordination and module-specific planning**

## Structure

### Monorepo-Level Coordination (Root)
- **`ROOT-CCL-INSTRUCTIONS.md`** - Root PM lead coordination
- **`MASTER-EXECUTION-PLAN.md`** - Overall strategy and timeline
- **`QUICK-START-EXECUTE-NOW.md`** - Startup guide for all modules
- **`CORRECTED-2-TIER-ARCHITECTURE.md`** - System architecture overview
- **`TECHNICAL-PROPOSALS-SUMMARY.md`** - Executive summary of all proposals

### Module-Specific Documentation (Subdirectories)

#### Writer Module (`writer/`)
BrainDump v3.0 - Privacy-first voice journaling desktop app
- CCL execution instructions
- Technical proposals
- Module-specific planning

See also: `../../writer/docs/pm/` for additional Writer PM docs

#### Research Module (`research/`)
IAC-032 Unified Scraper - Multi-platform content intelligence engine
- CCL execution instructions
- Technical proposals
- Scraping strategy

See also: `../../research/docs/pm/` for additional Research PM docs

#### Backend Module (`backend/`)
IAC-011 Sovereign Backend - Shared FastAPI foundation
- CCL execution instructions
- Technical proposals
- Backend architecture

See also: `../../backend/docs/pm/` for additional Backend PM docs

#### Orchestrator Module (`orchestrator/`)
Admin dashboard and project coordination
- CCL execution instructions
- Technical proposals
- Orchestration strategy

## About the 2-Tier CCL+CCW Model

This documentation implements a **2-tier execution system**:
- **CCL (Claude Code Local)**: Development lead instances running locally
- **CCW (Claude Code Web)**: Execution team instances running via web

Each module has:
1. **CCL-INSTRUCTIONS-{MODULE}.md** - Instructions for the development lead
2. **TECHNICAL-PROPOSAL-{MODULE}.md** - Detailed technical specifications

## Navigation

- **Root PM Docs**: Current directory
- **Writer PM**: `writer/` or `../../writer/docs/pm/`
- **Research PM**: `research/` or `../../research/docs/pm/`
- **Backend PM**: `backend/` or `../../backend/docs/pm/`
- **Orchestrator PM**: `orchestrator/`

---

**Last Updated**: 2025-11-18
**Archive**: Previous PM docs archived to `../archive/2025-11-18_021849/pm/`
