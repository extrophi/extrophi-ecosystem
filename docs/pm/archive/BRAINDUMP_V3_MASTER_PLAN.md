# BRAINDUMP V3.0 - MASTER PLAN

**Created:** Saturday, November 15, 2025 21:00 GMT  
**Status:** ACTIVE - Single Source of Truth  
**Version:** 1.0

---

## THE MISSION

**BrainDump is a black box recorder for people in crisis.**

This is not a productivity tool. This is not a note-taking app. This is a **lifeline** for trauma survivors, people with PTSD, neurodivergent individuals, and anyone experiencing mental health crises.

**When someone is in their darkest moment, this tool cannot fail them.**

### The User - "Alex"

**Profile:**
- Senior project manager with ADHD and PTSD
- Uses MacBook Air M2
- Experiences high-stress work situations
- Needs to process thoughts quickly during crisis moments
- Cannot tolerate complex interfaces or slow tools
- Values privacy above all else

**Crisis Scenario:**
1. Overwhelming thoughts flood Alex's mind at 2am
2. Opens BrainDump (must launch in <500ms)
3. Speaks stream-of-consciousness for 5 minutes
4. Gets instant transcription (local, private)
5. Sends to Claude for processing (optional, user choice)
6. Receives structured reflection and insights
7. Continues conversation to process emotions
8. Saves everything locally, encrypted, private

**If any step fails:** Alex loses trust. Tool is abandoned. Crisis unprocessed.

---

## NON-NEGOTIABLES

### 1. NO SILENT FAILURES

**Rule:** If something fails, the user MUST know immediately with a clear, actionable error message.

**Never:**
- ❌ Fail silently and show "Success"
- ❌ Log errors without user notification
- ❌ Use generic "Something went wrong" messages
- ❌ Crash without saving user's voice data

**Always:**
- ✅ Show specific error: "Microphone access denied. Click here to enable in System Settings."
- ✅ Auto-save partial recordings before any operation
- ✅ Offer recovery path: "Recording failed. Your audio is saved. Try again?"
- ✅ Log errors AND notify user

### 2. PRIVACY FIRST

**Rule:** User's data stays on their machine unless they explicitly choose cloud features.

**Core Principles:**
- All voice recordings stored locally
- Whisper transcription runs locally (no cloud API)
- Claude integration is OPT-IN with clear choice:
  - "Use my Claude Max plan" (OAuth, uses existing subscription)
  - "Use API key" (user provides, separate billing)
  - "No Claude integration" (local only)
- Database is local SQLite file
- No analytics, no tracking, no telemetry without explicit consent

**Future Privacy Gates:**
- Flag sensitive content before sending to Claude (medical, self-harm indicators)
- Regex + semantic matching for crisis keywords
- "Are you sure you want to send this?" prompts for flagged content
- Local-only mode for maximum privacy

### 3. PERFORMANCE

**Hard Limits:**
- App launch: <500ms cold start
- Microphone ready: <100ms after launch
- Transcription start: <1s after stopping recording
- UI response: <50ms for all interactions
- Memory idle: <50MB
- Bundle size: <20MB

**If we exceed these:** We failed. Fix it before shipping.

### 4. RELIABILITY

**Battle-Tested Standards:**
- 90%+ test coverage (Rust)
- 80%+ test coverage (Frontend)
- Zero crashes in 100 consecutive sessions
- Graceful degradation (if Claude fails, local features still work)
- Auto-recovery from errors (save state, restore on reopen)

### 5. QUALITY OVER SPEED

**Shipping broken code helps nobody.**

We don't ship:
- Untested features
- Known crashes
- Data loss bugs
- Silent failures
- Confusing UX

We DO ship:
- Working MVP (even if ugly)
- Clear error messages
- Documented limitations
- Honest about what works

---

## CURRENT STATE (Saturday Nov 15, 2025)

### What Actually Works ✅

