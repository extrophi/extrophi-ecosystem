## Agent: TAU (Backend Module)
**Duration:** 2 hours
**Branch:** `backend`
**Dependencies:** SIGMA #57, OMICRON #41

### Task
Build attribution API for citations, remixes, and replies

### Technical Reference
- `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`

### Deliverables
- `backend/api/attributions.py`
- Citation tracking
- Remix rewards
- Reply threading
- $EXTROPY transfers

### Attribution Types
1. **CITATION** - Reference someone's card (0.1 $EXTROPY to author)
2. **REMIX** - Build upon someone's card (0.5 $EXTROPY to author)
3. **REPLY** - Comment on someone's card (0.05 $EXTROPY to author)

### Features
- Track who attributes whom
- Automatic $EXTROPY transfers
- Attribution graph (who cited who)
- Backlinks (show where your content is cited)

### Implementation
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter()

class AttributionRequest(BaseModel):
    source_card_id: str  # Card being attributed
    target_card_id: str  # Card doing the attributing
    attribution_type: str  # 'citation', 'remix', 'reply'
    user_id: str

@router.post("/api/attributions")
async def create_attribution(
    request: AttributionRequest,
    user_id: str = Depends(require_api_key)
):
    """
    Create attribution and transfer $EXTROPY
    """
    # Get source card author
    source_card = await db.fetch_one(
        "SELECT user_id FROM cards WHERE id = %s",
        (request.source_card_id,)
    )

    if not source_card:
        raise HTTPException(404, "Source card not found")

    source_author = source_card["user_id"]

    # Determine reward amount
    rewards = {
        "citation": Decimal("0.1"),
        "remix": Decimal("0.5"),
        "reply": Decimal("0.05")
    }
    amount = rewards.get(request.attribution_type, Decimal("0"))

    # Store attribution
    await db.execute(
        """
        INSERT INTO attributions (
            source_card_id, target_card_id, attribution_type, attributed_by
        )
        VALUES (%s, %s, %s, %s)
        """,
        (request.source_card_id, request.target_card_id,
         request.attribution_type, user_id)
    )

    # Transfer $EXTROPY (if amount > 0)
    if amount > 0:
        await extropy_system.transfer_tokens(
            from_user=user_id,
            to_user=source_author,
            amount=amount,
            reason=f"{request.attribution_type}: {request.target_card_id}"
        )

    return {
        "attribution_id": "...",
        "extropy_transferred": amount,
        "to_user": source_author
    }

@router.get("/api/attributions/{card_id}")
async def get_attributions(card_id: str):
    """
    Get all attributions for a card (who cited it)
    """
    attributions = await db.fetch_all(
        """
        SELECT
            a.*,
            c.content as target_content,
            u.user_id as attributed_by_user
        FROM attributions a
        JOIN cards c ON a.target_card_id = c.id
        JOIN users u ON a.attributed_by = u.user_id
        WHERE a.source_card_id = %s
        ORDER BY a.created_at DESC
        """,
        (card_id,)
    )

    return {
        "card_id": card_id,
        "attribution_count": len(attributions),
        "attributions": attributions
    }

@router.get("/api/users/{user_id}/attributions/received")
async def get_received_attributions(user_id: str):
    """
    Get attributions received by user (citations of their work)
    """
    # Find all cards by user that have been attributed
    return await db.fetch_all(
        """
        SELECT
            c.id as card_id,
            c.content,
            COUNT(a.id) as attribution_count,
            SUM(CASE a.attribution_type
                WHEN 'citation' THEN 0.1
                WHEN 'remix' THEN 0.5
                WHEN 'reply' THEN 0.05
            END) as extropy_earned
        FROM cards c
        JOIN attributions a ON c.id = a.source_card_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.content
        ORDER BY attribution_count DESC
        """,
        (user_id,)
    )
```

### Database Schema
```sql
CREATE TABLE attributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_card_id UUID NOT NULL,  -- Card being attributed
    target_card_id UUID NOT NULL,  -- Card doing the attributing
    attribution_type VARCHAR(50) NOT NULL,  -- citation, remix, reply
    attributed_by VARCHAR(255) NOT NULL,  -- User ID
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (source_card_id) REFERENCES cards(id),
    FOREIGN KEY (target_card_id) REFERENCES cards(id)
);

CREATE INDEX idx_attributions_source ON attributions(source_card_id);
CREATE INDEX idx_attributions_target ON attributions(target_card_id);
```

### Success Criteria
✅ Citation creates attribution record
✅ $EXTROPY transfers automatically
✅ Remix rewards 0.5 tokens
✅ Reply rewards 0.05 tokens
✅ Backlinks query works
✅ Attribution graph queryable
✅ Tests pass

### Commit Message
```
feat(backend): Add attribution API with $EXTROPY rewards

Implements citation tracking and rewards:
- CITATION: +0.1 $EXTROPY to author
- REMIX: +0.5 $EXTROPY to author
- REPLY: +0.05 $EXTROPY to author

Features:
- Attribution graph (who cited who)
- Backlinks (where your content is cited)
- Automatic $EXTROPY transfers
- Received attributions query

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #58 when complete.**
