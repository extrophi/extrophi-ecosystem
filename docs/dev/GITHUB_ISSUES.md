# GitHub Issues for BrainDump v3.0 MVP

## Issue #1: Complete Manual Testing Checklist
**Priority**: HIGH
**Labels**: testing, MVP, blocked-by-pr

### Description
Complete the manual testing checklist from HANDOVER_MVP_v3.0.md now that build issues are resolved.

### Testing Checklist

#### Test 1: Application Build ✅
- [x] Application compiles with no errors
- [x] All dependencies resolve correctly
- [x] Build succeeds on macOS with M2

#### Test 2: Application Launch ✅
- [x] Application starts without crashes
- [x] Backend systems initialize (Whisper, OpenAI, Claude, Database)
- [x] UI renders all components

#### Test 3: OpenAI API Key Setup
- [ ] Open Settings panel
- [ ] Enter valid OpenAI API key
- [ ] Click Save button
- [ ] Verify key stored in macOS Keychain
- [ ] Click Test button
- [ ] Verify connection success message
- [ ] Test with invalid key - verify error handling

#### Test 4: Claude API Key Setup
- [ ] Enter valid Claude API key (sk-ant-...)
- [ ] Click Save button
- [ ] Verify key stored in Keychain
- [ ] Click Test button
- [ ] Verify connection success

#### Test 5: Provider Selection
- [ ] Toggle between OpenAI and Claude providers
- [ ] Verify selection persists across app restarts
- [ ] Verify correct API used for each provider

#### Test 6: Recording to Auto-Session Flow
- [ ] Click microphone/record button
- [ ] Record 5-10 seconds of clear speech
- [ ] Click stop button
- [ ] Verify auto-session created in sidebar
- [ ] Verify transcription appears in chat panel
- [ ] Verify AI response generated (using selected provider)
- [ ] Check response quality and relevance

#### Test 7: Chat Functionality
- [ ] Type message in chat input field
- [ ] Press Enter to send
- [ ] Verify message appears in chat history
- [ ] Verify AI response generated
- [ ] Send multiple messages
- [ ] Verify conversation context maintained
- [ ] Test with long messages (500+ characters)

#### Test 8: Markdown Export
- [ ] Create session with 5+ messages
- [ ] Click "Export to Markdown" button
- [ ] Verify file saved to ~/Downloads
- [ ] Open exported file
- [ ] Verify markdown formatting correct
- [ ] Verify all messages included
- [ ] Verify timestamps present
- [ ] Verify session title included

#### Test 9: Privacy Scanner
- [ ] Speak or type email address
- [ ] Verify privacy panel highlights it as "caution"
- [ ] Type SSN or credit card number
- [ ] Verify privacy panel highlights as "danger"
- [ ] Verify scanner is non-blocking (can still send)
- [ ] Type PII in multiple messages
- [ ] Verify all instances detected

#### Test 10: Error Handling
- [ ] Remove API key and attempt chat
- [ ] Verify graceful error message
- [ ] Disconnect network and send message
- [ ] Verify timeout handling
- [ ] Record corrupted/silent audio
- [ ] Verify error handling
- [ ] Fill database with 100+ sessions
- [ ] Verify performance remains acceptable

#### Test 11: Session Management
- [ ] Create multiple sessions
- [ ] Switch between sessions
- [ ] Verify correct messages load for each session
- [ ] Delete a session
- [ ] Verify session removed from sidebar
- [ ] Verify database cleaned up

### Acceptance Criteria
- All test cases pass
- No crashes or unhandled errors
- Performance acceptable on macOS M-series
- All features work as documented in HANDOVER_MVP_v3.0.md

### References
- See `docs/dev/TESTING_REPORT_2025-11-15.md` for current status
- See `docs/dev/HANDOVER_MVP_v3.0.md` for feature documentation

---

## Issue #2: Improve UI Accessibility
**Priority**: MEDIUM
**Labels**: accessibility, ui, enhancement

### Description
Add proper ARIA labels to interactive elements to improve screen reader support.

### Current Warnings
```
The button with text content 'Start Recording' does not have an aria-label attribute.
The button with text content 'Settings' does not have an aria-label attribute.
```