**Core Transcription (Stage C):**
- Audio recording via CPAL (48kHz capture)
- Resampling to 16kHz for Whisper
- Local transcription via whisper.cpp FFI
- WAV file storage
- SQLite database (recordings, transcripts)
- Basic Svelte UI (3 tabs: Record, History, Settings)

**Confirmed Working:**
- Codio has been using this daily for 3 months
- Real data, real usage
- Transcription quality is good
- No crashes in normal use

### What's Broken ❌

**CI Pipeline:**
- PR #21 attempted to fix whisper.cpp installation in GitHub Actions
- Tests are failing (need technical report from Claude Code Local)
- Cannot merge to main until CI is green

**Chat Integration:**
- Database schema for chat sessions: NOT IMPLEMENTED
- Tauri commands for chat: NOT IMPLEMENTED  
- Claude API integration: NOT IMPLEMENTED
- Chat UI: NOT IMPLEMENTED

**Claude OAuth Discovery:**
- Unknown if we can use Max plan OAuth
- No client_id discovered yet
- Fallback: API key entry (separate billing)

### What's In Progress 🚧

**Waiting on:**
- Technical report from Claude Code (Local) on current errors
- CI fix to get PR #21 green
- Decision on Claude integration approach (OAuth vs API key)

---

## TECHNICAL ARCHITECTURE

### Current (Stage C)

```
User Input (Voice)
    ↓
CPAL Audio Capture (48kHz)
    ↓
Rubato Resampler (16kHz)
    ↓
WAV File Writer
    ↓
Whisper.cpp FFI (C++ via Rust)
    ↓
Transcript Text
    ↓
SQLite Database
    ↓
Svelte UI Display
```

**Plugin System:**
- WhisperCppPlugin (primary, fast)
- CandlePlugin (fallback, pure Rust)

### Target (Chat Integration)

```
User Input (Voice)
    ↓
[Same transcription pipeline]
    ↓
Transcript appears in Chat UI
    ↓
User decides: Send to Claude? (YES/NO)
    ↓
IF YES:
    Claude API Call (OAuth or API key)
    ↓
    Claude Response
    ↓
    Display in Chat
    ↓
    Save to chat_sessions + messages tables
    ↓
    User can continue conversation
```

**New Database Schema Needed:**
```sql
chat_sessions (id, title, created_at, updated_at)
messages (id, session_id, role, content, created_at)
session_recordings (id, session_id, recording_id)
```

---

## CRITICAL PATH TO SHIP

### Phase 1: Fix CI ⚠️ BLOCKER

**Goal:** Get PR #21 merged with green tests

**Blockers:**
- Need technical report from Claude Code (Local)
- Understand what errors are occurring
- Fix or work around them

**Actions:**
1. Receive technical report
2. Analyze errors
3. Create focused fix (ONE thing at a time)
4. Test locally
5. Push, verify CI green
6. Merge

**Time:** Unknown until we see errors

### Phase 2: Chat Database

**Goal:** Add tables for chat sessions and messages

**Tasks:**
1. Create migration: `003_chat_sessions.sql`
2. Add Rust models: `ChatSession`, `Message`
3. Create `ChatRepository` with CRUD operations
4. Test locally

**Deliverable:** Can create sessions and messages in DB

**Time:** 1-2 hours

### Phase 3: Chat Commands

**Goal:** Expose chat operations to frontend

**Tasks:**
1. Create `src-tauri/src/commands/chat.rs`
2. Commands:
   - `create_chat_session(title) -> session_id`
   - `get_chat_sessions() -> Vec<ChatSession>`
   - `add_message(session_id, role, content) -> message_id`
   - `get_session_messages(session_id) -> Vec<Message>`
3. Register commands in `main.rs`
4. Test via browser console

**Deliverable:** Frontend can call chat operations

**Time:** 1 hour

### Phase 4: Claude API Integration

**Goal:** Send transcripts to Claude, get responses

**Tasks:**
1. Create `ClaudeService` (Rust)
2. API call implementation with error handling
3. Tauri commands:
   - `send_to_claude(messages, api_key) -> response`
   - `process_transcript_with_claude(transcript, api_key) -> response`
