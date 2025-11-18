# GitHub Issues for Web Claude Team
**Total Issues**: 14
**Estimated Total Effort**: 166 hours
**Priority Distribution**: 4 Critical | 3 High | 2 Medium | 5 Low

**Instructions**: Create these as individual GitHub issues. Copy each section as a separate issue with the specified labels and priority.

---

## PRIORITY 1: CRITICAL (Must Fix Before v1.0)

### Issue #1: Implement Provider Selection Persistence
**Labels**: `bug`, `P1-critical`, `backend`, `database`
**Estimated Effort**: 2-3 hours

#### Description
User selects OpenAI or Claude in Settings Panel but the selection is not saved to database. On app restart, it always defaults to "openai".

#### Current Behavior
- User selects provider via radio button in `SettingsPanel.svelte`
- Selection stored only in UI state variable `selectedProvider`
- App restart → resets to default ("openai")

#### Expected Behavior
- Selection saved to database settings table
- Loaded on app startup
- Persists across restarts

#### Implementation Steps
1. Add `provider_preference` column to settings table (or create settings table if missing)
2. Create Rust command: `save_provider_preference(provider: String)`
3. Create Rust command: `get_provider_preference() -> String`
4. Update `SettingsPanel.svelte` to call `save_provider_preference` on radio button change
5. Load preference on app startup, set UI state

#### Files to Modify
- `src-tauri/src/db/mod.rs` - Add settings table/column
- `src-tauri/src/commands.rs` - Add save/get commands
- `src/components/SettingsPanel.svelte` (lines 7, 138-156)

#### Acceptance Criteria
- [x] Provider selection persists across app restarts
- [x] Default is "openai" for fresh installs
- [x] Radio button reflects saved preference on load

---

### Issue #2: Connect Provider Selection to Backend Chat Routing
**Labels**: `bug`, `P1-critical`, `backend`, `frontend`
**Estimated Effort**: 4-5 hours

#### Description
Chat always uses Claude API regardless of which provider is selected in the UI.

#### Current Behavior
- User selects "OpenAI" in settings
- Clicks chat send button
- `ChatPanel.svelte:38` hardcoded to call `send_message_to_claude`
- Claude API used even though OpenAI was selected

#### Expected Behavior
- Chat checks selected provider preference
- Routes to `send_openai_message` if OpenAI selected
- Routes to `send_message_to_claude` if Claude selected

#### Implementation Steps
1. Pass selected provider to ChatPanel component
2. Create routing logic in `handleSend()` function
3. Call correct backend command based on provider:
   - `send_openai_message` for OpenAI
   - `send_message_to_claude` for Claude
4. Display provider indicator in chat UI
5. Handle API errors differently per provider

#### Files to Modify
- `src/components/ChatPanel.svelte` (line 38)
- `src/App.svelte` - Pass provider state to ChatPanel

#### Acceptance Criteria
- [x] Selecting OpenAI uses OpenAI GPT-4 API
- [x] Selecting Claude uses Claude API
- [x] Chat UI shows which provider is active
- [x] Error messages specific to provider used

---

### Issue #3: Create Prompt Management UI (CRUD Interface)
**Labels**: `feature`, `P1-critical`, `frontend`, `backend`
**Estimated Effort**: 12-16 hours

#### Description
Users can SELECT prompt templates but cannot CREATE, EDIT, or DELETE them. Must manually edit `.md` files in `/prompts/` directory.

#### Current State
- `TemplateSelector.svelte` shows dropdown of available prompts
- Loads from `/prompts/*.md` files
- Read-only interface

#### Needed Features
1. **Create Prompt**
   - Button to create new template
   - Modal with rich text editor
   - Save as `.md` file in `/prompts/`

2. **Edit Prompt**
   - Edit button next to each prompt
   - Load existing content into editor
   - Save changes back to file

3. **Delete Prompt**
   - Delete button with confirmation
   - Remove `.md` file
   - Can't delete default prompts

4. **Prompt Preview**
   - Show full prompt text when hovering/clicking
   - Variable substitution preview

#### Implementation Plan

**Backend Commands Needed:**
```rust
create_prompt(name: String, content: String, description: String)
update_prompt(name: String, content: String, description: String)
delete_prompt(name: String)
get_prompt_content(name: String) -> String
```

**Frontend Components Needed:**
- `PromptEditor.svelte` - Rich text editor modal
- `PromptList.svelte` - List view with CRUD actions
- Update `TemplateSelector.svelte` to include management link

