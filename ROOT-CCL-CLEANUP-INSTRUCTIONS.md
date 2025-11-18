# ROOT CCL: Phase 1 Cleanup Instructions

**CRITICAL:** Execute ONE phase at a time. After each phase, STOP and report results. Do NOT proceed to next phase until PM (Codio) approves.

---

**Your Role:** Claude Code Local at project root  
**Location:** `/Users/kjd/01-projects/IAC-033-extrophi-ecosystem`  
**Task:** Execute cleanup to prepare for sub-agent spawning

---

## CONTEXT

Read these files first:
1. `/CLEANUP_PLAN_UPDATED.md` - Full cleanup plan
2. `/SINGLE-ROOT-CCL-STRATEGY.md` - Architecture
3. `/AGENT-DISCIPLINE-PROTOCOL.md` - Operating protocol

---

## PHASE 1: Move Writer Files to writer/

Execute these git moves:

```bash
git mv index.html writer/ 2>/dev/null || mv index.html writer/
git mv vite.config.js writer/ 2>/dev/null || mv vite.config.js writer/
git mv svelte.config.js writer/ 2>/dev/null || mv svelte.config.js writer/
git mv tsconfig.json writer/ 2>/dev/null || mv tsconfig.json writer/
git mv tsconfig.node.json writer/ 2>/dev/null || mv tsconfig.node.json writer/
git mv package.json writer/ 2>/dev/null || mv package.json writer/
git mv package-lock.json writer/ 2>/dev/null || mv package-lock.json writer/
git mv eslint.config.js writer/ 2>/dev/null || mv eslint.config.js writer/
git mv vitest.config.js writer/ 2>/dev/null || mv vitest.config.js writer/
git mv test-privacy-scanner.js writer/ 2>/dev/null || mv test-privacy-scanner.js writer/
git mv src writer/ 2>/dev/null || mv src writer/
git mv src-tauri writer/ 2>/dev/null || mv src-tauri writer/
```

**Verify:**
```bash
ls writer/
```

**STOP HERE** - Report what moved. Wait for PM approval before Phase 2.

---

## PHASE 2: Investigate Backend Duplication

Check both locations:
```bash
echo "=== Contents of backend/ ==="
ls -la backend/

echo "=== Contents of research/backend/ ==="
ls -la research/backend/
```

**Report to PM:**
- Are they the same or different?
- What's in each?

**STOP HERE** - Wait for decision before Phase 3.

---

## PHASE 3: Move IAC-011 Files

(Execute after Phase 2 decision)

Create temp directory:
```bash
mkdir -p iac011-temp
```

Move IAC-011 files:
```bash
git mv main.py iac011-temp/ 2>/dev/null || mv main.py iac011-temp/
git mv run.py iac011-temp/ 2>/dev/null || mv run.py iac011-temp/
git mv run_tests.py iac011-temp/ 2>/dev/null || mv run_tests.py iac011-temp/
git mv pyproject.toml iac011-temp/ 2>/dev/null || mv pyproject.toml iac011-temp/
git mv uv.lock iac011-temp/ 2>/dev/null || mv uv.lock iac011-temp/
git mv .python-version iac011-temp/ 2>/dev/null || mv .python-version iac011-temp/
git mv .pre-commit-config.yaml iac011-temp/ 2>/dev/null || mv .pre-commit-config.yaml iac011-temp/
git mv bootstrap.sh iac011-temp/ 2>/dev/null || mv bootstrap.sh iac011-temp/
git mv pd-diag.sh iac011-temp/ 2>/dev/null || mv pd-diag.sh iac011-temp/
git mv admin iac011-temp/ 2>/dev/null || mv admin iac011-temp/
git mv scripts iac011-temp/ 2>/dev/null || mv scripts iac011-temp/
git mv testing-framework iac011-temp/ 2>/dev/null || mv testing-framework iac011-temp/
git mv tests iac011-temp/ 2>/dev/null || mv tests iac011-temp/
```

**Verify:**
```bash
ls iac011-temp/
```

**STOP HERE** - Report completion. Wait for Phase 4 approval.

---

## PHASE 4: Clean Remaining Files

Move research files:
```bash
git mv data research/ 2>/dev/null || mv data research/
git mv output research/ 2>/dev/null || mv output research/
git mv tools research/ 2>/dev/null || mv tools research/
git mv pytest.ini research/ 2>/dev/null || mv pytest.ini research/
git mv podman-compose.yml research/ 2>/dev/null || mv podman-compose.yml research/
```

**STOP HERE** - Report completion.

---

## PHASE 5: Git Commit

```bash
git add -A
git status
```

**Show status to PM, wait for approval to commit.**

Then:
```bash
git commit -m "chore: Reorganize monorepo structure

- Move Writer (IAC-031) files to writer/
- Organize IAC-011 files to iac011-temp/
- Move research files to research/
- Clean root directory

BREAKING CHANGE: File locations changed"

git push origin main
```

---

## WORKFLOW

- Execute phase
- Report results
- **STOP**
- Wait for PM approval
- PM says "continue Phase 2" or "continue Phase 3"
- Execute next phase

**Do NOT run all phases at once.**  
**Step-pause-step.**  
**ONE PHASE AT A TIME.**

---

## STARTING PROMPT FOR CCL

When you start CCL, paste:

```
I am ROOT CCL for IAC-033 Extrophi Ecosystem.

Read: /ROOT-CCL-CLEANUP-INSTRUCTIONS.md

Execute PHASE 1 ONLY.
After Phase 1, STOP and report results.
Wait for PM to approve before continuing.

Start Phase 1 now.
```
