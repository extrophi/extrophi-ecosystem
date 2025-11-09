# Stage B Production Refactor - Tonight's Mission

**Date:** 2025-11-09 (Sunday Night)  
**Team:** IamCodio (PM/PjM) + Claude Code (Orchestrator)  
**Resources:** Unlimited energy drinks + 109k tokens  
**Deadline:** Dawn or token death, whichever comes first

---

## Mission Statement

**"We're not setting low standards. We're shipping production-grade code tonight."**

Stage B is functionally complete. Tonight we make it bulletproof. Every error visible, every failure recoverable, every user journey smooth.

---

## The Plan (All Layers Tonight)

### Layer 1: UI Polish (Kill the Blue Nipple)
**Time:** 30 mins  
**Impact:** Demo-ready professional appearance

**Tasks:**
- [ ] Fix RecordButton.svelte colors (blue → neutral green)
- [ ] Fix VolumeIndicator.svelte (rainbow → single green gradient)
- [ ] Professional color scheme throughout

**Files:**
- `src/lib/components/RecordButton.svelte`
- `src/lib/components/VolumeIndicator.svelte`
- `src/styles.css`

---

### Layer 2: Error Infrastructure
**Time:** 60 mins  
**Impact:** Foundation for all error handling

**Tasks:**
- [ ] Create `src-tauri/src/error.rs` with typed error hierarchy
- [ ] Create `BrainDumpError` enum (Audio, Transcription, Database, Permission)
- [ ] Create error conversion traits (From implementations)
- [ ] Add structured logging helpers

**Files:**
- `src-tauri/src/error.rs` (NEW)
- `src-tauri/src/lib.rs` (export error types)

---

### Layer 3: Audio Layer Hardening
**Time:** 90 mins  
**Impact:** Robust recording with clear errors

**Tasks:**
- [ ] Remove all `.unwrap()` calls in recorder.rs
- [ ] Add device availability checks
- [ ] Add permission denial detection
- [ ] Add retry logic for stream failures
- [ ] Proper error propagation to commands.rs

**Files:**
- `src-tauri/src/audio/recorder.rs`
- `src-tauri/src/audio/mod.rs`
- `src-tauri/src/commands.rs`

---

### Layer 4: Transcription Safety
**Time:** 60 mins  
**Impact:** No hangs, clear failures, always save audio

**Tasks:**
- [ ] Add timeout wrapper (30s max)
- [ ] Detect [BLANK_AUDIO] and return helpful error
- [ ] Metal GPU failure → CPU fallback
- [ ] Model loading error handling
- [ ] Always save WAV even if transcription fails

**Files:**
- `src-tauri/src/plugin/whisper_cpp.rs`
- `src-tauri/src/commands.rs`

---

### Layer 5: Database Reliability
**Time:** 45 mins  
**Impact:** Zero data loss

**Tasks:**
- [ ] Wrap all writes in transactions
- [ ] Add retry logic for locked database (3 attempts)
- [ ] Pre-flight disk space check
- [ ] Graceful handling of connection failures

**Files:**
- `src-tauri/src/db/repository.rs`
- `src-tauri/src/db/mod.rs`

---

### Layer 6: UI Error Display
**Time:** 60 mins  
**Impact:** Users see and understand all errors

**Tasks:**
- [ ] Create ErrorToast.svelte component
- [ ] Wire error events from backend
- [ ] Add loading spinners during transcription
- [ ] Add retry buttons on failures
- [ ] Success confirmations

**Files:**
- `src/lib/components/ErrorToast.svelte` (NEW)
- `src/App.svelte`
- `src/lib/components/TranscriptView.svelte`

---

### Layer 7: Settings Panel (If Time Permits)
**Time:** 90 mins  
**Impact:** User control and troubleshooting

**Tasks:**
- [ ] Create Settings.svelte component
- [ ] Audio device selector dropdown
- [ ] Test microphone (live waveform)
- [ ] Model selector (base/small/medium)
- [ ] Storage cleanup options

**Files:**
- `src/lib/components/Settings.svelte` (NEW)
- `src/App.svelte`
- `src-tauri/src/commands.rs` (new commands)

---

