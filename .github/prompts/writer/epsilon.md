## Agent: EPSILON (Writer Module)
**Duration:** 2 hours
**Branch:** `writer`
**Dependencies:** DELTA #35

### Task
Build Terminal panel using xterm.js for command execution

### Technical Reference
- `/docs/pm/writer/TECHNICAL-PROPOSAL-WRITER.md`
- xterm.js documentation

### Deliverables
- `writer/src/islands/TerminalIsland.svelte`
- xterm.js integration
- Command execution via Tauri
- Command history (up/down arrows)
- Auto-completion (optional)

### Features
1. **Full terminal emulator** (xterm.js)
2. **Tauri shell commands** (execute via backend)
3. **Command history** (localStorage persistence)
4. **Directory awareness** (show current path)
5. **Color support** (ANSI escape codes)

### Integration
```typescript
// Tauri command
#[tauri::command]
async fn execute_shell_command(cmd: String) -> Result<String, String> {
    // Execute shell command
    // Return stdout + stderr
}
```

### UI Requirements
- Svelte 5 runes syntax
- xterm.js npm package
- Fit addon for responsive sizing
- Dark theme (matches Editor)
- Toggle visibility (Ctrl+`)

### Success Criteria
✅ xterm.js renders in island
✅ Commands execute via Tauri
✅ History navigation works
✅ ANSI colors display
✅ Resizable terminal
✅ Tests pass

### Commit Message
```
feat(writer): Add Terminal panel with xterm.js

Implements full terminal emulator:
- xterm.js integration
- Tauri shell command execution
- Command history (up/down arrows)
- ANSI color support
- Toggle with Ctrl+`

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #51 when complete.**
