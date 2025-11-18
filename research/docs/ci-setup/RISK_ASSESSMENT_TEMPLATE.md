# BrainDump v3.0 - Risk Assessment & Method Statement (RAMS)
**Date**: 2025-11-16
**Product**: BrainDump - Voice-to-AI Journaling for Anxiety Relief
**Target Users**: People experiencing anxiety in their hour of need

---

## Executive Summary

**User Context**: Someone experiencing anxiety needs to dump their thoughts IMMEDIATELY. They cannot troubleshoot tech problems. Every failure is catastrophic to user experience.

**Risk Tolerance**: **ZERO** for P1 critical path. The app MUST work flawlessly for:
1. Recording their voice
2. Knowing it's working
3. Getting transcribed results

---

## Risk Assessment Matrix

| Risk Level | Impact | Probability | Tolerance | Action |
|------------|--------|-------------|-----------|--------|
| **Critical** | User cannot record | Medium | ZERO | Must fix before release |
| **High** | Feature degraded | Low | Minimal | Fix if encountered |
| **Medium** | Inconvenience | Low | Acceptable | Fix in next version |
| **Low** | Cosmetic | Low | Acceptable | Backlog |

---

## CRITICAL RISKS (P1) - ZERO TOLERANCE

### 1. Permissions Failures

#### RISK: chmod/chown Incorrect
**Impact**: App won't execute, user sees cryptic error
**Probability**: HIGH on fresh macOS install
**Mitigation**:
- ✅ DMG installer handles permissions automatically
- ✅ CI tests executable permissions
- ✅ Clear error if execution blocked: "Right-click > Open to allow"
**Test**: Try to launch without granting permissions

#### RISK: Microphone Permission Denied
**Impact**: Cannot record, app useless
**Probability**: HIGH (macOS always asks)
**Mitigation**:
- ✅ Detect permission state before showing record button
- ✅ Clear UI: "Microphone access required - Allow in System Settings"
- ✅ Link directly to System Settings > Privacy > Microphone
- ✅ Recheck permissions when app gains focus
**Test**: Deny mic permission, verify clear error + guidance

---

### 2. Dependency Conflicts

#### RISK: whisper.cpp Missing/Wrong Version
**Impact**: Transcription fails, core feature broken
**Probability**: MEDIUM (user must install separately)
**Mitigation**:
- ✅ Check for whisper.cpp on startup via pkg-config
- ✅ If missing: Show install instructions "brew install whisper-cpp"
- ✅ If wrong version: Show version mismatch warning
- ✅ Graceful fallback: Offer to send audio to API for transcription
**Test**: Launch without whisper.cpp installed

#### RISK: NPM Dependency Conflicts
**Impact**: Build fails, can't install
**Probability**: LOW (npm handles most conflicts)
**Mitigation**:
- ✅ Use `npm ci` not `npm install` (exact versions from lock file)
- ✅ CI runs `npm ls` to detect conflicts
- ✅ Outdated dependency warnings (not errors)
**Test**: `npm ls` in CI, check for conflicts

#### RISK: Rust Dependency Conflicts
**Impact**: Build fails
**Probability**: LOW (cargo handles well)
**Mitigation**:
- ✅ CI runs `cargo tree` to detect conflicts
- ✅ Pin critical dependencies in Cargo.toml
- ✅ cargo-outdated checks weekly
**Test**: `cargo tree` in CI, check for conflicts

---

### 3. Silent Failures

#### RISK: Recording but No Audio Detected
**Impact**: User thinks it's working, gets empty transcription
**Probability**: MEDIUM (muted mic, wrong input device)
**Mitigation**:
- ✅ Real-time audio level indicator (MUST be visible)
- ✅ Warning if silent for >3 seconds: "No audio detected - check mic"
- ✅ Mic test button before first recording
- ✅ Show selected input device name
**Test**: Record with muted mic, verify warning

#### RISK: App Crash Mid-Recording
**Impact**: Lost recording, broken trust
**Probability**: LOW but HIGH IMPACT
**Mitigation**:
- ✅ Auto-save recording buffer every 5s to disk
- ✅ On crash recovery: Offer to restore last recording
- ✅ Clear message: "Recovered recording from unexpected shutdown"
**Test**: Kill app during recording, restart, verify recovery

