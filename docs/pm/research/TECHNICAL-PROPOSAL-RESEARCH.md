# TECHNICAL PROPOSAL: RESEARCH MODULE

**Budget:** ~$200  
**Timeline:** 10 hours  
**Agents:** 6 (THETA, KAPPA, LAMBDA, IOTA, MU, NU)

## AGENTS

**THETA (2 hrs):** FastAPI endpoints (`/api/enrich`, `/api/scrape`, `/health`)  
**KAPPA (2 hrs):** PostgreSQL + pgvector schema  
**LAMBDA (2 hrs):** Embedding generation (OpenAI ada-002)  
**IOTA (4 hrs):** Platform scrapers (Twitter, YouTube, Reddit, Web)  
**MU (3 hrs):** Enrichment engine - integrates all components  
**NU (1 hr):** Integration docs

## PARALLEL EXECUTION

```
THETA, KAPPA, IOTA, NU → START PARALLEL
  ↓
When KAPPA done → LAMBDA
  ↓
When ALL done → MU (integration)
```

## INTEGRATION

- From Writer: `POST /api/enrich` (receives card content)
- To Backend: Shared PostgreSQL database
- Returns: Suggestions array, sources

## RISK: Rate Limits

If scrapers hit limits → focus on web scraper, defer Twitter/YouTube
