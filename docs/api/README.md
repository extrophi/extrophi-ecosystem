# Extrophi Ecosystem API Documentation

Welcome to the Extrophi Ecosystem API documentation. This directory contains comprehensive API documentation for all services in the Extrophi platform.

## 📚 Documentation Structure

```
docs/api/
├── README.md                  # This file
├── openapi.json              # OpenAPI 3.0 specification
├── endpoints/                # Individual endpoint documentation
│   ├── get-health.md
│   ├── post-scrape-platform.md
│   ├── post-analyze-content.md
│   ├── post-query-rag.md
│   ├── post-publish.md
│   ├── post-attributions.md
│   ├── get-attributions-card_id.md
│   ├── get-tokens-balance-user_id.md
│   ├── post-tokens-transfer.md
│   └── post-api-enrich.md
```

## 🚀 API Services

The Extrophi Ecosystem provides the following API services:

### 1. **Content Intelligence**
- **Scraping** - Multi-platform content extraction (Twitter, YouTube, Reddit, Web)
- **Analysis** - LLM-powered content analysis with framework and pattern detection
- **RAG Search** - Semantic search using vector embeddings

### 2. **$EXTROPY Token System**
- **Balances** - Query user token balances
- **Transfers** - Transfer tokens between users
- **Awards** - Automatic token rewards for publishing and attributions

### 3. **Publishing Platform**
- **Card Publishing** - Publish content with privacy controls
- **Attribution System** - Track citations, remixes, and replies with automatic rewards

### 4. **Content Enrichment**
- **AI Suggestions** - Get AI-powered content suggestions
- **Source Attribution** - Track content sources and relationships

## 🔑 Authentication

Most endpoints require API key authentication. Include your API key in the `Authorization` header:

```bash
Authorization: Bearer YOUR_API_KEY
```

## 📖 Quick Start

### 1. Health Check

```bash
curl https://api.extrophi.ai/health
```

### 2. Scrape Twitter Content

```bash
curl -X POST https://api.extrophi.ai/scrape/twitter \
  -H "Content-Type: application/json" \
  -d '{"target": "dankoe", "limit": 50}'
```

### 3. Semantic Search

```bash
curl -X POST https://api.extrophi.ai/query/rag \
  -H "Content-Type: application/json" \
  -d '{"prompt": "content creation frameworks", "n_results": 10}'
```

### 4. Publish Cards

```bash
curl -X POST https://api.extrophi.ai/publish \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "cards": [{
      "title": "How to Build Momentum",
      "body": "The key is...",
      "category": "BUSINESS",
      "privacy_level": "BUSINESS"
    }]
  }'
```

## 📊 API Categories

### Health & Status
- `GET /health` - Service health check

### Scraping
- `POST /scrape/{platform}` - Scrape content from platform
- `GET /scrape/{platform}/health` - Check scraper health

### Analysis
- `POST /analyze/content` - Analyze content with LLM
- `POST /analyze/patterns` - Detect cross-content patterns

### RAG & Search
- `POST /query/rag` - Semantic search across all content

### Publishing
- `POST /publish` - Publish cards with privacy controls

### Attributions
- `POST /attributions` - Create attribution (citation/remix/reply)
- `GET /attributions/{card_id}` - Get card attributions (backlinks)
- `GET /attributions/{card_id}/graph` - Get attribution graph
- `GET /attributions/users/{user_id}/received` - Get received attributions

### Tokens
- `GET /tokens/balance/{user_id}` - Get token balance
- `POST /tokens/transfer` - Transfer tokens
- `POST /tokens/award` - Award tokens
- `GET /tokens/ledger/{user_id}` - Get transaction history
- `GET /tokens/stats/{user_id}` - Get token statistics

### Enrichment
- `POST /api/enrich` - Enrich card content with AI suggestions

## 💰 $EXTROPY Token Rewards

The API automatically awards $EXTROPY tokens for various actions:

| Action | Reward | Description |
|--------|--------|-------------|
| **Publish Card** | 1.0 $EXTROPY | Publish a BUSINESS or IDEAS card |
| **Citation** | 0.1 $EXTROPY | Someone cites your card |
| **Remix** | 0.5 $EXTROPY | Someone remixes your card |
| **Reply** | 0.05 $EXTROPY | Someone replies to your card |

## 🔒 Privacy Levels

Cards support multiple privacy levels:

- ✅ **BUSINESS** - Publicly publishable, earns tokens
- ✅ **IDEAS** - Publicly publishable, earns tokens
- ❌ **PERSONAL** - Private, not published
- ❌ **PRIVATE** - Private, not published
- ❌ **THOUGHTS** - Private, not published
- ❌ **JOURNAL** - Private, not published

## 📝 Response Formats

All API responses use JSON format:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional message"
}
```

Error responses include:

```json
{
  "detail": "Error description",
  "type": "error_type",
  "timestamp": "2025-11-18T10:30:00Z"
}
```

## 🌐 Base URLs

- **Production:** `https://api.extrophi.ai`
- **Development:** `http://localhost:8000`

## 📚 SDKs & Libraries

### Python

```python
import requests

class ExTrophiAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.extrophi.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def scrape(self, platform: str, target: str, limit: int = 20):
        """Scrape content from platform."""
        response = requests.post(
            f"{self.base_url}/scrape/{platform}",
            json={"target": target, "limit": limit}
        )
        return response.json()

    def rag_search(self, query: str, n_results: int = 10):
        """Semantic search across content."""
        response = requests.post(
            f"{self.base_url}/query/rag",
            json={"prompt": query, "n_results": n_results}
        )
        return response.json()

    def get_balance(self, user_id: str):
        """Get user's token balance."""
        response = requests.get(
            f"{self.base_url}/tokens/balance/{user_id}",
            headers=self.headers
        )
        return response.json()
```

### JavaScript/TypeScript

```javascript
class ExTrophiAPI {
  constructor(apiKey, baseUrl = 'https://api.extrophi.ai') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  async scrape(platform, target, limit = 20) {
    const response = await fetch(`${this.baseUrl}/scrape/${platform}`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ target, limit })
    });
    return response.json();
  }

  async ragSearch(query, nResults = 10) {
    const response = await fetch(`${this.baseUrl}/query/rag`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ prompt: query, n_results: nResults })
    });
    return response.json();
  }

  async getBalance(userId) {
    const response = await fetch(`${this.baseUrl}/tokens/balance/${userId}`, {
      headers: this.headers
    });
    return response.json();
  }
}
```

## 🛠️ Development

### Running Locally

```bash
# Backend API
cd backend
uvicorn main:app --reload --port 8000

# Research Module API
cd research/backend
uvicorn main:app --reload --port 8001
```

### Generating Documentation

To regenerate this documentation:

```bash
python scripts/generate_api_docs_simple.py
```

## 📄 OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- File: `docs/api/openapi.json`
- Endpoint: `https://api.extrophi.ai/docs` (Swagger UI)
- Endpoint: `https://api.extrophi.ai/redoc` (ReDoc)

## 🤝 Support

For API support and questions:
- GitHub Issues: https://github.com/extrophi/extrophi-ecosystem/issues
- Documentation: https://docs.extrophi.ai

## 📜 License

See LICENSE file in the repository root.

---

**Last Updated:** 2025-11-18
**Version:** 1.0.0
**Generated by:** DOC-ALPHA Agent
