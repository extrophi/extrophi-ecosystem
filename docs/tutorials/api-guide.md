# API Guide: Programmatic Access to Extrophi

Complete reference for using the Extrophi API programmatically. Covers authentication, publishing cards, managing attributions, and $EXTROPY token operations.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Publishing Cards](#publishing-cards)
4. [Attribution System](#attribution-system)
5. [Token Operations](#token-operations)
6. [API Key Management](#api-key-management)
7. [SDKs & Libraries](#sdks--libraries)
8. [Rate Limits](#rate-limits)
9. [Error Handling](#error-handling)
10. [Code Examples](#code-examples)

---

## API Overview

**Base URL:** `https://api.extrophi.ai`

**Protocol:** REST + JSON

**Authentication:** API Key (Bearer token)

**Rate Limits:**
- Free tier: 1,000 requests/hour
- Pro tier: 10,000 requests/hour

**Status:** `200` = Success, `4xx` = Client error, `5xx` = Server error

---

## Authentication

All API endpoints (except `/health`) require authentication via API key.

### Creating an Account

**Endpoint:** `POST /auth/register`

**Request:**
```bash
curl -X POST https://api.extrophi.ai/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "secure-password-here",
    "display_name": "John Doe"
  }'
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "extropy_balance": "0.00000000",
  "created_at": "2025-11-18T10:30:00Z"
}
```

### Getting Your API Key

**Endpoint:** `POST /auth/api-key`

**Request:**
```bash
curl -X POST https://api.extrophi.ai/auth/api-key \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "secure-password-here"
  }'
```

**Response:**
```json
{
  "api_key": "ext_1234567890abcdef",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_at": null,
  "created_at": "2025-11-18T10:30:00Z"
}
```

**⚠️ IMPORTANT:** Store your API key securely. It won't be shown again.

### Using Your API Key

**Method 1: Header (Recommended)**
```bash
curl https://api.extrophi.ai/endpoint \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Method 2: X-API-Key Header**
```bash
curl https://api.extrophi.ai/endpoint \
  -H "X-API-Key: ext_1234567890abcdef"
```

**Method 3: Query Parameter (Less secure)**
```bash
curl "https://api.extrophi.ai/endpoint?api_key=ext_1234567890abcdef"
```

---

## Publishing Cards

Publish cards from the Writer app or programmatically from any source.

### Publish Single Card

**Endpoint:** `POST /publish`

**Request:**
```bash
curl -X POST https://api.extrophi.ai/publish \
  -H "Authorization: Bearer ext_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "cards": [
      {
        "title": "How to Build Momentum in Business",
        "body": "The key to building momentum is consistency...\n\nHere are 5 strategies that work:\n\n1. Ship daily\n2. Document publicly\n3. Engage authentically\n4. Learn from feedback\n5. Iterate quickly",
        "category": "BUSINESS",
        "privacy_level": "BUSINESS",
        "tags": ["business", "growth", "momentum"]
      }
    ]
  }'
```

**Response:**
```json
{
  "published_urls": [
    "https://extrophi.ai/cards/how-to-build-momentum-in-business-a1b2c3d4"
  ],
  "extropy_earned": "1.00000000",
  "cards_published": 1,
  "cards_filtered": 0,
  "git_sha": null
}
```

### Publish Multiple Cards (Batch)

**Request:**
```bash
curl -X POST https://api.extrophi.ai/publish \
  -H "Authorization: Bearer ext_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "cards": [
      {
        "title": "Card 1",
        "body": "Content here...",
        "category": "BUSINESS",
        "privacy_level": "BUSINESS",
        "tags": ["tag1", "tag2"]
      },
      {
        "title": "Card 2",
        "body": "More content...",
        "category": "IDEAS",
        "privacy_level": "IDEAS",
        "tags": ["tag3"]
      },
      {
        "title": "Card 3 (Private)",
        "body": "Personal thoughts...",
        "category": "PERSONAL",
        "privacy_level": "PERSONAL",
        "tags": []
      }
    ]
  }'
```

**Response:**
```json
{
  "published_urls": [
    "https://extrophi.ai/cards/card-1-a1b2c3d4",
    "https://extrophi.ai/cards/card-2-e5f6g7h8"
  ],
  "extropy_earned": "2.00000000",
  "cards_published": 2,
  "cards_filtered": 1,
  "git_sha": null
}
```

**Note:** Card 3 was filtered out because `privacy_level: PERSONAL` is not publishable.

### Privacy Levels

Only these privacy levels can be published:
- ✅ `BUSINESS` - Professional, work-related content
- ✅ `IDEAS` - Creative ideas, concepts, insights

These privacy levels are NOT published:
- ❌ `PERSONAL` - Personal reflections
- ❌ `PRIVATE` - Sensitive information
- ❌ `THOUGHTS` - Stream of consciousness
- ❌ `JOURNAL` - Daily journal entries

### Card Metadata (Optional)

**Extended Request:**
```json
{
  "cards": [
    {
      "title": "My Card",
      "body": "Content...",
      "category": "BUSINESS",
      "privacy_level": "BUSINESS",
      "tags": ["tag1", "tag2"],
      "metadata": {
        "source": "writer-app",
        "session_id": "session-uuid",
        "transcription_model": "whisper-base",
        "word_count": 250,
        "reading_time_minutes": 2
      }
    }
  ]
}
```

**Metadata** is stored but not displayed publicly. Useful for your own tracking.

---

## Attribution System

Attributions track citations, remixes, and replies between cards, with automatic $EXTROPY rewards.

### Creating an Attribution

**Endpoint:** `POST /attributions`

**Attribution Types:**
- `citation` - Reference someone's card (+0.1 $EXTROPY to author)
- `remix` - Build upon someone's card (+0.5 $EXTROPY to author)
- `reply` - Comment on someone's card (+0.05 $EXTROPY to author)

**Request:**
```bash
curl -X POST https://api.extrophi.ai/attributions \
  -H "Authorization: Bearer ext_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
    "attribution_type": "citation",
    "user_id": "770e8400-e29b-41d4-a716-446655440002",
    "context": "Building on this idea in my latest post...",
    "excerpt": "Key insight from the original card"
  }'
```

**Response:**
```json
{
  "attribution_id": "880e8400-e29b-41d4-a716-446655440003",
  "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
  "attribution_type": "citation",
  "extropy_transferred": "0.10000000",
  "to_user_id": "990e8400-e29b-41d4-a716-446655440004",
  "context": "Building on this idea in my latest post...",
  "excerpt": "Key insight from the original card",
  "created_at": "2025-11-18T10:30:00Z"
}
```

**What Happened:**
1. Attribution created linking `source_card` → `target_card`
2. 0.1 $EXTROPY transferred from `user_id` to `source_card` author
3. Transaction recorded in immutable ledger

### Getting Attributions for a Card

**Endpoint:** `GET /attributions/{card_id}`

**Request:**
```bash
curl https://api.extrophi.ai/attributions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "card_id": "550e8400-e29b-41d4-a716-446655440000",
  "attribution_count": 15,
  "attributions": [
    {
      "attribution_id": "...",
      "target_card_id": "...",
      "target_card_title": "My Analysis of Your Idea",
      "attributed_by_user_id": "...",
      "attributed_by_username": "johndoe",
      "attribution_type": "citation",
      "extropy_transferred": "0.10000000",
      "context": "Great insights here, expanding on...",
      "created_at": "2025-11-18T10:30:00Z"
    }
  ]
}
```

**Use Case:** Show "backlinks" on your card page—who's citing your work.

### Getting Received Attributions (User)

**Endpoint:** `GET /attributions/users/{user_id}/received`

**Request:**
```bash
curl https://api.extrophi.ai/attributions/users/550e8400-e29b-41d4-a716-446655440000/received \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_attributions": 42,
  "total_extropy_earned": "15.25000000",
  "cards": [
    {
      "card_id": "...",
      "card_title": "My Popular Card",
      "attribution_count": 25,
      "extropy_earned": "10.50000000",
      "citations": 5,
      "remixes": 15,
      "replies": 5
    }
  ]
}
```

**Use Case:** Dashboard showing which of your cards are most cited.

### Attribution Graph

**Endpoint:** `GET /attributions/{card_id}/graph?depth=2`

**Request:**
```bash
curl "https://api.extrophi.ai/attributions/550e8400-e29b-41d4-a716-446655440000/graph?depth=2" \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "center_card_id": "550e8400-e29b-41d4-a716-446655440000",
  "nodes": [
    {
      "card_id": "...",
      "title": "Card Title",
      "user_id": "...",
      "attribution_count": 5
    }
  ],
  "edges": [
    {
      "source_card_id": "...",
      "target_card_id": "...",
      "attribution_type": "citation",
      "created_at": "2025-11-18T10:30:00Z"
    }
  ],
  "depth": 2
}
```

**Use Case:** Visualize knowledge graph—who cited whom, recursive relationships.

---

## Token Operations

Manage $EXTROPY tokens: check balances, view transaction history, transfer tokens.

### Get Token Balance

**Endpoint:** `GET /tokens/balance/{user_id}`

**Request:**
```bash
curl https://api.extrophi.ai/tokens/balance/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "balance": "25.50000000",
  "last_updated": "2025-11-18T10:30:00Z"
}
```

### Get Token Statistics

**Endpoint:** `GET /tokens/stats/{user_id}`

**Request:**
```bash
curl https://api.extrophi.ai/tokens/stats/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "balance": "25.50000000",
  "total_earned": "50.00000000",
  "total_spent": "24.50000000",
  "net_change": "25.50000000",
  "transaction_counts": {
    "earn": 50,
    "transfer": 15,
    "attribution": 30,
    "total": 95
  }
}
```

**Metrics Explained:**
- `total_earned`: All incoming tokens (publish + attributions received)
- `total_spent`: All outgoing tokens (attributions given + transfers)
- `net_change`: `total_earned - total_spent` (should equal `balance`)

### Get Transaction Ledger

**Endpoint:** `GET /tokens/ledger/{user_id}?limit=100&offset=0`

**Request:**
```bash
curl "https://api.extrophi.ai/tokens/ledger/550e8400-e29b-41d4-a716-446655440000?limit=100" \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_transactions": 95,
  "transactions": [
    {
      "id": "tx-uuid-1",
      "from_user_id": null,
      "to_user_id": "550e8400-e29b-41d4-a716-446655440000",
      "amount": "1.00000000",
      "transaction_type": "earn",
      "card_id": "card-uuid-1",
      "description": "Published card: How to Build Momentum",
      "to_user_balance_after": "26.50000000",
      "created_at": "2025-11-18T10:30:00Z"
    },
    {
      "id": "tx-uuid-2",
      "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
      "to_user_id": "other-user-uuid",
      "amount": "0.10000000",
      "transaction_type": "attribution",
      "attribution_id": "attr-uuid-1",
      "description": "CITATION: Referenced their card",
      "from_user_balance_after": "25.50000000",
      "created_at": "2025-11-18T10:25:00Z"
    }
  ]
}
```

**Transaction Types:**
- `earn`: System award (publish card)
- `transfer`: User-to-user transfer
- `attribution`: Attribution reward (citation, remix, reply)

**Use Case:** Full audit trail for accounting and transparency.

### Transfer Tokens (User to User)

**Endpoint:** `POST /tokens/transfer`

**Request:**
```bash
curl -X POST https://api.extrophi.ai/tokens/transfer \
  -H "Authorization: Bearer ext_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
    "amount": "5.00000000",
    "reason": "Payment for consulting",
    "metadata": {
      "invoice_id": "INV-001",
      "service": "content strategy consultation"
    }
  }'
