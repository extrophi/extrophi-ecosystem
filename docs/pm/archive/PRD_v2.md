# PRD: Unified Content Research & Copywriting Intelligence Engine
## IAC-032-unified-scraper | 3-Day MVP Implementation

**Last Updated:** Saturday, 15 Nov 2025 22:47 GMT  
**Token Budget Remaining:** 84K (44%)  
**Deadline:** Tuesday EOD (3 days)  
**Budget:** €900 (expires Wednesday)

---

## Executive Summary

**What This Is:** A prompt-driven RAG system for content creators that scrapes multi-platform sources, builds a queryable framework library from your 2TB copywriting archive, and outputs markdown research documents. Think Kortex-style card system but local, fast, and yours.

**NOT:** A SaaS product, web dashboard, or Notion integration. This is YOUR research machine.

**Core Value:** Transform scattered research (courses, tweets, videos, reviews) into a searchable knowledge base that feeds prompt-driven markdown outputs for newsletters, copy, and content.

---

## User: You (Not Sarah)

**Demographics:**
- Male, mid-40s
- Content creator, researcher, technologist
- Interests: Philosophy, psychology, history, tech, AI, culture
- Has 2TB archive of copywriting/marketing courses
- Uses MarkEdit for markdown writing
- Wants to publish newsletters (Markdown → HTML)

**Current Pain Points:**
1. 2TB of courses just sitting there - no way to query knowledge
2. Manual research across YouTube, Twitter, Reddit takes hours
3. Can't quickly reference frameworks from Dan Koe, Stefan Georgi, etc.
4. Notion is bloated RAM hog with feature creep
5. Need to link ideas from multiple domains (philosophy + tech + marketing)

**Desired State:**
- Ask questions against 2TB library: "What does Dan Koe say about focus?"
- Scrape fresh content from web sources with prompts
- Card-based UI for collecting "brain farts" and ideas
- Write newsletter in single markdown editor
- Export to HTML for publishing (Astro/Svelte static site)

**Jobs to Be Done:**
1. Query framework library (RAG on 2TB archive)
2. Scrape and analyze multi-platform content
3. Collect ideas in Kortex-style card system
4. Write long-form markdown content
5. Export markdown → newsletter/blog

---

## System Architecture: Modular + RAG-First

### Core Principle: Local-First, Prompt-Driven

```
┌─────────────────────────────────────────────────────┐
│              3-Window Desktop App                    │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │   Research   │   Markdown   │   Preview    │    │
│  │   Window     │   Editor     │   Window     │    │
│  │              │              │              │    │
│  │ Card system  │ Full editor  │ Rendered MD  │    │
│  │ Prompts      │ Highlighting │ HTML output  │    │
│  │ RAG queries  │ Word count   │              │    │
│  └──────────────┴──────────────┴──────────────┘    │
└─────────────────────────────────────────────────────┘
                       ↓
            ┌──────────────────────┐
            │   Backend Services   │
            ├──────────────────────┤
            │ • RAG Engine (2TB)   │
            │ • Scrapers (modular) │
            │ • LLM Router         │
            │ • Vector DB          │
            └──────────────────────┘
```

### Data Flow

```
Input Sources → Processing → Storage → Query → Output
     ↓              ↓           ↓        ↓        ↓
  Courses      Transcribe   Vector DB  Prompt  Markdown
  YouTube      Extract      ChromaDB    RAG     Editor
  Twitter      Analyze      SQLite    Search   Export
  Reddit       Embed        Files     Cards    HTML
```

---

## 3 Windows, 1 Workflow

### Window 1: Research Dashboard (Left)

**Kortex-Style Card System:**
- Create cards with: Title, Body, Tags, Source
- Drag cards to organize
- Filter by tag, source, date
- Prompt bar at top: "Find Dan Koe frameworks about focus"

**RAG Query Interface:**
- Prompt: "What does Stefan Georgi say about RMBC?"
- Returns: Relevant chunks from 2TB with sources
- Click to expand, add to card, or insert into editor

**Scraper Controls:**
- Quick scrape buttons: YouTube URL, Twitter handle, Subreddit
- Results appear as cards
- OpenAI API for analysis (cheap testing)

### Window 2: Markdown Editor (Center)

**Full-Featured Writing:**
- Syntax highlighting (like MarkEdit)
- Word count, reading time
- Hemingway-style readability scoring
- Save to local .md files
- Auto-save every 30 seconds

