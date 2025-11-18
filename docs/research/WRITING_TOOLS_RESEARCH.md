# Writing Enhancement Tools Research Report

**Date**: 2025-11-16
**Researcher**: Agent Eta2
**Purpose**: Evaluate writing improvement tools for voice-to-production workflows in BrainDump

---

## Executive Summary

This research evaluates writing enhancement tools suitable for transforming raw voice transcripts into polished prose. Key findings:

1. **No Hemingway API exists** - Must use open-source alternatives or reverse-engineer algorithms
2. **LanguageTool is the most comprehensive** open-source grammar checker (LGPL, self-hostable)
3. **Retext ecosystem** provides the most modular JavaScript solution with 15+ specialized plugins
4. **nlprule (Rust)** is ideal for native backend integration in Tauri apps
5. **Datamuse API** is free for thesaurus/synonym features (no API key required)

**Recommended Stack for BrainDump**:
- Frontend: retext + write-good + alex
- Backend: nlprule (Rust) for grammar checking
- API: Datamuse for synonyms, Free Dictionary API for definitions

---

## 1. Hemingway App Analysis

### Official Product

**Website**: https://hemingwayapp.com
**API Availability**: **No public API exists**
**Open Source**: **No** - proprietary JavaScript with obfuscated logic
**Pricing**: $19.99 one-time (desktop app) or free web version

### Core Algorithm (Reverse-Engineered)

The Hemingway algorithm was successfully reverse-engineered by Sam Williams (freeCodeCamp article). Key findings:

#### Readability Score Formula
```javascript
// Automated Readability Index variant
let level = Math.round(4.71 * (letters / words) + 0.5 * (words / sentences) - 21.43);
```

#### Detection Methods

| Feature | Method | Implementation |
|---------|--------|----------------|
| **Adverbs** | Regex + Exclusion List | Words ending in 'ly' minus non-adverbs (e.g., "family", "only") |
| **Passive Voice** | Pattern Matching | `[is|are|was|were|be|been|being] + [word ending in 'ed']` |
| **Hard Sentences** | Word Count + Level | > 14 words AND readability level 10-14 |
| **Very Hard Sentences** | Word Count + Level | > 14 words AND readability level 14+ |
| **Complex Words** | Dictionary Lookup | Words in predefined "complex words" list |

#### Color Coding System
- **Yellow**: Hard to read sentences
- **Red**: Very hard to read sentences
- **Purple**: Complex words with simpler alternatives
- **Blue**: Adverbs (weaken writing)
- **Green**: Passive voice constructions

### Open Source Clones

#### 1. hemingway-vscode
**GitHub**: https://github.com/iddl/hemingway-vscode
**Stack**: VSCode extension using retext-english + Unified ecosystem
**Quality**: High - leverages mature NLP infrastructure

#### 2. Proofreader
**GitHub**: https://github.com/kdzwinel/Proofreader
**Stack**: write-good + nodehun (spelling)
**Features**: Hemingway-like suggestions, spell checking
**Customization**: American/British English support

#### 3. Ernest
**GitHub**: https://github.com/Offroadcode/Ernest
**Stack**: React-based rich text editor
**Use Case**: Umbraco CMS backoffice integration
**Features**: Focus and clarity checking

#### 4. Minimal HTML/CSS/JS Implementation
**Source**: IndieWeb documentation
**Stack**: No frameworks, pure vanilla JavaScript
**Use Case**: Educational, understanding core algorithms

---

## 2. Grammar Checking Solutions

### LanguageTool (Recommended for Production)

**GitHub**: https://github.com/languagetool-org/languagetool
**License**: LGPL 2.1 (open source core)
**Languages**: 25+ (English, Spanish, French, German, etc.)

#### Architecture
```
┌─────────────────────┐
│  Client Extension   │  (closed source for most editors)
└──────────┬──────────┘
           │ HTTP/JSON
┌──────────▼──────────┐
│  LanguageTool API   │  (open source, self-hostable)
│   - Java backend    │
│   - Rules engine    │
│   - Spell checker   │
└─────────────────────┘
```

#### API Usage
```javascript
// Example HTTP request
fetch('https://api.languagetool.org/v2/check', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: `text=${encodeURIComponent(text)}&language=en-US`
})
.then(res => res.json())
.then(data => {
  data.matches.forEach(match => {
    console.log(match.message, match.replacements);
  });
});
```

