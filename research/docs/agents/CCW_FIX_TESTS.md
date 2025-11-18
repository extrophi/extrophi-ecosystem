# CCW Fix Unit Test Failures

**2 critical issues**

---

## Issue 1: SQLAlchemy Reserved Attribute

**File**: `backend/db/models.py`

**Error**:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

**Fix**: Rename `metadata` column to `extra_metadata` or `content_metadata`

```python
# In ContentORM class
# CHANGE THIS:
metadata = Column(JSONB, default={})

# TO THIS:
extra_metadata = Column(JSONB, default={})
```

Also update any code that references `metadata` column to use `extra_metadata`.

---

## Issue 2: YouTube Transcript Type Error

**File**: `backend/scrapers/adapters/youtube.py:115`

**Error**:
```
AttributeError: 'list' object has no attribute 'split'
```

**Fix**: Transcript is a list of dicts, not a string

```python
# In normalize() method
# CHANGE THIS:
word_count=len(transcript.split()),

# TO THIS:
word_count=len(" ".join([seg.get("text", "") for seg in transcript]).split()),

# Or if transcript is already joined:
word_count=len(transcript.split()) if isinstance(transcript, str) else len(" ".join([seg.get("text", "") for seg in transcript]).split()),
```

---

## Commands

```bash
# Fix the files
# Then run tests locally:
pytest tests/unit/ -v

# If passes:
git add -A
git commit -m "fix: Reserved 'metadata' column name and YouTube transcript type"
git push origin main
```

GO.
