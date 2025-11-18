# Tomorrow's Plan - 2025-11-17

## Session Summary (2025-11-16)

**Accomplished:**
- ✅ Fixed CI pipeline (ALSA, tempfile, schema version, prompt tests)
- ✅ Removed Ubuntu from CI - macOS only for MVP
- ✅ Merged PR #22 to main (86K+ lines, 201 files)
- ✅ Created 15+ CCW agent task files (they didn't execute)
- ✅ Researched Whisper models (Large-v3 Turbo, VAD, Q5_0 quantization)
- ✅ Frontend builds: 166 modules, 710ms
- ✅ Rust compiles with warnings only

**Current State:**
- Branch: `main`
- CI: GREEN (but doc tests skipped with `--lib --bins`)
- PR #22: MERGED
- 5 background processes still running (kill them)

---

## Priority 1: Fix Doc Tests (30 min)

Doc tests failing because examples missing imports. Fix these files:

1. `src-tauri/src/prompts.rs` (lines 20-23, 82-84)
2. `src-tauri/src/plugin/manager.rs` (lines 32, 77, 116, 201)

Add `use braindump::...` imports or change to ````no_run` for illustrative examples.

---

## Priority 2: Implement Model Manager (2-3 hours)

See `docs/agents/CCW_MODEL_MANAGER.md` for full spec.

Core files:
- `src-tauri/src/services/model_manager.rs` - Download models from HuggingFace
- `src/lib/components/ModelSettings.svelte` - Settings UI
- Auto-download base model on first launch
- Support: tiny, base, small, medium, large-v3-turbo
- Q5_0 quantization support
- VAD preprocessing (strip silence before transcription)

---

## Priority 3: Test Full App Flow (1 hour)

1. Kill stale processes: `pkill -f "npm run tauri:dev"`
2. Clean install: `npm ci`
3. Run app: `npm run tauri:dev`
4. Test:
   - Recording works
   - Transcription (when model downloaded)
   - Chat with OpenAI/Claude
   - Session persistence
   - Export functionality
   - Settings save

---

## Priority 4: Core Features (Pick 2-3)

From `docs/agents/CCW_BATCH_3_FEATURES.md`:

1. **Dark Mode** - System-aware theming (1-2 hours)
2. **Keyboard Shortcuts** - Cmd+R record, Cmd+N new, etc. (1-2 hours)
3. **Notification System** - Toast messages (1 hour)
4. **Waveform Visualization** - Real-time audio display (2-3 hours)
5. **Export Formats** - MD, JSON, PDF, ZIP bundle (2-3 hours)

---

## Files to Review

- `docs/agents/CCW_MODEL_MANAGER.md` - Model download implementation
- `docs/agents/CCW_BATCH_3_FEATURES.md` - Feature implementations
- `docs/agents/PLATFORM_SUPPORT.md` - macOS-only decision
- `docs/research/LOCAL_AI_MODELS.md` - Whisper model research

---

## Quick Commands

```bash
# Kill stale processes
pkill -f "npm run tauri:dev"

# Clean and rebuild
npm ci
npm run build

# Test Rust
cd src-tauri && cargo test --all-features --lib --bins

# Run app
npm run tauri:dev

# Check git status
git status
git log --oneline -10
```

---

## Notes

- CCW agents didn't deliver - do the work locally
- Main branch is stable, CI green
- Focus on getting whisper model download working
- Skip Linux support for now (macOS only)
- Doc tests are skipped in CI but should be fixed properly

---

**Start tomorrow fresh. Kill those background processes first.**