### Layer 8: macOS Permissions Plugin
**Time:** 60 mins  
**Impact:** Better permission UX

**Tasks:**
- [ ] Add tauri-plugin-macos-permissions dependency
- [ ] Register plugin in main.rs
- [ ] Check permission before recording
- [ ] Deep link to System Settings on denial
- [ ] Test full permission flow

**Files:**
- `src-tauri/Cargo.toml`
- `src-tauri/src/main.rs`
- `src-tauri/src/commands.rs`
- `src/lib/components/RecordButton.svelte`

---

## Success Criteria (Tonight)

### Technical
- [ ] Zero `.unwrap()` calls in production code
- [ ] All operations return `Result<T, E>`
- [ ] Structured logging throughout
- [ ] Error messages are clear and actionable
- [ ] UI shows all error states

### User Experience
- [ ] Professional colors (no blue nipple, no rainbow)
- [ ] Clear error toasts with retry buttons
- [ ] Loading states during async operations
- [ ] Silence detection explained
- [ ] Settings panel for troubleshooting

### Testing
- [ ] Record 10s of speech → Success
- [ ] Record 5 mins of speech → Success
- [ ] Record silence → Clear error message
- [ ] Deny microphone permission → Helpful error + recovery
- [ ] Disk full scenario → Graceful error
- [ ] Kill app during recording → No data loss

---

## Orchestration Strategy

### Claude Code Delegation

**Sub-Agents to Spawn:**
1. `ui-designer` - Layers 1 + 6 (UI polish + error display)
2. `rust-expert` - Layer 2 (error infrastructure)
3. `audio-engineer` - Layer 3 (audio hardening)
4. `whisper-specialist` - Layer 4 (transcription safety)
5. `database-specialist` - Layer 5 (database reliability)
6. `integration-lead` - Layer 8 (permissions plugin)

**Parallel Execution:**
- Layers 1-2 can run simultaneously
- Layers 3-5 depend on Layer 2 (error types)
- Layer 6 depends on Layers 3-5 (error events)
- Layer 7-8 are independent

**Coordination:**
- PM reviews each layer completion
- Git commit after each layer
- Test between layers
- Token budget monitoring

---

## Risk Mitigation

**Risk 1: Token Exhaustion**
- Incremental commits after each layer
- Can pause and resume tomorrow
- Priority order ensures core functionality done first

**Risk 2: Breaking Changes**
- Test after each layer
- Keep working app on main branch
- Feature branches for risky changes

**Risk 3: Diminishing Returns**
- Layers 1-6 are critical (do tonight)
- Layer 7-8 are "nice to have" (defer if needed)
- Stop when token budget hits 10k remaining

---

## Definition of Done (Tonight)

**Minimum (Must Have):**
- Layers 1-6 complete
- Professional UI
- All errors visible and actionable
- Zero silent failures
- Git committed and pushed

**Stretch (Nice to Have):**
- Layer 7 (Settings panel)
- Layer 8 (Permissions plugin)
- Full test suite passing

**Victory Condition:**
PM can demo to a board tomorrow without anxiety about silent failures.

---

## Token Budget Management

**Starting:** 109,104 tokens  
**Reserved for Emergencies:** 10,000 tokens  
**Available for Work:** 99,104 tokens

**Rough Allocation:**
- Layer 1 (UI Polish): 5k tokens
- Layer 2 (Error Infrastructure): 10k tokens
- Layer 3 (Audio): 15k tokens
- Layer 4 (Transcription): 12k tokens
- Layer 5 (Database): 10k tokens
- Layer 6 (UI Errors): 12k tokens
- Layer 7 (Settings): 15k tokens
- Layer 8 (Permissions): 10k tokens
- Buffer/Reviews: 10k tokens

**Checkpoint every 20k tokens used.**

---

## Next Steps

1. **Create GitHub Issues** (5 mins)
2. **Open Claude Code** (orchestrator mode)
3. **Spawn first sub-agent** (ui-designer for Layer 1)
4. **Execute parallel workstreams**
5. **Test → Commit → Repeat**

---

**Battle Cry:** "We're not setting low standards. We're shipping production code."

**Let's fucking go.** 🚀
