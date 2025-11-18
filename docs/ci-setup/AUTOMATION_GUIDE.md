# BrainDump Automation Guide
**Date**: 2025-11-16
**Status**: ✅ Fully Automated Pipeline Active

---

## Overview

BrainDump now has a comprehensive CI/CD and automation pipeline that handles:
- **Notifications**: Auto-notify web team when you push changes
- **Issue Creation**: One-click creation of all 14 implementation issues
- **Test Enforcement**: Block merges if tests fail or are missing
- **QA/QC**: Automated checklists and quality gates
- **Continuous Integration**: Build/test on every push

**You don't need to manage the handoff manually anymore - just push and the system handles it!**

---

## Workflows Active

### 1. **Handoff Notification** (`.github/workflows/handoff-notification.yml`)

**Triggers**: Every push to `claude/*` branches or PR opened

**What it does**:
- Creates/updates a GitHub issue to notify web team
- Includes links to all handoff documentation
- Shows latest commit info and CI status
- Auto-updates when you push new commits

**Result**: Web team gets notified automatically - you don't need to message them!

---

### 2. **CI Pipeline** (`.github/workflows/ci.yml`)

**Triggers**: Push to `main` or `claude/**` branches, PRs to `main`

**Jobs**:
- ✅ **Rust Check & Test** (macOS + Linux)
  - `cargo check`, `cargo test`, `cargo clippy`
  - Whisper.cpp installation
  - Dependency caching
- ✅ **Frontend Check & Test**
  - npm install, type check, lint, tests
  - Node.js 20 with caching
- ✅ **Build Verification** (macOS + Linux)
  - Full Tauri build
  - Upload artifacts (DMG, DEB)
- ✅ **Security Audit**
  - `cargo audit` for Rust dependencies
  - `npm audit` for Node dependencies

**Result**: Every push gets full CI validation - catches issues before merge

---

### 3. **Test Enforcement** (`.github/workflows/test-enforcement.yml`)

**Triggers**: PRs opened/updated

**What it does**:
- Detects if code changed but no tests added
- **Blocks merge** with status check if tests missing
- Comments on PR with requirements
- Runs full test suite and reports failures
- **Forces web team to add tests or justify why not needed**

**Key Feature**: If tests fail, **PR cannot be merged** until fixed!

**Override**: Comment `/skip-tests [reason]` if tests truly not applicable (requires review approval)

**Result**: Enforces test-driven development - no untested code gets merged

---

### 4. **QA Checklist** (`.github/workflows/qa-checklist.yml`)

**Triggers**: PR opened/ready for review

**What it does**:
- Posts comprehensive QA checklist as PR comment
- Adapts checklist based on files changed (backend, frontend, database, API)
- Includes manual testing requirements
- Tracks QA completion with labels

**Completion**: PR author comments `/qa-complete` to mark checklist done

**Result**: Systematic quality assurance - nothing gets missed

---

### 5. **Create Implementation Issues** (`.github/workflows/create-implementation-issues.yml`)

**Triggers**: Manual (workflow_dispatch)

**What it does**:
- Reads `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`
- Creates 7 GitHub issues + 1 tracker epic
- Includes full specs, testing requirements, acceptance criteria
- Labels with priority (P1, P2) and components (backend, frontend, etc.)

**How to run**:
```bash
# Via GitHub UI:
# 1. Go to Actions tab
# 2. Select "Create Implementation Issues"
# 3. Click "Run workflow"
# 4. Select dry_run: false
# 5. Click "Run workflow"

# Via gh CLI:
gh workflow run create-implementation-issues.yml -f dry_run=false
```

**Result**: 5 minutes to create all issues vs 30+ minutes manual copy-paste

---

## How It Works (End-to-End Flow)

### 1. You Push Changes
```bash
git add .
git commit -m "docs: Update handoff documentation"
git push origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
```

### 2. Automation Kicks In (Automatic)
- **Handoff Notification** workflow runs
  - Creates/updates issue: "🚀 Handoff Ready: BrainDump v3.0"
  - Web team gets notified via GitHub issue
- **CI Pipeline** runs
  - Builds on macOS + Linux
  - Runs all tests
  - Audits security
  - Reports status

### 3. Web Team Receives Notification (Automatic)
- GitHub issue opened/updated with:
  - Latest commit info
  - Links to all documentation
  - CI status
  - Next steps

### 4. Web Team Creates Issues (1-Click)
- Runs "Create Implementation Issues" workflow
- All 14 issues created in < 1 minute
- Tracker epic links everything together

### 5. Web Team Implements Features
- Creates PR for each issue
- **Test Enforcement** checks PR:
  - Code changed? Tests required!
  - Tests failing? PR blocked!
- **QA Checklist** posted automatically
- **CI** runs on every push

### 6. PR Review & Merge
- All CI checks must pass ✅
- Test coverage requirement met ✅
- QA checklist completed ✅
- Code review approved ✅
- Merge to main!

---

## Benefits

### For You (Local Claude Code)
- ✅ **No manual handoff coordination** - just push!
- ✅ **Automated notifications** - web team knows when to start
- ✅ **CI validates your work** - catch issues before handoff
- ✅ **Less usage consumed** - automation does the communication

