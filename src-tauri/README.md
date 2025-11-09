# BrainDump V3.0 - Tauri Backend

Rust backend for the BrainDump voice transcription app, built with Tauri 2.1.

## Quick Start

```bash
# Verify setup
./scripts/verify-setup.sh

# Run development mode
./scripts/dev.sh

# Build production bundle
./scripts/build.sh
```

## Architecture

### Thread-Safe Design

The backend uses a channel-based architecture to avoid Send/Sync issues with the cpal audio library:

```
┌─────────────┐
│   Tauri     │
│   Main      │
│   Thread    │
└──────┬──────┘
       │
       │ mpsc::channel
       │
       ▼
┌─────────────┐
│   Audio     │
│   Thread    │  ← Owns Recorder
└─────────────┘
```

**AppState** (shared across Tauri commands):
- `plugin_manager` - Transcription plugins (Whisper C++ FFI, Candle)
- `db` - SQLite repository for recordings and transcripts
- `audio_tx` - Channel to send commands to audio thread

**Audio Thread:**
- Owns the `Recorder` instance (cpal::Stream is !Send)
- Receives commands: StartRecording, StopRecording, GetPeakLevel
- Sends responses back via one-shot channels

### IPC Commands

Frontend can invoke these commands:

```typescript
// Start recording
await invoke('start_recording')

// Stop and get transcript
const transcript = await invoke<string>('stop_recording')

// Get transcript history
const transcripts = await invoke<[string, string][]>('get_transcripts', { limit: 10 })

// Get real-time audio level
const level = await invoke<number>('get_peak_level')
```

### Plugin System

Two transcription backends available:

1. **WhisperCppPlugin** (default) - FFI wrapper around Stage A C++ library
   - Fast: Metal GPU acceleration
   - Mature: Production whisper.cpp
   - Requires: libbraindump.dylib from Stage A

2. **CandlePlugin** - Pure Rust ML using Hugging Face Candle
   - Portable: No C++ dependencies
   - Flexible: Easy to modify/extend
   - Experimental: Not yet production-ready

Plugins implement `TranscriptionPlugin` trait:
```rust
pub trait TranscriptionPlugin: Send + Sync {
    fn name(&self) -> &str;
    fn version(&self) -> &str;
    fn initialize(&mut self) -> Result<(), PluginError>;
    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError>;
    fn shutdown(&mut self) -> Result<(), PluginError>;
    fn is_initialized(&self) -> bool;
}
```

### Database Schema

SQLite database with three tables:

**recordings** - Audio file metadata
```sql
CREATE TABLE recordings (
    id INTEGER PRIMARY KEY,
    filepath TEXT NOT NULL,
    duration_ms INTEGER,
    sample_rate INTEGER,
    channels INTEGER,
    file_size_bytes INTEGER,
    created_at TEXT,
    updated_at TEXT
);
```

**transcripts** - Transcription results
```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    language TEXT,
    confidence REAL,
    plugin_name TEXT,
    transcription_duration_ms INTEGER,
    created_at TEXT,
    FOREIGN KEY (recording_id) REFERENCES recordings(id)
);
```

**segments** - Word-level timestamps
```sql
CREATE TABLE segments (
    id INTEGER PRIMARY KEY,
    transcript_id INTEGER NOT NULL,
    start_ms INTEGER,
    end_ms INTEGER,
    text TEXT,
    confidence REAL,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);
```

## Project Structure

```
src-tauri/
├── src/
│   ├── main.rs              # App entry, audio thread spawn
│   ├── lib.rs               # AppState, channel types
│   ├── commands.rs          # Tauri IPC handlers
│   ├── audio/
│   │   ├── mod.rs
│   │   ├── recorder.rs      # cpal-based audio capture
│   │   └── wav_writer.rs    # WAV file writer
│   ├── db/
│   │   ├── mod.rs
│   │   ├── models.rs        # Database models
│   │   └── repository.rs    # CRUD operations
│   └── plugin/
│       ├── mod.rs
│       ├── types.rs         # Plugin trait
│       ├── manager.rs       # Plugin registry
│       ├── whisper_cpp.rs   # C++ FFI plugin
│       └── candle.rs        # Pure Rust plugin
├── Cargo.toml               # Dependencies
├── tauri.conf.json          # Tauri configuration
├── build.rs                 # C++ library linking
├── icons/                   # App icons
└── scripts/
    ├── dev.sh               # Run dev mode
    ├── build.sh             # Build production
    ├── run-binary.sh        # Run binary directly
    └── verify-setup.sh      # Check prerequisites
```

## Dependencies