#### Self-Hosting
```bash
# Docker deployment
docker pull silviof/docker-languagetool
docker run -d -p 8010:8010 silviof/docker-languagetool
```

**Advantages**:
- Most comprehensive rule set
- Active development (20+ years)
- Can be self-hosted for privacy
- N-gram data for context-aware corrections

**Disadvantages**:
- Java-based (heavyweight for desktop apps)
- Network dependency if using cloud API
- Extensions for editors are mostly closed source

### GrammarBot API
**Website**: https://grammarbot.io/
**Pricing**: Free tier available
**Limitation**: Rate limits apply, less comprehensive than LanguageTool

---

## 3. JavaScript/Node.js Libraries

### Primary Recommendation: Retext Ecosystem

**Core Package**: https://github.com/retextjs/retext
**Architecture**: Unified.js plugin system with natural language CST (Concrete Syntax Tree)
**License**: MIT

#### Plugin Library Comparison

| Plugin | Purpose | npm Weekly Downloads | Size |
|--------|---------|---------------------|------|
| `retext-readability` | Multiple readability algorithms | ~15K | 25KB |
| `retext-passive` | Passive voice detection | ~8K | 10KB |
| `retext-simplify` | Suggest simpler alternatives | ~6K | 50KB |
| `retext-equality` | Inclusive language checking | ~10K | 30KB |
| `retext-repeated-words` | Lexical illusion detection | ~3K | 5KB |
| `retext-profanities` | Filter inappropriate language | ~2K | 20KB |
| `retext-sentiment` | Analyze text sentiment | ~4K | 15KB |
| `retext-keywords` | Extract key terms | ~2K | 10KB |

#### Complete Integration Example

```javascript
import { unified } from 'unified';
import retextEnglish from 'retext-english';
import retextStringify from 'retext-stringify';
import retextReadability from 'retext-readability';
import retextPassive from 'retext-passive';
import retextSimplify from 'retext-simplify';
import retextEquality from 'retext-equality';

async function analyzeText(text) {
  const file = await unified()
    .use(retextEnglish)
    .use(retextReadability, {
      age: 18,           // Target audience age
      minWords: 5,       // Min words per sentence to check
      threshold: 4       // # of algorithms that must agree
    })
    .use(retextPassive)
    .use(retextSimplify)
    .use(retextEquality)
    .use(retextStringify)
    .process(text);

  return file.messages; // Array of warnings with line/column positions
}

// Example usage
const issues = await analyzeText('The report was completed by the team obviously.');
/*
Returns:
[
  { message: 'Passive voice', line: 1, column: 12 },
  { message: '"obviously" is potentially insensitive', line: 1, column: 45 }
]
*/
```

### write-good

**GitHub**: https://github.com/btford/write-good
**npm**: https://www.npmjs.com/package/write-good
**License**: MIT
**Philosophy**: "Naive linter" - simple but effective rules

#### Features Checked
- Passive voice
- Weasel words (very, extremely, significantly)
- Adverbs (especially -ly words)
- Lexical illusions (repeated words)
- "So" at sentence beginning
- "There is/are" constructions
- Clichés and overused phrases

#### Usage
```javascript
const writeGood = require('write-good');

const suggestions = writeGood('So the cat was stolen.', {
  passive: true,      // Check passive voice (default: true)
  illusion: true,     // Check word repetition
  so: true,           // Check "so" at start
  thereIs: true,      // Check "there is/are"
  weasel: true,       // Check weasel words
  adverb: true,       // Check adverbs
  tooWordy: true,     // Check wordy phrases
  cliches: true,      // Check clichés
  eprime: false       // E-Prime checking (experimental)
});

// Result:
[
  { index: 0, offset: 2, reason: '"So" adds no meaning' },
  { index: 11, offset: 10, reason: '"was stolen" may be passive voice' }
]
```

### alex

**Website**: https://alexjs.com/
**GitHub**: https://github.com/get-alex/alex
**Purpose**: Catch insensitive, inconsiderate writing
**License**: MIT

