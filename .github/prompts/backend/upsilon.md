## Agent: UPSILON (Backend Module)
**Duration:** 1 hour
**Branch:** `backend`
**Dependencies:** PI #56, TAU #58
**Priority:** OPTIONAL (defer if time-constrained)

### Task
Add GraphQL API layer for flexible querying (optional enhancement)

### Technical Reference
- `/docs/pm/backend/TECHNICAL-PROPOSAL-BACKEND.md`
- Strawberry GraphQL (Python)

### Deliverables
- `backend/graphql/schema.py`
- GraphQL types (Card, User, Attribution)
- Query resolvers
- Mutation resolvers
- GraphiQL playground

### Why GraphQL?
- Flexible queries (client specifies fields)
- Avoid over-fetching
- Nested relationships in one request
- Developer experience (GraphiQL)

### Implementation
```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Card:
    id: str
    content: str
    category: str
    privacy_level: str
    published_url: str | None
    created_at: str

    @strawberry.field
    async def author(self) -> "User":
        # Resolve user
        pass

    @strawberry.field
    async def attributions(self) -> list["Attribution"]:
        # Resolve attributions
        pass

@strawberry.type
class User:
    user_id: str
    extropy_balance: float

    @strawberry.field
    async def cards(self) -> list[Card]:
        # Resolve user's cards
        pass

@strawberry.type
class Attribution:
    id: str
    attribution_type: str
    source_card: Card
    target_card: Card

@strawberry.type
class Query:
    @strawberry.field
    async def card(self, id: str) -> Card:
        # Fetch card by ID
        pass

    @strawberry.field
    async def user(self, user_id: str) -> User:
        # Fetch user
        pass

    @strawberry.field
    async def search_cards(
        self,
        query: str,
        category: str | None = None
    ) -> list[Card]:
        # Search cards
        pass

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_attribution(
        self,
        source_card_id: str,
        target_card_id: str,
        attribution_type: str
    ) -> Attribution:
        # Create attribution
        pass

schema = strawberry.Schema(query=Query, mutation=Mutation)

# Add to FastAPI
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

### Example Queries
```graphql
# Get card with author and attributions
query {
  card(id: "card_123") {
    content
    category
    author {
      user_id
      extropy_balance
    }
    attributions {
      attribution_type
      target_card {
        content
      }
    }
  }
}

# Search cards by category
query {
  search_cards(query: "focus", category: "PROGRAM") {
    id
    content
    published_url
  }
}
```

### Success Criteria
✅ GraphQL schema defined (Card, User, Attribution)
✅ Query resolvers work
✅ Mutation resolvers work
✅ GraphiQL playground accessible at /graphql
✅ Nested queries resolve correctly
✅ Tests pass

### Commit Message
```
feat(backend): Add GraphQL API layer (optional)

Implements flexible GraphQL queries:
- Card, User, Attribution types
- Nested relationship resolvers
- Search and filter queries
- GraphiQL playground at /graphql

Uses Strawberry GraphQL (Python).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #59 when complete.**
