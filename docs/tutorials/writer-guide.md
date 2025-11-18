# Writer Guide: Privacy-First Voice Journaling

Complete guide to using BrainDump Writer for voice journaling, content creation, and knowledge capture. Learn to record, transcribe, organize, and publish your thoughts—all while keeping your data private and local.

---

## Table of Contents

1. [What is Writer?](#what-is-writer)
2. [Installation & Setup](#installation--setup)
3. [Recording Voice Notes](#recording-voice-notes)
4. [Privacy Levels](#privacy-levels)
5. [AI Chat Integration](#ai-chat-integration)
6. [Publishing Cards](#publishing-cards)
7. [Session Management](#session-management)
8. [Prompt Templates](#prompt-templates)
9. [Export & Backup](#export--backup)
10. [Advanced Features](#advanced-features)
11. [Workflow Examples](#workflow-examples)
12. [Troubleshooting](#troubleshooting)

---

## What is Writer?

**BrainDump Writer** is a desktop app for voice journaling and content capture. It's designed for:

- **Content creators** who need to capture ideas quickly
- **People under stress** who need to externalize thoughts
- **Privacy-conscious individuals** who don't trust cloud services
- **Knowledge workers** building a personal knowledge base

### Core Features

✅ **Local voice transcription** (whisper.cpp with Metal GPU)
✅ **AI chat integration** (OpenAI GPT-4, Claude Sonnet)
✅ **Privacy-aware publishing** (you control what's public)
✅ **$EXTROPY token rewards** (earn tokens for publishing)
✅ **Session management** (organize by topic, date, or project)
✅ **Markdown export** (portable, future-proof format)

### Privacy-First Design

- ✅ Voice never leaves your machine (100% local transcription)
- ✅ API keys stored in macOS Keychain (secure, encrypted)
- ✅ Privacy levels prevent accidental publishing of personal content
- ✅ No tracking, no analytics, no telemetry
- ❌ No cloud sync (deliberate choice—your data stays yours)

---

## Installation & Setup

### System Requirements

- **macOS** 11+ (Apple Silicon recommended for Metal GPU acceleration)
- **4GB RAM** minimum (8GB recommended)
- **500MB disk space** for app + Whisper model
- **Microphone** (built-in or external)

### Step 1: Install Dependencies

```bash
# Install system packages via Homebrew
brew install whisper-cpp portaudio

# Download Whisper base model (141MB)
mkdir -p ~/extrophi-models
curl -L -o ~/extrophi-models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

**Whisper Models Available:**
- `ggml-tiny.bin` (75MB) - Fastest, less accurate
- `ggml-base.bin` (141MB) - **Recommended balance**
- `ggml-small.bin` (466MB) - More accurate
- `ggml-medium.bin` (1.5GB) - Very accurate
- `ggml-large.bin` (2.9GB) - Best accuracy, slowest

### Step 2: Clone Repository

```bash
git clone https://github.com/extrophi/extrophi-ecosystem.git
cd extrophi-ecosystem/writer
```

### Step 3: Install Node Dependencies

```bash
# Use NVM to manage Node versions
nvm use 18

# Install dependencies
npm install
```

### Step 4: Build and Launch

**Development Mode** (with hot reload):
```bash
npm run tauri:dev
```

**Production Build** (create .app):
```bash
npm run tauri:build
# Output: src-tauri/target/release/bundle/macos/BrainDump.app
```

### Step 5: Grant Microphone Permissions

On first launch, macOS will prompt:
> "BrainDump would like to access the microphone"

Click **Allow** to enable voice recording.

If you missed this prompt:
1. Go to **System Settings > Privacy & Security > Microphone**
2. Enable **BrainDump**

---

## Recording Voice Notes

### Basic Recording

1. **Click the 🎤 Record button** (or press `Cmd+R`)
2. **Speak clearly** into your microphone
3. **Click Stop** when done (or press `Cmd+R` again)
4. **Wait for transcription** (usually <1 second per 10 seconds of audio)

### Recording Tips

**For Best Accuracy:**
- Speak clearly and at normal pace
- Minimize background noise
- Use a good microphone (built-in Mac mic works well)
- Avoid filler words like "um," "uh," "like"

**Optimal Recording Length:**
- **Short bursts**: 30-60 seconds per recording
- **Medium**: 2-3 minutes for detailed thoughts
- **Long**: 5-10 minutes for comprehensive ideas

Whisper handles long recordings well, but shorter recordings are easier to organize and publish as individual cards.

### Audio Settings

**Sample Rate**: 16kHz (optimized for Whisper)
**Channels**: Mono
**Format**: WAV (temporary, auto-deleted after transcription)

---

## Privacy Levels

Privacy levels determine whether a card can be published to the web. This prevents accidental exposure of personal or sensitive content.

### Available Privacy Levels

| Privacy Level | Publishable? | Use For | Examples |
|---------------|--------------|---------|----------|
| **BUSINESS** | ✅ Yes | Work, strategy, professional | "My Q4 marketing strategy" |
| **IDEAS** | ✅ Yes | Creative insights, concepts | "Novel concept for a SaaS product" |
| **PERSONAL** | ❌ No | Personal reflections | "Feeling stressed about finances" |
| **PRIVATE** | ❌ No | Sensitive information | "Password for X account is..." |
| **THOUGHTS** | ❌ No | Stream of consciousness | "Just rambling through my day..." |
| **JOURNAL** | ❌ No | Daily journal entries | "Today I woke up feeling..." |

### Setting Privacy Levels

**During Recording:**
1. After transcription completes
2. Select privacy level from dropdown
3. Card auto-saves with selected level

**Changing Later:**
1. Click on any card
2. Change the privacy level dropdown
3. Auto-saves immediately

### Privacy Level Best Practices

**Think Twice Before Publishing:**
- Would you tweet this?
- Would you post this on LinkedIn?
- Would you put this in a blog post?

If **no** to all three → use PERSONAL, PRIVATE, THOUGHTS, or JOURNAL.

**BUSINESS vs IDEAS:**
- **BUSINESS**: Tactical, actionable, professional advice
- **IDEAS**: Creative, conceptual, innovative thinking

**Example Workflow:**
```
Voice note about business strategy → BUSINESS
Voice note about cool product idea → IDEAS
Voice note about personal anxiety → PERSONAL
Voice note just to clear your head → THOUGHTS
```

---

## AI Chat Integration

Writer integrates with OpenAI GPT-4 and Claude Sonnet for AI-powered analysis, expansion, and refinement of your voice notes.

### Configuring API Keys

1. Click **Settings** (⚙️ icon)
2. Enter API keys:
   - **OpenAI API Key**: `sk-...` (from [platform.openai.com](https://platform.openai.com))
   - **Claude API Key**: `sk-ant-...` (from [console.anthropic.com](https://console.anthropic.com))
3. Click **Save** (keys stored in macOS Keychain)

**Cost Estimate:**
- OpenAI GPT-4: ~$0.03 per 1,000 words
- Claude Sonnet: ~$0.015 per 1,000 words

### Using AI Chat

**Step 1: Select a Transcribed Note**
Click on any card to open it in the editor.

**Step 2: Open Chat Panel**
Click **"Chat with AI"** button (or press `Cmd+K`)

**Step 3: Choose AI Model**
- **GPT-4**: Best for general analysis, expansion
- **Claude Sonnet**: Best for copywriting, refinement

**Step 4: Ask Questions**

**Example Prompts:**
```
"Expand this into a 500-word blog post"
"What are the key insights from this note?"
"Turn this into 5 tweets"
"What questions should I explore further?"
"Critique this idea—what are the weaknesses?"
```

**Step 5: Save AI Responses**
AI responses appear in the chat panel. Click **"Save to Card"** to add them to your card body.

### Advanced AI Workflows

**Content Creation Pipeline:**
1. Record voice note about topic (2 min)
2. Review transcription, fix any errors
3. Ask AI: "Turn this into a 750-word blog post with SEO-friendly structure"
4. Edit AI output in markdown editor
5. Publish as BUSINESS card
6. Export to your blog/newsletter

**Idea Refinement:**
1. Record rough idea (30 seconds)
2. Ask AI: "What are 10 ways to expand this concept?"
3. Pick best expansion
4. Record follow-up voice note exploring that angle
5. Repeat until idea is fully developed

**Content Repurposing:**
1. Record long-form thought (5 min)
2. Ask AI: "Extract 10 atomic ideas from this"
3. Create separate cards for each atomic idea
4. Publish individually as IDEAS cards
5. Build content library from one recording

---

## Publishing Cards

Publishing converts your private voice notes into public knowledge cards, hosted on `extrophi.ai` and rewarded with $EXTROPY tokens.

### Prerequisites for Publishing

✅ Privacy level must be **BUSINESS** or **IDEAS**
✅ Card must have a title (auto-generated from first line of transcription)
✅ Card must have body content (your transcribed text)

### How to Publish

**Method 1: Single Card Publishing**
1. Select a card
2. Ensure privacy level is BUSINESS or IDEAS
3. Click **"Publish"** button
4. Confirm publication

**Method 2: Batch Publishing**
1. Click **"Publish All Eligible"** button
2. Reviews all cards with BUSINESS/IDEAS privacy
3. Shows preview of what will be published
4. Confirm batch publish

### What Happens When You Publish?

1. **Privacy Filter**: Only BUSINESS and IDEAS cards are published
2. **Markdown Conversion**: Card converted to structured markdown format
3. **URL Generation**: Unique slug generated from title (e.g., `how-to-grow-on-twitter-a1b2c3d4`)
4. **Database Storage**: Card stored in PostgreSQL with full metadata
5. **Token Reward**: You earn **1.00000000 $EXTROPY token**
6. **Public URL**: Card published to `https://extrophi.ai/cards/{slug}`

### Published Card Format

Published cards are formatted as structured markdown:

```markdown
# Your Card Title

**Category:** BUSINESS
**Privacy:** BUSINESS
**Tags:** `business`, `strategy`, `growth`

---

Your transcribed content appears here, formatted as clean markdown.

You can edit this before publishing to:
- Fix transcription errors
- Add structure (headings, lists, bold)
- Remove filler words or tangents
- Add links or references
```

### Managing Published Cards

**View Published Cards:**
- Click **"Published"** tab to see all your published cards
- Shows: Title, URL, publish date, $EXTROPY earned

**Unpublish a Card:**
Currently not supported (by design—cards are permanent once published).

**Edit After Publishing:**
Currently not supported. Make sure your card is polished before publishing.

**Future Feature:** In-place editing with version history.

---

## Session Management

Sessions help you organize voice notes by topic, project, or time period.

### Creating Sessions

**Method 1: Auto-Creation**
When you start a new recording, Writer auto-creates a session named by date: `2025-11-18`

**Method 2: Manual Creation**
1. Click **"New Session"** button
2. Enter session name (e.g., "Marketing Strategy," "Book Ideas," "Daily Journal")
3. Click **Create**

### Switching Sessions

1. Click **Sessions** dropdown in sidebar
2. Select session from list
3. All recordings/cards now belong to that session

### Organizing Sessions

**By Topic:**
```
Sessions:
- Marketing Strategy
- Product Ideas
- Personal Reflections
- Client Meetings
```

**By Project:**
```
Sessions:
- Project X Launch
- Website Redesign
- Course Creation
```

**By Date:**
```
Sessions:
- 2025-11-18
- 2025-11-17
- 2025-11-16
```

### Session Actions

**Rename Session:**
1. Right-click session in sidebar
2. Select "Rename"
3. Enter new name

**Delete Session:**
1. Right-click session in sidebar
2. Select "Delete"
3. Confirm deletion

**WARNING:** Deleting a session deletes all cards within it. This action cannot be undone.

**Export Session:**
1. Right-click session in sidebar
2. Select "Export to Markdown"
3. Choose save location
4. All cards exported as `session-name-YYYY-MM-DD.md`

---

## Prompt Templates

Prompt templates are reusable AI prompts for common content creation tasks.

### Built-In Templates

Writer ships with these templates:

**1. Expand to Blog Post**
```
Expand this into a 750-word blog post with:
- SEO-friendly structure
- Clear introduction with hook
- 3-5 main points with subheadings
- Actionable conclusion
```

**2. Extract Key Insights**
```
Extract 5-10 key insights from this transcription.
Format as a bulleted list with brief explanations.
```

**3. Turn into Tweets**
```
Convert this into 5 standalone tweets (280 chars each).
Each tweet should be self-contained and valuable.
```

**4. Create Course Outline**
```
Turn this into a mini-course outline with:
- 5 modules
- 3-5 lessons per module
- Learning objectives for each lesson
```

**5. Identify Gaps**
```
What questions remain unanswered in this content?
What should I explore or record next?
```

### Creating Custom Templates

1. Click **Settings > Prompt Templates**
2. Click **"New Template"**
3. Enter template details:
   - **Name**: "My Custom Template"
   - **Prompt**: Your reusable prompt text
   - **Description**: What this template does
4. Click **Save**

### Using Templates

**Step 1: Open AI Chat**
Click "Chat with AI" on any card.

**Step 2: Select Template**
Click **"Use Template"** dropdown, select template.

**Step 3: Run Prompt**
Template auto-fills chat input. Click **Send** to execute.

**Step 4: Save Response**
Click **"Save to Card"** to add AI output to card.

### Template Variables (Advanced)

Templates support variables for dynamic content:

```
Expand this into a {{word_count}}-word {{format}} about {{topic}}.
```

When using template, you'll be prompted to fill in:
- `word_count`: 500
- `format`: blog post
- `topic`: content marketing

**Result:**
```
Expand this into a 500-word blog post about content marketing.
```

---

## Export & Backup

Writer supports multiple export formats for portability and backup.

### Export Formats

**1. Markdown (Recommended)**
- **Format**: `.md` files
- **Use for**: Blogs, static sites, note apps
- **Preserves**: Structure, formatting, links
- **Command**: File > Export > Markdown

**2. JSON (Raw Data)**
- **Format**: `.json` files
- **Use for**: Data analysis, custom processing
- **Preserves**: All metadata, timestamps, privacy levels
- **Command**: File > Export > JSON

**3. SQLite Database**
- **Format**: `.db` file
- **Use for**: Full backup, migration
- **Preserves**: Everything (1:1 database copy)
- **Command**: File > Export > Database Backup

### Exporting All Cards

**Step 1: Open Export Dialog**
Click **File > Export All Cards**

**Step 2: Choose Format**
Select export format (Markdown, JSON, or SQLite)

**Step 3: Choose Location**
Select destination folder

**Step 4: Export**
Click **Export** button

**Output:**
```
exported-cards-2025-11-18/
├── business-strategy-idea-a1b2c3d4.md
├── content-creation-workflow-e5f6g7h8.md
├── marketing-insights-i9j0k1l2.md
└── metadata.json
```

### Exporting Single Session

1. Right-click session in sidebar
2. Select "Export to Markdown"
3. Choose save location
4. Session exported as single file with all cards

### Backup Strategy

**Recommended Backup Workflow:**

**Daily Automatic Backup:**
```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

**backup-script.sh:**
```bash
#!/bin/bash
BACKUP_DIR="$HOME/Backups/BrainDump"
DATE=$(date +%Y-%m-%d)

# Export database
cp ~/Library/Application\ Support/com.extrophi.braindump/db.sqlite \
   "$BACKUP_DIR/db-$DATE.sqlite"

# Export as markdown
cd ~/extrophi-ecosystem/writer
npm run export -- --output "$BACKUP_DIR/markdown-$DATE"

# Keep last 30 days only
find "$BACKUP_DIR" -name "*.sqlite" -mtime +30 -delete
```

**Cloud Backup (Manual):**
If you use cloud storage (Dropbox, iCloud, etc.), export to a synced folder:

```bash
# Export to Dropbox
npm run export -- --output ~/Dropbox/BrainDump/exports
```

⚠️ **Privacy Warning:** Cloud storage means your data leaves your machine. Only export BUSINESS/IDEAS cards to cloud.

---

## Advanced Features

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+R` | Start/stop recording |
| `Cmd+N` | New session |
| `Cmd+K` | Open AI chat |
| `Cmd+E` | Export current card |
| `Cmd+P` | Publish current card |
| `Cmd+,` | Open settings |
| `Cmd+F` | Search cards |
| `Cmd+/` | Show keyboard shortcuts |

### Search and Filter

**Full-Text Search:**
1. Click search box (or press `Cmd+F`)
2. Type query
3. Results filter in real-time

**Search Tips:**
- Search by content, title, or tags
- Use quotes for exact phrases: `"content marketing"`
- Filter by privacy level: `privacy:BUSINESS`
- Filter by date: `date:2025-11-18`

**Advanced Filters:**
```
# Multiple filters
privacy:BUSINESS tag:marketing date:2025-11

# Exclude terms
marketing -twitter

# Date ranges
date:2025-11-01..2025-11-30
```

### Vim Mode (For Developers)

Writer includes Vim keybindings for the markdown editor.

**Enable Vim Mode:**
1. Settings > Editor > Enable Vim Mode
2. Restart Writer

**Basic Vim Commands:**
- `i` - Insert mode
- `Esc` - Normal mode
- `dd` - Delete line
- `yy` - Yank (copy) line
- `/` - Search
- `:w` - Save

### Accessibility Features

**Voice Feedback:**
- Enable in Settings > Accessibility
- Announces recording status, transcription complete, publish success

**High Contrast Mode:**
- Enable in Settings > Appearance > High Contrast
- Better visibility for low vision users

**Font Scaling:**
- Settings > Appearance > Font Size
- 12px to 24px (default: 16px)

---

## Workflow Examples

### Content Creator Workflow

**Goal:** Turn voice notes into blog posts, tweets, and course content.

**Workflow:**
1. **Morning Brain Dump** (10 min)
   - Record 5-10 voice notes about ideas, observations, insights
   - Set privacy: THOUGHTS (not yet ready to publish)

2. **Review and Refine** (20 min)
   - Review transcriptions
   - Pick 2-3 best ideas
   - Ask AI: "Expand this into a blog post"
   - Edit AI output

3. **Publish Best Content** (5 min)
   - Change privacy to BUSINESS
   - Click "Publish"
   - Earn $EXTROPY tokens

4. **Repurpose for Social** (10 min)
   - Ask AI: "Turn this into 5 tweets"
   - Copy tweets to Twitter
   - Link back to published card

**Time:** 45 min/day
**Output:** 2-3 blog posts, 10-15 tweets, ongoing course content

### Solo Founder Workflow

**Goal:** Capture strategic thinking, document decisions, track progress.

**Workflow:**
1. **Weekly Strategy Session** (30 min)
   - Create session: "Strategy 2025-W47"
   - Record strategic thoughts about business
   - Privacy: BUSINESS (share publicly for accountability)

2. **Daily Standup** (5 min)
   - Record what you shipped yesterday
   - Record what you're shipping today
   - Record blockers
   - Privacy: PERSONAL (private journal)

3. **Client Call Notes** (5 min after each call)
   - Record key takeaways immediately after client calls
   - Privacy: PERSONAL (contains client info)

4. **Publish Learnings** (Weekly)
   - Review personal notes
   - Extract generalizable insights
   - Create new BUSINESS cards with public-safe content
   - Publish and share on social media

**Time:** 1 hour/week
**Output:** Weekly strategy posts, daily progress journal

### Knowledge Worker Workflow

**Goal:** Build a personal knowledge base, connect ideas.

**Workflow:**
1. **Capture Ideas Throughout Day**
   - Voice notes while walking, driving, or working
   - Don't worry about structure—just capture
   - Privacy: THOUGHTS

2. **Weekly Review** (1 hour)
   - Review all THOUGHTS from the week
   - Identify patterns, connections, recurring themes
   - Promote best ideas to IDEAS or BUSINESS

3. **Monthly Knowledge Graph** (2 hours)
   - Export all cards as markdown
   - Import into Obsidian or Notion
   - Create connections between related ideas
   - Publish "Best of Month" compilation

**Time:** 10-15 min/day capturing, 3 hours/month reviewing
**Output:** Personal knowledge base, monthly best-of posts

---

## Troubleshooting

### Recording Issues

**Problem: No audio detected**
- Check microphone permissions (System Settings > Privacy > Microphone)
- Test microphone in System Settings > Sound > Input
- Try restarting Writer

**Problem: Recording is silent/very quiet**
- Increase input volume in System Settings > Sound > Input
- Move closer to microphone
- Reduce background noise

**Problem: Recording cuts off early**
- Check microphone connection (for external mics)
- Restart Writer
- Check Console.app for audio errors

### Transcription Issues

**Problem: "Whisper library not found"**
```bash
# Reinstall whisper.cpp
brew reinstall whisper-cpp

# Verify installation
pkg-config --libs whisper

# Check library path
ls -l /opt/homebrew/lib/libwhisper.*
```

**Problem: "Model file not found"**
```bash
# Verify model exists
ls -lh ~/extrophi-models/ggml-base.bin

# Re-download if missing
curl -L -o ~/extrophi-models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

**Problem: Transcription is inaccurate**
- Try a larger model (ggml-small.bin or ggml-medium.bin)
- Speak more clearly and slowly
- Reduce background noise
- Use a better microphone

**Problem: Transcription is slow**
- Whisper uses your GPU (Metal on Apple Silicon)
- Check Activity Monitor for GPU usage
- Close other GPU-heavy apps
- Try smaller model (ggml-tiny.bin) for speed

### AI Chat Issues

**Problem: "Invalid API key"**
- Verify key in Settings
- Check key hasn't expired on OpenAI/Anthropic dashboard
- Re-enter key (copy-paste to avoid typos)

**Problem: "Rate limit exceeded"**
- You've hit OpenAI/Anthropic rate limits
- Wait 60 seconds and try again
- Upgrade to paid API plan for higher limits

**Problem: AI responses are cut off**
- Increase max tokens in Settings > AI
- Default: 1000 tokens (~750 words)
- Max: 4000 tokens (~3000 words)

### Publishing Issues

**Problem: "Cannot publish—privacy level is PERSONAL"**
- Only BUSINESS and IDEAS cards can be published
- Change privacy level to BUSINESS or IDEAS first
- Then click Publish

**Problem: "Failed to publish—network error"**
- Check internet connection
- Verify API endpoint is reachable: `curl https://api.extrophi.ai/health`
- Check firewall settings

**Problem: "Published URL returns 404"**
- Cards may take 1-2 minutes to propagate to CDN
- Wait and try again
- If persists >5 minutes, report bug on GitHub

### Database Issues

**Problem: "Database is locked"**
- Close all Writer instances
- Restart Writer
- If persists, manually delete lock file:
  ```bash
  rm ~/Library/Application\ Support/com.extrophi.braindump/db.sqlite-wal
  ```

**Problem: "Database is corrupted"**
- Restore from backup (see Export & Backup section)
- If no backup, try SQLite recovery:
  ```bash
  sqlite3 ~/Library/Application\ Support/com.extrophi.braindump/db.sqlite
  PRAGMA integrity_check;
  .exit
  ```

**Problem: "Lost all my cards after update"**
- Cards are stored in: `~/Library/Application Support/com.extrophi.braindump/`
- Check if database file exists: `ls -lh ~/Library/Application\ Support/com.extrophi.braindump/db.sqlite`
- If file exists but Writer doesn't show cards, report bug on GitHub

---

## Getting Help

**Documentation:**
- [Quickstart](./quickstart.md) - 5-minute setup guide
- [API Guide](./api-guide.md) - Programmatic access
- [Research Guide](./research-guide.md) - Content scraping and intelligence

**Community:**
- GitHub Issues: [github.com/extrophi/extrophi-ecosystem/issues](https://github.com/extrophi/extrophi-ecosystem/issues)
- Discussions: [github.com/extrophi/extrophi-ecosystem/discussions](https://github.com/extrophi/extrophi-ecosystem/discussions)

**Bug Reports:**
When reporting bugs, please include:
- macOS version
- Writer version
- Steps to reproduce
- Error messages (check Console.app)
- Screenshots if relevant

---

## Philosophy

Writer exists because sometimes you need to get thoughts out of your head and onto paper (or screen). No judgment. No features. No bullshit.

**Built for:**
- People who can't organize thoughts under stress
- Those with no one safe to talk to
- Anyone who needs privacy above everything else
- Content creators building in public

**Not built for:**
- Competition with existing products
- Maximum features or complexity
- Cloud-based convenience
- Monetization

**Just:** A working tool for people who need it.

---

**Built with care. Shipped with purpose. Privacy-first by design.**

🎤 Voice → 📝 Text → 🧠 AI → 🌍 Publish → 💰 Tokens
