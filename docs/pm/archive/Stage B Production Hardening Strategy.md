# Stage B: Production Hardening Strategy

**Version:** 1.0  
**Date:** 2025-11-09  
**Status:** Planning  
**Owner:** IamCodio (PM) + Claude Code (Technical Lead)

---

## Executive Summary

Stage B is functionally complete (recording + transcription working). This document outlines the path to production-ready code suitable for crisis situations where reliability is non-negotiable.

**Current State:** Working prototype (10-30% error handling)  
**Target State:** Production-grade black box (90%+ error handling)  
**Timeline:** 2-3 days with Claude Code + sub-agents

---

## Mission-Critical Requirements

This app serves people in crisis at 3am when no support is available. Every failure mode must:
1. Be visible to the user (no silent failures)
2. Provide clear recovery actions
3. Preserve user data (never lose recordings)
4. Maintain user trust (professional UX)

---

## Architecture Layers

### Layer 1: Rust Audio Recorder (cpal)

**Current Issues:**
- No device availability checks
- Silent failures on permission denial
- No retry logic for stream errors
- Buffer overflow handling missing

**Hardening Tasks:**
```rust
// Error modes to handle:
enum AudioError {
    DeviceNotFound,
    PermissionDenied,
    StreamCreationFailed,
    BufferOverflow,
    UnexpectedDisconnect,
}

// Recovery strategies:
- Device selector UI (fallback to different mic)
- Permission re-request flow
- Automatic stream restart on disconnect
- Buffer size adjustment on overflow
```

**File:** `src-tauri/src/audio/recorder.rs`  
**Owner:** Claude Code sub-agent: `audio-engineer`

---

### Layer 2: FFI Bridge (Rust ↔ C++)

**Current Issues:**
- Potential null pointer dereferences
- No memory safety validation
- Type conversion can panic

**Hardening Tasks:**
```rust
// Safety checks at FFI boundary:
- Null pointer guards on all C++ returns
- Memory ownership validation
- Type size assertions (compile-time checks)
- Panic-free error propagation
```

**File:** `src-tauri/src/plugin/whisper_cpp.rs`  
**Owner:** Claude Code sub-agent: `rust-expert`

---

### Layer 3: Whisper Transcriber (C++)

**Current Issues:**
- No timeout mechanism (can hang indefinitely)
- Metal GPU failures not handled
- Model loading errors not propagated
- Invalid audio format crashes

**Hardening Tasks:**
```rust
// Error modes:
enum TranscriptionError {
    ModelNotLoaded,
    InvalidAudioFormat,
    TimeoutExceeded(Duration),
    MetalGPUFailed,
    OutOfMemory,
}

// Fallback chain:
1. Try Metal GPU (fastest)
2. Try CPU (slower but reliable)
3. Return error with saved audio file
```

**File:** `src-tauri/src/plugin/whisper_cpp.rs`  
**Owner:** Claude Code sub-agent: `whisper-specialist`

---

### Layer 4: Database Layer (SQLite)

**Current Issues:**
- No transaction rollback on failures
- File lock conflicts not handled
- Disk space not checked
- Connection pool missing

**Hardening Tasks:**
```rust
// Robust database operations:
- Wrap all writes in transactions
- Retry logic for locked database (3 attempts)
- Pre-flight disk space check (require 100MB free)
- Connection pool (prevent simultaneous writes)
- Backup before destructive operations
```

**File:** `src-tauri/src/db/repository.rs`  
**Owner:** Claude Code sub-agent: `database-specialist`

---

### Layer 5: UI Layer (Svelte)

**Current Issues:**
- No loading states (user sees nothing during transcription)
- Errors not displayed
- No retry buttons
- Blue button color (unprofessional)
- Rainbow progress bar (distracting)

**Hardening Tasks:**
```javascript
// UI states to implement:
- Loading spinner during transcription
- Error toast notifications (auto-dismiss after 5s)
- Retry button on failures
- Progress indicators (% complete)
- Professional color scheme (neutral grays/blues)
```

**Files:** `src/lib/components/*.svelte`  
**Owner:** Claude Code sub-agent: `ui-designer`

---

## Critical User Journeys

