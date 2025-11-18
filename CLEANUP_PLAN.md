# Root Directory Cleanup Plan

## Current Situation

**Problem**: Git merges created a mess - 3 projects mixed at root level:
1. **Writer** (IAC-031 BrainDump) - Tauri + Svelte files
2. **IAC-011 Sovereign Backend** - Python backend files at root
3. **Unified Scraper Backend** - Different Python backend in `backend/`
4. **Research** - Nested git repository (already self-contained)

## File Conflicts Identified

### Duplicate Files (Different Content)
- `pyproject.toml` (root: IAC-011) vs `backend/pyproject.toml` (unified-scraper)
- `main.py` (root: simple script) vs `backend/main.py` (FastAPI app)
- `tests/` (root: comprehensive suite) vs `backend/tests/` (simple tests)

### README.md Has Merge Conflicts
```
<<<<<<< HEAD
# Clear Voice App (Writer/BrainDump)
=======
# IAC-032 Unified Scraper
>>>>>>> iac032/main
```

## Recommended Structure

```
IAC-033-extrophi-ecosystem/
├── .git/                    (monorepo root)
├── .github/                 (CI/CD)
├── .gitignore
├── README.md                (monorepo overview - needs rewrite)
├── CLAUDE.md                (updated)
├── docs/                    (PM coordination)
│
├── writer/                  (IAC-031 BrainDump)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── svelte.config.js
│   ├── src/
│   ├── src-tauri/
│   └── docs/
│
├── backend/                 (Rename to 'scraper' or keep?)
│   ├── main.py              (FastAPI app)
│   ├── pyproject.toml       (unified-scraper)
│   ├── api/
│   ├── scrapers/
│   └── docs/
│
├── iac011-backend/          (NEW - move root backend files here)
│   ├── main.py              (from root)
│   ├── run.py
│   ├── pyproject.toml       (iac-011-sovereign-backend)
│   ├── bootstrap.sh
│   ├── admin/
│   ├── scripts/
│   ├── tests/
│   └── testing-framework/
│
└── research/                (nested git repo - don't touch)
    └── .git/
```

## Decision Required

**Option A: Keep Both Backends**
- Rename `backend/` → `scraper/` (unified scraper)
- Create `iac011-backend/` for IAC-011 files
- Pros: Preserves both projects
- Cons: More complex structure

**Option B: Merge Backends**
- Merge IAC-011 into `backend/`
- Delete duplicates
- Pros: Simpler structure
- Cons: Loses IAC-011 separate identity

**Option C: Archive IAC-011**
- Move IAC-011 files to `docs/archive/iac-011/`
- Keep only unified scraper in `backend/`
- Pros: Clean, focused
- Cons: Loses active IAC-011 code

## Cleanup Actions (Option A - Recommended)

### Step 1: Move Writer Files
```bash
git mv index.html writer/
git mv vite.config.js svelte.config.js writer/
git mv tsconfig.json tsconfig.node.json writer/
git mv package.json package-lock.json writer/
git mv eslint.config.js vitest.config.js writer/
git mv test-privacy-scanner.js writer/
git mv src writer/
git mv src-tauri writer/
```

### Step 2: Create iac011-backend/ and Move Files
```bash
mkdir iac011-backend
git mv main.py run.py run_tests.py iac011-backend/
git mv pyproject.toml uv.lock iac011-backend/
git mv bootstrap.sh pd-diag.sh iac011-backend/
git mv admin scripts testing-framework iac011-backend/
git mv tests iac011-backend/
```

### Step 3: Leave Research Alone
```bash
# research/ is a nested git repo - don't move files into it
# Root files like data/, output/ might belong to research project
# Check if they should be in research/ or deleted
```

### Step 4: Clean Up Root
```bash
# After moves, root should only have:
# - .git/, .github/, .gitignore
# - README.md (rewrite), CLAUDE.md
# - docs/
# - writer/, backend/, iac011-backend/, research/
```

### Step 5: Resolve README.md Merge Conflict
```bash
# Rewrite README.md as monorepo overview
# Remove merge conflict markers
# Document all 4 modules
```

## Post-Cleanup Verification

```bash
# Root should look like:
ls -la
# .git/ .github/ .gitignore README.md CLAUDE.md docs/
# writer/ backend/ iac011-backend/ research/

# Verify each module has correct files:
ls writer/     # Tauri + Svelte files
ls backend/    # Unified scraper (FastAPI)
ls iac011-backend/  # IAC-011 sovereign backend
ls research/   # Nested repo (untouched)
```

## Git Commit Strategy

```bash
# After cleanup:
git add -A
git commit -m "chore: Reorganize monorepo - move module files to correct directories

- Move Writer (BrainDump) files to writer/
- Move IAC-011 backend files to iac011-backend/
- Keep unified scraper in backend/
- Resolve README.md merge conflicts
- Clean root directory

BREAKING CHANGE: File locations changed for monorepo structure"

git push origin main
```

---

**Status**: Plan created, awaiting execution decision
**Next**: User chooses Option A, B, or C
