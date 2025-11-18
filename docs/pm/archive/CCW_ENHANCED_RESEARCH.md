# CCW Enhanced Research Prompt - All Platforms + Competitors

**COMPREHENSIVE research sprint covering scraping platforms AND competitor intelligence.**

---

## Mission Overview

Execute **7 parallel research streams** to build complete intelligence for IAC-032:

### Scraping Platforms (Choose Best Tool)
1. **ScraperAPI** (Issue #1) - Current leader, $49/mo
2. **Bright Data** (Issue #2) - Enterprise, $499/mo minimum
3. **Apify** (Issue #3) - Actor marketplace, variable pricing
4. **Jina.ai** (Issue #6) - **FREE tier**, 10M tokens/mo
5. **DataForSEO** (Issue #9) - SERP specialist, $0.0006/result

### Competitor Products (Reverse Engineer Features)
6. **SuperX.so** (Issue #7) - Chrome extension, Algorithm Simulator, $29/mo
7. **TweetHunter.io** (Issue #8) - 3M viral tweets, AI21 model, $49-99/mo

**Timeline**: 3-4 hours parallel execution
**Output**: Platform recommendation + feature roadmap from competitor analysis

---

## Research Stream Assignments

### Stream 1-5: Scraping Platform Documentation

Use existing CCW_RESEARCH_PROMPT.md for ScraperAPI, Bright Data, Apify (Issues #1-3).

#### ADDITIONAL: Jina.ai (Issue #6)

**Agent Prompt**:
```
OBJECTIVE: Research Jina.ai Reader API as FREE alternative to ScraperAPI.

TARGET: https://jina.ai/reader / https://docs.jina.ai/

KEY FOCUS:
- Free tier: 10M tokens, 200 RPM (massive for MVP)
- Simple content extraction (no anti-bot, no JS rendering)
- API simplicity vs ScraperAPI
- Use cases: blogs, documentation, simple pages
- Limitations: Can it handle Twitter/Amazon/dynamic content?

METHOD:
1. Scrape docs.jina.ai using doc-scraper tool
2. Test API with curl: `curl https://r.jina.ai/https://example.com`
3. Document response format, token counting, rate limits

OUTPUT: docs/dev/jina/*.md (5+ files)

COMPARISON ANGLE:
- When to use Jina (free, simple pages) vs ScraperAPI (paid, complex sites)
- Cost savings: 10M tokens free vs $49 ScraperAPI

SUCCESS: Clear recommendation on Jina for simple scraping, ScraperAPI for complex.

ESTIMATED TIME: 30 minutes
```

#### ADDITIONAL: DataForSEO (Issue #9)

**Agent Prompt**:
```
OBJECTIVE: Research DataForSEO SERP API for SEO intelligence use case.

TARGET: https://docs.dataforseo.com/

KEY FOCUS:
- SERP API: $0.0006/result (cheapest SERP data available)
- Google, Bing, YouTube SERP results
- Keyword research APIs
- Competitor SERP analysis
- 83,333 SERP pages for $50 (compare to ScraperAPI)

METHOD:
1. Scrape docs.dataforseo.com using doc-scraper
2. Focus on SERP API endpoints, pricing, data structure
3. Compare to scraping Google directly with ScraperAPI

OUTPUT: docs/dev/dataforseo/*.md (6+ files)

COMPARISON ANGLE:
- Specialized SERP vs general scraping
- Cost: $0.0006/SERP vs $0.00049/page ScraperAPI
- Data quality: Structured SERP data vs HTML parsing

SUCCESS: Decision on using DataForSEO for SERP + ScraperAPI for general scraping.

ESTIMATED TIME: 30-45 minutes
```

---

### Stream 6-7: Competitor Product Analysis

#### SuperX.so Analysis (Issue #7)

**Agent Prompt**:
```
OBJECTIVE: Reverse-engineer SuperX.so features as Twitter intelligence competitor.

TARGET: https://superx.so/ (marketing site + free trial if available)

METHOD:
1. Analyze public marketing pages
2. Screenshot key features (save to docs/research/superx_screenshots/)
3. Document feature list from sales copy
4. Sign up for free trial if available (use temp email)
5. Test Algorithm Simulator, on-page analytics, semantic search

KEY FEATURES TO DOCUMENT:
- Chrome extension approach (on-page vs separate platform)
- Algorithm Simulator: Predicts X algorithm treatment
- On-page analytics without leaving Twitter
- AI Shield (hides AI-generated replies)
- Semantic search with fresh filters (current week)
- Conversational AI chat learning user tone
- Pricing: $29/mo entry vs TweetHunter $49

ANALYSIS QUESTIONS:
1. Why Chrome extension vs web app? (Pros/cons for us)
2. Algorithm Simulator: How does it work? Can we replicate?
3. What data do they NOT have that we could provide?
4. Integration with our multi-platform approach?

OUTPUT: docs/research/SUPERX_ANALYSIS.md

FORMAT:
```markdown
# SuperX.so Competitive Analysis

## Product Overview
[Description, target audience, positioning]

## Feature Breakdown
| Feature | Description | Replicable? | Difficulty | Priority |
|---------|-------------|-------------|------------|----------|
| Algorithm Simulator | Predicts post performance | ? | High | High |
| ... | ... | ... | ... | ... |

## Architecture: Chrome Extension Approach
### Advantages
- No API costs (piggybacks on user session)
- On-page integration
- Bypasses rate limits

### Disadvantages
- Browser-only (no automation)
- Breaks when Twitter updates UI
- Limited to one platform

## Pricing Strategy
$29/mo entry point (vs TweetHunter $49, our target: $39?)

## Competitive Gaps (What They Don't Have)
1. Multi-platform (they're Twitter-only)
2. Course script generation
3. Cross-platform pattern detection
4. RAG semantic search across platforms

## Recommendations for IAC-032
[What to copy, what to improve, what to skip]
```

ESTIMATED TIME: 1 hour
```

#### TweetHunter.io Analysis (Issue #8)

**Agent Prompt**:
```
OBJECTIVE: Deep analysis of TweetHunter.io as PRIMARY competitor.

TARGET: https://tweethunter.io/ + https://app.tweethunter.io/ (free trial)

METHOD:
1. Analyze marketing site feature claims
2. Sign up for free trial (use iamcodio37+tweethunter@gmail.com)
3. Test key features: Viral Library, AI Writer, TweetPredict, CRM
4. Screenshot UI patterns
5. Document AI model capabilities (AI21 Labs partnership)

KEY FEATURES TO DOCUMENT:
- Viral tweet library: 3M+ tweets, 4K+ curated, 10 categories
- AI21 Labs custom language model (competitive moat)
- TweetPredict™ engagement forecasting
- CRM with lead finder
- Automation: Auto DM, Auto Plug, Auto Retweet, Clean Profile
- Scheduling with queue management
- Pricing: $49 Discover (AI+Library), $99 Grow (CRM+Automation)

DEEP DIVE QUESTIONS:
1. Viral Library: How is it categorized? What metadata?
2. AI Model: Can we match with GPT-4 + good prompting? (80% of value?)
3. TweetPredict: What signals does it use? (length, media, time, hashtags?)
4. CRM: How sophisticated? (Just contact mgmt or advanced segmentation?)
5. What's missing that Dan Koe needs? (Our research shows he wants pattern detection across YouTube/newsletter/Twitter)

REPLICABILITY ASSESSMENT:
| Feature | Easy | Medium | Hard | Defensible Moat? |
|---------|------|--------|------|------------------|
| Viral Library | ✅ | | | No (just data collection) |
| AI Writer | ✅ | | | No (GPT-4 = 80% of value) |
| TweetPredict | | ✅ | | Medium (ML training) |
| Custom AI21 Model | | | ✅ | Yes (partnership + training data) |
| CRM | ✅ | | | No (standard features) |

OUTPUT: docs/research/TWEETHUNTER_ANALYSIS.md

FORMAT:
```markdown
# TweetHunter.io Competitive Analysis

## Product Overview
[Market position, pricing, target audience]

## Feature Matrix
[Detailed table with replicability assessment]

## Revenue Model
$49-99/mo subscription, no usage limits

## Technical Architecture (Inferred)
- Backend: Likely Python/Node scraping + database
- AI: AI21 Labs Jurassic-2 custom fine-tuned model
- Frontend: React/Next.js web app
- Data: 3M+ scraped tweets, continuous ingestion

## Competitive Advantages (Defensible)
1. AI21 Labs partnership (custom model pricing)
2. Years of tweet performance data
3. Network effects (4K curated library)

## Competitive Disadvantages (Attack Surface)
1. Twitter-only (we're multi-platform)
2. No course creation (we generate scripts)
3. No pattern detection across platforms
4. No semantic search (keyword-based library)
5. No Dan Koe-style elaboration tracking

## Our Differentiation Strategy
### What to Copy (Table Stakes)
- Viral library (but multi-platform: Twitter+YouTube+Reddit)
- AI writing assistance (GPT-4 = 80% of their value)
- Engagement prediction (simpler ML model)

### What to Do BETTER
- Multi-platform intelligence (Twitter+YouTube+newsletter pattern detection)
- Course script generation (they don't have this)
- RAG semantic search (vs their keyword categories)
- Authority ranking across platforms
- Content gap analysis

### What to SKIP (Not Worth It)
- Custom AI model training (use GPT-4, good enough)
- Complex CRM (focus on research, not lead management)
- Heavy automation features (focus on intelligence)

## Pricing Positioning
TweetHunter: $49-99/mo (Twitter-only, AI+automation)
IAC-032: $39-69/mo (Multi-platform, intelligence+generation)

Value prop: "TweetHunter for your tweets. We're the intelligence layer for your entire content ecosystem."
```

ESTIMATED TIME: 1-2 hours (most critical analysis)
```

---

## Synthesis: Master Decision Matrix (After All Research)

**Deploy FINAL synthesis agent after streams 1-7 complete.**

**Prompt**:
```
OBJECTIVE: Create master decision document from ALL research.

INPUT FILES:
- docs/dev/scraperapi/*.md
- docs/dev/brightdata/*.md
- docs/dev/apify/*.md
- docs/dev/jina/*.md
- docs/dev/dataforseo/*.md
- docs/research/SUPERX_ANALYSIS.md
- docs/research/TWEETHUNTER_ANALYSIS.md

OUTPUT: docs/pm/MASTER_RESEARCH_SYNTHESIS.md

STRUCTURE:

# Master Research Synthesis - Day 1 Complete

## Part 1: Scraping Platform Decision

### Platform Comparison Matrix
[ScraperAPI vs Bright Data vs Apify vs Jina.ai vs DataForSEO]

### Recommendation: Hybrid Approach
- **Primary**: ScraperAPI ($49/mo) for complex scraping (Twitter, Amazon, dynamic sites)
- **Secondary**: Jina.ai (FREE) for simple content (blogs, docs, static pages)
- **Specialized**: DataForSEO ($0.0006/result) for SERP intelligence
- **Backup**: IAC-024 Playwright patterns for Twitter (already proven)

### Cost Projection
| Scenario | ScraperAPI | Jina.ai | DataForSEO | Total |
|----------|-----------|---------|------------|-------|
| MVP (Light usage) | $0 (free tier) | $0 | $0 | $0 |
| Production (100K scrapes) | $49 | $0 | $5 (SERP) | $54/mo |
| Scale (500K scrapes) | $149 | $0 | $20 (SERP) | $169/mo |

## Part 2: Competitive Intelligence

### Feature Gaps We Can Exploit
1. **Multi-platform** - TweetHunter/SuperX are Twitter-only
2. **Pattern detection** - Nobody tracks tweet→newsletter→video elaboration
3. **Course generation** - Unique capability
4. **RAG semantic search** - vs keyword-based libraries
5. **Authority ranking** - Cross-platform influence scoring

### Features We MUST Match (Table Stakes)
1. Viral content library (but multi-platform)
2. AI writing assistance (GPT-4 sufficient)
3. Engagement prediction (simple ML)
4. Clean UI (learn from SuperX's Chrome extension UX)

### Features to SKIP (Not Worth Effort)
1. Custom AI model training (TweetHunter's moat, not worth fighting)
2. Heavy CRM (not our focus)
3. Chrome extension (limits to browser, we want automation)

## Part 3: Product Positioning

### Market Positioning
**TweetHunter**: "Twitter growth tool for creators"
**SuperX**: "Twitter analytics Chrome extension"
**IAC-032**: "Multi-platform content intelligence engine for systematic creators"

### Pricing Strategy
- Entry: $39/mo (undercut TweetHunter $49)
- Pro: $69/mo (multi-platform + course generation)
- Enterprise: $149/mo (API access + custom analysis)

### Target Audience
- Content creators like Dan Koe (multi-platform strategy)
- Copywriters researching markets (RMBC framework users)
- Course creators (script generation unique value)
- Marketing agencies (client research automation)

## Part 4: Implementation Priorities

### Week 1 (MVP - Current Sprint)
1. ✅ ScraperAPI integration (primary)
2. ✅ Jina.ai integration (free tier)
3. ✅ Twitter scraper (IAC-024 reuse)
4. YouTube + Reddit scrapers
5. Basic RAG search
6. Simple course script generation

### Week 2 (Post-MVP)
1. DataForSEO SERP integration
2. Pattern detection algorithm
3. Tauri desktop UI (learn from SuperX UX patterns)
4. Engagement prediction (simple model)
5. Authority ranking

### Month 2 (Scale)
1. Viral library (multi-platform curated content)
2. Advanced pattern detection (cross-platform elaboration)
3. Content gap analysis
4. Export templates (Astro, markdown, tweets)

## Part 5: Technical Decisions

### Architecture Confirmed
- Backend: FastAPI + PostgreSQL + pgvector + ChromaDB
- Scraping: ScraperAPI (complex) + Jina.ai (simple) + Playwright (Twitter backup)
- LLM: OpenAI GPT-4 (bulk) + Claude Sonnet 4.5 (polish)
- Frontend: Tauri + Svelte (Week 2)

### Database Schema
[Unified content schema from CLAUDE.md]

### API Design
[Endpoint specifications]

---

**This synthesis becomes the foundation for Day 2-3 implementation.**
```

ESTIMATED TIME: 2 hours (critical document)
```

---

## Execution Instructions for CCW

### Parallel Execution (Maximize Speed)

**Launch simultaneously:**
- Agents 1-5: Platform documentation (ScraperAPI, Bright Data, Apify, Jina, DataForSEO)
- Agents 6-7: Competitor analysis (SuperX, TweetHunter)

**Total agents**: 7 running in parallel

**Timeline**:
- Agents 1-5: 30-60 min each → 1 hour elapsed (parallel)
- Agents 6-7: 1-2 hours each → 2 hours elapsed (parallel)
- **Total parallel execution: ~2 hours**
- Final synthesis: 2 hours
- **GRAND TOTAL: 4 hours to complete Day 1 research**

### Success Criteria

- [ ] docs/dev/scraperapi/ (10+ files)
- [ ] docs/dev/brightdata/ (8+ files)
- [ ] docs/dev/apify/ (8+ files)
- [ ] docs/dev/jina/ (5+ files)
- [ ] docs/dev/dataforseo/ (6+ files)
- [ ] docs/research/SUPERX_ANALYSIS.md (competitor features)
- [ ] docs/research/TWEETHUNTER_ANALYSIS.md (competitor features)
- [ ] docs/pm/MASTER_RESEARCH_SYNTHESIS.md (final decision doc)
- [ ] CLAUDE.md updated with findings
- [ ] Issues #1-9 closed

---

## GitHub Issues Summary

| # | Platform | Type | Time | Priority |
|---|----------|------|------|----------|
| #1 | ScraperAPI | Scraping | 60min | High |
| #2 | Bright Data | Scraping | 60min | High |
| #3 | Apify | Scraping | 60min | High |
| #6 | Jina.ai | Scraping | 30min | Medium |
| #9 | DataForSEO | Scraping | 45min | Medium |
| #7 | SuperX.so | Competitor | 60min | High |
| #8 | TweetHunter | Competitor | 120min | Critical |
| #4 | Synthesis | Analysis | 120min | Critical |

**Critical path**: #8 (TweetHunter) - most important competitor analysis

---

*Copy this entire file into CCW and execute 7 parallel agents. Complete research foundation in 4 hours.*
