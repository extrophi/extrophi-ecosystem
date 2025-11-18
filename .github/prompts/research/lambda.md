## Agent: LAMBDA (Research Module)
**Duration:** 2 hours
**Branch:** `research`
**Dependencies:** KAPPA #38

### Task
Implement embedding generation using OpenAI ada-002

### Technical Reference
- `/docs/pm/research/TECHNICAL-PROPOSAL-RESEARCH.md`
- OpenAI Embeddings API

### Deliverables
- `research/backend/embeddings/generator.py`
- OpenAI API integration
- Batch processing (max 2048 tokens per request)
- PostgreSQL vector storage (pgvector)
- Caching layer (avoid re-embedding)

### Features
1. **Text chunking** (split long content into 512-token chunks)
2. **Batch requests** (up to 100 chunks per API call)
3. **Vector storage** (pgvector column in PostgreSQL)
4. **Cache hits** (check if content already embedded)
5. **Cost tracking** (log tokens used)

### Implementation
```python
from openai import OpenAI
import numpy as np

class EmbeddingGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-ada-002"

    async def generate(self, text: str) -> list[float]:
        """Generate embedding for text"""
        response = await self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    async def batch_generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        # Chunk into batches of 100
        # Return list of embeddings
        pass
```

### Database Integration
```sql
-- Store embeddings in pgvector column
UPDATE contents
SET embedding = %s::vector(1536)
WHERE id = %s;

-- Similarity search
SELECT id, content, 1 - (embedding <=> query_embedding::vector) AS similarity
FROM contents
WHERE 1 - (embedding <=> query_embedding::vector) > 0.8
ORDER BY similarity DESC
LIMIT 10;
```

### Success Criteria
✅ OpenAI API integration works
✅ Batch processing (100 texts)
✅ Pgvector storage functional
✅ Cache prevents re-embedding
✅ Cost tracking logs tokens
✅ Tests pass

### Commit Message
```
feat(research): Add embedding generation with OpenAI ada-002

Implements vector embedding pipeline:
- Text chunking (512 tokens)
- Batch processing (100 chunks/request)
- Pgvector storage
- Cache layer (avoid duplicates)
- Cost tracking

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #53 when complete.**
