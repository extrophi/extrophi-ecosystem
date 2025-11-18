# GraphQL API for Extrophi Ecosystem

GraphQL interface for the Extrophi Ecosystem, built with Strawberry GraphQL.

## Overview

This GraphQL API provides a unified interface to:
- Query cards, users, and attributions
- Publish cards and earn $EXTROPY tokens
- Create attributions (citations, remixes, replies) with automatic token transfers
- Explore nested relationships between entities

**GraphQL Playground**: `http://localhost:8000/graphql`

## Authentication

All mutations and some queries require API key authentication via the `Authorization` header:

```bash
Authorization: Bearer extro_live_YOUR_API_KEY_HERE
```

## Quick Start

### 1. Start the Server

```bash
cd backend
uvicorn main:app --reload
```

### 2. Open GraphQL Playground

Navigate to `http://localhost:8000/graphql` to access the interactive GraphQL playground.

### 3. Try a Query

```graphql
query {
  searchCards(category: BUSINESS, limit: 10) {
    title
    author {
      username
      extropyBalance
    }
  }
}
```

## Schema Overview

### Types

- **User** - User account with $EXTROPY balance
- **Card** - Published content card
- **Attribution** - Citation, remix, or reply between cards
- **LedgerEntry** - $EXTROPY transaction record
- **UserBalance** - User balance summary with transactions

### Enums

- **PrivacyLevel** - BUSINESS, IDEAS, PERSONAL, PRIVATE, THOUGHTS, JOURNAL
- **CardCategory** - BUSINESS, IDEAS, PERSONAL, TECHNICAL, CREATIVE
- **AttributionType** - citation, remix, reply

## Queries

### Get Card by ID

```graphql
query GetCard {
  card(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    title
    body
    tags
    privacyLevel
    category
    isPublished
    publishedUrl
    author {
      username
      extropyBalance
    }
  }
}
```

### Get User by ID

```graphql
query GetUser {
  user(id: "660e8400-e29b-41d4-a716-446655440001") {
    id
    username
    email
    displayName
    extropyBalance
    cards(privacy: BUSINESS, limit: 10) {
      title
      category
      createdAt
    }
  }
}
```

### Search Cards

```graphql
query SearchCards {
  searchCards(
    query: "business growth"
    category: BUSINESS
    privacy: BUSINESS
    limit: 20
    offset: 0
  ) {
    id
    title
    body
    tags
    author {
      username
      displayName
    }
  }
}
```

**Filters:**
- `query` (String) - Text search in title and body
- `category` (CardCategory) - Filter by category
- `privacy` (PrivacyLevel) - Filter by privacy level
- `userId` (ID) - Filter by author
- `limit` (Int) - Maximum results (default: 50)
- `offset` (Int) - Results offset (default: 0)

### Get User Balance

```graphql
query GetUserBalance {
  userBalance(userId: "660e8400-e29b-41d4-a716-446655440001") {
    userId
    username
    balance
    totalEarned
    totalSpent
    netChange
    recentTransactions {
      id
      amount
      transactionType
      description
      createdAt
    }
  }
}
```

## Mutations

### Publish Card

Publish a card and earn 1 $EXTROPY token.

**Privacy Filtering:**
- ✅ BUSINESS and IDEAS cards are published
- ❌ PERSONAL, PRIVATE, THOUGHTS, JOURNAL cards are filtered out

```graphql
mutation PublishCard {
  publishCard(card: {
    title: "How to Build Momentum in Business"
    body: "The key to building momentum is consistency..."
    category: BUSINESS
    privacyLevel: BUSINESS
    tags: ["business", "growth", "momentum"]
  }) {
    publishedUrls
    extropyEarned
    cardsPublished
    cardsFiltered
  }
}
```

**Response:**
```json
{
  "data": {
    "publishCard": {
      "publishedUrls": ["https://extrophi.ai/cards/how-to-build-momentum-in-business-a1b2c3d4"],
      "extropyEarned": "1.00000000",
      "cardsPublished": 1,
      "cardsFiltered": 0
    }
  }
}
```

### Cite Card

Create a citation and transfer 0.1 $EXTROPY to the author.

```graphql
mutation CiteCard {
  citeCard(
    cardId: "550e8400-e29b-41d4-a716-446655440000"
    context: "This insight perfectly captures the essence of..."
  ) {
    attributionId
    sourceCardId
    targetCardId
    attributionType
    extropyTransferred
    toUserId
  }
}
```

**Response:**
```json
{
  "data": {
    "citeCard": {
      "attributionId": "770e8400-e29b-41d4-a716-446655440002",
      "sourceCardId": "550e8400-e29b-41d4-a716-446655440000",
      "targetCardId": "660e8400-e29b-41d4-a716-446655440001",
      "attributionType": "citation",
      "extropyTransferred": "0.10000000",
      "toUserId": "880e8400-e29b-41d4-a716-446655440003"
    }
  }
}
```

### Remix Card

Build upon someone's card and transfer 0.5 $EXTROPY to the author.

```graphql
mutation RemixCard {
  remixCard(
    cardId: "550e8400-e29b-41d4-a716-446655440000"
    context: "Building on this idea, I've discovered that..."
  ) {
    attributionId
    attributionType
    extropyTransferred
  }
}
```

### Reply Card

Reply to a card and transfer 0.05 $EXTROPY to the author.