### For Web Team
- ✅ **Clear notifications** when work is ready
- ✅ **Automated issue creation** - 5 min vs 30 min
- ✅ **Enforced quality gates** - tests required, no exceptions
- ✅ **Systematic QA** - nothing gets missed
- ✅ **Fast feedback** - CI runs on every push

### For Project Quality
- ✅ **Test coverage enforced** - no untested code
- ✅ **Security audits** on every change
- ✅ **Multi-platform testing** (macOS + Linux)
- ✅ **Consistent QA process**
- ✅ **Build artifacts** for debugging

---

## Workflow Commands

### Issue Creation
```bash
# Run issue creation workflow
gh workflow run create-implementation-issues.yml -f dry_run=false

# Check workflow status
gh run list --workflow=create-implementation-issues.yml

# View created issues
gh issue list --label P1-critical
```

### QA Checklist
```bash
# Mark QA complete (in PR comment)
/qa-complete

# View QA status
gh pr view <number> --json labels
```

### Test Enforcement
```bash
# Skip test requirement (in PR comment, needs justification)
/skip-tests Refactoring only, no logic changes

# View test coverage status
gh pr checks <number>
```

### CI Status
```bash
# View latest CI run
gh run list --workflow=ci.yml --limit 1

# View workflow run details
gh run view <run-id>

# Download build artifacts
gh run download <run-id>
```

---

## Troubleshooting

### Issue: Handoff notification not created
**Check**:
1. Is branch name `claude/*`?
2. Does `docs/dev/HANDOFF_TO_WEB_TEAM.md` exist?
3. Check workflow runs: `gh run list --workflow=handoff-notification.yml`

### Issue: CI failing on push
**Check**:
1. View logs: `gh run view <run-id> --log`
2. Run tests locally: `cargo test` / `npm test`
3. Check if whisper.cpp installed: `pkg-config --exists whisper`

### Issue: Test enforcement blocking PR incorrectly
**Solutions**:
1. Add tests if truly needed
2. Comment `/skip-tests [reason]` if not applicable
3. Request review approval to override

### Issue: QA checklist not posted
**Check**:
1. Is PR in draft mode? (QA only runs on ready-for-review)
2. Check workflow runs: `gh run list --workflow=qa-checklist.yml`

---

## Labels Used

| Label | Meaning | Applied By |
|-------|---------|------------|
| `handoff-notification` | Handoff issue tracker | Handoff Notification workflow |
| `needs-tests` | Tests required for code changes | Test Enforcement workflow |
| `blocked` | PR cannot merge (tests missing/failing) | Test Enforcement workflow |
| `needs-qa` | QA checklist pending | QA Checklist workflow |
| `qa-complete` | QA checklist completed | QA Checklist workflow (manual trigger) |
| `P1-critical`, `P2-high`, etc. | Priority levels | Issue Creation workflow |
| `backend`, `frontend`, `database`, etc. | Component areas | Issue Creation workflow |

---

## Configuration

### Branch Protection (Recommended)

Set up branch protection on `main`:

```yaml
Required status checks:
  - CI / Rust Check & Test (macos-latest)
  - CI / Rust Check & Test (ubuntu-latest)
  - CI / Frontend Check & Test
  - CI / Build Verification (macos-latest)
  - CI / Build Verification (ubuntu-latest)
  - CI / Security Audit
  - Test Coverage Enforcement
```

**How to enable**:
1. GitHub → Settings → Branches
2. Add rule for `main`
3. Enable "Require status checks to pass before merging"
4. Select all CI jobs above
5. Enable "Require branches to be up to date"
6. Save

**Result**: Cannot merge to `main` unless ALL checks pass

---

## Workflow Permissions

All workflows use minimum required permissions (security best practice):

| Workflow | Permissions |
|----------|-------------|
| Handoff Notification | `issues: write`, `pull-requests: write` |
| CI | `contents: read` (read-only) |
| Test Enforcement | `pull-requests: write`, `checks: write`, `statuses: write` |
| QA Checklist | `pull-requests: write`, `issues: write` |
| Create Issues | `issues: write` |

**Security**: No workflow has `contents: write` (code modification) permissions

---

## Future Enhancements

Potential additions to automation:

1. **AI-Powered Triage** (from research doc)
   - Auto-label new issues with category/priority
   - Estimate effort using GitHub Models
   - Suggest assignees based on expertise

2. **Release Automation**
   - Auto-create GitHub releases on version tags
   - Build multi-platform binaries
   - Generate changelog from commit history

3. **Performance Benchmarks**
   - Run `cargo bench` on PRs
   - Compare against main branch
   - Flag performance regressions

4. **Coverage Reports**
   - Generate code coverage with `cargo tarpaulin`
   - Upload to Codecov
   - Require >60% coverage for PRs

See `docs/dev/GITHUB_ACTIONS_RESEARCH_2025.md` for full implementation details.

---

## Resources

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Workflow Syntax**: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- **Events Reference**: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows
- **BrainDump CI/CD Research**: `docs/dev/GITHUB_ACTIONS_RESEARCH_2025.md`

---

**Last Updated**: 2025-11-16
**Status**: ✅ All workflows active and tested
**Next**: Push changes to trigger automation!