#### Files to Create
- `src/components/PromptEditor.svelte`
- `src/components/PromptList.svelte`
- `src-tauri/src/services/prompt_manager.rs`

#### Files to Modify
- `src-tauri/src/commands.rs` - Add prompt CRUD commands
- `src/components/TemplateSelector.svelte` - Add "Manage Prompts" button

#### Acceptance Criteria
- [x] Can create new prompt templates from UI
- [x] Can edit existing prompts
- [x] Can delete custom prompts (not defaults)
- [x] Prompt preview shows before using
- [x] Changes immediately available in selector

---

### Issue #4: Add Session Management (Delete & Rename)
**Labels**: `feature`, `P1-critical`, `frontend`, `backend`
**Estimated Effort**: 6-8 hours

#### Description
Can create and switch sessions but cannot delete or rename them. Sessions accumulate forever with no cleanup option.

#### Current State
- Sessions listed in sidebar
- Click to switch between sessions
- No delete button
- No rename functionality

#### Needed Features

**1. Delete Session**
- Delete button (trash icon) on each session
- Confirmation dialog: "Delete session '{title}'? This cannot be undone."
- Remove from database (messages + session record)
- Update UI to show remaining sessions
- If deleted session was active, switch to another session

**2. Rename Session**
- Double-click session title to edit inline
- Save on Enter, cancel on Escape
- Update database
- Validate: title cannot be empty

**3. Session List Improvements**
- Sort options (newest first, oldest first, alphabetical)
- Session count indicator
- Last modified timestamp

#### Implementation Steps

**Backend:**
```rust
delete_session(session_id: i64)
rename_session(session_id: i64, new_title: String)
```

**Frontend:**
- Add delete button to session list items
- Add inline editing for session titles
- Add confirmation modal component

#### Files to Modify
- `src-tauri/src/commands.rs` - Add delete/rename commands
- `src-tauri/src/db/mod.rs` - Add delete cascade logic
- `src/App.svelte` - Session list UI (around line 300-400)

#### Acceptance Criteria
- [x] Can delete sessions with confirmation
- [x] Deleting active session switches to another
- [x] Can rename sessions inline
- [x] Session list updates immediately

---

## PRIORITY 2: HIGH (Nice to Have for v1.0)

### Issue #5: Add Whisper Model Selection
**Labels**: `feature`, `P2-high`, `ml`, `ui`
**Estimated Effort**: 16-20 hours

#### Description
App is hardcoded to use `ggml-base.bin` model. Users can't choose different models for speed/accuracy tradeoffs.

#### Available Models
- `tiny.en` (75 MB) - Fastest, lowest accuracy
- `base.en` (142 MB) - Current default, balanced
- `small.en` (466 MB) - Better accuracy
- `medium.en` (1.5 GB) - High accuracy
- `large-v3` (2.9 GB) - Best accuracy, slowest

#### Needed Features

**1. Model Selection UI**
- Add to Settings Panel
- Dropdown to select model
- Show model size and description
- Indicate which model is currently loaded

**2. Model Download**
- Download button for uninstalled models
- Progress bar during download
- Download from official Hugging Face repo
- Store in `~/.braindump/models/`

**3. Model Switching**
- Unload current model
- Load selected model
- Show loading status
- Handle errors gracefully

**4. Storage Management**
- Show disk space used
- Option to delete unused models
- Warn if insufficient space

#### Implementation Plan

**Backend:**
```rust
list_available_models() -> Vec<ModelInfo>
list_installed_models() -> Vec<String>
download_model(model_name: String) -> Stream<DownloadProgress>
switch_model(model_name: String)
delete_model(model_name: String)
get_current_model() -> String
```

**Frontend:**
- Add model section to SettingsPanel
- Create ModelManager component
- Progress UI for downloads

#### Files to Modify
- `src-tauri/src/services/model_manager.rs` (NEW)
- `src/components/SettingsPanel.svelte`
- `src-tauri/src/plugin/whisper_cpp.rs` - Add model switching

#### Acceptance Criteria
- [x] Can select from 5 Whisper models
- [x] Can download models with progress indication
- [x] Can switch models without app restart
- [x] Model selection persists across restarts
- [x] Can delete unused models to free space

---

### Issue #6: Implement Recording Search
**Labels**: `feature`, `P2-high`, `database`, `frontend`
**Estimated Effort**: 8-10 hours

#### Description
Search box exists in sidebar but does nothing. Need full-text search on transcripts and messages.