```

**Response:**
```json
{
  "transaction_id": "tx-uuid-3",
  "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
  "amount": "5.00000000",
  "from_balance": "20.50000000",
  "to_balance": "105.00000000",
  "reason": "Payment for consulting"
}
```

**Error Cases:**
- `400`: Insufficient balance
- `400`: Cannot transfer to yourself
- `404`: User not found

---

## API Key Management

Manage multiple API keys for different environments or apps.

### List Your API Keys

**Endpoint:** `GET /api-keys`

**Request:**
```bash
curl https://api.extrophi.ai/api-keys \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "keys": [
    {
      "key_id": "key-uuid-1",
      "key_prefix": "ext_1234...",
      "name": "Production API Key",
      "created_at": "2025-11-01T00:00:00Z",
      "last_used_at": "2025-11-18T10:30:00Z",
      "expires_at": null
    },
    {
      "key_id": "key-uuid-2",
      "key_prefix": "ext_5678...",
      "name": "Development API Key",
      "created_at": "2025-11-15T00:00:00Z",
      "last_used_at": null,
      "expires_at": "2025-12-15T00:00:00Z"
    }
  ]
}
```

**Note:** Full keys are never returned (security). Only key prefix shown.

### Create New API Key

**Endpoint:** `POST /api-keys`

**Request:**
```bash
curl -X POST https://api.extrophi.ai/api-keys \
  -H "Authorization: Bearer ext_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App API Key",
    "expires_at": "2026-11-18T00:00:00Z"
  }'
