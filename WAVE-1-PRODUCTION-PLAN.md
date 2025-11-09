# Wave 1 Complete Production Refactor - NO DEFERRALS
## BrainDump v3.0 - Do It Right In One Pass

**Date:** November 9, 2025
**Lead Orchestrator:** Claude (Opus 4.1)
**Project Manager:** KJD
**Version:** FINAL - No Technical Debt
**Commitment:** One Shot, Production Grade

---

## PM DIRECTIVE: ZERO TECHNICAL DEBT

**No temporary fixes. No "we'll fix it later". No string error bridges.**

Every line of code ships production-ready or doesn't ship at all.

---

## Complete Execution Plan - 4 Phases, No Shortcuts

## Phase 0: Pre-Flight IPC Verification (15 mins)

**MUST VERIFY: Tauri can serialize BrainDumpError over IPC**

### Step 1: Add Serialize to ALL error types
```rust
// src-tauri/src/error.rs
use serde::Serialize;

#[derive(Debug, Serialize)]
#[serde(tag = "type", content = "data")]
pub enum BrainDumpError {
    Audio(AudioError),
    Database(DatabaseError),
    Transcription(TranscriptionError),
    Io(String),  // Convert io::Error to String for serialization
    Other(String),
}

#[derive(Debug, Serialize)]
pub enum AudioError {
    PermissionDenied,
    NoDeviceFound,
    DeviceInitFailed(String),
    AlreadyRecording,
    NotRecording,
    RecordingFailed(String),
    BufferOverflow,        // NEW
    StreamDisconnected,    // NEW
}

#[derive(Debug, Serialize)]
pub enum DatabaseError {
    ConnectionFailed(String),
    Corrupted,
    WriteFailed(String),
    ReadFailed(String),
    Locked,
    InsufficientDiskSpace,     // NEW
    TransactionFailed(String),  // NEW
}

#[derive(Debug, Serialize)]
pub enum TranscriptionError {
    ModelNotFound(String),
    ModelLoadFailed(String),
    ModelNotReady,
    TranscriptionFailed(String),
    Timeout,
    InvalidAudioData,
    BlankAudio,         // NEW
    MetalGPUFailed,     // NEW
}
```

### Step 2: Create test command
```rust
// Temporarily add to commands.rs
#[tauri::command]
pub async fn test_error_serialization() -> Result<String, BrainDumpError> {
    // Test each error type
    Err(BrainDumpError::Audio(AudioError::PermissionDenied))
}
```

### Step 3: Test from frontend
```javascript
// In browser console
try {
    await invoke('test_error_serialization');
} catch (error) {
    console.log('Received error:', error);
    // MUST see: {type: "Audio", data: "PermissionDenied"}
    // NOT: "[object Object]" or undefined
}
```

**GATE: If this fails, FIX IT NOW. Do not proceed to Phase 1.**

---

## Phase 1: Complete Safety Fixes (60 mins)

### Task 1A: Fix ALL 73 .unwrap() calls

**File by file elimination:**

#### main.rs (7 instances)
```rust
// Line 31 - BEFORE:
let home = dirs::home_dir().expect("Home directory not found");

// AFTER:
let home = dirs::home_dir().unwrap_or_else(|| {
    log_warn!("Main", "No home directory, using current directory");
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
});

// Line 38 - BEFORE:
std::fs::create_dir_all(&app_dir).expect("Failed to create app directory");

// AFTER:
if let Err(e) = std::fs::create_dir_all(&app_dir) {
    log_error!("Main", &format!("Failed to create app directory: {}", e));
    // Continue anyway - might have permissions later
}

// Lines 60-75 - Multiple .parent().unwrap() chains
// AFTER: Check each step
let model_path = exe_dir
    .parent()
    .and_then(|p| p.parent())
    .and_then(|p| p.parent())
    .map(|p| p.join("models").join("ggml-base.bin"))
    .unwrap_or_else(|| {
        log_error!("Main", "Could not determine model path");
        PathBuf::from("models/ggml-base.bin")  // Fallback
    });
```

#### recorder.rs (5 instances)
```rust
// Line 99 - CRITICAL: In audio callback
// BEFORE:
let mut state = state_clone.lock().unwrap();

// AFTER:
let mut state = match state_clone.lock() {
    Ok(guard) => guard,
    Err(poisoned) => {
        eprintln!("Audio thread mutex poisoned, recovering");
        poisoned.into_inner()
    }
};
```