#### Current State
- Search input at top of sidebar (`App.svelte:460`)
- No search functionality implemented
- Database has messages with content

#### Needed Features

**1. Full-Text Search**
- Search across all session messages
- Search transcripts (user messages)
- Search AI responses
- Case-insensitive
- Highlight search terms in results

**2. Search Results UI**
- Show matching sessions
- Show snippet of matching text
- Click result to jump to session + message
- Clear search to return to session list

**3. Search Filters** (Optional)
- Filter by date range
- Filter by session
- Filter by message role (user/assistant)

#### Implementation Steps

**Backend:**
```rust
search_messages(query: String) -> Vec<SearchResult>
search_sessions(query: String) -> Vec<Session>
```

**Frontend:**
- Connect search input to backend
- Create SearchResults component
- Highlight matching text
- Navigate to matching messages

#### Files to Modify
- `src-tauri/src/commands.rs` - Add search command
- `src-tauri/src/db/mod.rs` - Add SQL full-text search
- `src/App.svelte` (line 460) - Connect search input
- `src/components/SearchResults.svelte` (NEW)

#### Acceptance Criteria
- [x] Typing in search box filters sessions
- [x] Shows matching text snippets
- [x] Clicking result navigates to message
- [x] Clear search returns to full list
- [x] Search is fast (< 500ms for 1000 messages)

---

### Issue #7: Add Audio Playback Feature
**Labels**: `feature`, `P2-high`, `audio`, `storage`
**Estimated Effort**: 12-16 hours

#### Description
Original audio recordings are not saved. Users can't replay audio to verify transcription accuracy.

#### Current State
- Audio recorded to memory
- Transcribed via Whisper
- Audio discarded after transcription
- No way to replay original

#### Needed Features

**1. Audio Storage**
- Save recordings to database as blob
- Or save to `~/.braindump/recordings/` directory
- Associate with message ID
- Limit storage (e.g., last 100 recordings or 1GB max)

**2. Audio Player Component**
- Play/pause button next to user messages
- Waveform visualization
- Playback speed control (0.5x, 1x, 1.5x, 2x)
- Download audio button

**3. Storage Management**
- Settings to enable/disable audio saving
- Auto-delete old recordings
- Show storage used in settings

#### Implementation Plan

**Backend:**
```rust
save_recording(message_id: i64, audio_data: Vec<f32>, sample_rate: u32)
get_recording(message_id: i64) -> Option<AudioData>
delete_recording(message_id: i64)
cleanup_old_recordings(keep_count: usize)
```

**Frontend:**
- AudioPlayer.svelte component
- Add play button to user messages
- Storage settings in SettingsPanel

#### Files to Create
- `src/components/AudioPlayer.svelte`
- `src-tauri/src/services/audio_storage.rs`

#### Files to Modify
- `src-tauri/src/commands.rs` - Add audio storage commands
- `src-tauri/src/db/mod.rs` - Add recordings table or blob column
- `src/components/ChatPanel.svelte` - Add play button to messages

#### Acceptance Criteria
- [x] Recordings saved automatically
- [x] Can replay any saved recording
- [x] Audio player has basic controls
- [x] Can download recordings as .wav
- [x] Storage limit enforced
- [x] Can disable audio saving in settings

---

## PRIORITY 3: MEDIUM (Post v1.0)

### Issue #8: Settings Panel Enhancements
**Labels**: `feature`, `P3-medium`, `ui`, `settings`
**Estimated Effort**: 8-12 hours

#### Features Needed

**1. Theme Selection**
- Light mode (current default)
- Dark mode
- System preference auto-detect

**2. Audio Settings**
- Input device selection (if multiple mics)
- Input gain/volume slider
- Audio format selection (WAV quality)

**3. Export Settings**
- Default export location
- Filename format template
- Include timestamps toggle

**4. General Settings**
- Default session title format
- Language selection (i18n prep)
- Auto-start on login

#### Files to Modify
- `src/components/SettingsPanel.svelte` - Add new sections
- `src-tauri/src/db/mod.rs` - Expand settings table
- `src-tauri/src/commands.rs` - Add settings CRUD

---

### Issue #9: Advanced Session Features
**Labels**: `feature`, `P3-medium`, `sessions`, `organization`
**Estimated Effort**: 16-20 hours

#### Features Needed

**1. Session Tags/Labels**
- Add tags to sessions
- Filter by tag
- Tag management (create/edit/delete)