```

**Response:**
```json
{
  "key_id": "key-uuid-3",
  "api_key": "ext_abcdef1234567890",
  "name": "Mobile App API Key",
  "created_at": "2025-11-18T10:30:00Z",
  "expires_at": "2026-11-18T00:00:00Z"
}
```

**⚠️ IMPORTANT:** Save `api_key` immediately—it won't be shown again.

### Revoke API Key

**Endpoint:** `DELETE /api-keys/{key_id}`

**Request:**
```bash
curl -X DELETE https://api.extrophi.ai/api-keys/key-uuid-3 \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

**Response:**
```json
{
  "message": "API key revoked successfully",
  "key_id": "key-uuid-3"
}
```

**Use Case:** Revoke compromised keys or rotate keys for security.

---

## SDKs & Libraries

### Official SDKs

**JavaScript/TypeScript:**
```bash
npm install @extrophi/sdk
```

**Python:**
```bash
pip install extrophi
```

**Ruby:**
```bash
gem install extrophi
```

### JavaScript SDK Example

```javascript
import { ExTrophi } from '@extrophi/sdk';

const client = new Extrophi({
  apiKey: 'ext_1234567890abcdef',
});

// Publish a card
const result = await client.cards.publish({
  title: 'My Card',
  body: 'Content here...',
  category: 'BUSINESS',
  privacy_level: 'BUSINESS',
  tags: ['business', 'strategy'],
});

console.log('Published:', result.published_urls[0]);
console.log('Earned:', result.extropy_earned, '$EXTROPY');

// Create attribution
await client.attributions.create({
  source_card_id: 'source-uuid',
  target_card_id: 'target-uuid',
  attribution_type: 'citation',
  context: 'Referenced in my post...',
});

// Get token balance
const balance = await client.tokens.getBalance('user-uuid');
console.log('Balance:', balance.balance, '$EXTROPY');
```

