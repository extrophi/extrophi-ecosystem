# FFI Plugin Quick Start Guide

**For Sub-Agent 6:** Use this when Sub-Agent 5 completes Module 5

---

## Pre-Flight Checklist

Before starting, verify:

```bash
# 1. Tauri project exists
ls -la src-tauri/Cargo.toml
# Should exist

# 2. Plugin trait defined
grep "trait TranscriptionPlugin" src-tauri/src/plugin/mod.rs
# Should return trait definition

# 3. Types defined
grep "struct AudioData" src-tauri/src/plugin/types.rs
# Should return struct

# 4. Stage A library accessible
ls -lh build/src/api/libbraindump.dylib
# Should show 100KB file
```

---

## Implementation Steps

### Step 1: Create Branch (5 min)

```bash
cd /Users/kjd/01-projects/IAC-30-brain-dump-voice-processor
git checkout v3-development
git pull origin v3-development
git checkout -b stage-b-cpp-ffi-plugin
```

### Step 2: Create Directory Structure (5 min)

```bash
mkdir -p src-tauri/src/plugin/whisper_cpp
touch src-tauri/src/plugin/whisper_cpp/mod.rs
touch src-tauri/src/plugin/whisper_cpp/ffi.rs
touch src-tauri/src/plugin/whisper_cpp/plugin.rs
touch src-tauri/src/plugin/whisper_cpp/tests.rs
touch src-tauri/build.rs
```

### Step 3: Implement build.rs (20 min)

**File:** `src-tauri/build.rs`

```rust
fn main() {
    let project_root = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    let lib_path = format!("{}/../../build/src/api", project_root);

    println!("cargo:rustc-link-search=native={}", lib_path);
    println!("cargo:rustc-link-lib=dylib=braindump");

    // Rerun if library changes
    println!("cargo:rerun-if-changed=../../build/src/api/libbraindump.dylib");
}
```

**Test:**
```bash
cd src-tauri
cargo build
# Should succeed and link library
```

### Step 4: Implement FFI Declarations (1 hour)

**File:** `src-tauri/src/plugin/whisper_cpp/ffi.rs`

Key functions from `braindump.h`:

```rust
use std::ffi::{CStr, CString};
use std::os::raw::{c_char};

#[repr(C)]
pub struct BDTranscriber {
    _private: [u8; 0],
}

extern "C" {
    pub fn bd_transcriber_create(model_path: *const c_char) -> *mut BDTranscriber;
    pub fn bd_transcribe_file(
        transcriber: *mut BDTranscriber,
        audio_path: *const c_char
    ) -> *mut c_char;
    pub fn bd_transcriber_destroy(transcriber: *mut BDTranscriber);
    pub fn bd_free_string(s: *mut c_char);
    pub fn bd_get_last_error() -> *const c_char;
    pub fn bd_transcriber_has_gpu() -> bool;
}

// Safe wrapper example
pub fn get_last_error_safe() -> String {
    unsafe {
        let ptr = bd_get_last_error();
        if ptr.is_null() {
            String::new()
        } else {
            CStr::from_ptr(ptr).to_string_lossy().into_owned()
        }
    }
}
```

### Step 5: Implement Plugin (2 hours)

**File:** `src-tauri/src/plugin/whisper_cpp/plugin.rs`

