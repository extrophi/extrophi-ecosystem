# Export Button - Quick Reference Guide

## Location
**File**: `/home/user/IAC-031-clear-voice-app/src/components/ChatPanel.svelte`
**UI Position**: Chat Header (Top-right corner)

---

## Visual Layout

```
┌──────────────────────────────────────────────────────────┐
│  Chat Session                 [📥 Export to Markdown]    │ ← Header
├──────────────────────────────────────────────────────────┤
│                                                          │
│  👤 User: Hello, how are you?                           │
│                                                   10:30  │
│                                                          │
│  🤖 Assistant: I'm doing well, thanks!                  │
│  10:31                                                   │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  Type a message...                               [Send]  │
└──────────────────────────────────────────────────────────┘

Hover over button shows tooltip:
"Export session to Markdown (Cmd+E or Ctrl+E)"
```

---

## Keyboard Shortcut

**Mac**: `Cmd + E`
**Windows/Linux**: `Ctrl + E`

Works from anywhere in the application when:
- A session is selected
- Session has at least one message

---

## Button States

### 1. Normal (Ready to Export)
- Blue gradient background (#007aff → #0056b3)
- Drop shadow
- Download icon + "Export to Markdown" text

### 2. Hover
- Darker gradient (#0056b3 → #003d82)
- Button lifts up 2px
- Larger shadow for emphasis

### 3. Disabled (No Session or Empty)
- Gray background (#cccccc)
- No shadow
- Not clickable
- Shows when:
  - No session selected
  - Current session has 0 messages

### 4. Active (Clicked)
- Button presses down
- Reduced shadow

---

## Notifications

### Success Toast
```
┌────────────────────────────────────────┐
│ ✓ Exported to: ~/Documents/BrainDump/ │
│   session-2025-11-16.md                │
└────────────────────────────────────────┘
```
- Green background
- Shows for 5 seconds
- Displays full file path

### Error Toast
```
┌─────────────────────────────────┐
│ ✗ Cannot export empty session   │
└─────────────────────────────────┘
```
- Red background
- Shows for 3 seconds
- Clear error message

---

## User Flow

```
┌─────────────────┐
│ User has active │
│ chat session    │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    [Click button]   [Press Cmd+E]
         │                 │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  Validation:    │
         │  - Session?     │
         │  - Messages?    │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   Export to     │
         │   Markdown      │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  Show success   │
         │  toast with     │
         │  file path      │
         └─────────────────┘
```

---

## Code Snippets

### Keyboard Handler (Lines 108-116)
```javascript
function handleGlobalKeydown(event) {
  // Cmd+E (Mac) or Ctrl+E (Windows/Linux) for export
  if ((event.metaKey || event.ctrlKey) && event.key === 'e') {
    event.preventDefault();
    if (currentSession && messages.length > 0) {
      exportSession();
    }
  }
}
```

### Global Listener (Line 119)
```svelte
<svelte:window onkeydown={handleGlobalKeydown} />
```

### Button Element (Lines 130-143)
```svelte
<button
  onclick={exportSession}
  class="export-btn"
  disabled={!currentSession || messages.length === 0}
  title="Export session to Markdown (Cmd+E or Ctrl+E)"
  aria-label="Export session to Markdown"
>
  <svg>...</svg>
  Export to Markdown
</button>
```

### Key CSS (Lines 230-267)
```css
.export-btn {
  background: linear-gradient(135deg, #007aff 0%, #0056b3 100%);
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.2);
  font-weight: 600;
  /* ... */
}

.export-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 122, 255, 0.4);
}
```

---

## Testing Commands

```bash
# Build and verify
npm install
npm run build

# Run development mode
npm run tauri dev
```

---

## Accessibility Features

- ✅ Semantic `<button>` element
- ✅ ARIA label for screen readers
- ✅ Keyboard navigation support (Tab to focus)
- ✅ Keyboard shortcut (Cmd+E / Ctrl+E)
- ✅ Clear disabled states
- ✅ Descriptive tooltip
- ✅ Visual focus indicators

---

## Common Issues & Solutions

### Issue: Keyboard shortcut not working
**Solution**: Ensure chat window has focus

### Issue: Button disabled
**Solution**: Select a session and add messages

### Issue: Export path unclear
**Solution**: Check success toast for full path
**Default**: `~/Documents/BrainDump/`

---

## Related Files

- **Backend**: `src-tauri/src/commands/session.rs` (export_session command)
- **Database**: `src-tauri/src/database.rs` (message retrieval)
- **Types**: `src-tauri/src/models.rs` (Session/Message models)

---

## Changelog

**2025-11-16**: Issue #7 Complete
- ✅ Added keyboard shortcut (Cmd+E / Ctrl+E)
- ✅ Enhanced button styling (gradient + shadows)
- ✅ Added tooltip with shortcut hint
- ✅ Improved empty session validation
- ✅ Updated documentation

---

**Quick Links**:
- Full documentation: `ISSUE-7-EXPORT-BUTTON-IMPROVEMENTS.md`
- Source file: `src/components/ChatPanel.svelte`
- Build status: ✅ PASSING