#### logging.rs (3 instances)
```rust
// Lines 49, 74, 105 - BEFORE:
LOGGER.lock().unwrap()

// AFTER:
match LOGGER.lock() {
    Ok(guard) => guard,
    Err(poisoned) => {
        eprintln!("Logger mutex poisoned, recovering");
        poisoned.into_inner()
    }
}
```

#### repository.rs (8 instances)
```rust
// Lines 48-49 - Date parsing
// BEFORE:
created_at: row.get::<_, String>(6)?.parse().unwrap(),

// AFTER:
created_at: row.get::<_, String>(6)?
    .parse()
    .unwrap_or_else(|e| {
        log_warn!("Database", &format!("Invalid timestamp: {}", e));
        Utc::now()
    }),
```

### Task 1B: Update Critical Dependencies
```toml
# Cargo.toml
[dependencies]
tauri = "2.9"
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.43", features = ["full"] }

# package.json
"dependencies": {
  "@tauri-apps/api": "^2.9.0",
  "svelte": "^5.4.0"
},
"devDependencies": {
  "@tauri-apps/cli": "^2.9.0"
}
```

### Task 1C: Add Transcription Safety Wrapper
```rust
// commands.rs line 105 - CRITICAL: Protect against Whisper panic
let transcript = match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
    manager.transcribe(&audio_data)
})) {
    Ok(result) => result?,
    Err(panic_info) => {
        log_error!("Transcription", "Whisper panicked - audio is safe");
        return Err(BrainDumpError::Transcription(
            TranscriptionError::TranscriptionFailed(
                "Transcription crashed but your audio was saved successfully".to_string()
            )
        ));
    }
};
```

### Task 1D: Delete Duplicate Error Types
```rust
// DELETE from audio/recorder.rs:
pub enum RecorderError { ... }  // DELETE ENTIRE ENUM
pub type RecorderResult<T> = Result<T, RecorderError>;  // DELETE

// REPLACE ALL USES WITH:
use crate::error::{AudioError, Result};
```

---

## Phase 2: Complete Error Infrastructure Migration (45 mins)

### Task 2A: Change ALL Command Signatures

**No deferrals - every command gets migrated:**

```rust
// commands.rs - ALL commands change NOW

#[tauri::command]
pub async fn start_recording(state: State<'_, AppState>)
    -> Result<String, BrainDumpError> {  // Changed from Result<String, String>
    use crate::error::{AudioError, BrainDumpError};

    log_info!("Commands", "Starting recording");

    let (response_tx, response_rx) = mpsc::channel();

    state.audio_tx
        .send((AudioCommand::StartRecording, response_tx))
        .map_err(|e| {
            log_error!("Commands", &format!("Failed to send command: {}", e));
            BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string()))
        })?;

    match response_rx.recv_timeout(Duration::from_secs(5)) {
        Ok(AudioResponse::RecordingStarted) => {
            log_info!("Commands", "Recording started successfully");
            Ok("Recording started".to_string())
        }
        Ok(AudioResponse::Error(e)) => {
            log_error!("Commands", &format!("Failed to start recording: {}", e));
            Err(BrainDumpError::Audio(AudioError::RecordingFailed(e)))
        }
        _ => {
            log_error!("Commands", "Unexpected response from audio thread");
            Err(BrainDumpError::Audio(AudioError::DeviceInitFailed(
                "Audio system not responding".to_string()
            )))
        }
    }
}

#[tauri::command]
pub async fn stop_recording(state: State<'_, AppState>)
    -> Result<String, BrainDumpError> {  // Changed
    // ... similar pattern
}

#[tauri::command]
pub async fn get_transcripts(
    state: State<'_, AppState>,
    limit: Option<i64>
) -> Result<Vec<TranscriptRecord>, BrainDumpError> {  // Changed
    // ... similar pattern
}

#[tauri::command]
pub async fn get_peak_level(state: State<'_, AppState>)
    -> Result<f32, BrainDumpError> {  // Changed
    // ... similar pattern
}

#[tauri::command]
pub async fn is_model_loaded(state: State<'_, AppState>)
    -> Result<bool, BrainDumpError> {  // Changed
    // ... similar pattern
}
```

### Task 2B: Update Frontend Error Handling