#### RISK: Network Offline (API Fails)
**Impact**: Cannot process transcription/chat
**Probability**: MEDIUM (travel, poor connection)
**Mitigation**:
- ✅ Detect network state before API calls
- ✅ If offline: "Working offline - will sync when connected"
- ✅ Queue recordings for later transcription
- ✅ Local-only mode: Transcription works (Whisper local)
**Test**: Disconnect network, try to use app

---

### 4. User Doesn't Know It's Working

#### RISK: No Visual Feedback During Recording
**Impact**: Anxiety user panics, stops/restarts repeatedly
**Probability**: HIGH if UI unclear
**Mitigation**:
- ✅ **LARGE red recording indicator** (can't be missed)
- ✅ Live waveform animation
- ✅ Time counter updates every second
- ✅ Audio level meters (green/yellow/red)
- ✅ "Recording..." text label
**Test**: Show to non-technical user, ask "Is it recording?"

#### RISK: Processing Status Unknown
**Impact**: User thinks it froze, force-quits
**Probability**: MEDIUM for long recordings
**Mitigation**:
- ✅ Progress indicator: "Transcribing... 45%"
- ✅ Estimated time remaining
- ✅ Allow cancel with confirmation
- ✅ Show partial results as they come in
**Test**: Process 5-min recording, verify progress shown

---

### 5. Error Handling Missing

#### RISK: API Key Invalid
**Impact**: Cannot use chat feature
**Probability**: HIGH on first use
**Mitigation**:
- ✅ Validate API key format before saving
- ✅ Test API key with ping request
- ✅ Clear error: "Invalid OpenAI API key - Check at api.openai.com"
- ✅ Link to API key page
- ✅ Mask API key in UI (show only last 4 chars)
**Test**: Enter fake API key, verify clear error

#### RISK: API Rate Limit Hit
**Impact**: Cannot send messages temporarily
**Probability**: MEDIUM with heavy use
**Mitigation**:
- ✅ Detect 429 status code
- ✅ Show retry countdown: "Rate limit reached - retry in 60s"
- ✅ Auto-retry after backoff
- ✅ Suggest switching providers
**Test**: Trigger rate limit, verify graceful handling

#### RISK: Whisper Model Missing/Corrupt
**Impact**: Transcription fails
**Probability**: MEDIUM (user hasn't downloaded models)
**Mitigation**:
- ✅ Check model file exists on startup
- ✅ Verify model file size (detect corrupt)
- ✅ Clear error: "Whisper model not found - Download ggml-base.bin"
- ✅ Link to model download instructions
- ✅ Fallback: Offer API-based transcription
**Test**: Delete model file, verify error + guidance

---

## HIGH RISKS (P2) - MINIMAL TOLERANCE

### 6. Audio Quality Issues

#### RISK: Audio Levels Too Low/High
**Impact**: Poor transcription accuracy
**Probability**: MEDIUM (user mic settings)
**Mitigation**:
- ⚠️ Visual level meters (green = good, yellow = low, red = clipping)
- ⚠️ Auto-gain control (if possible)
- ⚠️ Warning if sustained clipping
- ⚠️ Mic test with feedback
**Test**: Record at various volumes, verify warnings

#### RISK: Sample Rate Wrong
**Impact**: Whisper expects 16kHz, other rates degrade quality
**Probability**: LOW (we control this)
**Mitigation**:
- ✅ Hardcode 16kHz in audio recording config
- ✅ Resample if input device doesn't support 16kHz
- ✅ Log actual sample rate for debugging
**Test**: Verify recording metadata shows 16kHz

---

### 7. Database Corruption

#### RISK: Database File Corrupt
**Impact**: Lost session history
**Probability**: LOW but HIGH IMPACT
**Mitigation**:
- ⚠️ Auto-backup database daily to `~/.braindump/backups/`
- ⚠️ Keep last 7 backups
- ⚠️ On corruption: Offer to restore from backup
- ⚠️ Clear error: "Database error - Restore from backup?"
**Test**: Corrupt database file, verify recovery option

#### RISK: Schema Migration Fails
**Impact**: App won't start after update
**Probability**: LOW
**Mitigation**:
- ⚠️ Backup database before migration
- ⚠️ Rollback on migration failure
- ⚠️ Clear error with rollback instructions
**Test**: Simulate failed migration, verify rollback

---

## MEDIUM RISKS (P3) - ACCEPTABLE

### 8. Performance Degradation

#### RISK: Slow Transcription
**Impact**: User waits longer
**Probability**: MEDIUM on older Macs
**Tolerance**: Acceptable if <30s for 1-min audio
**Mitigation**:
- Document minimum requirements (M1 or better)
- Show processing time estimates
- Allow model switching (base → tiny for speed)

#### RISK: Large Database Slowdown
**Impact**: App sluggish with 1000+ sessions
**Probability**: LOW initially
**Tolerance**: Acceptable if <2s to load
**Mitigation**:
- Add indexes to database queries
- Pagination for session list
- Archive old sessions

---

## LOW RISKS (P4) - ACCEPTABLE

### 9. UI/UX Polish

- Cosmetic bugs
- Minor layout issues
- Missing tooltips
- Accessibility gaps (screen reader)

**Tolerance**: Acceptable for v1.0, fix in v1.1

---

## TESTING METHOD STATEMENT

### Automated Tests (CI)

**Run on every PR**:
1. ✅ Permissions check (file executability)
2. ✅ Dependency resolution (Rust + NPM)
3. ✅ System dependencies (whisper.cpp via pkg-config)
4. ✅ Fresh build from scratch
5. ✅ Unit tests (all must pass)
6. ✅ Security audit (no high/critical vulns)

**Blocks merge if fails**: YES

---

### Manual Tests (QA Checklist)

**Required before release**:

#### Fresh Install Test (15 min)
1. Download DMG on clean Mac
2. Install to Applications
3. Launch first time
4. Verify permissions requested
5. Verify database created
6. Verify no crashes

#### Critical Path Test (10 min)
1. Click record button
2. Speak for 30 seconds
3. Click stop
4. Verify transcription appears
5. Send to chat
6. Verify response

#### Error Handling Test (20 min)
1. Deny mic permission → verify error
2. Disconnect network → verify offline mode
3. Enter invalid API key → verify error
4. Corrupt database → verify recovery
5. Delete model file → verify error

#### Stress Test (15 min)
1. Record 5-minute audio
2. Verify doesn't crash
3. Verify transcription completes
4. Send very long message
5. Verify chat handles it

**Sign-off required**: YES
**Tester**: Must be someone who hasn't used app before

---

## FAILURE RESPONSE PLAN

### If Critical Path Fails

1. **STOP release immediately**
2. Create P1-critical issue
3. Assign to developer
4. Block all other work until fixed
5. Re-test entire critical path
6. Document root cause

### If High Risk Fails

1. Create P2-high issue
2. Evaluate if blocking release
3. If not blocking: Schedule for next patch
4. If blocking: Fix before release

### If Tests Missing

1. PR automatically blocked (test-enforcement.yml)
2. Developer must add tests OR
3. Developer comments `/skip-tests [justification]`
4. Reviewer must approve skip with reason

---

## RISK MONITORING

### Daily
- ✅ CI status (all green?)
- ✅ Test coverage trend (improving?)

### Weekly
- ⚠️ Dependency updates (cargo outdated, npm outdated)
- ⚠️ Security advisories (cargo audit, npm audit)

### Pre-Release
- ⚠️ Full manual QA checklist
- ⚠️ Fresh install test on clean machine
- ⚠️ All P1 risks mitigated

---

## ACCEPTANCE CRITERIA FOR RELEASE

### Must Have (P1)
- [x] All critical path tests pass
- [x] No high/critical security vulnerabilities
- [x] Fresh install works on macOS 13+
- [x] Recording → Transcription → Chat flow works
- [x] All error states handled gracefully
- [x] Permissions errors show clear guidance

### Should Have (P2)
- [ ] All high-risk scenarios tested
- [ ] Database backup/recovery working
- [ ] Offline mode functional
- [ ] API error handling comprehensive

### Nice to Have (P3)
- [ ] Performance benchmarks met
- [ ] Accessibility basics covered
- [ ] UI polish complete

---

## SIGN-OFF

**Technical Lead**: _______________ Date: ___________
**QA Lead**: _______________ Date: ___________
**Product Owner**: _______________ Date: ___________

**Release Approved**: ☐ YES ☐ NO ☐ WITH CONDITIONS

**Conditions**:


---

**Last Updated**: 2025-11-16
**Next Review**: Before v1.0 release
**Owner**: Development Team