**2. Session Export/Import**
- Export session as JSON
- Import previously exported session
- Bulk export all sessions

**3. Session Archiving**
- Archive old sessions (hide from main list)
- View archived sessions
- Unarchive if needed

**4. Session Statistics**
- Total messages count
- Word count
- Duration
- AI usage costs estimate

#### Files to Modify
- `src-tauri/src/db/mod.rs` - Add tags table, archive column
- `src/App.svelte` - Session list enhancements
- `src-tauri/src/commands.rs` - Export/import commands

---

## PRIORITY 4: LOW (Future/Nice to Have)

### Issue #10: UI/UX Polish - Square Record Button
**Labels**: `ui`, `P4-low`, `design`
**Estimated Effort**: 1 hour

#### Description
Change record button from circular blue button to square with rounded corners for cleaner, less distracting design.

#### Current Design
- Shape: Circle (`border-radius: 50%`)
- Color: Blue (`#007aff`)

#### Requested Design
- Shape: Square with rounded corners
- Border radius: 12-16px
- Keep blue color (user confirmed blue is fine)

#### Files to Modify
- `src/App.svelte` - Record button styles

---

### Issue #11: Privacy Scanner Improvements
**Labels**: `feature`, `P4-low`, `privacy`, `ml`
**Estimated Effort**: 20-24 hours

#### Features Needed

**1. ML-Based PII Detection**
- Replace regex patterns with ML model
- Better accuracy for context-aware detection
- Detect more PII types

**2. Configurable Patterns**
- User can add custom patterns
- Enable/disable specific detectors
- Adjust sensitivity levels

**3. Auto-Redaction**
- Option to automatically redact detected PII
- Replace with `[REDACTED]` before sending to AI
- Show redacted version vs original

**4. Privacy Report Export**
- Export all detected PII instances
- Review history of privacy scans
- Analytics dashboard

---

### Issue #12: Multi-language Support (i18n)
**Labels**: `feature`, `P4-low`, `i18n`
**Estimated Effort**: 20-30 hours

#### Description
Add internationalization support for UI text.

#### Supported Languages (Initial)
- English (default)
- Spanish
- French
- German
- Japanese

#### Implementation
- Use `svelte-i18n` library
- Extract all UI strings
- Create translation files
- Language selector in settings

---

### Issue #13: Keyboard Shortcuts
**Labels**: `feature`, `P4-low`, `ux`, `accessibility`
**Estimated Effort**: 4-6 hours

#### Shortcuts Needed
- `Cmd+R` / `Ctrl+R` - Start/stop recording
- `Cmd+N` / `Ctrl+N` - New session
- `Cmd+E` / `Ctrl+E` - Export current session
- `Cmd+,` / `Ctrl+,` - Open settings
- `Cmd+F` / `Ctrl+F` - Focus search box
- `Esc` - Close modals/panels

#### Implementation
- Use Tauri global shortcuts
- Add to Svelte components
- Create shortcuts help modal (`Cmd+?`)

---

### Issue #14: Accessibility Improvements
**Labels**: `accessibility`, `P4-low`, `a11y`
**Estimated Effort**: 8-10 hours

#### Current Issues
- Missing ARIA labels on buttons
- No keyboard navigation for session list
- No screen reader announcements
- Poor focus indicators

#### Fixes Needed
- Add `aria-label` to all interactive elements
- Keyboard navigation (Tab, Arrow keys)
- Screen reader announcements for actions
- High contrast mode support
- Focus visible indicators

**See Also**: `docs/dev/GITHUB_ISSUES.md` Issue #2

---

## SUMMARY

**Total Issues**: 14
**Total Estimated Effort**: 166 hours

### By Priority
- **P1 (Critical)**: 4 issues, 32 hours - *Must complete before v1.0*
- **P2 (High)**: 3 issues, 46 hours - *Should complete for v1.0*
- **P3 (Medium)**: 2 issues, 28 hours - *Nice to have*
- **P4 (Low)**: 5 issues, 60 hours - *Future enhancements*

### Recommended Approach
1. Create all 14 issues in GitHub immediately
2. Assign P1 issues to web Claude team (30 agents available)
3. Complete P1 in Sprint 1 (1 week)
4. Complete P2 in Sprint 2 (1 week)
5. Defer P3/P4 to post-v1.0 releases

---

**Document Created By**: Claude Code Assistant
**Date**: 2025-11-16
**For**: Web Claude Team Handoff
