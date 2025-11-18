# CCW Research Agent Prompt

**Copy and paste this into Claude Code Web to spawn Plan agents for parallel research execution.**

---

## Primary Objective

You are coordinating a research team for the IAC-032 Unified Scraper project. Spawn **3 parallel Plan agents** to scrape official documentation from ScraperAPI, Bright Data, and Apify, then create a comparison matrix to recommend the best platform.

**Budget**: €900 expires in 3 days
**Timeline**: Complete all research in 2-4 hours
**Output**: Clean markdown documentation for decision-making

---

## Context

Read these files first:
1. `CLAUDE.md` - Complete project context
2. `ORCHESTRATION.md` - Execution guardrails
3. `docs/pm/PRD_PROPER.md` - Requirements (source of truth)
4. `tools/doc-scraper/scrape_docs.py` - Documentation scraping tool

**Goal**: Build a multi-platform content intelligence engine that scrapes Twitter/YouTube/Reddit/Amazon, analyzes with LLM, and generates course scripts. We need to choose the best web scraping platform.

---

## Agent Assignments

### Plan Agent 1: ScraperAPI Research (Issue #1)

**Prompt**:
```
You are a research specialist for the IAC-032 Unified Scraper project.

OBJECTIVE: Scrape complete ScraperAPI.com documentation and convert to clean markdown.

TARGET: https://docs.scraperapi.com/

REQUIRED PAGES:
- Getting Started / Quick Start
- API Reference / Endpoints
- Structured Data Endpoints (Amazon, Google, eBay, Walmart)
- JavaScript Rendering (+5 credits feature)
- Premium Features (CAPTCHA solving, geotargeting, proxy rotation)
- Rate Limits & Concurrent Threads
- Pricing (Hobby: $49/mo, 100K credits)
- Error Handling & Retry Logic
- Best Practices & Examples

IMPLEMENTATION:
1. Navigate to tools/doc-scraper/
2. Edit scrape_docs.py - extend DOCS_TO_SCRAPE dictionary:
   ```python
   "scraperapi": {
       "base_url": "https://docs.scraperapi.com",
       "pages": [
           "/getting-started",
           "/api-reference",
           "/structured-data/amazon",
           "/structured-data/google",
           # ... add all relevant paths
       ]
   }
   ```
3. Run: `cd tools/doc-scraper && uv venv && source .venv/bin/activate && python scrape_docs.py`
4. Output goes to: docs/dev/scraperapi/*.md

GUARDRAILS:
✅ Use ONLY the existing scrape_docs.py tool
✅ Extend DOCS_TO_SCRAPE config dictionary ONLY
✅ Output to docs/dev/scraperapi/
❌ DO NOT modify scraper core logic (BeautifulSoup, MarkItDown)
❌ DO NOT install new dependencies
❌ DO NOT create new tools

SUCCESS CRITERIA:
- 10+ clean markdown files
- API endpoints fully documented
- Pricing table extracted ($/request, credits, concurrency)
- Rate limits captured
- Structured endpoint details (Amazon, Google, eBay)

COMMIT MESSAGE:
```
docs(scraperapi): Add official API documentation

Scraped docs.scraperapi.com using doc-scraper tool.
Output: 12 markdown files in docs/dev/scraperapi/

Key findings:
- Structured endpoints for Amazon/Google/eBay
- JS rendering costs +5 credits per request
- Hobby plan: $49/mo, 100K credits, 20 concurrent threads
- Rate limit: 99.9% success rate, no charge on failures

Related: #1

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

ESTIMATED TIME: 30-60 minutes
```

---

### Plan Agent 2: Bright Data Research (Issue #2)

**Prompt**:
```
You are a research specialist for the IAC-032 Unified Scraper project.

OBJECTIVE: Scrape complete Bright Data documentation and convert to clean markdown.

TARGET: https://docs.brightdata.com/

REQUIRED PAGES:
- Getting Started
- Web Scraper API Reference
- Proxy Networks (residential, datacenter, mobile)
- Structured Data Collectors
- SERP API
- JavaScript Rendering
- Pricing (compare to ScraperAPI: $/1K requests)
- Rate Limits & Concurrency
- Success Rates & SLA
- Browser Automation Features

IMPLEMENTATION:
1. Navigate to tools/doc-scraper/
2. Edit scrape_docs.py - extend DOCS_TO_SCRAPE:
   ```python
   "brightdata": {
       "base_url": "https://docs.brightdata.com",
       "pages": [
           "/introduction/getting-started",
           "/scraping-automation/web-scraper",
           "/proxies/residential-proxies",
           # ... add all relevant paths
       ]
   }
   ```
