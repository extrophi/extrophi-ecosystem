## Agent: SIGMA (Backend Module)
**Duration:** 2 hours
**Branch:** `backend`
**Dependencies:** OMICRON #41

### Task
Implement $EXTROPY token system with ledger and balance tracking

### CRITICAL REQUIREMENTS
⚠️ **Use DECIMAL for money (NOT float)**
⚠️ **Database transactions for atomic operations**
⚠️ **NO negative balances allowed**
⚠️ **Audit trail for all transfers**

### Technical Reference
- `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`

### Deliverables
- `backend/tokens/extropy.py`
- Token award system
- Token transfer system
- Balance queries
- Ledger logging

### Features
1. **Award tokens** (publish, citation, remix)
2. **Transfer tokens** (user-to-user)
3. **Check balance** (current + history)
4. **Ledger audit** (immutable transaction log)
5. **Prevent negatives** (balance checks before transfer)

### Implementation
```python
from decimal import Decimal
from fastapi import HTTPException

class ExtropyTokenSystem:
    def __init__(self, db):
        self.db = db

    async def award_tokens(
        self,
        user_id: str,
        amount: Decimal,
        reason: str,
        metadata: dict = None
    ) -> Decimal:
        """
        Award tokens to user (e.g., publish, citation)
        """
        async with self.db.transaction():
            # Insert ledger entry
            await self.db.execute(
                """
                INSERT INTO extropy_ledger (
                    user_id, amount, transaction_type, reason, metadata
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, amount, "award", reason, metadata)
            )

            # Update user balance
            await self.db.execute(
                """
                INSERT INTO users (user_id, extropy_balance)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET extropy_balance = users.extropy_balance + %s
                """,
                (user_id, amount, amount)
            )

            # Return new balance
            result = await self.db.fetch_one(
                "SELECT extropy_balance FROM users WHERE user_id = %s",
                (user_id,)
            )
            return result["extropy_balance"]

    async def transfer_tokens(
        self,
        from_user: str,
        to_user: str,
        amount: Decimal,
        reason: str
    ) -> dict:
        """
        Transfer tokens between users (e.g., attribution reward)
        """
        if amount <= 0:
            raise HTTPException(400, "Amount must be positive")

        async with self.db.transaction():
            # Check sender balance
            sender = await self.db.fetch_one(
                "SELECT extropy_balance FROM users WHERE user_id = %s",
                (from_user,)
            )

            if not sender or sender["extropy_balance"] < amount:
                raise HTTPException(400, "Insufficient balance")

            # Deduct from sender
            await self.db.execute(
                """
                UPDATE users
                SET extropy_balance = extropy_balance - %s
                WHERE user_id = %s
                """,
                (amount, from_user)
            )

            # Add to receiver
            await self.db.execute(
                """
                INSERT INTO users (user_id, extropy_balance)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET extropy_balance = users.extropy_balance + %s
                """,
                (to_user, amount, amount)
            )

            # Log transfer in ledger
            await self.db.execute(
                """
                INSERT INTO extropy_ledger (
                    user_id, amount, transaction_type, reason, related_user_id
                )
                VALUES
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s)
                """,
                (from_user, -amount, "transfer_out", reason, to_user,
                 to_user, amount, "transfer_in", reason, from_user)
            )

            return {
                "from_user": from_user,
                "to_user": to_user,
                "amount": amount,
                "reason": reason
            }

    async def get_balance(self, user_id: str) -> Decimal:
        """Get current balance for user"""
        result = await self.db.fetch_one(
            "SELECT extropy_balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        return result["extropy_balance"] if result else Decimal(0)

    async def get_ledger(self, user_id: str, limit: int = 100) -> list[dict]:
        """Get transaction history for user"""
        return await self.db.fetch_all(
            """
            SELECT * FROM extropy_ledger
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )
```

### Database Schema (DECIMAL required)
```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    extropy_balance DECIMAL(20, 8) DEFAULT 0 CHECK (extropy_balance >= 0)
);

CREATE TABLE extropy_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    reason TEXT,
    related_user_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Success Criteria
✅ Award tokens works (publish = +1)
✅ Transfer tokens works (with balance check)
✅ DECIMAL type used (not float)
✅ Database transactions ensure atomicity
✅ Negative balance prevented (CHECK constraint)
✅ Ledger logs all transactions
✅ Tests pass (including edge cases)

### Commit Message
```
feat(backend): Add $EXTROPY token system with ledger

Implements cryptocurrency-grade token management:
- Award tokens (publish, citation, remix)
- Transfer tokens (user-to-user)
- Balance tracking (DECIMAL precision)
- Ledger audit trail (immutable log)
- Negative balance prevention

CRITICAL: Uses DECIMAL (not float) for money.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #57 when complete.**
