## Agent: RHO (Backend Module)
**Duration:** 1 hour
**Branch:** `backend`
**Dependencies:** OMICRON #41

### Task
Implement API key authentication system

### Technical Reference
- `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`

### Deliverables
- `backend/auth/api_keys.py`
- API key generation
- Key validation middleware
- Rate limiting per key
- Key management endpoints

### Features
1. **Generate API keys** (secure random, 32+ chars)
2. **Validate requests** (check Authorization header)
3. **Rate limiting** (1000 req/hour per key)
4. **Key management** (create, revoke, list)
5. **User association** (keys tied to user accounts)

### Implementation
```python
from fastapi import Header, HTTPException, Depends
import secrets
import hashlib

class APIKeyAuth:
    def __init__(self, db):
        self.db = db

    def generate_key(self, user_id: str) -> str:
        """Generate new API key"""
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Store hash in database
        self.db.execute(
            "INSERT INTO api_keys (user_id, key_hash) VALUES (%s, %s)",
            (user_id, key_hash)
        )

        return raw_key  # Return once, never stored plaintext

    async def validate_key(self, authorization: str = Header(None)) -> str:
        """Validate API key from Authorization header"""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Missing API key")

        key = authorization.replace("Bearer ", "")
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        # Check database
        result = await self.db.fetch_one(
            "SELECT user_id FROM api_keys WHERE key_hash = %s AND revoked = false",
            (key_hash,)
        )

        if not result:
            raise HTTPException(401, "Invalid API key")

        return result["user_id"]

# FastAPI dependency
async def require_api_key(user_id: str = Depends(api_key_auth.validate_key)):
    return user_id
```

### Endpoints
```python
# Generate new API key
POST /api/keys
{
  "user_id": "user_123"
}
→ {"api_key": "sk_live_..."}

# List user's keys
GET /api/keys
Authorization: Bearer sk_live_...
→ [{"id": "key_1", "created_at": "..."}]

# Revoke key
DELETE /api/keys/{key_id}
```

### Success Criteria
✅ API key generation works (secure random)
✅ Validation middleware functional
✅ Rate limiting enforced
✅ Keys stored as hashes (never plaintext)
✅ Revoke functionality works
✅ Tests pass

### Commit Message
```
feat(backend): Add API key authentication system

Implements secure API key management:
- Secure key generation (32+ chars)
- SHA-256 hashed storage
- Authorization middleware
- Rate limiting (1000 req/hour)
- Key revocation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #55 when complete.**
