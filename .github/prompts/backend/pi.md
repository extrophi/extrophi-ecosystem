## Agent: PI (Backend Module)
**Duration:** 2 hours
**Branch:** `backend`
**Dependencies:** RHO #55, OMICRON #41

### Task
Build publish endpoint that accepts cards from Writer module

### Technical Reference
- `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`

### Deliverables
- `backend/api/publish.py`
- Card publishing endpoint
- Markdown conversion
- URL generation
- $EXTROPY reward calculation

### Features
1. **Accept cards** from Writer (BUSINESS + IDEAS only)
2. **Convert to markdown** (structured format)
3. **Generate URLs** (slug from title or ID)
4. **Store in database** (cards table)
5. **Award $EXTROPY** tokens (1 token per publish)
6. **Return published URLs**

### Implementation
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class PublishRequest(BaseModel):
    cards: list[dict]  # From Writer
    user_id: str

class PublishResponse(BaseModel):
    published_urls: list[str]
    extropy_earned: float
    git_sha: str | None

@router.post("/api/publish", response_model=PublishResponse)
async def publish_cards(
    request: PublishRequest,
    user_id: str = Depends(require_api_key)
):
    """
    Publish cards from Writer module
    """
    published_urls = []
    extropy_earned = 0.0

    for card in request.cards:
        # Validate privacy level (BUSINESS or IDEAS only)
        if card["privacy_level"] not in ["BUSINESS", "IDEAS"]:
            continue

        # Convert to markdown
        markdown = convert_to_markdown(card)

        # Generate URL slug
        slug = generate_slug(card["content"][:50])
        url = f"https://extrophi.ai/cards/{slug}"

        # Store in database
        await db.execute(
            """
            INSERT INTO cards (user_id, content, category, privacy_level, published_url)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, card["content"], card["category"], card["privacy_level"], url)
        )

        # Award $EXTROPY (1 token per publish)
        await award_extropy(user_id, 1.0, f"Published card: {slug}")

        published_urls.append(url)
        extropy_earned += 1.0

    return PublishResponse(
        published_urls=published_urls,
        extropy_earned=extropy_earned,
        git_sha=None  # Populated by Writer's Git integration
    )
```

### Database Schema (from OMICRON)
```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    privacy_level VARCHAR(50),
    published_url TEXT,
    git_sha VARCHAR(40),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Success Criteria
✅ Accepts cards from Writer
✅ Filters by privacy (BUSINESS + IDEAS only)
✅ Converts to markdown
✅ Generates URLs (unique slugs)
✅ Stores in PostgreSQL
✅ Awards $EXTROPY tokens
✅ Tests pass

### Commit Message
```
feat(backend): Add publish endpoint for Writer cards

Implements card publishing pipeline:
- Accept cards from Writer module
- Privacy filtering (BUSINESS + IDEAS)
- Markdown conversion
- URL generation (slugs)
- PostgreSQL storage
- $EXTROPY rewards (1 token/publish)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #56 when complete.**