```rust
use super::ffi;
use crate::plugin::{AudioData, PluginError, Transcript, TranscriptionPlugin};
use std::ffi::CString;
use std::path::PathBuf;

pub struct WhisperCppPlugin {
    transcriber: Option<*mut ffi::BDTranscriber>,
    model_path: String,
    initialized: bool,
}

impl WhisperCppPlugin {
    pub fn new(model_path: String) -> Self {
        Self {
            transcriber: None,
            model_path,
            initialized: false,
        }
    }
}

// SAFETY: BDTranscriber uses internal mutex (whisper.cpp design)
unsafe impl Send for WhisperCppPlugin {}
unsafe impl Sync for WhisperCppPlugin {}

impl TranscriptionPlugin for WhisperCppPlugin {
    fn name(&self) -> &str {
        "whisper-cpp"
    }

    fn version(&self) -> &str {
        "1.8.2"
    }

    fn initialize(&mut self) -> Result<(), PluginError> {
        if self.initialized {
            return Ok(());
        }

        let model_path_c = CString::new(self.model_path.clone())
            .map_err(|e| PluginError::InitFailed(format!("Invalid model path: {}", e)))?;

        // SAFETY: Calling C function with valid CString
        let transcriber = unsafe { ffi::bd_transcriber_create(model_path_c.as_ptr()) };

        if transcriber.is_null() {
            let error = ffi::get_last_error_safe();
            return Err(PluginError::InitFailed(format!("Model load failed: {}", error)));
        }

        self.transcriber = Some(transcriber);
        self.initialized = true;
        Ok(())
    }

    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError> {
        if !self.initialized {
            return Err(PluginError::NotInitialized);
        }

        let transcriber = self.transcriber.ok_or(PluginError::NotInitialized)?;

        // Write audio to temp WAV file (Stage A C API needs file path)
        let temp_path = write_temp_wav(audio)?;

        let path_c = CString::new(temp_path.to_string_lossy().as_ref())
            .map_err(|e| PluginError::TranscriptionFailed(format!("Path error: {}", e)))?;

        // SAFETY: Calling C function with valid transcriber and path
        let result_text = unsafe {
            ffi::bd_transcribe_file(transcriber, path_c.as_ptr())
        };

        // Clean up temp file
        let _ = std::fs::remove_file(&temp_path);

        if result_text.is_null() {
            let error = ffi::get_last_error_safe();
            return Err(PluginError::TranscriptionFailed(error));
        }

        // SAFETY: result_text is valid C string from C++ (non-null, null-terminated)
        let text = unsafe {
            let c_str = CStr::from_ptr(result_text);
            let text = c_str.to_string_lossy().into_owned();
            ffi::bd_free_string(result_text); // CRITICAL: Free C string
            text
        };

        Ok(Transcript {
            text: text.clone(),
            language: Some("en".to_string()),
            segments: vec![/* Create from audio duration */],
        })
    }

    fn shutdown(&mut self) -> Result<(), PluginError> {
        if let Some(transcriber) = self.transcriber.take() {
            // SAFETY: Calling C destructor with valid pointer
            unsafe { ffi::bd_transcriber_destroy(transcriber) };
        }
        self.initialized = false;
        Ok(())
    }

    fn is_initialized(&self) -> bool {
        self.initialized
    }
}

impl Drop for WhisperCppPlugin {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

fn write_temp_wav(audio: &AudioData) -> Result<PathBuf, PluginError> {
    use hound::{WavSpec, WavWriter};
    use std::env;

    let temp_dir = env::temp_dir();
    let temp_path = temp_dir.join(format!("braindump_{}.wav", std::process::id()));

    let spec = WavSpec {
        channels: audio.channels,
        sample_rate: audio.sample_rate,
        bits_per_sample: 16,
        sample_format: hound::SampleFormat::Int,
    };

    let mut writer = WavWriter::create(&temp_path, spec)
        .map_err(|e| PluginError::TranscriptionFailed(format!("WAV write error: {}", e)))?;

    for &sample in &audio.samples {
        let sample_i16 = (sample * i16::MAX as f32) as i16;
        writer.write_sample(sample_i16)
            .map_err(|e| PluginError::TranscriptionFailed(format!("WAV write error: {}", e)))?;
    }

    writer.finalize()
        .map_err(|e| PluginError::TranscriptionFailed(format!("WAV finalize error: {}", e)))?;

    Ok(temp_path)
}
```

### Step 6: Write Tests (2 hours)

**File:** `src-tauri/src/plugin/whisper_cpp/tests.rs`

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::plugin::TranscriptionPlugin;

    #[test]
    fn test_plugin_lifecycle() {
        let model_path = "/Users/kjd/01-projects/IAC-30-brain-dump-voice-processor/models/ggml-base.bin";
        let mut plugin = WhisperCppPlugin::new(model_path.to_string());

        // Initialize
        assert!(plugin.initialize().is_ok());
        assert!(plugin.is_initialized());

        // Transcribe dummy audio
        let audio = AudioData {
            samples: vec![0.0; 16000 * 5], // 5 seconds silence
            sample_rate: 16000,
            channels: 1,
        };

        let result = plugin.transcribe(&audio);
        assert!(result.is_ok());

        // Shutdown
        assert!(plugin.shutdown().is_ok());
        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_real_audio() {
        // Load cli-test.wav
        // Transcribe
        // Verify text not empty
    }
}
```

**Run tests:**
```bash
cd src-tauri
cargo test whisper_cpp
```

### Step 7: Memory Leak Test (1 hour)

```bash
# Build release
cd src-tauri
cargo build --release --tests

