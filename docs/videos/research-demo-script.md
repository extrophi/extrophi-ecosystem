# Research (Unified Scraper) - Demo Script
## Duration: 3 minutes
## Format: Teleprompter-style with timestamps

---

## [0:00-0:15] OPENING

Welcome to Research - the multi-platform content intelligence engine that transforms how you gather, analyze, and synthesize information from across the web.

Let me show you how to go from scattered content to actionable intelligence in minutes.

---

## [0:15-0:40] THE PROBLEM WE'RE SOLVING

If you're a content creator, you've been here before:

You want to create content about a topic - let's say "focus systems for knowledge workers."

So you manually search Twitter for experts. You watch YouTube videos and take notes. You browse Reddit threads. You read blog posts.

Hours later, you have dozens of tabs open, scattered notes, and no clear picture of what works.

Research solves this.

---

## [0:40-1:10] MULTI-PLATFORM SCRAPING

Here's how it works. I'll create a new research project about focus systems.

[DEMONSTRATE: Create project]

Now I'll tell Research which sources to scrape:

- Twitter: @dankoe, @calnewport, @james_clear
- YouTube: Cal Newport's "Deep Work" video
- Reddit: r/productivity, r/getdisciplined
- Web: James Clear's blog on focus

[DEMONSTRATE: Configure sources]

Click "Start Research" and watch what happens.

Research simultaneously scrapes all these platforms, normalizes the data into a unified format, generates embeddings for semantic search, and stores everything in PostgreSQL with vector support.

Twitter OAuth? Handled with Playwright automation.

YouTube transcripts? Extracted with youtube-transcript-api.

Reddit threads? PRAW API integration.

Web content? Jina.ai Reader for clean markdown conversion.

All of this happens in the background while you work on something else.

---

## [1:10-1:40] INTELLIGENT ANALYSIS

Now here's where it gets powerful.

Every piece of content is analyzed using LLM technology - GPT-4 for bulk processing, Claude Sonnet for nuanced copywriting analysis.

[DEMONSTRATE: View analysis results]

Look at this tweet from Dan Koe. Research has automatically:

- Identified the copywriting framework - in this case, PAS: Problem, Agitation, Solution
- Extracted the hook - a curiosity-based opener about productivity myths
- Detected themes - focus, deep work, creator economy
- Calculated an engagement score based on likes, retweets, and replies
- Generated a semantic embedding for similarity search

This happens for every single piece of content across all platforms.

---

## [1:40-2:10] SEMANTIC SEARCH & PATTERN DETECTION

Now I can ask questions in natural language.

[DEMONSTRATE: RAG query]

"What do successful creators say about maintaining focus while building an audience?"

Research doesn't just keyword match - it uses RAG semantic search to find conceptually similar content across all platforms.

Look at these results:

A tweet from Dan Koe about two-hour focus blocks.

A YouTube video from Cal Newport about attention residue.

A Reddit comment with a personal focus system.

All semantically related, even though they use different words.

[DEMONSTRATE: Pattern detection]

But here's what's really interesting - the pattern detection.

Research has identified that Dan Koe tested the "two-hour focus block" concept in a tweet on Tuesday, expanded it in his newsletter on Saturday, and referenced it again in a YouTube video the following week.

This is cross-platform elaboration - and Research automatically detects it by comparing embeddings and timestamps.

You can now reverse-engineer successful content strategies.

---

## [2:10-2:35] COURSE SCRIPT GENERATION

Let's put it all together.

I'll ask Research to generate a course script about focus systems.

[DEMONSTRATE: Generate script]

"Create a video script for Module 1: The Focus Crisis. Target audience: knowledge workers and creators. 20 minutes long."

Watch as Research:

- Pulls pain points from Reddit threads
- Uses hooks from viral tweets
- Structures content using detected frameworks
- Cites sources with URLs
- Organizes everything into a production-ready script with timestamps

[Show generated script]

Here's the output - a complete course module with introduction, problem statement, framework explanation, examples, and citations.

Every claim is sourced. Every hook is tested. Every framework is proven.

---

## [2:35-2:50] EXPORT & INTEGRATION

When you're done, export everything:

Markdown documents for your blog or documentation.

Tweet threads optimized for engagement.

Video scripts with timestamps and visuals.

Research briefs with citations and data.

[DEMONSTRATE: Export options]

And if you're using the Extrophi Backend, you can track attribution - Research remembers which sources contributed to your final content and rewards them with $EXTROPY tokens.

---

## [2:50-3:00] CLOSING

Research - from scattered content to structured intelligence.

Stop researching manually. Start researching systematically.

---

## PRODUCTION NOTES

**Screen Recording Sections:**
- 0:40-1:10: Show dashboard with multi-platform scraping in progress (use progress bars/spinners)
- 1:10-1:40: Display analysis panel with framework detection, hooks, themes
- 1:40-2:10: Demonstrate RAG search with query and results appearing
- 2:10-2:35: Show script generation in real-time (or sped up with overlay)
- 2:35-2:50: Display export dialog with format options

**Visual Overlays:**
- Platform logos when mentioning sources (Twitter, YouTube, Reddit)
- Highlight key terms: "PAS Framework", "Semantic Search", "Cross-Platform Elaboration"
- Show data flow diagram during scraping section
- Display embedding visualization (optional - could be too technical)

**Demo Preparation:**
- Pre-scrape sample data (200-300 pieces of content)
- Have analysis results ready to display
- Prepare a sample course script output
- Set up export examples (markdown, tweet thread)
- Have network/API calls recorded (don't rely on live scraping)

**Data Privacy:**
- Blur any API keys or credentials
- Use public Twitter profiles only
- Ensure scraped content is publicly available
- Follow platform ToS for demonstration purposes

**Tone:** Enthusiastic but professional. This is powerful technology - let that excitement show through.

**Pacing:** Fast enough to show capability, slow enough to let users absorb what's happening.

**Key Messages:**
1. Multi-platform = comprehensive intelligence
2. LLM analysis extracts patterns humans would miss
3. Semantic search > keyword search
4. Pattern detection reveals content strategies
5. Production-ready outputs save hours of work
6. Attribution system rewards original creators