4. Test with real API key

**Deliverable:** Can send prompts, receive Claude responses

**Time:** 2 hours

**Decision Needed:** OAuth or API key?
- OAuth: Use Max plan, no extra billing (if we can crack it)
- API key: User provides, separate billing (guaranteed to work)

### Phase 5: Chat UI

**Goal:** Sidebar with sessions, main window with messages

**Tasks:**
1. Create Svelte stores (chat state)
2. `ChatSidebar.svelte` (list sessions, create new)
3. `ChatMessages.svelte` (show messages, input box)
4. Wire up to Tauri commands
5. Integrate with existing Record tab

**Deliverable:** Working chat interface

**Time:** 3-4 hours

### Phase 6: Integration & Testing

**Goal:** Record → Transcribe → Send to Claude → Chat flow works end-to-end

**Tasks:**
1. Wire recording to chat (create session on record)
2. Add "Send to Claude" button
3. Handle loading states
4. Error handling (API failures, rate limits)
5. Test full user journey 100 times

**Deliverable:** Alex can use BrainDump for crisis processing

**Time:** 2-3 hours

---

## TOTAL TIME TO SHIP

**Optimistic:** 10-12 hours (if CI fixes quickly)  
**Realistic:** 15-20 hours (accounting for debugging)  
**Pessimistic:** 30+ hours (if major blockers)

**Target:** Ship by end of next week (Nov 22)

---

## QUALITY GATES

Before shipping, we MUST verify:

### Functional Requirements ✅

- [ ] Can record audio
- [ ] Can transcribe locally
- [ ] Can create chat sessions
- [ ] Can send to Claude
- [ ] Can receive Claude response
- [ ] Can continue conversation
- [ ] All data saves to DB
- [ ] Can view chat history

### Non-Functional Requirements ✅

- [ ] App launches in <500ms
- [ ] No crashes in 100 sessions
- [ ] Clear error messages (no silent failures)
- [ ] Works without internet (local mode)
- [ ] Privacy preserved (local-only option)
- [ ] Bundle size <20MB

### User Acceptance ✅

- [ ] Codio can use it for real crisis processing
- [ ] Flow feels natural (no friction)
- [ ] Errors are helpful, not scary
- [ ] Fast enough to not interrupt thought
- [ ] Private enough to trust with sensitive content

**If ANY gate fails:** Fix before shipping.

---

## CURRENT BLOCKERS (As of Saturday Nov 15)

### 1. CI Pipeline Failures ⚠️ HIGH PRIORITY

**Status:** Waiting for technical report from Claude Code (Local)

**What we know:**
- PR #21 attempted whisper.cpp CI fix
- Some tests are failing
- Cannot merge until green

**What we need:**
- Specific error messages
- Which tests are failing
- Root cause analysis

**Action:** Receive report, analyze, create focused fix

### 2. Claude Web Execution Issues ⚠️ MEDIUM PRIORITY

**Status:** Claimed work done, likely hallucinated or incomplete

**What happened:**
- Gave Claude Web overnight execution plan
- Claimed completion after 20 minutes
- Suspicious (should take 4-6 hours)

**What we need:**
- Verify what actually exists on GitHub
- Check for any salvageable work
- Decide: Redo ourselves or different approach

**Action:** Manual verification of GitHub state

### 3. OAuth vs API Key Decision 🤔 NEEDS DECISION

**Status:** Unknown if Claude Max plan OAuth is accessible

**Options:**
A. **OAuth (preferred):** Use Max plan, no extra billing
B. **API Key (fallback):** User provides, separate billing

**Blocker:** Need to reverse engineer Claude Code's OAuth flow

**Action:** 
- Try discovery (2 hours max)
- If blocked, use API key approach
- Ship with API key, add OAuth later if possible

---

## LESSONS LEARNED

### What Works 🎯

