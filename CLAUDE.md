# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BrainDump V3.0** - Privacy-first voice journaling desktop application
- **Architecture:** Svelte 5 frontend → Tauri 2.1 IPC → Rust backend → Whisper C++ (FFI) → Metal GPU
- **Privacy-first:** 100% local processing, no cloud dependencies, no telemetry
- **Stage B complete:** Recording + transcription working with basic UI
- **Stage C in progress:** Claude API integration (C2) for AI-assisted journaling

## Essential Commands

### Setup
```bash
# Prerequisites (macOS Apple Silicon)
brew install whisper-cpp portaudio
nvm use 22  # Node.js v22 (DO NOT use Homebrew for Node)

# Install dependencies
npm install
cd src-tauri && cargo build && cd ..

# Download Whisper model (required, 141MB base model)
mkdir -p src-tauri/models
curl -L -o src-tauri/models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

### Development
```bash
npm run tauri:dev    # Full stack dev mode (Rust backend + Svelte frontend hot reload)
npm run dev          # Frontend only (Vite dev server on localhost:5173)
npm run tauri:build  # Production .app bundle for macOS
```

### Testing
```bash
cd src-tauri
cargo test                   # All Rust tests
cargo test -- --nocapture    # With console output
cargo test test_name         # Single test

# Test Whisper.cpp independently
whisper-cli -m src-tauri/models/ggml-base.bin -f test-recordings/sample.wav -otxt -nt

# Inspect database
sqlite3 ~/.braindump/data/braindump.db ".schema"
sqlite3 ~/.braindump/data/braindump.db "SELECT * FROM transcripts ORDER BY created_at DESC LIMIT 5;"
```

### Debugging
```bash
# Logs are written to ~/.braindump/logs/
tail -f ~/.braindump/logs/braindump_*.log

# Check model loading status (takes 30+ seconds on first launch)
grep "Model" ~/.braindump/logs/braindump_*.log
```

## High-Level Architecture

### System Layers
```
┌─────────────────────────────────────────────────────────┐
│  Svelte 5 Frontend (src/)                               │
│  - App.svelte (main layout, tabs)                       │
│  - RecordButton, VolumeIndicator, HistoryList           │
│  - SettingsPanel (API key management)                   │
│  - PrivacyPanel (C2 chat interface)                     │
└──────────────────────┬──────────────────────────────────┘
                       │ Tauri IPC (@tauri-apps/api invoke)
┌──────────────────────▼──────────────────────────────────┐
│  Tauri Commands Layer (src-tauri/src/commands.rs)       │
│  - Audio: start_recording, stop_recording, get_peak     │
│  - Transcription: get_transcripts, is_model_loaded      │
│  - C2: create_chat_session, send_message_to_claude      │
│  - API: store_api_key, has_api_key, test_api_key        │
└─────────┬──────────────┬────────────────┬───────────────┘
          │              │                │
    ┌─────▼─────┐  ┌─────▼─────┐   ┌─────▼──────┐
    │Audio Thread│ │PluginMgr  │   │ Database   │
    │ (CPAL)     │ │ (Whisper) │   │ (SQLite)   │
    └────────────┘  └─────┬─────┘   └────────────┘
                          │ FFI
                    ┌─────▼──────────┐
                    │ libwhisper.dylib│
                    │ (Homebrew C++)  │
                    └─────────────────┘
