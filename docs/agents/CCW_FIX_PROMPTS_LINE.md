# CCW Fix Line Too Long

**SINGLE FIX NEEDED**

---

## File
`backend/analysis/prompts.py` line 53

## Problem
```
E501 Line too long (102 > 100)
PATTERN_DETECTION_PROMPT = """Compare these content pieces from the same author and identify patterns:
```

Line is 102 chars, max is 100.

## Fix
Change line 53 from:
```python
PATTERN_DETECTION_PROMPT = """Compare these content pieces from the same author and identify patterns:
```

To:
```python
PATTERN_DETECTION_PROMPT = """Compare these content pieces from the same author \
and identify patterns:
```

Or use string concatenation:
```python
PATTERN_DETECTION_PROMPT = (
    "Compare these content pieces from the same author and identify patterns:\n"
    "\n"
    "Content pieces:\n"
    ...rest of the string
)
```

## Commands
```bash
# Edit the file to fix line 53
# Then:
ruff check backend/analysis/prompts.py
git add -A
git commit -m "fix: Shorten line 53 in prompts.py to pass Ruff lint"
git push origin main
```

GO.