### Tasks
- [ ] Add aria-label to record button
- [ ] Add aria-label to settings button
- [ ] Add aria-label to export button
- [ ] Add aria-label to session delete buttons
- [ ] Add aria-label to chat send button
- [ ] Add aria-label to privacy panel close button
- [ ] Test with screen reader (VoiceOver on macOS)

### Acceptance Criteria
- All interactive elements have descriptive aria-labels
- No accessibility warnings in console
- Screen reader can navigate entire UI

---

## Issue #3: Add Integration Tests
**Priority**: HIGH
**Labels**: testing, ci/cd

### Description
Add automated integration tests for core workflows to prevent regressions.

### Test Suites Needed

#### Backend Tests (Rust)
- [ ] Database CRUD operations
- [ ] Session creation and retrieval
- [ ] Message storage and retrieval
- [ ] Keychain key storage/retrieval
- [ ] OpenAI API client (with mocked API)
- [ ] Claude API client (with mocked API)

#### Frontend Tests (Svelte + Vitest)
- [ ] Component rendering tests
- [ ] User interaction tests (button clicks)
- [ ] State management tests
- [ ] Privacy scanner pattern matching
- [ ] Markdown export formatting

#### End-to-End Tests (Playwright or Tauri Test)
- [ ] Complete recording → transcription → chat flow
- [ ] API key setup flow
- [ ] Session creation and switching
- [ ] Export functionality

### Implementation
```bash
# Backend tests
cd src-tauri
cargo test

# Frontend tests
npm test

# E2E tests (to be added)
npm run test:e2e
```

### Acceptance Criteria
- 80%+ code coverage
- All core workflows covered
- Tests run in CI on every PR
- Tests pass before merge allowed

---

## Issue #4: Document whisper-cpp Installation
**Priority**: HIGH
**Labels**: documentation, setup

### Description
Create clear installation guide for whisper-cpp dependency across all platforms.

### Documentation Needed

#### README.md Update
Add Prerequisites section:
```markdown
## Prerequisites

### macOS
\`\`\`bash
brew install whisper-cpp
\`\`\`

### Linux (Ubuntu/Debian)
\`\`\`bash
# Install from source
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
sudo make install
\`\`\`

### Linux (Fedora)
\`\`\`bash
sudo dnf install whisper-cpp
\`\`\`

### Verification
\`\`\`bash
pkg-config --libs whisper
# Should output: -L/path/to/lib -lwhisper
\`\`\`
```

#### INSTALL.md (New File)
- [ ] Detailed installation steps for each platform
- [ ] Troubleshooting section for common errors
- [ ] Model download instructions
- [ ] GPU acceleration setup (Metal, CUDA, OpenCL)

#### build.rs Comments
- [ ] Add comments explaining pkg-config usage
- [ ] Document fallback behavior
- [ ] Link to installation guide in error messages

### Acceptance Criteria
- New users can install dependencies without Claude assistance
- All platforms documented (macOS, Linux)
- Troubleshooting covers common issues
- Error messages link to installation guide

---

## Issue #5: Set Up Continuous Integration
**Priority**: HIGH
**Labels**: ci/cd, automation

### Description
Configure GitHub Actions workflow for automated testing on every PR.

### Workflow Requirements

#### Jobs Needed
1. **Rust Backend Tests**
   - Run `cargo check`
   - Run `cargo test`
   - Run `cargo clippy`

2. **Frontend Tests**
   - Run `npm test`
   - Run `npm run check` (Svelte type checking)
   - Run `npm run lint`

3. **Build Verification**
   - Build on macOS (Intel + M-series if possible)
   - Build on Linux (Ubuntu)
   - Verify application launches

4. **Security Checks**
   - Run `cargo audit` for Rust dependencies
   - Run `npm audit` for JavaScript dependencies

### Example Workflow
See `.github/workflows/ci.yml` (to be created)

### Branch Protection
- [ ] Require CI to pass before merge
- [ ] Require at least 1 approval
- [ ] Require branch up to date with main

### Acceptance Criteria
- CI runs on every PR and push to main
- All checks must pass for merge
- Clear failure messages for debugging
- Workflow completes in < 10 minutes

---

## Issue #6: SECURITY - Improve API Key Management
**Priority**: CRITICAL
**Labels**: security, enhancement

### Description
Improve API key handling to prevent accidental exposure.

### Security Issues
- ⚠️ API keys should NEVER be committed to git
- ⚠️ .env files should be in .gitignore
- ⚠️ Keys should only be stored in system keychain

