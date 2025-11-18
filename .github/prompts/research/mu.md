## Agent: MU (Research Module)
**Duration:** 3 hours
**Branch:** `research`
**Dependencies:** THETA #37, LAMBDA #53, IOTA #39

### Task
Build enrichment engine that integrates scrapers + embeddings + LLM analysis

### Technical Reference
- `/docs/pm/research/TECHNICAL-PROPOSAL-RESEARCH.md`

### Deliverables
- `research/backend/enrichment/engine.py`
- RAG pipeline (retrieval + generation)
- LLM analysis (GPT-4)
- Suggestion generation
- Source attribution

### Workflow
```python
# Input: Card content from Writer
POST /api/enrich
{
  "content": "How to build focus systems...",
  "context": "knowledge_work"
}

# Process:
1. Generate embedding (LAMBDA)
2. Vector similarity search (retrieve related content)
3. Scrape additional sources (IOTA scrapers)
4. LLM analysis (GPT-4) - extract frameworks, hooks, patterns
5. Generate suggestions

# Output:
{
  "suggestions": [
    "Consider Dan Koe's 2-hour focus blocks",
    "Cal Newport's Deep Work principles apply here",
    "Reference: Reddit r/productivity top posts"
  ],
  "sources": [
    {"url": "twitter.com/dankoe/...", "relevance": 0.92},
    {"url": "youtube.com/watch?v=...", "relevance": 0.88}
  ],
  "frameworks": ["Deep Work", "Pomodoro", "Time Blocking"]
}
```

### Implementation
```python
class EnrichmentEngine:
    def __init__(self, embeddings, scrapers, llm):
        self.embeddings = embeddings
        self.scrapers = scrapers
        self.llm = llm

    async def enrich(self, content: str, context: str) -> dict:
        # 1. Generate embedding
        embedding = await self.embeddings.generate(content)

        # 2. Vector search (find similar content)
        similar = await self.vector_search(embedding, limit=10)

        # 3. Scrape fresh sources (if needed)
        fresh_sources = await self.scrape_related(context)

        # 4. LLM analysis
        analysis = await self.llm.analyze(content, similar, fresh_sources)

        # 5. Generate suggestions
        suggestions = await self.llm.suggest(content, analysis)

        return {
            "suggestions": suggestions,
            "sources": similar + fresh_sources,
            "frameworks": analysis["frameworks"]
        }
```

### Integration Points
- **From Writer**: `POST /api/enrich` receives card content
- **Uses LAMBDA**: Embedding generation
- **Uses IOTA**: Platform scrapers
- **Uses KAPPA**: PostgreSQL + pgvector storage

### Success Criteria
✅ RAG pipeline works (retrieval + generation)
✅ Embedding search returns relevant content
✅ Scrapers fetch fresh sources
✅ LLM generates useful suggestions
✅ Source attribution included
✅ Tests pass (mock LLM responses)

### Commit Message
```
feat(research): Add enrichment engine with RAG pipeline

Implements content intelligence:
- Vector similarity search (pgvector)
- Multi-platform scraping (Twitter, YouTube, Reddit)
- LLM analysis (GPT-4) - frameworks, patterns
- Suggestion generation
- Source attribution

Integrates LAMBDA (embeddings) + IOTA (scrapers).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #54 when complete.**