#### Example Catches
- Gendered terms: "fireman" → "firefighter"
- Ableist language: "crippled" → "person with a disability"
- Condescending: "obviously", "simply", "everyone knows"
- Intolerant: "master/slave" → "primary/replica"

```javascript
const alex = require('alex');

const result = alex('He is a garbage man working on the master server.');
/*
[
  { message: 'he may be insensitive, use "they", "it" instead' },
  { message: '"garbage man" may be insensitive, use "garbage collector"' },
  { message: '"master" / "slave" may be insensitive, use "primary"' }
]
*/
```

### Comparison Matrix: JavaScript Libraries

| Feature | retext | write-good | alex | textlint |
|---------|--------|------------|------|----------|
| **Passive voice** | Yes (plugin) | Yes | No | Yes (via rules) |
| **Readability score** | Yes (7 algorithms) | No | No | Yes (via rules) |
| **Inclusive language** | Yes (equality) | No | Primary focus | Yes (via rules) |
| **Customizable** | Highly | Moderate | Limited | Highly |
| **TypeScript** | Yes | No | Yes | Yes |
| **Bundle size** | Varies by plugin | 15KB | 50KB | Varies |
| **Real-time use** | Excellent | Excellent | Good | Good |
| **Markdown support** | Via remark-retext | No | Yes | Native |
| **ESM only** | Yes (v8+) | No (CJS) | Yes | Yes |

---

## 4. Rust Libraries (For Tauri Backend)

### nlprule (Primary Recommendation)

**GitHub**: https://github.com/bminixhofer/nlprule
**Crates.io**: https://crates.io/crates/nlprule
**License**: Apache 2.0
**Language Support**: English, German, Spanish

#### Key Features
- **Rule-based**: 1000+ grammar rules (derived from LanguageTool)
- **Fast**: Optimized Rust implementation
- **Low resource**: No neural network, minimal memory footprint
- **Pipeline**: Sentence segmentation → POS tagging → Lemmatization → Chunking → Grammar checking

#### Installation
```toml
# Cargo.toml
[dependencies]
nlprule = "0.6"
```

#### Usage Example
```rust
use nlprule::{Tokenizer, Rules};

// Load English language rules
let tokenizer = Tokenizer::new("en/en_tokenizer.bin")?;
let rules = Rules::new("en/en_rules.bin")?;

let text = "He was went to the store.";
let suggestions = rules.suggest(&text, &tokenizer);

for suggestion in suggestions {
    println!("{}: {}", suggestion.span(), suggestion.message());
    for replacement in suggestion.replacements() {
        println!("  Suggestion: {}", replacement);
    }
}
```

#### Binary Size Considerations
- Tokenizer: ~15MB
- Rules: ~25MB
- Total: ~40MB added to app bundle
- Can be downloaded on first run if size is concern

### Related Rust Tools Using nlprule

1. **prosemd** - Proofreading language server for Markdown
2. **cargo-spellcheck** - Documentation spell checking

### Other Rust NLP Libraries

| Library | Purpose | GitHub Stars | Use Case |
|---------|---------|-------------|----------|
| **rust-bert** | Transformer models | 2.5K | Advanced NLP, entity recognition |
| **whatlang-rs** | Language detection | 900 | Auto-detect transcript language |
| **rs-natural** | NLP utilities | 500 | Stemming, TF-IDF, distance algorithms |
| **rsnltk** | Python NLP wrapper | 200 | Access Python NLP in Rust |

---

## 5. Readability Algorithms

### Implemented in retext-readability

The package applies 7 different algorithms and flags text when a configurable threshold (default: 4) agree it's difficult:

#### 1. Flesch Reading Ease
```
Score = 206.835 - 1.015(words/sentences) - 84.6(syllables/words)

90-100: Very easy (5th grade)
60-70:  Standard (8th-9th grade)
0-30:   Very difficult (college graduate)
```

#### 2. Flesch-Kincaid Grade Level
```
Grade = 0.39(words/sentences) + 11.8(syllables/words) - 15.59
```
Returns US grade level (1-16+)

#### 3. Gunning Fog Index
```
Index = 0.4[(words/sentences) + 100(complex_words/words)]
```
Complex words = 3+ syllables (excluding proper nouns, compound words, -ed/-es/-ing endings)

