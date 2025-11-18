# Enrichment Engine

**Agent:** MU
**Wave:** 2
**Dependencies:** THETA (#37), LAMBDA (#53), IOTA (#39)

## Overview

The Enrichment Engine provides intelligent content enrichment through a **RAG (Retrieval-Augmented Generation) pipeline**. It integrates vector similarity search, multi-platform scraping, and LLM analysis to generate contextual suggestions for user content.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Enrichment Engine (MU)                       │
│                                                                   │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  LAMBDA    │  │    THETA     │  │     IOTA     │            │
│  │ Embeddings │  │ Vector Search│  │   Scrapers   │            │
│  └─────┬──────┘  └──────┬───────┘  └──────┬───────┘            │
│        │                 │                  │                    │
│        └─────────────────┼──────────────────┘                    │
│                          │                                       │
│                  ┌───────▼────────┐                              │
│                  │  LLM Analyzer  │                              │
│                  │    (GPT-4)     │                              │
│                  └───────┬────────┘                              │
│                          │                                       │
│                  ┌───────▼────────┐                              │
│                  │  Suggestions   │                              │
│                  └────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow

1. **Generate Embedding** (LAMBDA)
   - User content → OpenAI ada-002 embedding
   - 1536-dimensional vector

2. **Vector Search** (THETA)
   - Find similar content using pgvector
   - Cosine similarity > threshold (default: 0.7)
   - Returns top 20 matches

3. **Scrape Fresh Sources** (IOTA) - _Optional_
   - Extract keywords from content
   - Scrape Twitter, YouTube, Reddit, Web
   - Currently placeholder (scrapers run async)

4. **LLM Analysis** (GPT-4)
   - Extract frameworks, patterns, hooks
   - Analyze sentiment and themes
   - Generate contextual suggestions

5. **Return Results**
   - Suggestions with confidence scores
   - Source attribution
   - Processing metadata

## Usage

### Basic Enrichment

```python
from enrichment import EnrichmentEngine
from db import get_db_manager
import os

# Initialize
db_manager = get_db_manager()
await db_manager.connect()

engine = EnrichmentEngine(
    db_manager=db_manager,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    embedding_model="text-embedding-ada-002",
    llm_model="gpt-4"
)

await engine.initialize()

# Enrich content
result = await engine.enrich(
    content="How to build better focus systems?",
    context="Previous discussion about productivity",
    max_suggestions=5,
    similarity_threshold=0.7
)

print(result["suggestions"])
# [
#   {
#     "text": "Consider 2-hour Deep Work blocks",
#     "type": "framework",
#     "confidence": 0.85,
#     "source": {...}
#   }
# ]
```

### API Endpoint

The enrichment engine is exposed via FastAPI:

```bash
POST /api/enrich
Content-Type: application/json

{
  "card_id": "card-123",
  "content": "Building a second brain system",
  "context": "Knowledge management workflow",
  "max_suggestions": 5
}
```

Response:

```json
{
  "card_id": "card-123",
  "suggestions": [
    {
      "text": "Use the PARA method for organization",
      "type": "framework",
      "confidence": 0.88,
      "source": {
        "platform": "web",
        "url": "https://fortelabs.com/blog/para/",
        "title": "The PARA Method",
        "author": "Tiago Forte",
        "relevance_score": 0.92
      }
    }
  ],
  "sources": [...],
  "processing_time_ms": 1250.5,
  "timestamp": "2025-11-18T16:30:00Z"
}
```

## Components

### EnrichmentEngine

**File:** `enrichment/engine.py`

Main orchestrator for the RAG pipeline.

**Methods:**

- `enrich(content, context, max_suggestions, similarity_threshold)` - Full enrichment pipeline
- `enrich_batch(cards, max_suggestions)` - Batch enrichment for multiple cards
- `get_related_content(content, limit, platform_filter)` - Get similar content without LLM
- `health_check()` - Check component health
- `get_stats()` - Get usage and performance stats

### LLMAnalyzer

**File:** `enrichment/llm_analyzer.py`

GPT-4 powered content analysis.

**Methods:**

- `extract_frameworks(content, similar_content)` - Extract methodologies and mental models
- `extract_patterns(content, similar_content)` - Extract hooks, themes, sentiment
- `generate_suggestions(content, similar_content, frameworks, max_suggestions)` - Generate suggestions
- `analyze_content(content, similar_content, max_suggestions)` - Full analysis pipeline
- `get_usage_stats()` - API usage and cost tracking

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
LLM_MODEL=gpt-4  # or gpt-3.5-turbo, gpt-4-turbo-preview
```

### Similarity Threshold

Controls how closely related content must be to be included:

- `0.9-1.0` - Very similar (narrow focus)
- `0.7-0.9` - Similar (recommended)
- `0.5-0.7` - Loosely related (broader context)
- `<0.5` - Not recommended (too much noise)

## Performance

### Typical Latency

- **Embedding generation:** 100-200ms
- **Vector search:** 50-100ms
- **LLM analysis:** 2-5 seconds
- **Total:** 2.5-6 seconds per enrichment

### Cost Estimation

Per enrichment (typical):

- **Embeddings (ada-002):** $0.0001
- **LLM (GPT-4):** $0.01-0.05
- **Total:** ~$0.01-0.05

Using `gpt-3.5-turbo` reduces costs by ~10x.

### Optimization Tips

1. **Cache embeddings** - Don't regenerate for same content
2. **Batch requests** - Use `enrich_batch()` for multiple cards
3. **Lower threshold** - Reduce similarity threshold to get more results from cache
4. **Use GPT-3.5** - For less critical suggestions

## Testing

Run unit tests:

```bash
cd research/backend
pytest tests/test_enrichment.py -v
```

Run integration tests (requires OpenAI API key):

```bash
pytest tests/test_enrichment.py -m integration -v
```

Test coverage:

```bash
pytest tests/test_enrichment.py --cov=enrichment --cov-report=term-missing
```

## Integration

### With Writer Module

The Writer module calls the enrichment API when users are editing cards:

```typescript
// Writer (Svelte frontend)
const enrichCard = async (cardId: string, content: string) => {
  const response = await fetch("http://localhost:8000/api/enrich", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      card_id: cardId,
      content,
      max_suggestions: 5
    })
  });

  return await response.json();
};
```

### With Backend Scrapers (IOTA)

Fresh content scraping integration (future):

```python
# Enable scraping for specific platforms
result = await engine.enrich(
    content="Latest AI developments",
    enable_scraping=True,
    scrape_platforms=["twitter", "reddit"]
)
```

## Success Criteria

✅ RAG pipeline works (retrieval + generation)
✅ Embedding search returns relevant content
✅ LLM generates useful suggestions
✅ Source attribution included
✅ Tests pass (mock LLM responses)
✅ Integration with LAMBDA + THETA + IOTA

## Future Enhancements

1. **Real-time scraping** - Integrate IOTA scrapers for fresh content
2. **Suggestion caching** - Cache suggestions for common queries
3. **Multi-language support** - Support non-English content
4. **Fine-tuned models** - Custom LLM for domain-specific suggestions
5. **User feedback loop** - Learn from accepted/rejected suggestions
6. **Streaming responses** - Stream suggestions as they're generated

## Troubleshooting

### "Enrichment engine not initialized"

```python
# Make sure to call initialize() after construction
engine = EnrichmentEngine(...)
await engine.initialize()  # Required!
```

### "No similar content found"

- Lower similarity threshold
- Check if database has content with embeddings
- Verify pgvector extension is enabled

### "OpenAI API errors"

- Check API key is valid: `OPENAI_API_KEY`
- Verify you have credits remaining
- Check rate limits (tier-based)

### "LLM returns empty suggestions"

- Content may be too short/vague
- Try providing more context
- Lower confidence threshold
- Check LLM model settings

## References

- **LAMBDA (Embeddings):** `research/backend/embeddings/`
- **THETA (Vector Search):** `research/backend/db/search.py`
- **IOTA (Scrapers):** `backend/scrapers/`
- **API Docs:** http://localhost:8000/docs

## License

Part of IAC-033 Extrophi Ecosystem. See root LICENSE.
