# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**BrainDump v3.0** - Privacy-first voice journaling desktop application
**Stack**: Tauri 2.0 + Svelte 5 + Rust + whisper.cpp FFI
**Status**: 60% feature-complete, buildable and runnable
**Current Branch**: `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`

---

## Essential Commands

### Development
```bash
# Start full development server (Tauri + Svelte with hot reload)
npm run tauri:dev

# Frontend only (Svelte dev server)
npm run dev
```

### Build
```bash
# Build production app (creates .app/.dmg)
npm run tauri:build

# Build frontend only
npm run build
```

### Testing
```bash
# Run Rust unit tests
cd src-tauri && cargo test

# Frontend tests (not yet configured)
npm test
```

### First-Time Setup
```bash
# 1. Install whisper.cpp (macOS)
brew install whisper-cpp

# 2. Install dependencies
npm install
cd src-tauri && cargo build

# 3. Download Whisper model (141MB)
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# 4. Create .env file with API keys
echo 'OPENAI_API_KEY=sk-...' > .env
echo 'CLAUDE_API_KEY=sk-ant-...' >> .env

# 5. Run development server
npm run tauri:dev
```

---

## Architecture Overview

### Stack Diagram
```
┌─────────────────────────────────────────────────┐
│         TAURI 2.0 DESKTOP APPLICATION           │
├─────────────────────────────────────────────────┤
│  Frontend: Svelte 5 (Runes API)                │
│  └─ Components: ChatPanel, SettingsPanel,       │
│     PrivacyPanel, TemplateSelector              │
├─────────────────────────────────────────────────┤
│  Backend: Rust                                  │
│  ├─ Audio: cpal + hound (recording)             │
│  ├─ Transcription: whisper.cpp FFI (Metal GPU)  │
│  ├─ Database: SQLite + Repository pattern       │
│  ├─ AI APIs: Claude + OpenAI HTTP clients       │
│  └─ Security: macOS Keychain (API keys)         │
└─────────────────────────────────────────────────┘
```

### Data Flow: Recording → Transcription → Chat

1. **User Records Audio**
   ```
   Click Record
   ├─> Tauri command: start_recording()
   ├─> Audio thread: cpal captures mic input
   └─> Real-time peak level visualization
   ```

2. **User Stops Recording**
   ```
   Click Stop
   ├─> Tauri command: stop_recording()
   ├─> Returns: f32 audio samples + sample_rate
   ├─> Resample to 16kHz (Whisper requirement)
   ├─> Save WAV to test-recordings/ (dev mode)
   ├─> Whisper.cpp FFI: transcribe via Metal GPU
   ├─> Auto-create chat session
   ├─> Save transcript as first user message
   └─> Return: transcript + session_id
   ```

3. **AI Chat Response**
   ```
   User sends message
   ├─> Check provider selection (OpenAI/Claude)
   ├─> ⚠️ BUG: Always routes to Claude API
   │   (Should route based on selected provider)
   ├─> API client sends HTTP request
   ├─> Save AI response as assistant message
   └─> Update chat UI
   ```

---

## Critical Documentation

⭐ **READ THESE FIRST** before making changes:

### Project Status & Missing Features
- **`docs/dev/PROJECT_STATUS_2025-11-16.md`**
  - Current state: what works vs what's broken
  - Feature completion matrix (60% complete)
  - 14 missing features before v1.0
  - Known bugs and issues

### Implementation Guide
- **`docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`**
  - 14 detailed GitHub issues with implementation steps
  - Priority breakdown (P1-P4)
  - Effort estimates (166 hours total)
  - Code file references for each issue

### Development Workflow
- **`docs/dev/HANDOFF_TO_WEB_TEAM.md`**
  - Complete development setup
  - Testing requirements
  - Code style conventions
  - Git workflow and PR process

### Agent Work Logs
- **`docs/agents/`** - 3 agent deliverable reports from overnight sprint

### Planning Archive
- **`docs/pm/archive/`** - Historical planning documents and proposals

---

## Key Architecture Patterns

### 1. Whisper.cpp FFI Integration

**Pattern**: Direct C FFI to whisper.cpp library (not subprocess).

```rust
// src-tauri/src/plugin/whisper_cpp.rs
extern "C" {
    fn whisper_init_from_file(path: *const c_char) -> *mut WhisperContext;
    fn whisper_full(ctx: *mut WhisperContext, ...);
}
```

**Build System** (`src-tauri/build.rs`):
- Uses `pkg-config` to find whisper.cpp installation
- Portable across systems (no hardcoded paths)
- Fallback with helpful error messages
- Feature flag: `[features] whisper = []`

**Model Path Logic**:
```rust
// Development: ./models/ggml-base.bin
// Production: Contents/Resources/models/ggml-base.bin
```

### 2. .env Auto-Import to Keychain

