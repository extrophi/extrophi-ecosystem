# CCW Fix Lint Issues

**COPY INTO CLAUDE CODE WEB**

---

Clone: https://github.com/Iamcodio/IAC-032-unified-scraper.git

## Task
Fix all lint issues so CI passes.

## Commands to Run

```bash
# Install tools
pip install black isort ruff mypy

# Auto-fix all formatting
black backend/
isort backend/
ruff check backend/ --fix

# Verify
black --check backend/
isort --check-only backend/
ruff check backend/

# Commit and push
git add -A
git commit -m "style: Fix all lint issues (Black, isort, Ruff)"
git push origin main
```

## If Ruff Can't Auto-Fix

Check for:
- Line too long (>100 chars) - Split strings
- Variable naming (N806) - Use lowercase for function variables
- Unused imports (F401) - Remove them

## GO