#### 4. Automated Readability Index (ARI)
```
ARI = 4.71(characters/words) + 0.5(words/sentences) - 21.43
```
Used by Hemingway App

#### 5. Coleman-Liau Index
```
CLI = 0.0588L - 0.296S - 15.8
L = average letters per 100 words
S = average sentences per 100 words
```

#### 6. SMOG Index
```
SMOG = 1.0430 * sqrt(polysyllables * (30/sentences)) + 3.1291
```

#### 7. Dale-Chall Formula
```
Score = 0.1579(difficult_words/words*100) + 0.0496(words/sentences)
```
Uses list of 3,000 "easy words"

### JavaScript Implementation
```javascript
import { syllable } from 'syllable';
import { fleschKincaid } from 'flesch-kincaid';
import { gunningFog } from 'gunning-fog';

function calculateReadability(text) {
  const sentences = text.split(/[.!?]+/).length;
  const words = text.split(/\s+/).length;
  const syllables = text.split(/\s+/).reduce((sum, word) =>
    sum + syllable(word), 0);
  const characters = text.replace(/\s/g, '').length;

  return {
    fleschKincaid: fleschKincaid({ sentence: sentences, word: words, syllable: syllables }),
    ari: Math.round(4.71 * (characters / words) + 0.5 * (words / sentences) - 21.43),
    avgWordsPerSentence: words / sentences,
    avgSyllablesPerWord: syllables / words
  };
}
```

---

## 6. API Services (Thesaurus & Dictionary)

### Datamuse API (Free, No Key Required)

**Website**: https://www.datamuse.com/api/
**Rate Limit**: 100K queries/day
**Response**: JSON

#### Endpoints

```javascript
// Synonyms
fetch('https://api.datamuse.com/words?rel_syn=happy')
// Returns: [{"word":"cheerful","score":12000},{"word":"joyful","score":11000}...]

// Related words (broader concept)
fetch('https://api.datamuse.com/words?ml=writing+style')
// Returns words related to the concept

// Rhymes
fetch('https://api.datamuse.com/words?rel_rhy=mind')

// Words that often follow
fetch('https://api.datamuse.com/words?rel_bga=storm')

// Autocomplete
fetch('https://api.datamuse.com/sug?s=writ')
```

### Free Dictionary API

**Website**: https://dictionaryapi.dev/
**Cost**: Free, no API key
**Data Source**: Wiktionary

```javascript
fetch('https://api.dictionaryapi.dev/api/v2/entries/en/eloquent')
  .then(res => res.json())
  .then(data => {
    console.log(data[0].meanings[0].definitions[0].definition);
    console.log(data[0].phonetics[0].audio); // Audio pronunciation URL
  });
```

### WordsAPI (Paid, More Features)

**Website**: https://www.wordsapi.com/
**Pricing**: $10/month for 2,500 requests
**Features**:
- 150,000+ word definitions
- Part of speech
- Syllable count
- Pronunciation
- Usage examples
- Frequency data

---

## 7. Implementation Architecture for BrainDump

### Proposed Integration Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    BrainDump Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────┐      ┌──────────────────────────┐    │
│   │  Svelte Frontend │      │      Rust Backend        │    │
│   │                  │      │                          │    │
│   │  - Real-time     │ IPC  │  - nlprule grammar       │    │
│   │    highlights    │<────>│  - whisper.cpp (exists)  │    │
│   │  - Suggestions   │      │  - Database storage      │    │
│   │    sidebar       │      │                          │    │
│   │  - Score widget  │      └──────────────────────────┘    │
│   │                  │                                       │
│   │  JavaScript:     │      External APIs:                   │
│   │  - retext stack  │      - Datamuse (synonyms)           │
│   │  - write-good    │      - Dictionary API                │
│   │  - alex          │      - LanguageTool (optional)       │
│   └─────────────────┘                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: Frontend-Only Implementation (MVP)

Install core dependencies:
```bash
npm install retext retext-english retext-stringify \
  retext-readability retext-passive retext-simplify \
  write-good alex syllable flesch-kincaid
```