3. Run: `python scrape_docs.py`
4. Output: docs/dev/brightdata/*.md

FOCUS AREAS FOR COMPARISON:
- Pricing structure vs ScraperAPI
- Proxy network quality (150M+ IPs vs competitors)
- Structured data capabilities
- CAPTCHA solving approach
- Ease of integration (SDK, API simplicity)

GUARDRAILS:
✅ Use existing scrape_docs.py ONLY
✅ Config-only changes
❌ NO new dependencies or tools

SUCCESS CRITERIA:
- 8+ markdown files
- Clear pricing comparison data
- Proxy network specifications
- API complexity assessment

COMMIT MESSAGE:
```
docs(brightdata): Add official platform documentation

Scraped docs.brightdata.com for comparison analysis.
Output: 10 markdown files in docs/dev/brightdata/

Key findings:
- Web Scraper API: $0.001/request (2x ScraperAPI cost)
- 150M+ residential proxy pool
- Enterprise focus (minimum $499/mo commitment)
- More complex setup than ScraperAPI

Related: #2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

ESTIMATED TIME: 30-60 minutes
```

---

### Plan Agent 3: Apify Research (Issue #3)

**Prompt**:
```
You are a research specialist for the IAC-032 Unified Scraper project.

OBJECTIVE: Scrape complete Apify documentation and convert to clean markdown.

TARGET: https://docs.apify.com/

REQUIRED PAGES:
- Getting Started
- Actors (pre-built scrapers)
- Web Scraping Actors
- Twitter/X Scraper Actor
- YouTube Scraper Actor
- Reddit Scraper Actor
- Amazon Scraper Actor
- Pricing (compute units vs API credits)
- Platform vs Actors approach
- SDK Integration (JavaScript, Python)
- Rate Limits

IMPLEMENTATION:
1. Edit scrape_docs.py - extend DOCS_TO_SCRAPE:
   ```python
   "apify": {
       "base_url": "https://docs.apify.com",
       "pages": [
           "/platform/getting-started",
           "/platform/actors",
           "/academy/web-scraping",
           # ... add paths for Twitter/YouTube/Reddit actors
       ]
   }
   ```
2. Run scraper
3. Output: docs/dev/apify/*.md

FOCUS FOR COMPARISON:
- Actor system vs direct API (complexity tradeoff)
- Pre-built scrapers for our platforms (Twitter, YouTube, Reddit)
- Pricing: compute units model vs ScraperAPI credits
- Maintenance burden (actors break when sites change)
- Python SDK quality

GUARDRAILS:
Same as agents 1-2 (existing tool only)

SUCCESS CRITERIA:
- 8+ markdown files
- Actor catalog for Twitter/YouTube/Reddit documented
- Pricing model clearly explained (compute units)
- Complexity assessment vs ScraperAPI

COMMIT MESSAGE:
```
docs(apify): Add platform and actor documentation

Scraped docs.apify.com for actor-based scraping analysis.
Output: 9 markdown files in docs/dev/apify/

Key findings:
- Actor marketplace: pre-built Twitter/YouTube/Reddit scrapers
- Pricing: $0.25/compute unit (variable per scrape)
- Higher complexity than ScraperAPI (actor management)
- Actors break when platforms change (maintenance risk)

Related: #3

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

ESTIMATED TIME: 30-60 minutes
```

---

## Synthesis Agent: Comparison Matrix (Issue #4)

**Deploy AFTER agents 1-3 complete**

**Prompt**:
```
You are the synthesis lead for IAC-032 Unified Scraper research.

OBJECTIVE: Create comprehensive comparison matrix from completed research (Issues #1-3).

INPUT FILES:
- docs/dev/scraperapi/*.md
- docs/dev/brightdata/*.md
- docs/dev/apify/*.md

OUTPUT FILE: docs/pm/SCRAPER_COMPARISON.md

COMPARISON CRITERIA:

1. PRICING
   - $/1K requests (normalize all pricing models)
   - Monthly minimums
   - Free tier availability
   - Cost for 100K requests/month

2. FEATURES
   - CAPTCHA solving (automatic, manual, N/A)
   - JavaScript rendering (included, extra cost, N/A)
   - Structured endpoints (Amazon, Google, eBay)
   - Proxy rotation (automatic, manual)
   - Geotargeting options

3. RELIABILITY
   - Success rate SLA (%)
   - Uptime guarantee
   - Failed request charging policy
   - Retry logic (automatic, manual)

4. EASE OF INTEGRATION
   - SDK quality (Python rating: 1-10)
   - API complexity (simple, medium, complex)
   - Documentation quality (1-10)
   - Code examples availability

5. PLATFORM SUPPORT
   - Twitter/X scraping capability
   - YouTube scraping
   - Reddit scraping
   - Amazon reviews extraction
   - General web scraping

6. RATE LIMITS
   - Concurrent requests (threads)
   - Requests per minute
   - Bandwidth limits

7. MAINTENANCE BURDEN
   - Platform changes handling (automatic, manual)
   - Breaking changes frequency
   - Support responsiveness

DECISION MATRIX FORMAT:
```markdown
# Web Scraping Platform Comparison

## Executive Summary
[2-3 paragraph recommendation with winner]

## Detailed Comparison

| Criterion | ScraperAPI | Bright Data | Apify |
|-----------|-----------|-------------|-------|
| **Pricing** | | | |
| $/1K requests | $0.49 | $1.00 | $X.XX |
| Monthly minimum | $49 | $499 | $49 |
| 100K req/mo cost | $49 | $100 | $X |
| **Features** | | | |
| ... | ... | ... | ... |

[Continue all criteria]

## Recommendations

### For IAC-032 (3-day MVP, €900 budget)
**Winner**: [Platform Name]

**Rationale**:
- [Reason 1]
- [Reason 2]
- [Reason 3]

**Runner-up**: [Platform] - Use if [scenario]

### Week 2+ Considerations
[Long-term platform evaluation if needs change]

## Implementation Notes
[Specific integration steps for winner]

## Cost Projections
| Usage Level | Monthly Cost | Notes |
|-------------|--------------|-------|
| MVP (10K/mo) | $X | Testing phase |
| Production (100K/mo) | $X | Expected usage |
| Scale (1M/mo) | $X | Future growth |
```

GUARDRAILS:
✅ Base ALL data on scraped docs (no assumptions)
✅ Show calculations for pricing conversions
✅ Cite specific doc pages for claims
❌ DO NOT invent features or pricing
❌ DO NOT bias toward any platform without data

COMMIT MESSAGE:
```
docs(pm): Add web scraping platform comparison matrix

Synthesized research from ScraperAPI, Bright Data, and Apify docs.

Comparison across:
- Pricing: ScraperAPI $0.49/1K, Bright Data $1.00/1K, Apify variable
- Features: ScraperAPI has best structured endpoints + simplicity
- Reliability: All 99%+ uptime, ScraperAPI no-charge on failures
- Integration: ScraperAPI simplest API, Apify most complex

RECOMMENDATION: ScraperAPI for MVP
- Lowest cost ($49/mo vs $499 Bright Data)
- Structured endpoints for Amazon/Google
- Simple integration (1 API call vs actor management)
- 3-day timeline favors ease over features

Output: docs/pm/SCRAPER_COMPARISON.md

Related: #4, closes #1, #2, #3

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

ESTIMATED TIME: 1-2 hours (depends on agents 1-3 completion)
```

---

## Execution Instructions for CCW

### Step 1: Spawn Parallel Plan Agents
```
Launch 3 Plan agents simultaneously with "medium" thoroughness:
- Agent 1: ScraperAPI research (prompt above)
- Agent 2: Bright Data research (prompt above)
- Agent 3: Apify research (prompt above)

Run in parallel to maximize speed (agents are independent).
```

### Step 2: Monitor Progress
```
Check each agent's output:
- Verify docs/dev/{platform}/ directories created
- Confirm 8-10+ markdown files per platform
- Ensure pricing/features/rate-limits captured
```

### Step 3: Deploy Synthesis Agent
```
Once agents 1-3 commit their findings:
- Launch synthesis agent (Issue #4 prompt above)
- Creates comparison matrix in docs/pm/SCRAPER_COMPARISON.md
- Makes platform recommendation for MVP
```

### Step 4: Update CLAUDE.md
```
Add research findings to CLAUDE.md under new section:
## Platform Research Findings (Day 1)

[Paste exec summary from SCRAPER_COMPARISON.md]

Key decision: [ScraperAPI/Bright Data/Apify] chosen because [reasons]
```

---

## Success Criteria

**Agents Complete When:**
- [ ] docs/dev/scraperapi/ has 10+ markdown files
- [ ] docs/dev/brightdata/ has 8+ markdown files
- [ ] docs/dev/apify/ has 8+ markdown files
- [ ] docs/pm/SCRAPER_COMPARISON.md exists with recommendation
- [ ] CLAUDE.md updated with findings
- [ ] All agents committed with proper format
- [ ] Issues #1-4 closed

**Timeline:**
- Agents 1-3: 30-60 min each (run parallel = 1 hour total)
- Agent 4 (synthesis): 1-2 hours
- **Total: 2-3 hours for complete research phase**

---

## Emergency Fallback

If `tools/doc-scraper/scrape_docs.py` fails:
1. Use WebFetch tool directly on documentation pages
2. Save output to docs/dev/{platform}/
3. Still create comparison matrix
4. Note in commit message: "Manual WebFetch method used"

**Do NOT let tooling block research completion.**

---

*Copy this entire prompt into CCW and execute. Agents will run in parallel and complete Day 1 research foundation.*