```

### Critical Threading Architecture
CPAL audio streams are `!Send` (cannot cross thread boundaries safely):
- **Main thread:** Tauri event loop handles IPC commands
- **Audio thread:** Dedicated thread owns CPAL stream lifecycle
- **Communication:** `mpsc::channel` with `(AudioCommand, Sender<AudioResponse>)` messages

**DO NOT** attempt to move CPAL streams across threads or store them in `Arc<Mutex<>>`.

### Tauri IPC Commands

**Audio Recording:**
```typescript
await invoke('start_recording')  // → AudioCommand::StartRecording → audio thread
await invoke('stop_recording')   // → Returns {samples, sample_rate}
await invoke('get_peak_level')   // → f32 (0.0-1.0 for volume indicator)
```

**Transcription:**
```typescript
await invoke('is_model_loaded')           // → bool (model loads async in background)
await invoke('get_transcripts', {limit})  // → Transcript[]
```

**C2 Integration (Claude API):**
```typescript
await invoke('create_chat_session', {title})  // → i64 session_id
await invoke('send_message_to_claude', {sessionId, content, systemPrompt?})
await invoke('store_api_key', {apiKey})       // → Stores in system keyring
await invoke('has_api_key')                   // → bool
await invoke('test_api_key')                  // → {valid: bool, error?: string}
```

## Key Implementation Details

### Plugin System (`src-tauri/src/plugin/`)
Two transcription backends implementing `TranscriptionPlugin` trait:
- **WhisperCppPlugin** (default): FFI bindings to Homebrew `libwhisper.dylib`, Metal GPU acceleration
- **CandlePlugin** (experimental): Pure Rust ML using Hugging Face Candle

**Plugin initialization is async** and happens in background thread on app startup:
1. `main.rs` spawns async task in `setup()` hook
2. Emits `model-loading` events: `{status: "loading"|"ready"|"error"}`
3. Takes 30+ seconds to load ggml-base.bin model on first run

### Whisper.cpp FFI Integration
Direct C FFI bindings in `whisper_cpp.rs`:
```rust
extern "C" {
    fn whisper_init_from_file(path: *const c_char) -> *mut WhisperContext;
    fn whisper_full(ctx: *mut WhisperContext, params: WhisperFullParams,
                    samples: *const f32, n_samples: i32) -> i32;
    fn whisper_full_get_segment_text(ctx: *mut WhisperContext, i: i32) -> *const c_char;
}
```

**Build configuration** in `build.rs`:
- Links against `/opt/homebrew/Cellar/whisper-cpp/1.8.2/libexec/lib/libwhisper.dylib`
- Sets rpath for dylib loading: `@executable_path` and `@executable_path/../Frameworks`

### Database Schema (SQLite)
Located at `~/.braindump/data/braindump.db`, managed by Repository pattern:

**Stage B (Voice Transcription):**
- `recordings` - Audio metadata (filepath, duration_ms, sample_rate, channels)
- `transcripts` - Transcription text linked to recording_id (text, language, confidence, plugin_name)
- `segments` - Time-aligned segments (start_ms, end_ms, text) for future subtitle support

**Stage C (C2 Integration):**
- `chat_sessions` - Conversation threads (id, title, created_at, updated_at)
- `messages` - Chat messages (session_id, recording_id?, role: user|assistant, content, privacy_tags)
- `prompt_templates` - Reusable system prompts (name, content, category)

### Audio Processing Pipeline
1. **Capture:** CPAL streams at device native rate (44.1kHz or 48kHz) → 32-bit float samples
2. **Buffer:** Accumulate in `Vec<f32>` during recording
3. **Save:** Write 16-bit PCM WAV to `test-recordings/{timestamp}.wav` (using `hound`)
4. **Resample:** Convert to 16kHz mono using `rubato::SincFixedIn` (Whisper requirement)
5. **Transcribe:** Pass f32 samples to WhisperCppPlugin via FFI
6. **Store:** Save to database + markdown file `test-transcripts/{timestamp}.md`

### Error Handling Pattern
Custom error types in `src-tauri/src/error.rs`:
```rust
#[derive(Debug, thiserror::Error)]
pub enum BrainDumpError {
    #[error("Audio error: {0}")]
    Audio(#[from] AudioError),
    #[error("Database error: {0}")]
    Database(#[from] DatabaseError),
    #[error("Transcription error: {0}")]
    Transcription(#[from] TranscriptionError),
}
```

All errors implement `serde::Serialize` for IPC transport to frontend.

### Claude API Integration (`src-tauri/src/services/claude_api.rs`)
- **Client:** `ClaudeClient` manages HTTP requests to Anthropic API
- **Model:** `claude-3-7-sonnet-20250219` (configurable)
- **API Key Storage:** System keyring via `keyring` crate (service: "braindump", username: "claude_api_key")
- **Security:** API key never logged, stored securely outside SQLite database

## File Locations

**Development:**
- Recordings: `test-recordings/{timestamp}.wav`
- Transcripts: `test-transcripts/{timestamp}.md`
- Whisper model: `src-tauri/models/ggml-base.bin` (gitignored, 141MB)
- Logs: `~/.braindump/logs/braindump_{date}.log`
- Database: `~/.braindump/data/braindump.db`

**Production (.app bundle):**
- Model: `BrainDump.app/Contents/Resources/models/ggml-base.bin`
- Dylib: `BrainDump.app/Contents/Frameworks/libwhisper.dylib`

## Development Patterns

### Adding New Tauri Commands
1. Define command in `src-tauri/src/commands.rs`
2. Register in `main.rs` `invoke_handler!` macro
3. Call from frontend: `import { invoke } from '@tauri-apps/api/core'`

### Modifying Database Schema
1. Update `src-tauri/src/db/models.rs` (add structs)
2. Add migration in `src-tauri/src/db/mod.rs` `initialize_db()`
3. Update `Repository` methods in `src-tauri/src/db/repository.rs`
4. Database auto-migrates on next app launch

### Testing Transcription Changes
```bash
# Record 5-second test audio
npm run tauri:dev  # Click record, speak, click stop

# Or use pre-recorded sample
whisper-cli -m src-tauri/models/ggml-base.bin \
  -f test-recordings/sample.wav -otxt -nt -l en

# Check output
cat test-transcripts/*.md | tail -1
```

## Current Known Issues

**Production Hardening (from `docs/pm/Stage B: Production Hardening Strategy.md`):**
- Remove all `.unwrap()` calls (use `?` or `.unwrap_or_else()`)
- Add timeout protection for transcription (currently blocks indefinitely)
- Implement proper microphone permission checking (macOS Privacy & Security)
- Frontend error handling shows generic "Error" instead of detailed messages

**UI/UX:**
- Record button color hardcoded (needs theme consistency)
- No loading state indicator during 30s model initialization
- Volume indicator doesn't show when not recording (should show ambient level)

**Performance:**
- First transcription takes 30+ seconds (model loading)
- Large audio files (>5min) may cause UI freeze during resampling