### Python SDK Example

```python
from extrophi import ExTrophi

client = Extrophi(api_key='ext_1234567890abcdef')

# Publish a card
result = client.cards.publish(
    title='My Card',
    body='Content here...',
    category='BUSINESS',
    privacy_level='BUSINESS',
    tags=['business', 'strategy'],
)

print(f"Published: {result['published_urls'][0]}")
print(f"Earned: {result['extropy_earned']} $EXTROPY")

# Create attribution
client.attributions.create(
    source_card_id='source-uuid',
    target_card_id='target-uuid',
    attribution_type='citation',
    context='Referenced in my post...',
)

# Get token balance
balance = client.tokens.get_balance('user-uuid')
print(f"Balance: {balance['balance']} $EXTROPY")
```

### Ruby SDK Example

```ruby
require 'extrophi'

client = Extrophi::Client.new(api_key: 'ext_1234567890abcdef')

# Publish a card
result = client.cards.publish(
  title: 'My Card',
  body: 'Content here...',
  category: 'BUSINESS',
  privacy_level: 'BUSINESS',
  tags: ['business', 'strategy']
)

puts "Published: #{result[:published_urls][0]}"
puts "Earned: #{result[:extropy_earned]} $EXTROPY"

# Create attribution
client.attributions.create(
  source_card_id: 'source-uuid',
  target_card_id: 'target-uuid',
  attribution_type: 'citation',
  context: 'Referenced in my post...'
)

# Get token balance
balance = client.tokens.get_balance('user-uuid')
puts "Balance: #{balance[:balance]} $EXTROPY"
```

