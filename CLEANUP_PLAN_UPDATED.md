# UPDATED ROOT CLEANUP PLAN
## Execute IMMEDIATELY Before CCW Agents Start

**Current Time:** Check `date`  
**Deadline:** Wednesday 7:00 AM  
**Priority:** CRITICAL - Must complete before spawning CCW agents

---

## CURRENT MESS

```bash
Root level has mixed files from 3 merged projects:
- Writer files (IAC-031): index.html, vite.config.js, package.json, src-tauri/
- Backend files (IAC-011): main.py, run.py, admin/, scripts/, testing-framework/
- Research files (IAC-032): Already in research/ but duplicated

writer/: EMPTY (needs files moved in)
backend/: Has scraper/research code (correct)
research/: Has nested backend/ (duplicate - investigate)
```

---

## TARGET STRUCTURE

```
IAC-033-extrophi-ecosystem/
├── .git/
├── .github/
├── .gitignore
├── README.md           (rewrite as monorepo overview)
├── CLEANUP_PLAN_UPDATED.md  (this file)
├── docs/               (PM coordination docs)
│
├── writer/             (IAC-031 voice app)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   ├── src-tauri/
│   └── [all Tauri/Svelte files]
│
├── research/           (IAC-032 unified scraper)
│   ├── backend/
│   ├── scrapers/
│   ├── docs/
│   └── [scraper infrastructure]
│
├── backend/            (IAC-011 sovereign backend)
│   ├── main.py         (from root)
│   ├── admin/
│   ├── scripts/
│   ├── testing-framework/
│   └── [FastAPI backend]
│
└── orchestrator/       (empty, to be built)
    └── README.md
```

---

## CLEANUP SCRIPT

```bash
#!/bin/bash
cd /Users/kjd/01-projects/IAC-033-extrophi-ecosystem

echo "=== PHASE 1: Move Writer Files ==="
# Move all writer-specific files to writer/
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

# Move directories
[ -d "src" ] && git mv src writer/ 2>/dev/null || mv src writer/
[ -d "src-tauri" ] && git mv src-tauri writer/ 2>/dev/null || mv src-tauri writer/

echo "=== PHASE 2: Investigate backend/ vs research/backend/ ==="
# Check what's in research/backend/ vs backend/
echo "Checking research/backend/..."
ls -la research/backend/ > /tmp/research-backend-list.txt

echo "Checking backend/..."
ls -la backend/ > /tmp/backend-list.txt

# Decision point: Are they the same or different?
# If same → delete research/backend/, keep backend/
# If different → rename backend/ to something else

echo "=== PHASE 3: Move IAC-011 Backend Files ==="
# For now, create temp directory for IAC-011 files
mkdir -p iac011-temp

# Move IAC-011 files
git mv main.py iac011-temp/ 2>/dev/null || mv main.py iac011-temp/
git mv run.py iac011-temp/ 2>/dev/null || mv run.py iac011-temp/
git mv run_tests.py iac011-temp/ 2>/dev/null || mv run_tests.py iac011-temp/
git mv pyproject.toml iac011-temp/ 2>/dev/null || mv pyproject.toml iac011-temp/
git mv uv.lock iac011-temp/ 2>/dev/null || mv uv.lock iac011-temp/
git mv .python-version iac011-temp/ 2>/dev/null || mv .python-version iac011-temp/
git mv .pre-commit-config.yaml iac011-temp/ 2>/dev/null || mv .pre-commit-config.yaml iac011-temp/
git mv bootstrap.sh iac011-temp/ 2>/dev/null || mv bootstrap.sh iac011-temp/
git mv pd-diag.sh iac011-temp/ 2>/dev/null || mv pd-diag.sh iac011-temp/

# Move directories
[ -d "admin" ] && git mv admin iac011-temp/ 2>/dev/null || mv admin iac011-temp/
[ -d "scripts" ] && git mv scripts iac011-temp/ 2>/dev/null || mv scripts iac011-temp/
[ -d "testing-framework" ] && git mv testing-framework iac011-temp/ 2>/dev/null || mv testing-framework iac011-temp/

# Move tests if they're IAC-011 tests (check first)
if [ -d "tests" ]; then
    echo "Found tests/ at root - need to check if IAC-011 or scraper tests"
    # For now, move to iac011-temp
    git mv tests iac011-temp/ 2>/dev/null || mv tests iac011-temp/
fi

echo "=== PHASE 4: Clean Remaining Files ==="
# Move research-specific files if at root
[ -d "data" ] && git mv data research/ 2>/dev/null || mv data research/
[ -d "output" ] && git mv output research/ 2>/dev/null || mv output research/
[ -d "tools" ] && git mv tools research/ 2>/dev/null || mv tools research/
[ -f "pytest.ini" ] && git mv pytest.ini research/ 2>/dev/null || mv pytest.ini research/
[ -f "podman-compose.yml" ] && git mv podman-compose.yml research/ 2>/dev/null || mv podman-compose.yml research/

echo "=== PHASE 5: Decision Point ==="
echo "Current state:"
echo "- writer/ populated: $(ls writer/ | wc -l) files"
echo "- backend/ exists: $(ls backend/ | wc -l) files"
echo "- research/backend/ exists: $(ls research/backend/ | wc -l) files"
echo "- iac011-temp/ created: $(ls iac011-temp/ | wc -l) files"
echo ""
echo "DECISION NEEDED:"
echo "1. Are backend/ and research/backend/ duplicates?"
echo "2. Where should IAC-011 code go?"
echo ""
echo "OPTIONS:"
echo "A) backend/ = IAC-011, research/backend/ = scraper (rename)"
echo "B) backend/ = scraper, iac011-temp/ = IAC-011 (keep separate)"
echo "C) Merge IAC-011 into backend/ (complex)"

# Wait for decision before proceeding
```

---

## EXECUTION BY ROOT CCL

### Step 1: Run Investigation
```bash
cd /Users/kjd/01-projects/IAC-033-extrophi-ecosystem
chmod +x cleanup.sh
./cleanup.sh
```

### Step 2: Review Output
CCL will see:
- How many files moved to writer/
- backend/ vs research/backend/ comparison
- IAC-011 files in iac011-temp/

### Step 3: Make Decision
Root CCL consults Codio:
- "backend/ and research/backend/ appear to be [same/different]"
- "Recommend: [Option A/B/C]"

### Step 4: Execute Final Cleanup
Based on decision, complete the reorganization.

### Step 5: Commit
```bash
git add -A
git commit -m "chore: Reorganize monorepo structure

- Move Writer (IAC-031) files to writer/
- Clarify backend/ vs research/backend/
- Organize IAC-011 files
- Clean root directory

BREAKING CHANGE: File locations changed"

git push origin main
```

---

## VERIFICATION CHECKLIST

After cleanup:
- [ ] `ls /` shows only: docs/, writer/, research/, backend/, orchestrator/, .git/, README.md
- [ ] writer/ has index.html, package.json, src-tauri/
- [ ] backend/ purpose is clear (scraper or IAC-011?)
- [ ] research/ is organized
- [ ] No duplicate backend/ confusion
- [ ] All git commits successful

---

## THEN SPAWN SUB-CCLS

**Only after cleanup complete:**
1. Root CCL commits cleanup
2. Root CCL spawns 4 sub-CCLs
3. Each sub-CCL reads their module's CCL-INSTRUCTIONS
4. Sub-CCLs start monitoring GitHub issues
5. CCW agents can begin work

---

**TIME ESTIMATE:** 15-30 minutes for cleanup  
**CRITICAL:** Must happen before any coding work begins  
**OWNER:** Root CCL in orchestrator tmux window