**Unique Pattern**: On app startup, API keys from `.env` are automatically imported to macOS Keychain.

```rust
// src-tauri/src/main.rs:12-42
fn main() {
    dotenv::dotenv().ok();  // Load .env file
    import_env_keys_to_keychain();  // Auto-import to keychain
    // ... rest of initialization
}
```

**Why**: Improves fresh install UX - users don't need to manually enter keys in Settings.

### 3. Auto-Session Creation

**Pattern**: Recording completion automatically creates a chat session with transcript as first message.

```rust
// src-tauri/src/commands.rs:212-252
// After transcription completes:
let session = ChatSession {
    title: Some(format!("Brain Dump {}", now.format("%Y-%m-%d %H:%M"))),
    ...
};
let session_id = db.create_chat_session(&session)?;
```

### 4. Repository Pattern (Database)

**Pattern**: All database operations go through `Repository` struct.

```rust
// src-tauri/src/db/repository.rs
pub struct Repository {
    conn: Arc<Mutex<Connection>>,
}

impl Repository {
    pub fn create_chat_session(&self, session: &ChatSession) -> Result<i64>
    pub fn get_messages(&self, session_id: i64) -> Result<Vec<Message>>
    // ... all CRUD operations
}
```

**Schema Location**: `src-tauri/src/db/schema.sql` (V2 migration applied)

### 5. Privacy Scanner (Client-Side)

**Pattern**: Regex-based PII detection before sending to AI.

```javascript
// src/lib/privacy_scanner.js
const PATTERNS = [
    { regex: /\b\d{3}-\d{2}-\d{4}\b/g, type: 'ssn', severity: 'danger' },
    { regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, type: 'email' },
    // ... more patterns
];

export function scanText(text) {
    // Returns: [{ type, value, severity }]
}
```

**Non-Blocking**: User can proceed even with detected PII.

---

## Critical Gotchas

### 1. Svelte 5 Runes (Breaking Change)

**MUST USE** new Svelte 5 syntax:

```javascript
// ❌ OLD (Svelte 4) - DO NOT USE
export let myProp;
$: derivedValue = myProp * 2;

// ✅ NEW (Svelte 5) - REQUIRED
let { myProp = $bindable() } = $props();
let derivedValue = $derived(myProp * 2);
```

**Files Using Runes**:
- `src/App.svelte` - Main state management
- `src/components/ChatPanel.svelte` - Two-way binding with `$bindable()`
- `src/components/SettingsPanel.svelte` - Provider selection state
- `src/components/PrivacyPanel.svelte` - Reactive PII scanning

### 2. Provider Selection Bug (P1 Critical)

**Bug**: User can select OpenAI or Claude in Settings, but chat **always uses Claude**.

**Location**: `src/components/ChatPanel.svelte:38`

```javascript
// ❌ BUG: Hardcoded to Claude
const response = await invoke('send_message_to_claude', { message: userMessage });

// ✅ FIX: Route based on provider
const command = selectedProvider === 'openai'
    ? 'send_openai_message'
    : 'send_message_to_claude';
const response = await invoke(command, { message: userMessage });
```

**Also Missing**: Provider selection is NOT persisted to database (resets on app restart).

### 3. Database Location Issue

**Current**: `~/.braindump/data/braindump.db`
**Should Be**: `~/Library/Application Support/com.braindump.app/braindump.db` (macOS standard)

### 4. Documentation is NOT in Git

**Critical**: `docs/` directory is in `.gitignore` - documentation won't be committed!

This is intentional (IP protection), but means:
- Documentation only exists locally
- Future contributors won't see it in GitHub
- Keep local copies safe

### 5. Test Data Accumulation

**Directories** (both in `.gitignore`):
- `test-recordings/` - WAV files from manual testing
- `test-transcripts/` - Markdown transcripts

**Privacy**: These contain user voice recordings - must NOT be committed to git.

---

## Database Schema (V2)

```sql
-- Core Tables
recordings          -- Audio file metadata (path, duration, sample_rate)
├─> transcripts     -- Whisper output (text, language, confidence)
    └─> segments    -- Future: Timestamp-aligned segments

chat_sessions       -- Conversation threads
├─> messages        -- User + AI messages
    └─> recording_id (nullable FK)

-- Configuration
prompt_templates    -- RAG prompts (brain_dump, end_of_day, crisis_support)
metadata            -- Schema version, app settings
```

**Migration**: V1 → V2 adds `chat_sessions` and `messages` tables.

---

## Common Development Tasks

### Adding a New Tauri Command

1. **Define command in `src-tauri/src/commands.rs`**:
```rust
#[tauri::command]
pub async fn my_new_command(
    param: String,
    state: tauri::State<'_, AppState>
) -> Result<String, String> {
    // Implementation
    Ok("result".to_string())
}
```

