# BrainDump Error Handling Philosophy
**Version**: 1.0  
**Date**: 2025-11-09  
**Status**: Foundation Document

---

## Mission Statement

**"This is a black box recorder for people in crisis."**

When someone in crisis loads this app, silence is violence. If we fail, we fail loudly, 
clearly, and with a path to resolution. We never leave users wondering what went wrong.

---

## The User Journey That Drives This

### The Crisis Scenario

A person experiencing a mental health crisis:
- Has limited executive function
- May be neurodivergent
- Is in acute distress
- Needs immediate help, not troubleshooting

**What happens now:**
1. Downloads BrainDump
2. Double-clicks the app
3. **Nothing appears**
4. No error, no message, no log
5. Feels abandoned by the one tool promising to help

**What MUST happen:**
1. Downloads BrainDump
2. Double-clicks the app
3. **App launches OR shows clear error dialog**
4. If error: "BrainDump couldn't start. [Clear reason]. Log saved to: [path]"
5. User knows what's wrong, can get help, feels supported

---

## Core Principles

### 1. Fail Loudly, Never Silently
- No `.unwrap()` in production code
- Every error surfaces somewhere visible
- Users deserve to know what's happening

### 2. Log Everything That Matters
- Startup sequence
- Model loading (5-10 second process)
- Audio initialization
- Database operations
- Transcription attempts

### 3. Cross-Platform By Design
- No macOS-specific error handling
- Works identically on Mac/Windows/Linux/Android
- File paths resolve correctly everywhere

### 4. Three-Layer Error Strategy
- **File Log**: Persistent record for debugging
- **UI Dialog**: Critical failures block startup
- **Event System**: Real-time errors to frontend

### 5. Graceful Degradation
- If model fails → app still opens, shows error in UI
- If database fails → in-memory fallback, warn user
- If audio fails → clear troubleshooting steps

---

## Why We Use Frameworks

We chose Tauri + Rust because:
- **Type safety** catches errors at compile time
- **Result types** force explicit error handling
- **Cross-platform** without rewriting for each OS
- **Professional grade** for production software

We're not cutting corners. We're building on solid foundations.

---

## Error Handling Architecture

### Layer 1: Rust Error Types
```rust
// Every function returns Result
fn load_model(path: &Path) -> Result<Model, BrainDumpError>
fn start_recording() -> Result<RecordingHandle, AudioError>
fn save_transcript(data: &Transcript) -> Result<i64, DatabaseError>
```

**No exceptions:**
- No `.unwrap()` in production paths
- No `.expect()` without user-facing messages
- Every error is typed and handled

### Layer 2: File Logging
```
~/.braindump/logs/app.log

[2025-11-09 15:30:00] INFO  Startup: BrainDump v3.0.0 initializing
[2025-11-09 15:30:01] INFO  Database: Connected to ~/.braindump/data.db
[2025-11-09 15:30:01] INFO  Model: Loading from ~/.braindump/models/ggml-base.bin
[2025-11-09 15:30:03] ERROR Model: File not found at expected path
[2025-11-09 15:30:03] CRITICAL Startup failed: Model file missing
```

**Log Format:**
- Timestamp (ISO 8601)
- Level (INFO, WARN, ERROR, CRITICAL)
- Component (Startup, Audio, Transcription, Database)
- Message (clear, actionable)
- Context (file paths, error codes)

**Log Rotation:**
- Daily rotation
- Keep 7 days
- Max 10MB per file

### Layer 3: UI Error Dialogs
When critical failures occur at startup:
```
┌────────────────────────────────────────┐
│  BrainDump Could Not Start            │
├────────────────────────────────────────┤
│                                        │
│  The Whisper AI model file is missing.│
│                                        │
│  Expected location:                    │
│  ~/.braindump/models/ggml-base.bin    │
│                                        │
│  Log file saved to:                    │
│  ~/.braindump/logs/app.log            │
│                                        │
│  [View Troubleshooting Guide] [Quit]  │
└────────────────────────────────────────┘
```