---

## Rate Limits

### Tiers

| Tier | Requests/Hour | Cost |
|------|---------------|------|
| Free | 1,000 | $0 |
| Pro | 10,000 | $20/mo |
| Enterprise | Unlimited | Custom |

### Rate Limit Headers

Every API response includes rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1638360000
```

**Check your limits:**
```bash
curl -I https://api.extrophi.ai/health \
  -H "Authorization: Bearer ext_1234567890abcdef"
```

### Handling Rate Limits

**HTTP 429: Too Many Requests**

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600,
  "limit": 1000,
  "window": "hour"
}
```

**Retry Logic:**
```javascript
async function callAPIWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers['Retry-After'] || 60;
        await sleep(retryAfter * 1000);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Fix request parameters |
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 429 | Rate Limit | Retry after wait |
| 500 | Server Error | Retry or contact support |

### Error Response Format

**Standard Error:**
```json
{
  "error": "Invalid card data",
  "detail": "Privacy level must be BUSINESS or IDEAS for publishing",
  "field": "privacy_level",
  "code": "INVALID_PRIVACY_LEVEL"
}
```

**Validation Error:**
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "title",
      "message": "Title is required"
    },
    {
      "field": "body",
      "message": "Body must be at least 10 characters"
    }
  ]
}
```

### Error Handling Best Practices

**JavaScript:**
```javascript
try {
  const result = await client.cards.publish({...});
} catch (error) {
  if (error.status === 401) {
    // Invalid API key
    console.error('Authentication failed. Check your API key.');
  } else if (error.status === 400) {
    // Bad request
    console.error('Invalid request:', error.detail);
  } else if (error.status === 429) {
    // Rate limit
    const retryAfter = error.headers['Retry-After'];
    console.error(`Rate limited. Retry after ${retryAfter} seconds.`);
  } else {
    // Unknown error
    console.error('Unexpected error:', error);
  }
}
```

**Python:**
```python
from extrophi import ExTrophi, ExTrophiError

client = Extrophi(api_key='...')

try:
    result = client.cards.publish(...)
except ExTrophiError as e:
    if e.status_code == 401:
        print('Authentication failed. Check your API key.')
    elif e.status_code == 400:
        print(f'Invalid request: {e.detail}')
    elif e.status_code == 429:
        retry_after = e.headers.get('Retry-After', 60)
        print(f'Rate limited. Retry after {retry_after} seconds.')
    else:
        print(f'Unexpected error: {e}')
```

---

## Code Examples

### Publishing from GitHub Actions

Automatically publish cards when you push to GitHub:

**`.github/workflows/publish-cards.yml`:**
```yaml
name: Publish Cards

on:
  push:
    branches: [main]
    paths:
      - 'cards/*.md'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Extrophi SDK
        run: npm install @extrophi/sdk

      - name: Publish Cards
        env:
          EXTROPHI_API_KEY: ${{ secrets.EXTROPHI_API_KEY }}
        run: node publish.js
```