### Journey 1: Happy Path
1. Click Record → Mic permission granted → Recording starts
2. User speaks → Audio levels visible → Stop pressed
3. Transcription runs → Progress shown → Text appears
4. Saved to database → Added to history → Success message

**Success Criteria:** 0 clicks after "Stop" button. Fully automatic.

---

### Journey 2: Permission Denied
1. Click Record → Permission denied → Clear error message
2. Show: "Microphone access required. Open System Settings?"
3. Button: "Open Settings" (deep link to Privacy & Security)
4. User grants permission → Return to app → Retry works

**Success Criteria:** User can fix permission without leaving app context.

---

### Journey 3: Transcription Failure
1. Recording succeeds → Whisper fails → Audio still saved
2. Show: "Transcription failed. Audio saved to [path]. Retry?"
3. Button: "Retry Transcription" (re-run Whisper on saved file)
4. Option: "Use Different Model" (fallback to smaller model)

**Success Criteria:** Zero data loss. User maintains control.

---

### Journey 4: Silence Detection
1. Recording finishes → Whisper returns [BLANK_AUDIO]
2. Show: "No speech detected. Check microphone levels?"
3. Button: "Test Microphone" (show live waveform)
4. Option: "Save Silent Recording" or "Discard"

**Success Criteria:** User understands why transcription failed.

---

## Implementation Plan

### Phase 1: Error Handling (Day 1)
- [ ] Wrap all operations in Result types
- [ ] Create error enum for each layer
- [ ] Add structured logging (debug/info/warn/error)
- [ ] Remove all `.unwrap()` calls
- [ ] Add panic hooks for crash reporting

### Phase 2: User Feedback (Day 2)
- [ ] Loading spinners for async operations
- [ ] Error toast component
- [ ] Retry button logic
- [ ] Progress indicators
- [ ] Success confirmations

### Phase 3: Settings Panel (Day 2-3)
- [ ] Audio device selector
- [ ] Test microphone (live waveform)
- [ ] Model selector (base/small/medium)
- [ ] Language selector
- [ ] Storage settings (cleanup policy)

### Phase 4: Testing (Day 3)
- [ ] Manual testing checklist (10 scenarios)
- [ ] Permission flow testing
- [ ] Long recording test (5+ minutes)
- [ ] Disk full scenario
- [ ] Network offline scenario

---

## Success Criteria

### Technical Metrics
- Zero silent failures (all errors visible)
- Zero crashes in 100 recording sessions
- <1% data loss rate (recordings always saved)
- <5s error recovery time (retry available immediately)

### User Experience Metrics
- Clear error messages (12-year-old can understand)
- Recovery actions always available (no dead ends)
- Professional UI (suitable for board presentations)
- Confidence-inspiring (PM trusts it for crisis situations)

---

## Delegation Strategy

### Claude Code + Sub-Agents
Each module assigned to specialized sub-agent:
- `audio-engineer`: Layer 1 (cpal recording)
- `rust-expert`: Layer 2 (FFI safety)
- `whisper-specialist`: Layer 3 (transcription)
- `database-specialist`: Layer 4 (SQLite)
- `ui-designer`: Layer 5 (Svelte components)

### Coordination
- PM (IamCodio) reviews all changes
- Claude Code orchestrates sub-agents
- Daily checkpoint: What's done, what's blocked
- Token budget: 100k tokens reserved for refactor

---

## Risk Mitigation

### Risk 1: Token Budget Exhaustion
**Mitigation:** Incremental commits after each layer. Can pause/resume.

### Risk 2: Breaking Changes
**Mitigation:** Test suite runs after each sub-agent change.

### Risk 3: Scope Creep
**Mitigation:** Strict adherence to 5 layers. No new features.

### Risk 4: Timeline Slip
**Mitigation:** Phase 4 (testing) can be done manually if needed.

---

## Definition of Done

**Stage B can be called "Production Ready" when:**

1. PM can demo to a board without anxiety
2. App works reliably in crisis situations at 3am
3. All errors have clear recovery paths
4. UI is professional and polished
5. Manual testing checklist: 10/10 scenarios pass

**Final Test:** "Would I trust this app to help my friend in crisis when I'm not available to debug it?"

If yes → Ship it.  
If no → More hardening needed.

---

**Next Steps:** Run this plan past PM for approval, then delegate to Claude Code.