**Editor Features:**
- Insert card content with citation
- Highlight text → Create card
- Markdown preview toggle
- Export options (MD, HTML, PDF)

### Window 3: Preview/Output (Right)

**Live Preview:**
- Rendered markdown
- Hemingway readability analysis (highlight complex sentences, passive voice)
- Export to HTML with Astro/Svelte templates
- Newsletter preview

---

## Technical Stack Revised

### Backend Services

| Component | Choice | Why | Cost |
|-----------|--------|-----|------|
| **LLM** | OpenAI GPT-4o | Cheap testing, good quality | $20/mo |
| **Future LLM** | Claude Sonnet 4.5 | Best copywriting analysis | Later |
| **Embeddings** | text-embedding-3-small | Cheapest ($0.02/1M) | $5/mo |
| **Vector DB** | ChromaDB | Free, local, simple | $0 |
| **Relational DB** | SQLite | Local, fast, zero-config | $0 |
| **Scraping** | ScraperAPI Trial | 5K credits free | $0 (testing) |
| **Package Mgr** | UV | Fast Python package mgmt | $0 |
| **Container** | Podman | Not Docker | $0 |

**Total MVP Cost:** ~$25/month (just OpenAI)

### Frontend (Desktop App)

**Option 1: Tauri + Svelte** (Your Rust experience)
- Rust backend + web frontend
- Small binary (~10MB)
- Native file access
- Fast startup

**Option 2: Python + PyQt/PySide** (Simpler for MVP)
- All Python stack
- QWebEngine for markdown preview
- Faster development (3 days)

**Recommendation:** Start with Python + PyQt for speed, port to Tauri later if needed.

---

## Module Breakdown (Unix Philosophy)

### Scrapers (Independent CLIs)

```bash
# Each scraper outputs JSON to stdout
python scrapers/youtube_scraper.py --url=VIDEO_URL
python scrapers/twitter_scraper.py --handle=dankoe --limit=100
python scrapers/reddit_scraper.py --subreddit=copywriting --limit=50
python scrapers/course_processor.py --input=/path/to/course
```

### RAG Engine

```bash
# Index 2TB library
python rag/index_library.py --input=/path/to/2TB --output=chroma_db/

# Query
python rag/query.py --prompt="Dan Koe focus frameworks" --top_k=5
```

### LLM Router (Model Switching)

```python
# Supports OpenAI, Claude, local models
from llm_router import get_completion

response = get_completion(
    prompt="Analyze this tweet",
    provider="openai",  # or "claude" or "local"
    model="gpt-4o"
)
```

---

## 3-Day Implementation Plan

### Day 1: Backend + RAG

**Alpha Tasks:**
- UV project setup
- SQLite schema (cards, sources, analyses)
- ChromaDB setup
- YouTube scraper (reuse from existing)
- Basic RAG query

**Deliverable:** Can index 10 videos, query with prompt, get results

### Day 2: Scrapers + Desktop Shell

**Beta Tasks:**
- Twitter scraper (reuse IAC-024 patterns)
- Reddit scraper (PRAW)
- Course processor (transcribe with Whisper)
- PyQt shell with 3-window layout
- Card system data model

**Deliverable:** Desktop app opens, can create cards, run scrapers

### Day 3: Editor + Integration

**Gamma Tasks:**
- Markdown editor with syntax highlighting
- Hemingway analysis integration
- RAG → Card → Editor workflow
- Export markdown → HTML (Astro template)
- Polish UI, test end-to-end

**Deliverable:** Full workflow: Scrape → RAG query → Card → Write → Export

---

## Project Structure

```
IAC-032-unified-scraper/
├── backend/
│   ├── scrapers/
│   │   ├── youtube_scraper.py
│   │   ├── twitter_scraper.py
│   │   ├── reddit_scraper.py
│   │   └── course_processor.py
│   ├── rag/
│   │   ├── indexer.py
│   │   ├── query_engine.py
│   │   └── chroma_db/
│   ├── llm/
│   │   ├── router.py
│   │   ├── openai_client.py
│   │   └── claude_client.py
│   └── db/
│       ├── models.py
│       └── content.db (SQLite)
├── desktop/
│   ├── main.py (PyQt app)
│   ├── windows/
│   │   ├── research_window.py
│   │   ├── editor_window.py
│   │   └── preview_window.py
│   ├── components/
│   │   ├── card_widget.py
│   │   ├── markdown_editor.py
│   │   └── hemingway_analyzer.py
│   └── assets/
├── templates/
│   ├── newsletter.html (Astro)
│   └── blog_post.html
├── data/
│   ├── library/ (2TB indexed here)
│   ├── cards/
│   └── exports/
└── docs/
    └── pm/ (this file)
```