Create writing analyzer service:
```javascript
// src/lib/writing_analyzer.js

import { unified } from 'unified';
import retextEnglish from 'retext-english';
import retextPassive from 'retext-passive';
import retextSimplify from 'retext-simplify';
import retextReadability from 'retext-readability';
import retextStringify from 'retext-stringify';
import writeGood from 'write-good';
import alex from 'alex';

export async function analyzeWriting(text) {
  // Retext analysis
  const retextResult = await unified()
    .use(retextEnglish)
    .use(retextReadability, { age: 18, minWords: 5, threshold: 4 })
    .use(retextPassive)
    .use(retextSimplify)
    .use(retextStringify)
    .process(text);

  // write-good analysis
  const writeGoodIssues = writeGood(text);

  // alex analysis
  const alexResult = alex(text);

  // Combine results
  return {
    issues: [
      ...retextResult.messages.map(msg => ({
        type: msg.ruleId || 'style',
        message: msg.reason,
        line: msg.line,
        column: msg.column,
        severity: msg.fatal ? 'error' : 'warning'
      })),
      ...writeGoodIssues.map(issue => ({
        type: 'write-good',
        message: issue.reason,
        offset: issue.index,
        length: issue.offset,
        severity: 'suggestion'
      })),
      ...alexResult.messages.map(msg => ({
        type: 'inclusive',
        message: msg.reason,
        line: msg.line,
        column: msg.column,
        severity: 'info'
      }))
    ],
    readabilityScore: calculateReadabilityScore(text),
    stats: {
      wordCount: text.split(/\s+/).length,
      sentenceCount: text.split(/[.!?]+/).filter(s => s.trim()).length,
      adverbCount: countAdverbs(text),
      passiveCount: writeGoodIssues.filter(i => i.reason.includes('passive')).length
    }
  };
}

function calculateReadabilityScore(text) {
  const words = text.split(/\s+/).length;
  const sentences = text.split(/[.!?]+/).filter(s => s.trim()).length;
  const chars = text.replace(/\s/g, '').length;

  if (words === 0 || sentences === 0) return { grade: 0, score: 100 };

  // Automated Readability Index (Hemingway's formula)
  const grade = Math.round(4.71 * (chars / words) + 0.5 * (words / sentences) - 21.43);

  return {
    grade: Math.max(1, Math.min(16, grade)),
    score: Math.max(0, 100 - (grade * 5)), // Higher score = easier to read
    label: getReadabilityLabel(grade)
  };
}

function getReadabilityLabel(grade) {
  if (grade <= 6) return 'Elementary';
  if (grade <= 8) return 'Middle School';
  if (grade <= 10) return 'High School';
  if (grade <= 12) return 'College Prep';
  if (grade <= 14) return 'College';
  return 'Graduate';
}

function countAdverbs(text) {
  const nonAdverbs = ['family', 'only', 'early', 'daily', 'likely'];
  return text.split(/\s+/)
    .filter(word => word.endsWith('ly') && !nonAdverbs.includes(word.toLowerCase()))
    .length;
}
```

### Phase 2: UI Components

#### Readability Score Widget
```svelte
<!-- src/components/ReadabilityScore.svelte -->
<script>
  let { score = 0, grade = 0, label = '' } = $props();

  let color = $derived(
    score >= 70 ? '#4ade80' :  // Green - easy
    score >= 50 ? '#facc15' :  // Yellow - moderate
    '#f87171'                   // Red - difficult
  );
</script>

<div class="score-widget" style="--score-color: {color}">
  <div class="score-circle">
    <span class="grade">{grade}</span>
    <span class="label">Grade Level</span>
  </div>
  <div class="details">
    <div class="score-bar" style="width: {score}%"></div>
    <span>{label} reading level</span>
  </div>
</div>

<style>
  .score-widget {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1rem;
  }
  .score-circle {
    width: 80px;
    height: 80px;
    border: 4px solid var(--score-color);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .grade {
    font-size: 1.5rem;
    font-weight: bold;
  }
  .score-bar {
    height: 6px;
    background: var(--score-color);
    border-radius: 3px;
    transition: width 0.3s ease;
  }
</style>
```

