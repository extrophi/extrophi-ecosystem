# CCW START - Copy This Into Claude Code Web

**Repository**: https://github.com/Iamcodio/IAC-032-unified-scraper

---

## Your Mission

You are the research coordinator for IAC-032 Unified Scraper. Execute **7 parallel Plan agents** to complete Day 1 research foundation in 4 hours.

---

## Instructions

1. **Clone/connect to repo**: `Iamcodio/IAC-032-unified-scraper`
2. **Read context files**:
   - `CLAUDE.md` - Complete project overview
   - `ORCHESTRATION.md` - Execution guardrails
   - `docs/pm/CCW_ENHANCED_RESEARCH.md` - Full agent prompts
3. **Spawn 7 Plan agents in parallel** using prompts from `CCW_ENHANCED_RESEARCH.md`:
   - Agent 1: ScraperAPI docs (Issue #1)
   - Agent 2: Bright Data docs (Issue #2)
   - Agent 3: Apify docs (Issue #3)
   - Agent 4: Jina.ai docs (Issue #6)
   - Agent 5: DataForSEO docs (Issue #9)
   - Agent 6: SuperX.so analysis (Issue #7)
   - Agent 7: TweetHunter.io analysis (Issue #8)
4. **After agents complete**: Spawn synthesis agent (Issue #4) to create master decision document
5. **Commit all results** with proper format from `ORCHESTRATION.md`
6. **Close issues** #1-9 when complete

---

## Expected Outputs

**After 4 hours you will have:**
- `docs/dev/scraperapi/*.md` (10+ files)
- `docs/dev/brightdata/*.md` (8+ files)
- `docs/dev/apify/*.md` (8+ files)
- `docs/dev/jina/*.md` (5+ files)
- `docs/dev/dataforseo/*.md` (6+ files)
- `docs/research/SUPERX_ANALYSIS.md`
- `docs/research/TWEETHUNTER_ANALYSIS.md`
- `docs/pm/MASTER_RESEARCH_SYNTHESIS.md`

**This becomes the foundation for Day 2-3 implementation.**

---

## Guardrails

✅ Use ONLY `tools/doc-scraper/scrape_docs.py` for documentation scraping
✅ Follow commit format from `ORCHESTRATION.md`
✅ Close issues when complete
❌ DO NOT modify core scraper logic
❌ DO NOT install new dependencies
❌ DO NOT go off-scope

---

**START NOW. FAST CYCLES. PUSH EARLY, PUSH OFTEN.**