1. **Codio as PM, Claude as executor** - Clear roles prevent circular problem-solving
2. **One feature = One PR** - Easy to review, easy to revert
3. **Test locally first** - Don't rely on CI to catch basic errors
4. **Document decisions** - Prevents re-litigation of settled questions
5. **Real user testing** - Codio's 3 months of daily use validated Stage C

### What Doesn't Work ❌

1. **Autonomous overnight execution** - LLMs hallucinate completion
2. **Clumping features in PRs** - Creates merge conflicts, hard to debug
3. **Circular AI problem-solving** - Multiple Claudes going in circles
4. **Ignoring knowledge cutoff** - Old docs become obsolete quickly
5. **Timeline-based planning** - Estimates are always wrong, focus on execution

### What We'll Do Differently ✅

1. **One task at a time** - Complete before starting next
2. **Verify before trusting** - Check GitHub, don't trust claims
3. **Document technical state** - What actually works, not plans
4. **Clear handoffs** - Specific, executable instructions
5. **Quality gates** - Don't skip testing to hit arbitrary deadlines

---

## NEXT ACTIONS (When Technical Report Arrives)

### Immediate

1. **Read technical report from Claude Code (Local)**
2. **Analyze errors** - What's actually broken?
3. **Create fix strategy** - ONE focused fix, not multiple changes
4. **Test fix locally** - Before pushing to CI
5. **Push to PR #21** - Get CI green
6. **Merge** - Move to next phase

### Short-term (After CI Green)

1. **Implement chat database schema** (Phase 2)
2. **Add Tauri chat commands** (Phase 3)
3. **Decide on Claude integration** (OAuth or API key)
4. **Build Claude API service** (Phase 4)

### Medium-term (Next Week)

1. **Build chat UI** (Phase 5)
2. **Integration testing** (Phase 6)
3. **User acceptance testing** (Codio uses it for real)
4. **Fix bugs found in testing**
5. **Ship v3.0**

---

## SUCCESS METRICS

### We succeeded when:

✅ Codio can open BrainDump during a crisis moment  
✅ Record stream-of-consciousness voice  
✅ Get instant transcription  
✅ Send to Claude for processing  
✅ Receive helpful, empathetic reflection  
✅ Continue conversation to process emotions  
✅ All data stays private and local  
✅ Zero friction, zero failures, zero data loss

### We failed if:

❌ App crashes during crisis  
❌ Transcription fails silently  
❌ Claude integration doesn't work  
❌ Data is lost  
❌ Privacy is compromised  
❌ Too slow or complex to use in crisis

---

## RESOURCES

### Technical Contacts
- **Claude Desktop (Me):** Product Development Manager, documentation keeper
- **Claude Code (Local):** Technical consultant, has CLI access
- **Claude Code (Web):** Execution engine (use with caution, verify output)
- **Codio:** Product Manager, ultimate decision maker, real user

### Repository
- **GitHub:** https://github.com/Iamcodio/IAC-031-clear-voice-app
- **Main Branch:** `main`
- **Active PRs:** Check status before creating new ones

### Documentation
- **This File:** Master plan (single source of truth)
- **Technical Status:** TECHNICAL_STATUS_2025-11-15.md (current state snapshot)
- **Current Checkpoint:** CHECKPOINT_SATURDAY_EVENING.md (active session)
- **Archive:** /docs/pm/archive/ (old stage work, for reference only)

---

## FINAL NOTES

**This is a mission, not a job.**

We're building a tool that could save someone's life. Not hyperbole - literally. When someone is in crisis, this tool needs to work. Every time. Without fail.

**Quality over timeline.** Ship when ready, not when planned.

**Privacy is sacred.** User's darkest moments stay private unless they choose otherwise.

**Fail loudly, never silently.** If something breaks, tell the user clearly and offer a path forward.

**Test like lives depend on it.** Because they might.

---

**Status:** ACTIVE  
**Owner:** Codio (Product Manager)  
**Maintained By:** Claude Desktop (Product Development Manager)  
**Last Updated:** Saturday, November 15, 2025 21:00 GMT

**Next Update:** After receiving technical report and fixing CI
