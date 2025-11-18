# Lightweight Markdown Editor Research for BrainDump

**Date**: 2025-11-16
**Agent**: Omega
**Focus**: Privacy-first markdown editing for voice journaling application
**Stack Compatibility**: Tauri 2.0 + Svelte 5 + Rust

---

## Executive Summary

This research evaluates lightweight, privacy-first markdown editors to enhance BrainDump's voice-to-text workflow. The key finding is that **CodeMirror 6** combined with **marked.js** or **markdown-it** provides the optimal balance of performance, extensibility, and bundle size for BrainDump's Tauri + Svelte architecture.

**Top Recommendation**: CodeMirror 6 for editing + marked.js for parsing + local-first architecture with optional E2E encryption.

---

## Table of Contents

1. [Why Notion/Obsidian Are Heavy](#why-notionobsidian-are-heavy)
2. [JavaScript Markdown Library Comparison](#javascript-markdown-library-comparison)
3. [Editor Framework Comparison](#editor-framework-comparison)
4. [Privacy-First Architecture Patterns](#privacy-first-architecture-patterns)
5. [Voice-to-Markdown Workflows](#voice-to-markdown-workflows)
6. [Open Source Editors to Study](#open-source-editors-to-study)
7. [Feature Requirements for BrainDump](#feature-requirements-for-braindump)
8. [Recommended Stack](#recommended-stack)
9. [Implementation Roadmap](#implementation-roadmap)
10. [GitHub Repositories to Study](#github-repositories-to-study)

---

## 1. Why Notion/Obsidian Are Heavy

### Notion Pain Points
- **Requires internet connection** for most operations
- **Slow performance** with extensive data
- **Cloud-dependent architecture** - user doesn't own data
- **Complex feature set** with significant overhead
- **No offline-first design** - server is source of truth

### Obsidian Trade-offs
- **Plugin ecosystem bloat** - hundreds of plugins lead to complexity
- **Steep learning curve** for workflow optimization
- **Memory overhead** from Electron runtime (~150-200MB base)
- **Chromium bundling** increases app size significantly
- **Not fully open source** (core is proprietary)

### BrainDump Advantages (Tauri Stack)
| Feature | Electron (Obsidian) | Tauri (BrainDump) |
|---------|--------------------|--------------------|
| Bundle Size | 150-200MB | 3-10MB |
| Memory Usage | Full Chromium | Native WebView |
| Startup Time | 2-5 seconds | <1 second |
| Security | Same-process model | Rust sandboxing |
| Backend Speed | Node.js | Native Rust |

---

## 2. JavaScript Markdown Library Comparison

### Performance Matrix

| Library | Bundle Size | Speed | Extensibility | Best For |
|---------|-------------|-------|---------------|----------|
| **marked.js** | ~40KB min | Fastest | Limited | Simple rendering, speed-critical |
| **markdown-it** | ~60KB min | Very Fast | Excellent plugins | Balanced performance + features |
| **remark/rehype** | ~100KB+ | Slower | Maximum (AST) | Complex transformations |
| **showdown** | ~50KB | Fast | Moderate | Simple projects |
| **remarkable** | ~45KB | Fastest (benchmarks) | Good | Performance-focused |

### Detailed Analysis

#### marked.js
```javascript
// Installation: npm install marked (3.5M weekly downloads)
import { marked } from 'marked';
const html = marked.parse('# Hello World');
```
**Pros:**
- Fastest parser with low memory footprint
- Simple API, easy integration
- Well-maintained, large community

**Cons:**
- Less extensible than markdown-it
- No AST access for transformations
- Limited plugin ecosystem

**Use When:** Speed is critical, simple markdown needs

#### markdown-it
```javascript
// Installation: npm install markdown-it
import MarkdownIt from 'markdown-it';
const md = new MarkdownIt();
const html = md.render('# Hello World');
```
**Pros:**
- Streaming approach for large documents
- Excellent plugin system (tables, footnotes, custom syntax)
- Good balance of speed and features

**Cons:**
- Slightly larger than marked.js
- More complex configuration

**Use When:** Need extensibility without sacrificing too much speed

#### remark/rehype (unified ecosystem)
```javascript
// Installation: npm install remark remark-html
import { remark } from 'remark';
import remarkHtml from 'remark-html';

const result = await remark()
  .use(remarkHtml)
  .process('# Hello World');
```
**Pros:**
- Full AST access and manipulation
- Massive plugin ecosystem (200+ plugins)
- Best for complex transformations
- Syntax tree enables advanced features

**Cons:**
- Slower due to AST processing
- Larger bundle size
- Steeper learning curve

**Use When:** Complex processing, content transformations, academic writing

### Recommendation for BrainDump

**Primary: markdown-it**
- Balance of performance and extensibility
- Plugin support for future features (tables, checklists, math)
- Stream processing handles transcripts well

**Alternative: marked.js**
- If bundle size is critical constraint
- Simpler implementation for MVP

---

## 3. Editor Framework Comparison

### Core Editor Frameworks

| Framework | Type | Size (min+gzip) | Mobile Support | Learning Curve |
|-----------|------|-----------------|----------------|----------------|
| **CodeMirror 6** | Code/Text Editor | ~300KB modular | Excellent | Moderate |
| **ProseMirror** | Rich Text | ~200KB | Good | High |
| **Monaco** | Code Editor (VS Code) | 5-10MB | Poor | Low |
| **Milkdown** | WYSIWYG Markdown | ~40KB | Good | Low |
| **Tiptap** | Rich Text (ProseMirror) | ~100KB+ | Good | Moderate |

### CodeMirror 6 - TOP RECOMMENDATION

```javascript
// Installation: npm install @codemirror/view @codemirror/state @codemirror/lang-markdown
import { EditorView, basicSetup } from 'codemirror';
import { markdown } from '@codemirror/lang-markdown';

const view = new EditorView({
  extensions: [basicSetup, markdown()],
  parent: document.body
});
```

**Why CodeMirror 6 for BrainDump:**
- **Modular architecture** - only load what you need
- **Best mobile support** - 70% retention increase at Replit
- **Efficient data structures** - tree-based document, viewport rendering
- **No performance cliffs** - handles gigantic documents
- **Same author as ProseMirror** - proven expertise
- **TypeScript support** - type safety
- **Svelte compatible** - easy integration

**Features:**
- Syntax highlighting for markdown
- Auto-indentation and formatting
- Search and replace
- Multiple selections
- Vim/Emacs keybindings optional
- Customizable themes
- Accessibility support

### ProseMirror - Rich Text Alternative

**Use Case:** If WYSIWYG markdown editing is required (like Typora)

```javascript
// More complex setup for rich-text behavior
import { EditorState } from 'prosemirror-state';
import { EditorView } from 'prosemirror-view';
import { schema } from 'prosemirror-schema-basic';
```

**Pros:**
- Collaborative editing support
- Schema-based content model
- Transaction-based state updates

**Cons:**
- Higher complexity
- Steeper learning curve
- More boilerplate code

### Milkdown - WYSIWYG Markdown

**Use Case:** If Typora-like experience is desired

```javascript
import { Editor } from '@milkdown/core';
import { commonmark } from '@milkdown/preset-commonmark';

Editor.make()
  .use(commonmark)
  .create();
```

**Pros:**
- Plugin-driven architecture
- Built on ProseMirror + Remark
- Headless and customizable
- 40KB gzipped
- Y.js collaboration support

**Cons:**
- Newer, smaller community
- May have edge cases
- Opinionated design

### Monaco Editor - NOT RECOMMENDED

**Why Not:**
- 5-10MB bundle size (Sourcegraph measured 6MB)
- Optimized for code editing, not prose
- Poor mobile support
- Overkill for markdown

### Recommendation for BrainDump

**MVP Phase: CodeMirror 6**
- Lightweight, fast, mobile-friendly
- Built-in markdown language support
- Gradual enhancement path
- Active development and community

**Future Consideration: Milkdown**
- If users demand WYSIWYG editing
- Plugin system for advanced features
- Still lightweight enough for Tauri

---

## 4. Privacy-First Architecture Patterns

### Core Principles

1. **Local-First Storage**
   - Primary data on user's device
   - User owns all data
   - Works offline by default
   - Optional sync is secondary

2. **Data Ownership**
   - Plain text files (markdown)
   - Standard formats (no vendor lock-in)
   - Export/import capabilities
   - User controls sharing

3. **Optional End-to-End Encryption**
   - Encrypt at rest
   - Key derived from user password
   - Never send plaintext to servers

### Local-First Software Ideals (Ink & Switch Research)

Seven key properties of local-first software:
1. **No spinners** - instant access to data
2. **Works offline** - network optional
3. **Long-term preservation** - files exist forever
4. **Secure and private** - user controls access
5. **Collaboration** - optional, user-initiated
6. **Multi-device** - sync when wanted
7. **Data ownership** - user is in control

### BrainDump Privacy Architecture

```
┌─────────────────────────────────────────────────┐
│                LOCAL STORAGE                     │
├─────────────────────────────────────────────────┤
│  Markdown Files: ~/BrainDump/journals/          │
│  SQLite Database: ~/BrainDump/metadata.db       │
│  Audio Files: ~/BrainDump/recordings/ (optional)│
│  Encryption Keys: macOS Keychain / OS Keystore  │
└─────────────────────────────────────────────────┘
                      │
                      ▼ (Optional)
┌─────────────────────────────────────────────────┐
│           OPTIONAL E2E ENCRYPTED SYNC           │
├─────────────────────────────────────────────────┤
│  Pattern: AES-256-GCM + RSA-2048 key exchange  │
│  Keys: Generated locally, never leave device    │
│  Sync: Encrypted blobs only                    │
│  Conflict: CRDTs for resolution                │
└─────────────────────────────────────────────────┘
```

### E2E Encryption Implementation Pattern

```rust
// Rust backend encryption (recommended for BrainDump)
use ring::{aead, pbkdf2};

fn encrypt_note(plaintext: &[u8], password: &str) -> Result<Vec<u8>> {
    // 1. Derive key from password
    let salt = generate_salt();
    let mut key = [0u8; 32];
    pbkdf2::derive(
        pbkdf2::PBKDF2_HMAC_SHA256,
        NonZeroU32::new(100_000).unwrap(),
        &salt,
        password.as_bytes(),
        &mut key,
    );

    // 2. Generate nonce
    let nonce = generate_nonce();

    // 3. Encrypt with AES-256-GCM
    let cipher = aead::UnboundKey::new(&aead::AES_256_GCM, &key)?;
    let encrypted = seal_in_place(&cipher, &nonce, plaintext)?;

    // 4. Return salt + nonce + ciphertext
    Ok([salt, nonce, encrypted].concat())
}
```

### Data Format Recommendation

```markdown
<!-- ~/BrainDump/journals/2025-11-16_brain_dump.md -->
---
created: 2025-11-16T14:30:00Z
modified: 2025-11-16T14:35:00Z
tags: [reflection, work, ideas]
encrypted: false
audio_source: recordings/2025-11-16_143000.wav
---

# Brain Dump - November 16, 2025

## Transcription
[Auto-generated from voice recording]

Today I want to talk about...

## AI Analysis
[Optional: Claude/OpenAI insights]

Key themes identified:
- Theme 1
- Theme 2

## My Notes
[User additions]
```

### Privacy Scanner Enhancement

Current BrainDump has basic regex PII detection. Enhanced version:

```javascript
// src/lib/privacy_scanner.js - Enhanced
const PATTERNS = [
    // Existing patterns...
    { regex: /\b\d{3}-\d{2}-\d{4}\b/g, type: 'ssn', severity: 'danger' },

    // Add: Location detection
    { regex: /\b(my address is|I live at|located at)\b.{0,100}/gi,
      type: 'location', severity: 'warning' },

    // Add: Financial info
    { regex: /\$\d{1,3}(,\d{3})*(\.\d{2})?/g,
      type: 'financial', severity: 'info' },

    // Add: Health info (HIPAA)
    { regex: /\b(diagnosed with|medication|prescription|doctor)\b.{0,50}/gi,
      type: 'health', severity: 'warning' }
];

export function scanAndRedact(text, autoRedact = false) {
    const findings = scanText(text);
    if (autoRedact) {
        findings.forEach(f => {
            text = text.replace(f.value, `[REDACTED:${f.type}]`);
        });
    }
    return { text, findings };
}
```

---

## 5. Voice-to-Markdown Workflows

### Current BrainDump Flow

```
Record Audio → Whisper.cpp FFI → Raw Transcript → Chat Session
```

### Enhanced Voice-to-Markdown Flow

```
Record Audio
    │
    ▼
Whisper.cpp Transcription (with timestamps)
    │
    ▼
Auto-Formatting Pipeline
├─ Detect sentence boundaries
├─ Identify paragraph breaks (long pauses)
├─ Apply markdown structure
├─ Insert timestamp markers
└─ Detect speaker changes (diarization - future)
    │
    ▼
Template Application
├─ Brain Dump template
├─ Meeting Notes template
├─ Daily Reflection template
└─ Custom templates
    │
    ▼
Privacy Scan
├─ Highlight PII
├─ Suggest redactions
└─ Warn before AI processing
    │
    ▼
Markdown Note Created
├─ Frontmatter metadata
├─ Structured content
├─ Ready for editing
└─ Optional AI analysis
```

### Auto-Formatting Transcript to Markdown

```javascript
// src/lib/transcript_formatter.js
export function formatTranscript(rawText, timestamps = []) {
    let markdown = '';
    let currentParagraph = '';

    const sentences = rawText.split(/(?<=[.!?])\s+/);

    sentences.forEach((sentence, i) => {
        // Add timestamp marker for each segment
        if (timestamps[i]) {
            const time = formatTimestamp(timestamps[i]);
            markdown += `\n[${time}] `;
        }

        // Detect section breaks (keywords)
        if (/^(first|next|finally|another thing|also|however)/i.test(sentence)) {
            if (currentParagraph) {
                markdown += currentParagraph + '\n\n';
                currentParagraph = '';
            }
        }

        currentParagraph += sentence + ' ';

        // Paragraph break after 3-4 sentences
        if (currentParagraph.split(/[.!?]/).length > 4) {
            markdown += currentParagraph.trim() + '\n\n';
            currentParagraph = '';
        }
    });

    if (currentParagraph) {
        markdown += currentParagraph.trim();
    }

    return markdown;
}

function formatTimestamp(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
```

### WhisperX Integration (Future Enhancement)

WhisperX provides word-level timestamps and speaker diarization:

```bash
# Install WhisperX
pip install whisperx

# Transcribe with diarization
whisperx audio.wav --model base --diarize --highlight_words True
```

Output structure:
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 4.5,
      "text": "Today I want to talk about...",
      "speaker": "SPEAKER_0",
      "words": [
        {"word": "Today", "start": 0.0, "end": 0.3},
        {"word": "I", "start": 0.4, "end": 0.5}
        // ...
      ]
    }
  ]
}
```

### Template System for BrainDump

```javascript
// src/lib/templates.js
export const TEMPLATES = {
    brain_dump: {
        name: 'Brain Dump',
        frontmatter: {
            type: 'brain_dump',
            mood: '{{user_input}}',
            energy: '{{user_input}}'
        },
        structure: `
# Brain Dump - {{date}}

## Raw Thoughts
{{transcript}}

## Key Insights
-

## Action Items
- [ ]

## Reflection
_What patterns do I notice?_

`
    },

    meeting_notes: {
        name: 'Meeting Notes',
        frontmatter: {
            type: 'meeting',
            attendees: '{{user_input}}',
            project: '{{user_input}}'
        },
        structure: `
# Meeting: {{title}} - {{date}}

## Attendees
-

## Agenda
1.

## Discussion
{{transcript}}

## Decisions Made
-

## Action Items
- [ ]

## Next Steps

`
    },

    daily_reflection: {
        name: 'Daily Reflection',
        structure: `
# Daily Reflection - {{date}}

## What went well today?
{{transcript}}

## What could be improved?


## Gratitude
1.
2.
3.

## Tomorrow's Focus

`
    }
};
```

### Voice Command Integration (Future)

Pattern from MarkdownViewer app:

```javascript
// Keyword detection during transcription
const VOICE_COMMANDS = {
    'new header': () => insertMarkdown('## '),
    'bullet point': () => insertMarkdown('- '),
    'action item': () => insertMarkdown('- [ ] '),
    'new paragraph': () => insertMarkdown('\n\n'),
    'make it bold': () => wrapSelection('**'),
    'highlight this': () => wrapSelection('==')
};

function processVoiceCommands(transcript) {
    let processed = transcript;
    Object.entries(VOICE_COMMANDS).forEach(([phrase, action]) => {
        if (processed.includes(phrase)) {
            action();
            processed = processed.replace(phrase, '');
        }
    });
    return processed;
}
```

---

## 6. Open Source Editors to Study

### Mark Text - WYSIWYG Markdown

**GitHub**: https://github.com/marktext/marktext (45k stars)
**Status**: Unmaintained since July 2022
**Fork**: https://github.com/jacobwhall/marktext

**Architecture:**
- Electron-based
- Custom WYSIWYG rendering
- Typora-like inline preview
- Source view available

**Learn From:**
- WYSIWYG markdown rendering approach
- Theme system
- Export functionality (HTML, PDF)

**Caution:** Not maintained, potential security issues

### Zettlr - Academic Markdown Editor

**GitHub**: https://github.com/Zettlr/Zettlr (10k stars)
**Status**: Actively maintained

**Architecture:**
- Electron Forge + TypeScript
- CodeMirror 6 for editing (migrated from v5)
- Webpack bundling
- Node 22 required

**Key Features:**
- Zettelkasten (wiki links)
- Citation management
- LaTeX math support
- Bibliography integration
- File linking across notes
- Academic writing focus

**Learn From:**
- Electron Forge setup
- CodeMirror 6 integration
- File system management
- Project/workspace architecture
- Citation/reference system

### Joplin - Privacy-First Notes

**GitHub**: https://github.com/laurent22/joplin (45k stars)
**Status**: Very actively maintained

**Architecture:**
- React Native (mobile) + Electron (desktop)
- SQLite database
- E2E encryption
- Multiple sync backends

**Key Features:**
- End-to-end encryption
- Sync to Nextcloud/S3/WebDAV/Dropbox
- Web clipper
- Note history
- Search functionality

**Learn From:**
- E2E encryption implementation
- Sync backend abstraction
- Cross-platform architecture
- Database migration patterns

### Obsidian - Local-First Knowledge Base

**Status**: Proprietary, not open source
**Architecture**: Electron + Custom engine

**Learn From:** (via documentation/usage)
- Plugin system design
- Graph view concept
- Backlink implementation
- Workspace management
- Settings persistence

### Logseq - Outliner + Knowledge Graph

**GitHub**: https://github.com/logseq/logseq (31k stars)
**Status**: Actively maintained

**Architecture:**
- ClojureScript + Datascript
- Block-based editing
- Local-first with P2P sync

**Learn From:**
- Block-based data model
- Graph database for notes
- Outliner UX patterns

### Notable - Markdown Note-Taking

**GitHub**: https://github.com/notable/notable (22k stars)
**Status**: Limited maintenance

**Architecture:**
- Electron + React
- File-based storage
- Multi-note management

**Learn From:**
- Tagging system
- Multi-note selection
- Attachment handling

### SilverBullet - Self-Hosted Wiki

**GitHub**: https://github.com/silverbulletmd/silverbullet (4k stars)
**Status**: Actively maintained

**Architecture:**
- Deno backend
- Plain text files
- Plugin system via JavaScript

**Learn From:**
- Plugin architecture
- Self-hosting patterns
- Template system

---

## 7. Feature Requirements for BrainDump

### Essential Features (MVP)

| Feature | Priority | Complexity | Library/Tool |
|---------|----------|------------|--------------|
| Markdown editing | P0 | Medium | CodeMirror 6 |
| Syntax highlighting | P0 | Low | @codemirror/lang-markdown |
| Auto-save | P0 | Low | Custom (debounced) |
| Basic formatting toolbar | P0 | Medium | Custom Svelte |
| File export (md, txt) | P0 | Low | Native file API |
| Transcript formatting | P1 | Medium | Custom parser |
| Template insertion | P1 | Medium | Template system |
| Privacy scanning | P1 | Low | Enhanced regex |
| Search within note | P1 | Low | CodeMirror search |
| Undo/Redo | P1 | Low | CodeMirror built-in |

### Enhanced Features (v1.0)

| Feature | Priority | Complexity | Library/Tool |
|---------|----------|------------|--------------|
| Full-text search | P2 | Medium | SQLite FTS5 |
| Note linking | P2 | High | Custom wiki-link syntax |
| Tag management | P2 | Medium | Database + UI |
| Export to PDF | P2 | Medium | Rust PDF lib |
| Word count/statistics | P2 | Low | Custom calculation |
| Multiple themes | P2 | Low | CSS variables |
| Keyboard shortcuts | P2 | Low | CodeMirror keymaps |
| Split view (edit/preview) | P2 | Medium | Dual CodeMirror instances |

### Advanced Features (Future)

| Feature | Priority | Complexity | Library/Tool |
|---------|----------|------------|--------------|
| E2E encryption | P3 | High | Rust crypto (ring) |
| WYSIWYG mode | P3 | High | Milkdown or ProseMirror |
| Graph view | P3 | High | D3.js or similar |
| Sync (optional) | P3 | Very High | CRDTs (automerge) |
| Speaker diarization | P3 | High | WhisperX integration |
| Voice commands | P3 | Medium | Custom parser |
| Plugin system | P4 | Very High | Custom architecture |
| Collaborative editing | P4 | Very High | Y.js + server |

---

## 8. Recommended Stack

### Primary Recommendation

```
┌─────────────────────────────────────────────────┐
│              BRAINDUMP MARKDOWN STACK            │
├─────────────────────────────────────────────────┤
│                                                  │
│  EDITOR: CodeMirror 6                           │
│  ├─ @codemirror/view                            │
│  ├─ @codemirror/state                           │
│  ├─ @codemirror/lang-markdown                   │
│  ├─ @codemirror/search                          │
│  └─ Custom themes (CSS)                         │
│                                                  │
│  PARSER: markdown-it                            │
│  ├─ markdown-it-footnote (future)               │
│  ├─ markdown-it-task-lists (checklists)         │
│  └─ Custom plugins as needed                    │
│                                                  │
│  STORAGE: Local File System                     │
│  ├─ Plain .md files                             │
│  ├─ YAML frontmatter                            │
│  ├─ SQLite for metadata/search index            │
│  └─ macOS Keychain for sensitive data           │
│                                                  │
│  UI FRAMEWORK: Svelte 5                         │
│  ├─ Custom toolbar component                    │
│  ├─ Template selector                           │
│  ├─ Privacy panel (enhanced)                    │
│  └─ File browser sidebar                        │
│                                                  │
│  BACKEND: Tauri 2.0 + Rust                      │
│  ├─ File system operations                      │
│  ├─ SQLite via rusqlite                         │
│  ├─ Optional encryption (ring crate)            │
│  └─ Whisper.cpp FFI (existing)                  │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Bundle Size Estimate

| Component | Size (min+gzip) | Notes |
|-----------|-----------------|-------|
| CodeMirror 6 core | ~100KB | Modular, load needed |
| CodeMirror markdown | ~50KB | Syntax support |
| markdown-it | ~30KB | Parsing |
| Svelte runtime | ~5KB | Compiler advantage |
| Custom components | ~20KB | Estimate |
| **Total Frontend** | **~205KB** | Very lightweight |

Compare to:
- Electron apps: 150-200MB
- Monaco Editor alone: 5-10MB
- Obsidian: 400MB+ with plugins

### Performance Targets

| Metric | Target | Approach |
|--------|--------|----------|
| App startup | <1 second | Tauri + Svelte efficiency |
| Note opening | <100ms | Lazy loading, efficient parsing |
| Typing latency | <16ms | CodeMirror optimized rendering |
| Large note (10k words) | No degradation | Viewport rendering |
| Search (1000 notes) | <200ms | SQLite FTS5 index |
| Privacy scan | <50ms | Optimized regex |

---

## 9. Implementation Roadmap

### Phase 1: Basic Markdown Editor (Week 1-2)

**Goal**: Replace basic textarea with CodeMirror 6

```svelte
<!-- src/components/MarkdownEditor.svelte -->
<script>
    import { onMount, onDestroy } from 'svelte';
    import { EditorView, basicSetup } from 'codemirror';
    import { markdown } from '@codemirror/lang-markdown';
    import { EditorState } from '@codemirror/state';

    let { content = $bindable(''), onSave } = $props();
    let editorContainer;
    let view;

    onMount(() => {
        const state = EditorState.create({
            doc: content,
            extensions: [
                basicSetup,
                markdown(),
                EditorView.updateListener.of(update => {
                    if (update.docChanged) {
                        content = update.state.doc.toString();
                    }
                })
            ]
        });

        view = new EditorView({
            state,
            parent: editorContainer
        });
    });

    onDestroy(() => {
        view?.destroy();
    });
</script>

<div class="editor-wrapper" bind:this={editorContainer}></div>

<style>
    .editor-wrapper {
        height: 100%;
        font-family: 'JetBrains Mono', monospace;
    }

    :global(.cm-editor) {
        height: 100%;
    }
</style>
```

**Tasks:**
1. Install CodeMirror 6 dependencies
2. Create MarkdownEditor Svelte component
3. Add basic toolbar (bold, italic, headers)
4. Implement auto-save with debouncing
5. Add keyboard shortcuts

### Phase 2: Transcript Integration (Week 3-4)

**Goal**: Auto-format Whisper transcripts into structured markdown

**Tasks:**
1. Create transcript formatting pipeline
2. Implement template system
3. Add timestamp markers (if available from Whisper)
4. Integrate with existing recording flow
5. Frontmatter generation

### Phase 3: File Management (Week 5-6)

**Goal**: Save/load markdown files with proper organization

**Tasks:**
1. Create file browser sidebar component
2. Implement save/load commands in Rust
3. Set up directory structure (~/BrainDump/journals/)
4. Add YAML frontmatter parsing
5. Implement note metadata tracking in SQLite

### Phase 4: Enhanced Features (Week 7-8)

**Goal**: Search, tags, and export

**Tasks:**
1. Full-text search with SQLite FTS5
2. Tag management system
3. Export to PDF/HTML
4. Multiple themes
5. Statistics (word count, etc.)

### Phase 5: Privacy & Security (Week 9-10)

**Goal**: Enhanced privacy features

**Tasks:**
1. Improve PII detection patterns
2. Add auto-redaction option
3. Implement optional E2E encryption
4. Secure key derivation
5. Encrypted export option

---

## 10. GitHub Repositories to Study

### Must Study

1. **Zettlr** - https://github.com/Zettlr/Zettlr
   - CodeMirror 6 integration
   - Electron Forge setup
   - TypeScript architecture
   - Academic features

2. **Joplin** - https://github.com/laurent22/joplin
   - E2E encryption
   - Sync implementation
   - SQLite patterns
   - Cross-platform

3. **Milkdown** - https://github.com/Milkdown/milkdown
   - Plugin architecture
   - WYSIWYG markdown
   - ProseMirror + Remark

4. **SilverBullet** - https://github.com/silverbulletmd/silverbullet
   - Template system
   - Plugin architecture
   - Self-hosting

### Worth Reviewing

5. **Tiptap** - https://github.com/ueberdosis/tiptap
   - Headless rich text
   - Framework agnostic
   - Extension system

6. **Logseq** - https://github.com/logseq/logseq
   - Block-based editing
   - Graph view
   - Local-first

7. **Ink & Switch Research** - https://github.com/inkandswitch
   - Local-first principles
   - CRDT implementations
   - Privacy-first design

8. **v2md** - https://v2md.app/
   - Voice-to-markdown
   - Obsidian integration
   - Template system

### Code Examples to Extract

9. **CodeMirror 6 Examples** - https://codemirror.net/examples/
   - All official examples
   - Configuration patterns
   - Extension development

10. **markdown-it Plugins** - https://github.com/markdown-it/markdown-it#plugins-list
    - Plugin architecture
    - Custom syntax
    - Extension patterns

---

## Conclusion

### Key Takeaways

1. **CodeMirror 6 is the optimal editor** for BrainDump
   - Lightweight, modular, mobile-friendly
   - Perfect match for Tauri + Svelte
   - Active development and community

2. **markdown-it provides best parsing balance**
   - Fast enough for real-time
   - Extensible for future features
   - Smaller than remark ecosystem

3. **Local-first is achievable**
   - Plain markdown files = user ownership
   - SQLite for metadata = fast search
   - Optional encryption = enhanced privacy

4. **Voice-to-markdown workflow is unique differentiator**
   - Auto-formatting transcripts
   - Template system
   - Privacy scanning
   - Not offered by existing tools

5. **Tauri advantage is significant**
   - 50x smaller than Electron apps
   - Better performance
   - Enhanced security
   - Perfect for privacy-first app

### Next Steps

1. **Immediate**: Install CodeMirror 6 and create basic editor component
2. **Short-term**: Implement transcript auto-formatting pipeline
3. **Medium-term**: Build file management and search features
4. **Long-term**: Add optional encryption and advanced features

The recommended stack positions BrainDump as a **lightweight, privacy-first alternative** to heavy tools like Notion/Obsidian, with a **unique voice journaling focus** that differentiates it in the market.

---

**Report Generated**: 2025-11-16
**Research Duration**: Comprehensive web search analysis
**Confidence Level**: High - based on current industry standards and proven technologies
