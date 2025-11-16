# CCW Fix MyPy Type Errors

**14 errors in 5 files**

---

## Errors to Fix

### 1. backend/tests/conftest.py:18
```
error: The return type of a generator function should be "Generator" or one of its supertypes
```

**Fix**: Change return type annotation
```python
from typing import Generator
from sqlalchemy.orm import Session

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    # fixture code
    yield session
```

### 2. backend/db/models.py (lines 21, 70, 110, 137)
```
error: Variable "backend.db.models.Base" is not valid as a type
error: Invalid base class "Base"
```

**Fix**: Use DeclarativeBase from SQLAlchemy 2.0
```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Content(Base):
    __tablename__ = "contents"
    # ...
```

### 3. backend/scrapers/adapters/twitter.py:52
```
error: Need type annotation for "tweets" (hint: "tweets: list[<type>] = ...")
```

**Fix**: Add type annotation
```python
tweets: list[dict[str, Any]] = []
```

### 4. backend/api/routes/analyze.py:46
```
error: Need type annotation for "content_list" (hint: "content_list: list[<type>] = ...")
```

**Fix**: Add type annotation
```python
content_list: list[dict[str, Any]] = []
```

### 5. backend/queue/tasks.py (lines 11, 50, 79)
```
error: Missing return statement
```

**Fix**: Add explicit return at end of each function
```python
def scrape_task(...) -> dict[str, Any]:
    # ... task code ...
    return {"status": "completed", "result": result}
```

---

## Commands

```bash
# Fix all files
# Then verify:
mypy --ignore-missing-imports backend/

# If passes:
git add -A
git commit -m "fix: MyPy type errors (Generator, DeclarativeBase, annotations)"
git push origin main
```

GO.