```javascript
// App.svelte - Complete error handling update

// Create error handler utility
function handleError(error) {
    console.error('Command error:', error);

    // Handle both legacy strings and new structured errors
    if (typeof error === 'string') {
        return error;
    }

    // New structured error format
    if (error.type && error.data) {
        return getHumanReadableError(error);
    }

    // Fallback
    return error.message || JSON.stringify(error);
}

function getHumanReadableError(error) {
    // Map backend errors to user-friendly messages
    const errorMap = {
        'Audio': {
            'PermissionDenied': 'Microphone access denied. Please check System Settings.',
            'NoDeviceFound': 'No microphone found. Please connect a microphone.',
            'AlreadyRecording': 'Already recording. Please stop the current recording first.',
            'NotRecording': 'Not currently recording.',
            'BufferOverflow': 'Audio buffer overflow. Try reducing system load.',
            'StreamDisconnected': 'Microphone disconnected. Please reconnect and try again.'
        },
        'Transcription': {
            'ModelNotReady': 'AI model is still loading. Please wait...',
            'BlankAudio': 'No speech detected. Please speak clearly and try again.',
            'Timeout': 'Transcription took too long. Please try a shorter recording.',
            'MetalGPUFailed': 'GPU acceleration failed, falling back to CPU...'
        },
        'Database': {
            'Locked': 'Database is busy. Please close other BrainDump windows.',
            'InsufficientDiskSpace': 'Not enough disk space. Please free up space.',
            'Corrupted': 'Database corrupted. Attempting recovery...'
        }
    };

    const category = errorMap[error.type];
    if (category && category[error.data]) {
        return category[error.data];
    }

    // Handle errors with string data
    if (typeof error.data === 'string') {
        return `${error.type} error: ${error.data}`;
    }

    // Handle complex error data
    if (error.data && typeof error.data === 'object') {
        const key = Object.keys(error.data)[0];
        const value = error.data[key];
        return `${error.type} error: ${value}`;
    }

    return `${error.type} error occurred`;
}

// Update ALL try-catch blocks
async function handleRecord() {
    try {
        if (!isRecording) {
            status = 'Starting recording...';
            await invoke('start_recording');
            isRecording = true;
            status = 'Recording...';
        } else {
            status = 'Stopping recording...';
            const transcript = await invoke('stop_recording');
            isRecording = false;
            currentTranscript = transcript;
            status = 'Ready';
            await loadHistory();
        }
    } catch (error) {
        const errorMessage = handleError(error);
        status = `Error: ${errorMessage}`;
        isRecording = false;

        // Show retry button for recoverable errors
        if (error.type === 'Audio' || error.type === 'Transcription') {
            showRetryButton = true;
        }
    }
}

// Similar updates for all other invoke calls...
```

---

## Phase 3: UI Polish (30 mins - can run parallel with Phase 2)

### Task 3A: Fix Record Button Colors
```css
/* src/lib/components/RecordButton.svelte */
/* Line 52-54 - CHANGE FROM: */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* TO: */
background: linear-gradient(135deg, #10b981 0%, #059669 100%);

/* src/App.svelte - Line ~470 */
/* CHANGE FROM: */
background: linear-gradient(135deg, #5CBDB9, #4A90E2);

/* TO: */
background: linear-gradient(135deg, #10b981 0%, #059669 100%);
```

### Task 3B: Fix Volume Meter
```css
/* src/App.svelte - Line ~575 */
/* CHANGE FROM: */
background: linear-gradient(90deg, #34c759 0%, #007aff 50%, #5856d6 100%);

/* TO: */
background: linear-gradient(90deg,
  #10b981 0%,
  #10b981 ${peakPercentage}%,
  #e5e7eb ${peakPercentage}%,
  #e5e7eb 100%
);
```

---

## Phase 4: Complete Testing & Validation (60 mins)

### Task 4A: Automated Safety Checks

