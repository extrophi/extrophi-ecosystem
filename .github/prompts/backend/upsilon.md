# IAC-033 Extrophi Ecosystem - UPSILON Agent
## GraphQL API Layer

See full prompt in issue #72

**Repository**: https://github.com/extrophi/extrophi-ecosystem  
**Branch**: `claude/graphql-api-upsilon`  
**Issue**: Closes #72  
**Duration**: 1 hour

## Quick Start

```bash
# Create branch
git checkout -b claude/graphql-api-upsilon

# Install Strawberry
pip install strawberry-graphql[fastapi]==0.217.1

# Create GraphQL directory
mkdir -p backend/graphql
```

## Mission
Add GraphQL API layer using Strawberry on top of existing REST endpoints.

## Files to Create

1. **`backend/graphql/schema.py`** (300+ lines)
   - Types: Card, User, Attribution, LedgerEntry
   - Queries: card, user, searchCards, userBalance
   - Mutations: publishCard, citeCard, remixCard, replyCard

2. **`backend/graphql/resolvers.py`** (200+ lines)
   - Database query logic
   - Vector similarity search
   - Nested field resolvers

3. **`backend/graphql/context.py`** (50+ lines)
   - Request context
   - API key authentication

4. **`backend/tests/test_graphql.py`** (200+ lines, 20+ tests)
   - Query tests
   - Mutation tests
   - Nested query tests
   - Authentication tests

5. **`backend/graphql/README.md`**
   - Usage examples
   - Query/mutation samples

## Key GraphQL Features

### Queries
```graphql
query {
  card(id: "123") {
    title
    author {
      username
      extropyBalance
      cards(privacy: "BUSINESS") {
        title
      }
    }
  }
}
```

### Mutations
```graphql
mutation {
  publishCard(
    title: "New Insight"
    body: "Content"
    category: "IDEAS"
    privacyLevel: "BUSINESS"
  ) {
    id
    title
  }
  
  citeCard(cardId: "456") {
    amount
    card {
      author {
        extropyBalance
      }
    }
  }
}
```

### Integration Points
- FastAPI: Register GraphQLRouter at `/graphql`
- Auth: Extract API key from headers
- Database: Use existing SQLAlchemy models
- Rewards: Trigger $EXTROPY transfers via TAU

## Success Criteria
- ✅ GraphQL playground at `/graphql`
- ✅ All REST endpoints exposed
- ✅ Nested queries working
- ✅ Mutations trigger $EXTROPY
- ✅ API key auth
- ✅ 20+ tests passing

## Update Files
- `backend/main.py` - Register GraphQL router
- `backend/pyproject.toml` - Add strawberry-graphql

**When complete**: Create PR "Wave 2 Phase 3: UPSILON - GraphQL API"