#### Suggestions Panel
```svelte
<!-- src/components/SuggestionsPanel.svelte -->
<script>
  let { issues = [] } = $props();

  let grouped = $derived({
    errors: issues.filter(i => i.severity === 'error'),
    warnings: issues.filter(i => i.severity === 'warning'),
    suggestions: issues.filter(i => i.severity === 'suggestion'),
    info: issues.filter(i => i.severity === 'info')
  });
</script>

<aside class="suggestions-panel">
  {#if grouped.errors.length > 0}
    <section class="issue-group error">
      <h3>Grammar Errors ({grouped.errors.length})</h3>
      {#each grouped.errors as issue}
        <div class="issue-item">{issue.message}</div>
      {/each}
    </section>
  {/if}

  {#if grouped.warnings.length > 0}
    <section class="issue-group warning">
      <h3>Style Warnings ({grouped.warnings.length})</h3>
      {#each grouped.warnings as issue}
        <div class="issue-item">{issue.message}</div>
      {/each}
    </section>
  {/if}

  <!-- Similar for suggestions and info -->
</aside>
```

### Phase 3: Rust Backend Integration (nlprule)

Add to Cargo.toml:
```toml
[dependencies]
nlprule = "0.6"
serde_json = "1.0"
```

Create grammar checking command:
```rust
// src-tauri/src/services/grammar.rs

use nlprule::{Rules, Tokenizer};
use serde::Serialize;

#[derive(Serialize)]
pub struct GrammarSuggestion {
    pub start: usize,
    pub end: usize,
    pub message: String,
    pub replacements: Vec<String>,
}

pub struct GrammarChecker {
    tokenizer: Tokenizer,
    rules: Rules,
}

impl GrammarChecker {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let tokenizer_path = get_resource_path("nlprule/en_tokenizer.bin");
        let rules_path = get_resource_path("nlprule/en_rules.bin");

        Ok(Self {
            tokenizer: Tokenizer::new(tokenizer_path)?,
            rules: Rules::new(rules_path)?,
        })
    }

    pub fn check(&self, text: &str) -> Vec<GrammarSuggestion> {
        self.rules
            .suggest(text, &self.tokenizer)
            .into_iter()
            .map(|s| GrammarSuggestion {
                start: s.span().byte().start,
                end: s.span().byte().end,
                message: s.message().to_string(),
                replacements: s.replacements()
                    .iter()
                    .map(|r| r.to_string())
                    .collect(),
            })
            .collect()
    }
}
```

Tauri command:
```rust
// src-tauri/src/commands.rs

#[tauri::command]
pub async fn check_grammar(
    text: String,
    state: tauri::State<'_, AppState>
) -> Result<Vec<GrammarSuggestion>, String> {
    let checker = state.grammar_checker.lock().unwrap();
    Ok(checker.check(&text))
}
```

### Phase 4: Synonym/Thesaurus Feature

```javascript
// src/lib/thesaurus.js

export async function getSynonyms(word) {
  const response = await fetch(
    `https://api.datamuse.com/words?rel_syn=${encodeURIComponent(word)}`
  );
  const data = await response.json();
  return data.slice(0, 10).map(item => ({
    word: item.word,
    score: item.score
  }));
}