2. **Register in `src-tauri/src/main.rs`**:
```rust
.invoke_handler(tauri::generate_handler![
    // ... existing commands
    commands::my_new_command,
])
```

3. **Call from frontend**:
```javascript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke('my_new_command', { param: 'value' });
```

### Adding a Database Table

1. **Update schema**: `src-tauri/src/db/schema.sql`
2. **Create Rust model**: `src-tauri/src/db/models.rs`
3. **Add Repository methods**: `src-tauri/src/db/repository.rs`
4. **Increment schema version** in metadata table
5. **Test migration** from previous version

### Creating a New Svelte Component

1. **Create file**: `src/components/MyComponent.svelte`
2. **Use Svelte 5 runes**:
```svelte
<script>
    let { propName = $bindable('default') } = $props();
    let computed = $derived(propName.toUpperCase());
</script>

<div>{computed}</div>
```

3. **Import in parent**:
```svelte
<script>
    import MyComponent from './components/MyComponent.svelte';
</script>

<MyComponent bind:propName={myState} />
```

---

## Known Issues (See docs/ for Full List)

### P1 Critical (Blocks v1.0)
1. **Provider selection NOT persisted** - Resets to "openai" on app restart
2. **Provider selection NOT connected to backend** - Always uses Claude API
3. **Prompt management UI missing** - Can SELECT but not CREATE/EDIT/DELETE
4. **Session management incomplete** - Can't delete or rename sessions

### P2 High
5. **No Whisper model selection** - Stuck with base model
6. **Search box non-functional** - UI exists but does nothing
7. **No audio playback** - Can't replay original recordings

**See**: `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md` for all 14 issues with implementation details.

---

## File Reference Map

### When Adding Features

**Audio Recording**:
- Commands: `src-tauri/src/commands.rs:14-82`
- Audio Module: `src-tauri/src/audio/mod.rs`
- UI: `src/App.svelte` (record button)

**Transcription**:
- Whisper FFI: `src-tauri/src/plugin/whisper_cpp.rs`
- Command: `src-tauri/src/commands.rs:168-252`

**Chat/AI**:
- Claude Client: `src-tauri/src/services/claude_api.rs`
- OpenAI Client: `src-tauri/src/services/openai_api.rs`
- UI: `src/components/ChatPanel.svelte`
- Commands: `src-tauri/src/commands.rs:254-406`

**Database**:
- Schema: `src-tauri/src/db/schema.sql`
- Models: `src-tauri/src/db/models.rs`
- Repository: `src-tauri/src/db/repository.rs`

**Settings**:
- UI: `src/components/SettingsPanel.svelte`
- Keychain: Uses `keyring` crate
- Commands: `src-tauri/src/commands.rs:408-526`

---

## Testing Strategy (Not Yet Implemented)

### Recommended Structure
```
src-tauri/tests/
├── integration/
│   ├── audio_recording_test.rs
│   ├── transcription_test.rs
│   └── chat_session_test.rs
└── unit/
    ├── db_repository_test.rs
    └── api_client_test.rs

src/tests/
├── privacy_scanner.test.js
└── components/
    ├── ChatPanel.test.js
    └── SettingsPanel.test.js
```

**Current Coverage**: ~5% (only basic unit tests in some modules)

**Goal**: 60%+ coverage before v1.0 release

---

## Debugging Tips

### Rust Backend Logs
```bash
# Logs go to stdout during development
npm run tauri:dev

# Or check system logs
tail -f ~/Library/Logs/braindump/app.log
```

### Frontend Console
- Open Developer Tools in running app: `Cmd+Option+I`
- Console shows: Tauri command errors, Svelte warnings, API responses

### Common Errors

**"library 'whisper' not found"**:
```bash
# Solution: Install whisper.cpp
brew install whisper-cpp
```

**"Cannot use `export let` in runes mode"**:
```bash
# Solution: Migrate to Svelte 5 runes syntax
# Change: export let prop
# To: let { prop } = $props()
```

**"API key not found"**:
```bash
# Solution: Create .env file or add via Settings panel
echo 'OPENAI_API_KEY=sk-...' > .env
npm run tauri:dev  # Auto-imports to keychain
```

---

## Quick Links

- **Project Status**: `docs/dev/PROJECT_STATUS_2025-11-16.md`
- **Missing Features**: `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`
- **Development Guide**: `docs/dev/HANDOFF_TO_WEB_TEAM.md`
- **GitHub Repo**: https://github.com/Iamcodio/IAC-031-clear-voice-app
- **Tauri Docs**: https://v2.tauri.app/
- **Svelte 5 Docs**: https://svelte.dev/docs/svelte/what-are-runes

---

**Last Updated**: 2025-11-16
**Current Branch**: `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`
**Completion Status**: 60% feature-complete, 14 features missing before v1.0