### Layer 4: Event System
Real-time errors to frontend:
```javascript
// Frontend listens for errors
await listen('error:critical', (event) => {
  // Show banner: "Recording failed: Microphone permission denied"
})

await listen('error:recoverable', (event) => {
  // Show warning: "Transcription slower than usual"
})
```

---

## Critical Error Points

### Startup Sequence
1. **Database Initialization**
   - File permissions
   - Schema migration
   - Corruption detection

2. **Model File Check**
   - File exists
   - File readable
   - File size correct (141MB for base model)

3. **Model Loading**
   - Memory allocation
   - GPU acceleration
   - Loading timeout (30 second max)

4. **Plugin Registration**
   - FFI bindings valid
   - Dependencies present

### Recording Flow
1. **Microphone Permission**
   - Permission requested
   - Permission granted/denied
   - Clear error if denied

2. **Audio Device**
   - Device enumeration
   - Device selection
   - Device initialization

3. **Recording Start**
   - Buffer allocation
   - Sample rate configuration
   - Recording thread spawn

### Transcription Flow
1. **Pre-checks**
   - Model loaded and ready
   - Audio data valid format
   - Sufficient memory

2. **Processing**
   - Transcription timeout (60s max)
   - Progress updates
   - Cancellation support

3. **Post-processing**
   - Result parsing
   - Database save
   - UI update

### Database Operations
1. **Writes**
   - Disk space available
   - Write permissions
   - Transaction rollback on error

2. **Reads**
   - Handle missing records gracefully
   - Detect corruption
   - Fallback to safe defaults

---

## Error Message Guidelines

### Good Error Messages
✅ "Microphone permission denied. Please grant access in System Preferences → Privacy → Microphone"
✅ "Model file not found. Expected at: ~/.braindump/models/ggml-base.bin"
✅ "Database locked by another process. Close other BrainDump instances."

### Bad Error Messages
❌ "Error 500"
❌ "Something went wrong"
❌ "null pointer exception"
❌ *Silent failure with no message*

---

## Testing Error Paths

We test error conditions explicitly:
- Missing model file
- Denied microphone permission
- Corrupted database
- Disk full
- No internet (shouldn't matter, but test anyway)
- Low memory
- Audio device unplugged mid-recording

---

## Metrics We Track

- Startup success rate
- Model loading time (p50, p95, p99)
- Recording failure reasons (permission, device, buffer)
- Transcription timeout rate
- Database write failures
- Crash-free sessions

---

## Why This Matters

**This isn't just good engineering. This is humane design.**

When someone in crisis uses this app:
- They need reliability
- They need clarity
- They need dignity

A black box recorder doesn't just capture voice. It captures trust. If we fail to 
start, we fail clearly. If we encounter errors, we handle them gracefully. If we 
crash, we leave breadcrumbs.

**We never abandon users to silence.**

---

## Implementation Checklist

- [ ] Create `src-tauri/src/error.rs` (custom error types)
- [ ] Create `src-tauri/src/logging.rs` (file logger)
- [ ] Update `main.rs` (wrap everything in Result)
- [ ] Update `audio/mod.rs` (proper error propagation)
- [ ] Update `plugin/whisper_cpp.rs` (detailed FFI errors)
- [ ] Update `db/repository.rs` (database error handling)
- [ ] Add startup error dialog (native Tauri dialog)
- [ ] Add event emission (frontend integration)
- [ ] Add entitlements (microphone permission)
- [ ] Test error paths (unit tests for each failure mode)
- [ ] Document troubleshooting (user-facing guide)

---

## Success Criteria

✅ **No silent failures** - Every error logs, shows, or emits
✅ **Clear messages** - Users understand what went wrong
✅ **Actionable guidance** - Users know how to fix it
✅ **Log persistence** - We can debug reported issues
✅ **Graceful degradation** - App doesn't crash, shows error UI
✅ **Cross-platform** - Works identically on all OSes

---

**Document Status**: Ready for implementation  
**Next Step**: Create `error.rs` with typed error hierarchy  
**Token Budget**: Track carefully, implement incrementally