---

## Workflow Example

**Morning Research Session:**

1. Open app → Research window active
2. Prompt: "Find all Dan Koe content about Kortex tool"
3. RAG engine searches 2TB + recent scrapes
4. Returns 10 cards with quotes, sources
5. Drag 3 cards to "Newsletter Ideas" tag
6. Switch to Editor window
7. Insert card contents with citations
8. Write 1000-word section
9. Preview window shows Hemingway score (Grade 8 reading level)
10. Export → markdown file saved
11. Later: Astro builds HTML for blog

**Afternoon Scraping:**

1. Research window → Scrape controls
2. Enter: twitter.com/naval/status/123...
3. Scraper fetches tweet + thread
4. LLM analyzes: "Stoicism framework, contrarian thinking"
5. Auto-creates card with analysis
6. Tag: "Philosophy", "Copywriting Angles"
7. Card available for future writing

---

## RAG Architecture Details

### Indexing Pipeline

```python
# Course → Chunks → Embeddings → Vector DB

1. Extract audio/video with ffmpeg
2. Transcribe with Whisper (local or OpenAI)
3. Chunk into 500-token segments with overlap
4. Generate embeddings (text-embedding-3-small)
5. Store in ChromaDB with metadata:
   - source: "Dan Koe - 2 Hour Writer.mp4"
   - timestamp: 00:23:45
   - speaker: "Dan Koe"
   - topic: "Newsletter frameworks"
```

### Query Pipeline

```python
# Prompt → Embedding → Search → Re-rank → LLM Context

1. User enters: "Best newsletter hooks"
2. Embed query
3. ChromaDB similarity search (top 20)
4. Re-rank with cross-encoder
5. Take top 5 chunks
6. Feed to LLM with prompt:
   "Based on these sources, list best newsletter hooks with examples"
7. LLM response appears in card
```

### Metadata Schema

```python
{
  "id": "uuid",
  "content": "chunk text...",
  "embedding": [0.123, ...],
  "metadata": {
    "source": "path/to/file",
    "author": "Stefan Georgi",
    "course": "RMBC Framework",
    "timestamp": "01:23:45",
    "topic": "Research phase",
    "framework": "RMBC"
  }
}
```

---

## Hemingway Integration

**Open-Source Alternative:** `textstat` Python library

```python
from textstat import flesch_kincaid_grade, passive_voice_ratio

text = "Your newsletter content..."

grade_level = flesch_kincaid_grade(text)  # Target: 6-8
passive = passive_voice_ratio(text)  # Target: <10%
complex_words = count_complex_words(text)

# Highlight in editor:
# - Grade 10+ sentences → yellow
# - Passive voice → blue
# - Complex words → purple
```

**Features:**
- Real-time readability scoring
- Highlight problem areas
- Suggest simpler alternatives (LLM-powered)
- Word count, reading time

---

## Card System Design

### Card Schema

```python
class Card:
    id: UUID
    title: str
    body: str  # Markdown supported
    tags: List[str]
    source: str  # URL or file path
    created_at: datetime
    updated_at: datetime
    metadata: dict  # Flexible JSON
```

### Card Operations

- **Create:** Click "+", paste content, or LLM-generate from scrape
- **Edit:** Double-click to modify
- **Link:** Drag card onto another to create relationship
- **Filter:** Tag selector, full-text search
- **Export:** Batch export cards to markdown file

### Card UI

```
┌─────────────────────────────────┐
│ Dan Koe: Newsletter Frameworks  │ [x]
├─────────────────────────────────┤
│ "Start with one idea, expand    │
│  into 5-7 tweets, 1 thread,     │
│  then full newsletter..."       │
│                                 │
│ Tags: [Workflow] [Dan Koe]      │
│ Source: 2-Hour-Writer.mp4       │
│ 00:45:23                        │
└─────────────────────────────────┘
```

---

## Markdown to HTML Publishing

### Astro Static Site Generator

**Why Astro:**
- Markdown-native
- Fast builds
- Component islands (Svelte/React)
- SEO-friendly
- Zero JS by default

**Workflow:**

```bash
# Write in app, export to:
/content/newsletters/2025-11-15-focus-frameworks.md

# Astro builds:
npm run build

# Deploy to:
- Netlify (free)
- Vercel (free)
- GitHub Pages (free)
- Your own server
```