export async function getWordDefinition(word) {
  const response = await fetch(
    `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`
  );
  const data = await response.json();

  if (data.title === 'No Definitions Found') {
    return null;
  }

  return {
    word: data[0].word,
    phonetic: data[0].phonetic,
    meanings: data[0].meanings.map(m => ({
      partOfSpeech: m.partOfSpeech,
      definitions: m.definitions.slice(0, 3).map(d => d.definition)
    }))
  };
}
```

---

## 8. Voice-to-Polished-Prose Workflow

### Proposed User Experience

1. **Record Voice** (existing feature)
   - Captures raw thoughts via microphone
   - Whisper.cpp transcribes to text

2. **Initial Transcript Review**
   - Show raw transcript with obvious errors
   - Automatic analysis runs in background

3. **Writing Enhancement Dashboard**
   ```
   ┌──────────────────────────────────────────────────┐
   │  Transcript Editor                               │
   │  ┌────────────────────────────────┐  ┌────────┐ │
   │  │                                │  │ Grade  │ │
   │  │  [Highlighted text with        │  │   8    │ │
   │  │   color-coded issues]          │  │        │ │
   │  │                                │  │ Middle │ │
   │  │                                │  │ School │ │
   │  └────────────────────────────────┘  └────────┘ │
   │                                                  │
   │  Issues Found:                                   │
   │  ┌────────────────────────────────────────────┐ │
   │  │ [x] Passive voice (3 instances)            │ │
   │  │ [x] Complex sentences (2 instances)        │ │
   │  │ [!] Adverb overuse (5 instances)          │ │
   │  │ [i] Inclusive language suggestion          │ │
   │  └────────────────────────────────────────────┘ │
   │                                                  │
   │  [Fix All] [Ignore] [Export Polished]          │
   └──────────────────────────────────────────────────┘
   ```

4. **Interactive Editing**
   - Click on highlighted text to see suggestions
   - One-click accept/reject
   - Undo/redo stack

5. **Final Polish**
   - AI (Claude/OpenAI) for semantic improvements
   - Tone adjustment (formal, casual, professional)
   - Export options (Markdown, HTML, plain text)

---

## 9. Estimated Implementation Effort

| Feature | Complexity | Hours | Dependencies |
|---------|-----------|-------|--------------|
| Frontend analyzer (retext+write-good) | Medium | 16 | npm packages |
| Readability score widget | Low | 4 | None |
| Suggestions sidebar UI | Medium | 12 | None |
| Text highlighting in editor | High | 20 | DOM manipulation |
| Synonym lookup (Datamuse) | Low | 6 | API call |
| nlprule Rust integration | High | 24 | Binary download |
| Settings for checker options | Low | 4 | Existing settings |
| Export polished text | Low | 4 | Existing export |
| **Total** | | **90 hours** | |

---

## 10. Recommendations

### Immediate Implementation (Week 1)
1. Install retext ecosystem packages
2. Create `writing_analyzer.js` service
3. Add readability score widget to UI
4. Basic suggestions panel

### Short-term (Week 2-3)
1. Text highlighting with color coding
2. Datamuse synonym integration
3. Interactive suggestion acceptance
4. Save analysis results to database

### Medium-term (Month 2)
1. nlprule Rust backend integration
2. Custom rule creation
3. Style guide presets (formal, casual, technical)
4. Export with tracked changes

### Long-term Considerations
1. LanguageTool self-hosted option for advanced users
2. Machine learning for personalized suggestions
3. Multi-language support (Whisper already supports this)
4. Tone detection and adjustment

---

## 11. Resource Links

### Primary Documentation
- **Retext**: https://github.com/retextjs/retext/blob/main/doc/plugins.md
- **write-good**: https://github.com/btford/write-good
- **alex**: https://alexjs.com/
- **LanguageTool API**: https://languagetool.org/proofreading-api
- **nlprule**: https://github.com/bminixhofer/nlprule
- **Datamuse**: https://www.datamuse.com/api/

### Research Articles
- **Reverse-engineering Hemingway**: https://www.freecodecamp.org/news/https-medium-com-samwcoding-deconstructing-the-hemingway-app-8098e22d878d/
- **Readability Formulas**: https://readable.com/features/readability-formulas/
- **Passive Voice Detection**: https://eastedit.com.au/2015/03/coding-passive-voice-detection/

### NPM Packages
- `retext`: Natural language processor
- `write-good`: Naive English linter
- `alex`: Inclusive language checker
- `syllable`: Count syllables in words
- `flesch-kincaid`: Readability formula
- `gunning-fog`: Fog index calculator
- `textlint`: Pluggable linting tool

### Rust Crates
- `nlprule`: Grammar checking
- `whatlang`: Language detection
- `rust-bert`: Transformer models

---

## Conclusion

The research reveals a mature ecosystem of open-source writing enhancement tools. For BrainDump's voice-to-production workflow, I recommend:

1. **Frontend**: Retext ecosystem with write-good and alex for comprehensive analysis
2. **Backend**: nlprule for fast, native grammar checking without network dependency
3. **APIs**: Datamuse (free, no key) for synonyms
4. **No external dependency** on Hemingway (closed-source) or Grammarly (SaaS only)

The proposed implementation preserves BrainDump's privacy-first philosophy by performing all analysis locally, with optional cloud services only for thesaurus/dictionary lookups that don't contain sensitive user data.

Total estimated effort: **90 hours** for full implementation with real-time feedback, highlighting, and suggestion acceptance.