# Run with macOS leaks detector
leaks --atExit -- cargo test --release whisper_cpp

# Should show: "0 leaks for 0 total leaked bytes"
```

### Step 8: Benchmark (30 min)

```bash
# Use performance_test.wav from root (962 KB ≈ 10s audio)
time cargo test --release test_real_audio
# Should complete in <2s (within 10% of Stage A)
```

---

## Safety Checklist

Before committing, verify every `unsafe` block:

- [ ] Null pointer check before dereference
- [ ] `CString::new()` for Rust→C strings (stored until C call completes)
- [ ] `CStr::from_ptr()` for C→Rust strings (null-checked)
- [ ] `bd_free_string()` called on every C-allocated string
- [ ] Raw pointer validity documented in comment
- [ ] Drop impl calls cleanup (even on panic)

---

## Common Pitfalls

### 1. String Memory Leak
```rust
// ❌ WRONG: Leaks C string
let text = CStr::from_ptr(result_text).to_string_lossy().into_owned();
// Missing: bd_free_string(result_text);

// ✅ CORRECT:
let text = unsafe {
    let c_str = CStr::from_ptr(result_text);
    let text = c_str.to_string_lossy().into_owned();
    ffi::bd_free_string(result_text); // FREE HERE
    text
};
```

### 2. Null Pointer Dereference
```rust
// ❌ WRONG: No null check
let transcriber = bd_transcriber_create(path.as_ptr());
self.transcriber = Some(transcriber); // Might be NULL!

// ✅ CORRECT:
let transcriber = unsafe { bd_transcriber_create(path.as_ptr()) };
if transcriber.is_null() {
    return Err(PluginError::InitFailed("Model load failed".into()));
}
self.transcriber = Some(transcriber);
```

### 3. CString Lifetime
```rust
// ❌ WRONG: CString dropped before C call
let path_c = CString::new(path)?;
unsafe { bd_transcribe_file(transcriber, path_c.as_ptr()) }; // Dangling pointer!

// ✅ CORRECT: Keep CString alive
let path_c = CString::new(path)?;
let result = unsafe {
    bd_transcribe_file(transcriber, path_c.as_ptr())
}; // path_c lives until here
```

---

## Git Workflow

```bash
# 1. Commit implementation
git add src-tauri/
git commit -m "feat(plugin): implement Module 6 - C++ FFI Plugin

- FFI bindings to libbraindump.dylib
- WhisperCppPlugin implementing TranscriptionPlugin trait
- Unit and integration tests
- Memory leak verification (0 leaks)
- Performance benchmark (<2s for 10s audio)

Refs #46"

# 2. Push branch
git push -u origin stage-b-cpp-ffi-plugin

# 3. Create PR (via gh CLI or GitHub UI)
# Do NOT close issue #46 - leave for PM
```

---

## Acceptance Criteria

Before marking complete:

- [ ] `cargo build` succeeds
- [ ] `cargo test` passes (all tests green)
- [ ] `cargo clippy` zero warnings
- [ ] Memory leak test: 0 leaks
- [ ] Performance test: <2s for 10s audio
- [ ] Integration test matches Stage A output
- [ ] All `unsafe` blocks documented
- [ ] PR created (not merged)
- [ ] Issue #46 updated (not closed)

---

## Handoff to Module 10

Once complete, notify Sub-Agent 10:

```markdown
✅ MODULE 6 COMPLETE - C++ FFI Plugin Ready

Branch: stage-b-cpp-ffi-plugin
Files:
- src-tauri/build.rs
- src-tauri/src/plugin/whisper_cpp/

Usage Example:
```rust
use crate::plugin::{PluginManager, whisper_cpp::WhisperCppPlugin};

let mut manager = PluginManager::new();
let plugin = Box::new(WhisperCppPlugin::new("models/ggml-base.bin".into()));
manager.register(plugin)?;

// Now transcribe
let audio = load_audio("recording.wav")?;
let transcript = manager.transcribe(&audio)?;
```

Test Results:
- Unit tests: PASS
- Memory leaks: 0
- Performance: 1.8s for 10s audio (10% faster than Stage A)

Sub-Agent 10 can now integrate into Tauri app.
```

---

**Quick Start Author:** Sub-Agent 6 (FFI Specialist)
**Last Updated:** 2025-11-08
**Status:** Ready for execution

**END OF QUICK START**