**`publish.js`:**
```javascript
import { Extrophi } from '@extrophi/sdk';
import fs from 'fs';
import path from 'path';

const client = new Extrophi({
  apiKey: process.env.EXTROPHI_API_KEY,
});

const cardsDir = './cards';
const files = fs.readdirSync(cardsDir).filter(f => f.endsWith('.md'));

for (const file of files) {
  const content = fs.readFileSync(path.join(cardsDir, file), 'utf-8');
  const [title, ...bodyLines] = content.split('\n');

  const result = await client.cards.publish({
    title: title.replace(/^#\s*/, ''),
    body: bodyLines.join('\n'),
    category: 'BUSINESS',
    privacy_level: 'BUSINESS',
    tags: ['auto-published', 'github'],
  });

  console.log(`✅ Published: ${result.published_urls[0]}`);
  console.log(`💰 Earned: ${result.extropy_earned} $EXTROPY`);
}
```

### Webhook Integration

Receive webhooks when someone attributes your cards:

**Webhook Endpoint:**
```javascript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json());

// Verify webhook signature
function verifySignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(payload).digest('hex');
  return signature === digest;
}

app.post('/webhooks/extrophi', (req, res) => {
  const signature = req.headers['x-extrophi-signature'];
  const payload = JSON.stringify(req.body);

  if (!verifySignature(payload, signature, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }

  const { event, data } = req.body;

  if (event === 'attribution.created') {
    console.log(`🎉 Your card was cited!`);
    console.log(`Card: ${data.source_card_title}`);
    console.log(`By: ${data.attributed_by_username}`);
    console.log(`Earned: ${data.extropy_transferred} $EXTROPY`);

    // Send notification email, Slack message, etc.
  }

  res.status(200).send('OK');
});

app.listen(3000);
```

### Automated Attribution Script

Automatically cite sources when you publish:

```python
from extrophi import Extrophi
import re

client = Extrophi(api_key='ext_1234567890abcdef')

def extract_citations(text):
    """Extract Extrophi card URLs from markdown text."""
    pattern = r'https://extrophi\.ai/cards/([\w-]+)'
    return re.findall(pattern, text)

def publish_with_citations(title, body, user_id):
    """Publish card and auto-create citations."""

    # Publish card
    result = client.cards.publish(
        title=title,
        body=body,
        category='BUSINESS',
        privacy_level='BUSINESS',
    )

    target_card_id = result['content_id']

    # Extract cited cards
    cited_card_slugs = extract_citations(body)

    # Create attributions for all citations
    for slug in cited_card_slugs:
        source_card = client.cards.get_by_slug(slug)

        client.attributions.create(
            source_card_id=source_card['id'],
            target_card_id=target_card_id,
            attribution_type='citation',
            user_id=user_id,
            context=f'Referenced in: {title}',
        )

        print(f"✅ Attributed: {source_card['title']}")

    return result

# Usage
publish_with_citations(
    title='My Analysis',
    body='Building on this idea: https://extrophi.ai/cards/original-card-xyz...',
    user_id='user-uuid',
)
```

---

## API Documentation (Interactive)

**Swagger UI:** `https://api.extrophi.ai/docs`

**ReDoc:** `https://api.extrophi.ai/redoc`

**OpenAPI Spec:** `https://api.extrophi.ai/openapi.json`

---

## Support

**Questions?**
- GitHub Issues: [github.com/extrophi/extrophi-ecosystem/issues](https://github.com/extrophi/extrophi-ecosystem/issues)
- Email: support@extrophi.ai
- Discord: [discord.gg/extrophi](https://discord.gg/extrophi)

**Found a bug?** Please report with:
- API endpoint
- Request payload
- Response (including headers)
- Expected behavior

---

## Resources

- **Quickstart**: [./quickstart.md](./quickstart.md) - 5-minute setup guide
- **Writer Guide**: [./writer-guide.md](./writer-guide.md) - Voice journaling workflow
- **Research Guide**: [./research-guide.md](./research-guide.md) - Content intelligence
- **GitHub**: [github.com/extrophi/extrophi-ecosystem](https://github.com/extrophi/extrophi-ecosystem)

---

**Built for developers who build in public.**

🔑 Authenticate → 📝 Publish → 🔗 Attribute → 💰 Earn