```graphql
mutation ReplyCard {
  replyCard(
    cardId: "550e8400-e29b-41d4-a716-446655440000"
    context: "Interesting point! Have you considered..."
  ) {
    attributionId
    attributionType
    extropyTransferred
  }
}
```

## Nested Queries

GraphQL's power comes from nested queries. Fetch related data in a single request.

### Example: Deep Nested Query

```graphql
query DeepNested {
  card(id: "550e8400-e29b-41d4-a716-446655440000") {
    title
    author {
      username
      extropyBalance
      cards(privacy: BUSINESS, limit: 5) {
        title
        category
        attributions(limit: 3) {
          attributionType
          targetCard {
            title
            author {
              username
            }
          }
        }
      }
    }
  }
}
```

This single query fetches:
1. The card
2. Its author
3. The author's other cards
4. Attributions on those cards
5. The cards that made those attributions
6. The authors of those cards

## Token Economics

| Action | Reward | Recipient |
|--------|--------|-----------|
| Publish Card | +1.0 $EXTROPY | Author |
| Cite Card | +0.1 $EXTROPY | Cited author |
| Remix Card | +0.5 $EXTROPY | Original author |
| Reply Card | +0.05 $EXTROPY | Original author |

**Rules:**
- Cannot attribute your own cards
- Each attribution requires sufficient balance
- All transactions are recorded in immutable ledger

## Error Handling

GraphQL returns errors in the `errors` array:

```json
{
  "errors": [
    {
      "message": "Authentication required",
      "path": ["publishCard"]
    }
  ],
  "data": null
}
```

**Common Errors:**
- `Authentication required` - Missing or invalid API key
- `User not found` - Invalid user ID
- `Card not found` - Invalid card ID
- `Cannot attribute your own card` - Attempted self-attribution
- `Insufficient balance` - Not enough $EXTROPY for transfer

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_graphql.py -v
```

**Test Coverage:**
- 9 Query tests
- 8 Mutation tests
- 2 Nested query tests
- 4 Edge case tests

Total: **23 tests**

## Integration Examples

### Python (httpx)

```python
import httpx

GRAPHQL_URL = "http://localhost:8000/graphql"
API_KEY = "extro_live_YOUR_API_KEY"

query = """
query SearchCards($category: CardCategory) {
  searchCards(category: $category, limit: 10) {
    title
    author {
      username
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "query": query,
    "variables": {"category": "BUSINESS"}
}

response = httpx.post(GRAPHQL_URL, json=payload, headers=headers)
data = response.json()
print(data["data"]["searchCards"])
```

### JavaScript (fetch)

```javascript
const GRAPHQL_URL = "http://localhost:8000/graphql";
const API_KEY = "extro_live_YOUR_API_KEY";

const query = `
  mutation PublishCard($card: CardInput!) {
    publishCard(card: $card) {
      publishedUrls
      extropyEarned
    }
  }
`;

const variables = {
  card: {
    title: "New Insight",
    body: "Content here",
    category: "BUSINESS",
    privacyLevel: "BUSINESS",
    tags: []
  }
};

fetch(GRAPHQL_URL, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ query, variables })
})
.then(res => res.json())
.then(data => console.log(data.data.publishCard));
```

### cURL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer extro_live_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { searchCards(category: BUSINESS, limit: 5) { title } }"
  }'
```

## GraphQL Playground Tips

1. **Auto-completion**: Press `Ctrl+Space` to see available fields
2. **Documentation**: Click "Docs" in the right panel to explore the schema
3. **History**: Access previous queries from the "History" tab
4. **Variables**: Use the "Query Variables" panel for dynamic values
5. **Headers**: Set authentication headers in the "HTTP Headers" panel

## Architecture

```
backend/
├── graphql/
│   ├── __init__.py         # Module exports
│   ├── schema.py           # GraphQL types, queries, mutations (350+ lines)
│   ├── resolvers.py        # Query/mutation logic (550+ lines)
│   ├── context.py          # Request context with auth (80+ lines)
│   └── README.md           # This file
├── main.py                 # FastAPI app with GraphQL router
└── tests/
    └── test_graphql.py     # Comprehensive test suite (700+ lines, 23 tests)
```

## Performance Considerations

### N+1 Query Problem

GraphQL can cause N+1 queries. Use DataLoaders (future enhancement) for batching:

```python
# Without DataLoader (N+1 queries)
cards = get_cards()  # 1 query
for card in cards:
    author = get_author(card.user_id)  # N queries

# With DataLoader (2 queries)
cards = get_cards()  # 1 query
authors = batch_get_authors([card.user_id for card in cards])  # 1 query
```

### Query Complexity

Limit query depth and complexity to prevent abuse:

```graphql
# Bad: Very deep nesting
query {
  user {
    cards {
      author {
        cards {
          author {
            cards {  # Too deep!
              ...
            }
          }
        }
      }
    }
  }
}
```

**Current Limits:**
- Default `limit` parameter: 50
- Maximum `limit`: 500 (enforced by resolvers)
- No explicit depth limit (add if needed)

## Future Enhancements

- [ ] DataLoaders for batching
- [ ] Subscriptions (real-time updates)
- [ ] Query complexity analysis
- [ ] Field-level permissions
- [ ] Cursor-based pagination
- [ ] Aggregation queries (counts, sums)
- [ ] Full-text search with ranking

## Support

- **GraphQL Playground**: http://localhost:8000/graphql
- **REST API Docs**: http://localhost:8000/docs
- **Issue Tracker**: GitHub Issues

## License

Part of the Extrophi Ecosystem project.