Create `scripts/safety-check.sh`:
```bash
#!/bin/bash

echo "🔍 Safety Check for Production Release"

# Check 1: No .unwrap() in production code
echo "Checking for .unwrap() calls..."
UNWRAPS=$(grep -r "\.unwrap()" src-tauri/src/ --exclude-dir=target | wc -l)
if [ $UNWRAPS -gt 0 ]; then
    echo "❌ FAIL: Found $UNWRAPS .unwrap() calls"
    grep -r "\.unwrap()" src-tauri/src/ --exclude-dir=target
    exit 1
fi
echo "✅ PASS: No .unwrap() calls found"

# Check 2: No .expect() in production code
echo "Checking for .expect() calls..."
EXPECTS=$(grep -r "\.expect(" src-tauri/src/ --exclude-dir=target | wc -l)
if [ $EXPECTS -gt 0 ]; then
    echo "❌ FAIL: Found $EXPECTS .expect() calls"
    grep -r "\.expect(" src-tauri/src/ --exclude-dir=target
    exit 1
fi
echo "✅ PASS: No .expect() calls found"

# Check 3: Compilation
echo "Checking compilation..."
cd src-tauri
cargo check --all-features || exit 1
echo "✅ PASS: Compilation successful"

# Check 4: Clippy
echo "Running clippy..."
cargo clippy -- -D warnings || exit 1
echo "✅ PASS: Clippy passed"

# Check 5: Tests
echo "Running tests..."
cargo test || exit 1
echo "✅ PASS: Tests passed"

echo "🎉 All safety checks passed!"
```

### Task 4B: Manual Crisis Scenario Tests

**Test 1: No Home Directory**
```bash
unset HOME
cargo run
# App must start without panic
```

**Test 2: Microphone Permission Denied**
1. Deny microphone in System Settings
2. Click Record
3. Must see: "Microphone access denied. Please check System Settings."
4. NOT: Technical error or crash

**Test 3: Silence Detection**
1. Record without speaking
2. Must see: "No speech detected. Please speak clearly and try again."
3. WAV file must still exist in test-recordings/

**Test 4: Crash During Recording**
1. Start recording
2. Force quit app
3. Restart app
4. Check test-recordings/ - partial WAV must exist

**Test 5: Database Lock**
```bash
# Terminal 1
sqlite3 ~/.braindump/data/braindump.db
.tables  # Keep connection open

# Terminal 2
cargo run
# Try to record
# Must see helpful error, not crash
```

### Task 4C: User Journey Validation

**Crisis Simulation at 3am:**
1. Set system time to 3:00 AM
2. Dim screen to minimum
3. Record while simulating emotional state:
   - Speak softly (test volume sensitivity)
   - Pause frequently (test silence handling)
   - Stop abruptly (test incomplete recordings)
4. Every error must be:
   - Non-technical language
   - Actionable (clear next step)
   - Reassuring (data is safe)

---

## Token Budget Management

**Available:** 71,000 tokens (after initial 200k - 129k used)

**Allocation:**
- Phase 0: 5k (IPC verification)
- Phase 1: 25k (safety fixes - complex)
- Phase 2: 20k (error migration)
- Phase 3: 10k (UI - simple)
- Phase 4: 10k (testing)
- Buffer: 1k
- **Total: 71k** (exactly at limit)

**If tokens exhausted:**
- MINIMUM: Complete Phase 0-2 (core safety)
- UI can wait if absolutely necessary
- But NO partial error migration

---

## Success Criteria - BINARY (All or Nothing)

### Must Have (100% Required)
- ✅ Zero .unwrap() or .expect() in production
- ✅ All commands use BrainDumpError (not String)
- ✅ Frontend handles structured errors properly
- ✅ Transcription wrapped in catch_unwind
- ✅ Dependencies updated to latest
- ✅ WAV always saved (even on crash)
- ✅ All errors user-friendly
- ✅ Professional green UI (no blue/rainbow)
- ✅ Compiles without warnings
- ✅ All manual tests pass

### Definition of Done
Can you give this to someone in crisis at 3am with 100% confidence it won't fail them?

If NO → Not done. Fix it.
If YES → Ship it.

---

## Rollback Strategy

### Level 1: Fix in place
```bash
cargo check  # Find error
cargo fix    # Auto-fix if possible
```

### Level 2: Revert file
```bash
git checkout HEAD -- src-tauri/src/commands.rs
```

### Level 3: Nuclear option
```bash
git reset --hard pre-wave1-safety
```

---

## Final Commitment

**I will deliver:**
1. **Complete error system** - No deferrals
2. **Zero panics** - All .unwrap() eliminated
3. **Production grade** - Every line shippable
4. **User-first errors** - Crisis-appropriate messages
5. **No technical debt** - One pass, done right

**I will NOT:**
- Use temporary String bridges
- Defer command signature changes
- Leave any .unwrap() calls
- Ship half-measures
- Hide problems

**If I cannot deliver this, I will stop and report immediately.**

---

## Sign-Off

**Lead Orchestrator:** Claude (Opus 4.1)
**Commitment:** Production-grade code in one pass
**No excuses. No shortcuts. No debt.**

---

*"One shot. Production grade. For people in crisis."*