### Rust Crates

**Core:**
- `tauri 2.1` - Desktop app framework
- `serde` / `serde_json` - Serialization

**Audio:**
- `cpal 0.15` - Cross-platform audio I/O
- `hound 3.5` - WAV file reading/writing

**ML:**
- `candle-core` / `candle-transformers` - Pure Rust ML
- FFI to whisper.cpp (via Stage A)

**Database:**
- `rusqlite 0.32` - SQLite with bundled library

**Utilities:**
- `parking_lot 0.12` - Faster mutexes
- `chrono 0.4` - Date/time handling
- `thiserror 1.0` - Error derive macros

### External Libraries

**libbraindump.dylib** - Stage A C++ transcriber
- Location: `../build/src/api/libbraindump.dylib`
- Built from: `../src/api/transcriber.cpp`
- Links against: whisper.cpp (Metal GPU)

**ggml-base.bin** - Whisper model file
- Location: `../models/ggml-base.bin`
- Size: ~141MB
- Download: See scripts/verify-setup.sh

## Build Configuration

### Linking C++ Library

`build.rs` tells Cargo where to find libbraindump:

```rust
fn main() {
    let project_root = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    let lib_path = format!("{}/../build/src/api", project_root);

    println!("cargo:rustc-link-search=native={}", lib_path);
    println!("cargo:rustc-link-lib=dylib=braindump");
}
```

### Runtime Library Path

macOS requires DYLD_LIBRARY_PATH to find dylibs:

```bash
export DYLD_LIBRARY_PATH=/path/to/project/build/src/api:$DYLD_LIBRARY_PATH
```

All scripts handle this automatically.

### Tauri Configuration

`tauri.conf.json`:
```json
{
  "build": {
    "frontendDist": "../"  // Looks for index.html in project root
  },
  "bundle": {
    "icon": ["icons/32x32.png", "icons/128x128.png", ...]
  }
}
```

## Development Workflow

### 1. First Time Setup

```bash
# Build Stage A C++ library
cd ..
./build-stage-a.sh

# Download Whisper model
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# Verify setup
cd src-tauri
./scripts/verify-setup.sh
```

### 2. Development Loop

```bash
# Edit Rust code
vim src/commands.rs

# Run with hot-reload
./scripts/dev.sh

# Frontend changes auto-reload
# Rust changes require restart
```

### 3. Testing

```bash
# Build only (no bundle)
cargo build --bin braindump

# Run tests
cargo test

# Run with logs
RUST_LOG=debug ./scripts/run-binary.sh
```

### 4. Production Build

```bash
# Create .app bundle
./scripts/build.sh

# Output: target/release/bundle/macos/BrainDump.app
```

## Troubleshooting

### "dyld: Library not loaded"

The C++ library can't be found. Make sure:
1. `libbraindump.dylib` exists in `../build/src/api/`
2. `DYLD_LIBRARY_PATH` is set (scripts do this automatically)
3. Build Stage A first: `cd .. && ./build-stage-a.sh`

### "Failed to load model"

Whisper model missing or wrong path:
1. Download to `../models/ggml-base.bin` (see verify-setup.sh)
2. Check file size is ~141MB
3. Model path is relative to CWD when running binary

### "No input device found"

Audio permissions issue:
1. Grant microphone access in System Preferences
2. Check no other app is using the microphone
3. Try listing devices: `./scripts/test-audio.sh` (if exists)

### Build fails with "can't find crate"

Corrupted cargo cache:
1. `cargo clean`
2. Remove `~/.cargo/registry/cache`
3. `cargo build` again

## Performance

**Recording Latency:** <100ms start time
**Transcription Speed:** ~25× faster than real-time (11s audio in 436ms)
**Memory Usage:** ~200MB idle, ~500MB during transcription
**Binary Size:** 25MB debug, ~15MB release

## Security

- **100% Local** - No data leaves the machine
- **No Network** - App works offline
- **SQLite Encrypted** - Can enable with feature flag
- **Sandboxed** - Tauri security policies applied

## Future Enhancements

- [ ] Configurable model path (not hardcoded)
- [ ] Multiple model support (base, small, medium)
- [ ] Background transcription queue
- [ ] Export to various formats (JSON, TXT, SRT)
- [ ] Real-time streaming transcription
- [ ] Speaker diarization
- [ ] Custom vocabulary injection

## License

See parent project LICENSE file.

## Resources

- [Tauri Docs](https://tauri.app/v2/)
- [cpal Audio Library](https://github.com/RustAudio/cpal)
- [Candle ML Framework](https://github.com/huggingface/candle)
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