### Newsletter Template

```astro
---
// newsletter.astro
import { getCollection } from 'astro:content';
const { title, date, readingTime } = Astro.props;
---

<article>
  <header>
    <h1>{title}</h1>
    <time>{date}</time>
    <span>{readingTime} min read</span>
  </header>
  
  <slot />  <!-- Your markdown content -->
  
  <footer>
    <a href="/subscribe">Subscribe for more</a>
  </footer>
</article>
```

---

## Scraper Specifications

### YouTube Scraper

```python
# Input: URL or channel
# Output: JSON with transcript, metadata

{
  "video_id": "abc123",
  "title": "How to Build $2M Business",
  "author": "Dan Koe",
  "transcript": "full text...",
  "duration": 3600,
  "views": 150000,
  "published": "2025-10-15",
  "chapters": [...],
  "description": "..."
}
```

### Twitter Scraper

```python
# Reuse IAC-024 patterns
# Input: Handle or URL
# Output: Tweets with engagement

{
  "tweets": [
    {
      "id": "123",
      "text": "How I built...",
      "likes": 1250,
      "retweets": 45,
      "replies": 23,
      "created_at": "2025-11-15T10:00:00Z"
    }
  ]
}
```

### Course Processor

```python
# Input: Video/audio files
# Steps:
# 1. Extract audio (ffmpeg)
# 2. Transcribe (Whisper API)
# 3. Chunk transcript
# 4. Detect chapters/topics (LLM)
# 5. Index to RAG

# Output: Indexed in ChromaDB
```

---

## LLM Costs Comparison

| Task | OpenAI GPT-4o | Claude Sonnet 4.5 | Notes |
|------|---------------|-------------------|-------|
| Analyze tweet | $0.0001 | $0.0003 | OpenAI cheaper |
| Extract frameworks | $0.001 | $0.003 | Both good |
| Write newsletter | $0.01 | $0.03 | Claude better quality |
| Summarize course | $0.05 | $0.15 | OpenAI for bulk |

**Strategy:**
- **MVP (Day 1-3):** Use OpenAI for everything (cheap testing)
- **Week 2:** Add Claude Sonnet 4.5 for copywriting analysis
- **Production:** Model router - OpenAI for scraping, Claude for writing

---

## Critical Success Metrics

**Day 3 Deliverable:**
- [ ] Desktop app opens with 3 windows
- [ ] Can create/edit/delete cards
- [ ] RAG query returns results from 10 indexed videos
- [ ] YouTube scraper works
- [ ] Markdown editor with syntax highlighting
- [ ] Export markdown file
- [ ] Hemingway analysis shows readability score

**Week 2 Goals:**
- [ ] 2TB library fully indexed
- [ ] Twitter + Reddit scrapers integrated
- [ ] Course processor handles video files
- [ ] Card linking/relationships
- [ ] Astro template for HTML export

---

## What We're NOT Building

**Scope Constraints:**
- ❌ Web dashboard (desktop only)
- ❌ Multi-user (single-user tool)
- ❌ Notion integration (local files)
- ❌ Real-time sync (local DB)
- ❌ Mobile app (desktop workflow)
- ❌ Video editing (scraping only)
- ❌ Image generation (text focus)

---

## Risks & Mitigation

**Risk: 2TB indexing takes forever**  
→ Mitigation: Start with 10 courses, optimize pipeline, then scale

**Risk: PyQt learning curve**  
→ Mitigation: Use simple layouts, focus on function over form

**Risk: Hemingway analysis slow**  
→ Mitigation: Cache results, run on-demand not real-time

**Risk: RAG quality poor**  
→ Mitigation: Tune chunk size, test re-ranking, improve prompts

---

## Next Steps

**Right Now:**
1. Create project structure with UV
2. Set up SQLite + ChromaDB
3. Test RAG with 5 YouTube transcripts
4. Build basic PyQt window

**Day 1 Focus:**
- Get RAG working end-to-end
- One scraper functional (YouTube)
- Basic card storage in SQLite

**Handoff to Claude Code:**
- Technical implementation of each module
- Type errors, dependency issues
- PyQt UI polish

---

## File to Save Location

**Path:** `/Users/kjd/01-projects/IAC-032-unified-scraper/docs/pm/PRD_v2.md`

**Ready for:**
- Claude Code to implement modules
- Agent delegation (Alpha, Beta, Gamma)
- 3-day sprint execution

---

**Focus:** Simple, local, fast. YOUR research machine. Not a product. A tool.