### Implementation Tasks

#### Backend
- [x] Keys stored in macOS Keychain (already implemented)
- [ ] Add key validation before storage
- [ ] Add key encryption at rest (additional layer)
- [ ] Rate limit API key test attempts
- [ ] Log key access attempts for security audit

#### Frontend
- [ ] Mask API keys in UI (show only last 4 chars)
- [ ] Add "Show/Hide" toggle for key input
- [ ] Clear input field after successful save
- [ ] Add "Delete Key" button
- [ ] Show key status indicator (✓ configured, ⚠ not configured)

#### Documentation
- [ ] Add security best practices to README
- [ ] Document key rotation process
- [ ] Add warning about .env files
- [ ] Create SECURITY.md with responsible disclosure

### Current Implementation
The SettingsPanel.svelte already has provider selection:
```svelte
<div class=\"provider-choice\">
  <label>
    <input type=\"radio\" bind:group={selectedProvider} value=\"openai\" />
    OpenAI (GPT-4) - $0.15/1M tokens
  </label>
  <label>
    <input type=\"radio\" bind:group={selectedProvider} value=\"claude\" />
    Claude (Anthropic) - $3/1M tokens
  </label>
</div>
```

### Improvements Needed
- [ ] Save provider selection to database
- [ ] Load provider selection on app start
- [ ] Pass selected provider to backend commands
- [ ] Update backend to use selected provider for chat
- [ ] Add visual indicator of active provider

### Acceptance Criteria
- Keys never appear in git history
- Keys never logged to console
- Keys encrypted in keychain
- Clear security documentation
- Provider selection persists across restarts

---

## Issue #7: Add Whisper Model Selection
**Priority**: MEDIUM
**Labels**: enhancement, whisper

### Description
Allow users to select different Whisper models for different accuracy/speed tradeoffs.

### Models Available
- tiny.en (75 MB) - Fastest, lowest accuracy
- base.en (142 MB) - Currently used, good balance
- small.en (466 MB) - Better accuracy
- medium.en (1.5 GB) - High accuracy
- large-v3 (2.9 GB) - Best accuracy, slowest

### UI Design
Add to Settings Panel:
```svelte
<section class=\"model-section\">
  <h3>Whisper Model</h3>
  <p class=\"help-text\">Larger models are more accurate but slower</p>

  <select bind:value={selectedModel}>
    <option value=\"tiny.en\">Tiny (Fastest)</option>
    <option value=\"base.en\">Base (Balanced) - Recommended</option>
    <option value=\"small.en\">Small (More Accurate)</option>
    <option value=\"medium.en\">Medium (High Accuracy)</option>
    <option value=\"large-v3\">Large (Best Accuracy)</option>
  </select>

  <button onclick={downloadModel}>Download Model</button>
</section>
```

### Backend Tasks
- [ ] Add model selection to database schema
- [ ] Implement model download command
- [ ] Show download progress
- [ ] Implement model switching
- [ ] Cache multiple models

### Acceptance Criteria
- Users can select and download models
- App switches models without restart
- Download progress shown
- Models cached locally

---

---

## Issue #8: Change Record Button to Square with Rounded Corners
**Priority**: LOW
**Labels**: ui, design

### Description
Change the main record button from a circular blue button to a square button with rounded corners.

### Current Design
- Shape: Circle (`border-radius: 50%`)
- Color: Blue (`background: #007aff`)

### Requested Design
- Shape: Square with rounded corners
- Border radius: 12px-16px (rounded, not circular)
- Keep existing color scheme (blue is fine)
- Maintain same functionality

### File to Update
- `src/App.svelte` - Main recording button component

### Acceptance Criteria
- Record button is square with rounded corners
- Button maintains same size (approximately)
- All existing functionality works
- Visual design is clean and simple

---

## Priority Order for Coding Team

1. **Issue #6** (SECURITY) - Fix API key exposure risk
2. **Issue #4** (DOCS) - Document installation
3. **Issue #5** (CI/CD) - Set up automated testing
4. **Issue #1** (TESTING) - Complete manual QA
5. **Issue #3** (TESTS) - Add integration tests
6. **Issue #2** (UI) - Accessibility improvements
7. **Issue #7** (FEATURE) - Model selection
8. **Issue #8** (UI) - Remove blue tint
