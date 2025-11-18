# Archive Index - 2025-11-18 02:18:49

## Archive Summary

This archive contains all historical documentation from the IAC-033 Extrophi Ecosystem monorepo, created before the documentation cleanup on 2025-11-18.

## What Was Archived

### Agent Work Logs (`agents/`)
- 28 agent task reports and deliverables
- Overnight sprint implementation reports
- Feature integration summaries
- Testing and verification reports

### Development Documentation (`dev/`)
- 43+ technical documents including:
  - Svelte 5 runes documentation
  - Tauri 2.0 guides
  - Rust FFI patterns
  - GitHub Actions CI/CD guides
  - Project status reports
  - Implementation guides
  - Quick reference sheets

### Research Documentation (`research/`)
- 31 research documents including:
  - Technology evaluations
  - Framework comparisons
  - Business planning frameworks
  - Integration research (health, finance, wearables)
  - OAuth and security analysis

### CI/CD Setup (`ci-setup/`)
- GitHub Actions workflows
- CI/CD configuration documentation
- Deployment scripts and guides

### Templates (`templates/`)
- Document templates
- Code scaffolding templates
- Report formats

### Root Documentation Files
- `ARCHITECTURE.md` - System architecture overview
- `backend-review.md` - Backend code review
- `KEYBOARD_SHORTCUTS_QUICK_REFERENCE.md` - UI shortcuts
- `TASKS.md` - Historical task list

## Why This Was Archived

The documentation was becoming cluttered with:
- Multiple overlapping guides from different project phases
- Outdated implementation details from early sprints
- Agent reports that were valuable historically but not for current work
- Duplicate information across various documents

## What Was Preserved (Not Archived)

### Project Management (`docs/pm/`)
**Kept active** because it contains:
- Current PRDs (Product Requirements Documents)
- Active planning documents
- Decision logs
- Current project specifications

## How to Use This Archive

### Finding Specific Information

**Agent Implementation Details**:
Check `agents/` directory for specific feature implementations.

**Technical Patterns**:
Look in `dev/` for guides on:
- Svelte 5 migration (`dev/svelte/`)
- Tauri patterns (`dev/tauri/`)
- FFI integration (`dev/rust-ffi/`)

**Research Findings**:
Browse `research/` for technology evaluations and analysis.

### Extracting Useful Content

When pulling information from the archive:
1. Verify it's still relevant (check dates)
2. Update any outdated technical details
3. Place extracted content in appropriate new docs location
4. Reference the archive location in the new document

## Archive Structure

```
2025-11-18_021849/
├── agents/                    # 28 agent reports
│   ├── AGENT_ALPHA_DELIVERABLES.md
│   ├── AGENT_DELTA_SETTINGS_REPORT.md
│   ├── AGENT_EPSILON_VERIFICATION.md
│   └── ... (25 more files)
│
├── dev/                       # 43+ technical docs
│   ├── svelte/                # Svelte 5 documentation
│   ├── tauri/                 # Tauri 2.0 guides
│   ├── rust-ffi/              # FFI patterns
│   ├── github-actions/        # CI/CD guides
│   ├── github-cli/            # GitHub CLI docs
│   ├── whisper-cpp/           # Whisper integration
│   ├── PROJECT_STATUS_2025-11-16.md
│   ├── GITHUB_ISSUES_FOR_WEB_TEAM.md
│   └── ... (30+ more files)
│
├── research/                  # 31 research docs
│   ├── compass_artifact_*.md  # Analysis artifacts
│   ├── CONTENT_CREATION_WORKFLOW.md
│   ├── ENCRYPTION_SECURITY.md
│   ├── BUSINESS_PLANNING_FRAMEWORKS.md
│   └── ... (27 more files)
│
├── ci-setup/                  # 9 CI/CD files
│   ├── github-actions/
│   └── deployment-configs/
│
├── templates/                 # 4 template files
│   ├── agent-task-template.md
│   └── pr-template.md
│
├── ARCHITECTURE.md            # System architecture
├── backend-review.md          # Backend review
├── KEYBOARD_SHORTCUTS_QUICK_REFERENCE.md
├── TASKS.md                   # Historical tasks
└── ARCHIVE_INDEX.md           # This file
```

## Statistics

- **Total Files**: ~115 documents
- **Total Size**: ~2.5MB of markdown documentation
- **Date Range**: 2025-11-15 to 2025-11-18
- **Primary Authors**: Claude Code agents (Alpha, Delta, Epsilon, Theta, etc.)

## Related Documentation

- **Current Docs**: See `/docs/README.md` for new documentation structure
- **CLAUDE.md**: Updated with archive information
- **Project Management**: `/docs/pm/` (active, not archived)

---

**Archive Created**: 2025-11-18 02:18:49
**Archive Reason**: Documentation cleanup and reorganization
**Archived By**: Claude Code (documentation cleanup task)
