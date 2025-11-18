# Keyboard Shortcuts - Visual Demo

## Help Modal Preview

When users press `Cmd/Ctrl + ?`, they see:

```
┌─────────────────────────────────────────────────────────────┐
│  Keyboard Shortcuts                                      [×] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GLOBAL                        NAVIGATION                  │
│  ⌘+R     Start/Stop recording  ⌘+1    Switch to Chat      │
│  ⌘+N     New chat session      ⌘+2    Switch to Transcript│
│  ⌘+E     Export session        ⌘+3    Switch to Prompts   │
│  ⌘+,     Open settings         ⌘+4    Toggle Privacy      │
│  ⌘+F     Focus search                                      │
│  ⌘+?     Show shortcuts                                    │
│                                                             │
│  CHAT INPUT                    SESSIONS                    │
│  ↵        Send message         ↑/↓    Navigate sessions   │
│  ⇧+↵      New line             ↵      Select session      │
│  Esc      Clear input                                      │
│                                                             │
│  GENERAL                                                    │
│  ⇥        Navigate elements                                │
│  Esc      Close modals                                     │
│                                                             │
│                                           [ Got it! ]      │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Quick Recording
```
User: *presses Cmd+R*
App:  ⏺️  Recording... (0:05)
User: *speaks into microphone*
User: *presses Cmd+R again*
App:  ✅ Transcribing...
App:  ✅ Session created! Ready for chat.
```

### Example 2: Fast Navigation
```
User: *presses Cmd+1*
App:  💬 [Switches to Chat view]

User: *presses Cmd+2*
App:  📝 [Switches to Transcript view]

User: *presses Cmd+4*
App:  🔒 [Opens Privacy panel]
```

### Example 3: Session Navigation
```
User: *clicks on sessions list*
User: *presses ↓ ↓ ↓*
App:  [Highlights session 4]
User: *presses Enter*
App:  [Loads session 4 messages]
```

### Example 4: Chat Workflow
```
User: *types message in chat*
User: "How can I improve this transcript?"
User: *presses Enter*
App:  ✅ Message sent
App:  🤖 [Claude responds]

User: *starts typing another message*
User: "Actually, never mind"
User: *presses Escape*
App:  [Input cleared]
```

## Platform Differences

### macOS Display
- `⌘+R` (Command symbol)
- `⇧+↵` (Shift + Return)
- `⌥` (Option symbol, future use)

### Windows/Linux Display
- `Ctrl+R` (Text-based)
- `Shift+Enter` (Text-based)
- `Alt` (Text-based, future use)

## Visual Focus Indicators

### Sessions List
```
┌──────────────────────────┐
│ Chat Sessions         [+]│
├──────────────────────────┤
│ Session 1                │
│ Session 2           ← Selected (blue border)
│ Session 3                │
└──────────────────────────┘
    ↑
When focused (light blue outline)
```

### Chat Input
```
┌────────────────────────────────────┐
│ Type a message...                  │ ← Escape clears
│                                    │
│                               [>]  │ ← Enter sends
└────────────────────────────────────┘
```

## Smart Behavior

### Context Awareness
```
Scenario: User is typing in search box
Input:    "brain dump session"
Action:   Presses Cmd+R
Result:   ❌ Nothing happens (typing detected)

But...

Action:   Presses Cmd+?
Result:   ✅ Help modal opens (always works!)
```

### Modal Priority
```
State: Help modal open
       Settings panel open
       Privacy panel open

User:  Presses Escape
App:   Closes help modal first

User:  Presses Escape again
App:   Closes settings panel

User:  Presses Escape again
App:   Closes privacy panel
```

## Accessibility Features

### Keyboard-Only Navigation
```
1. Press Tab to focus record button
2. Press Space to start recording
3. Press Tab to move to sessions list
4. Press ↑/↓ to navigate sessions
5. Press Enter to select
6. Press Tab to focus message input
7. Type message and press Enter
8. Press Cmd+E to export session
```

### Screen Reader Support
```
ARIA labels:
- role="dialog" for help modal
- role="listbox" for sessions list
- aria-label="Start recording" for buttons
- aria-modal="true" for modals
```

## Mobile Behavior

On mobile devices (touch screens):
- ✅ Help modal still accessible (tap help icon)
- ✅ All shortcuts documented for reference
- ⚠️ Physical keyboard required for shortcuts
- ℹ️ Help shows "keyboard not available" message

## Error Prevention

### Invalid States
```
Shortcut: Cmd+R (record)
State:    Model not loaded
Result:   ❌ No action (prevented)
Message:  "Please wait for model to load..."

Shortcut: Cmd+E (export)
State:    No session or empty session
Result:   ❌ No action (prevented)
Message:  [No message, silently ignored]
```

## Performance

### Load Impact
- Help modal: Only rendered when visible
- Event listeners: Single global listener
- Memory: ~50 KB when help modal shown
- CPU: Negligible overhead

### Responsiveness
- Shortcut response: <10ms
- Modal animation: 200-300ms
- No input lag
- Smooth transitions

## Browser Compatibility

| Browser | Shortcuts | Help Modal | Navigation |
|---------|-----------|------------|------------|
| Chrome 90+ | ✅ | ✅ | ✅ |
| Firefox 88+ | ✅ | ✅ | ✅ |
| Safari 14+ | ✅ | ✅ | ✅ |
| Edge 90+ | ✅ | ✅ | ✅ |

## Known Edge Cases

1. **Browser Extensions**
   - Some extensions intercept shortcuts
   - Example: Vimium intercepts Cmd+F
   - Solution: Disable extension or remap

2. **Non-English Keyboards**
   - `?` key location varies
   - May require Shift on some layouts
   - Future: Support alternative help key

3. **Sticky Modifiers**
   - Accessibility feature on macOS
   - Can cause modifier to "stick"
   - Not a bug, system behavior

## Future Enhancements

Coming in v3.1:
- [ ] Customizable shortcuts
- [ ] Quick command palette (Cmd+K)
- [ ] Shortcut recording
- [ ] Export shortcuts cheat sheet
