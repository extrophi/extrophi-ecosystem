# BrainDump v3.0 - Implementation Task for Web Claude Team

## Context

You have 30 agents and unlimited usage. A local Claude Code session has prepared everything for you.

## Your Mission

Complete the missing 14 features for BrainDump v3.0 MVP. The app is **60% complete** - builds and runs, but missing critical features before production release.

---

## Start Here

### 1. Clone the repository:
```bash
git clone https://github.com/Iamcodio/IAC-031-clear-voice-app.git
cd IAC-031-clear-voice-app
git checkout claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
```

### 2. Read these documents IN ORDER:
1. **`README.md`** - Project overview
2. **`docs/dev/PROJECT_STATUS_2025-11-16.md`** - Current state (what works, what's broken)
3. **`docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`** - 14 detailed issues to implement
4. **`docs/dev/HANDOFF_TO_WEB_TEAM.md`** - Development workflow and guidelines

### 3. Create 14 GitHub issues from `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`
- Each issue has full implementation details
- Priority labels: `P1-critical`, `P2-high`, `P3-medium`, `P4-low`
- File references and code examples included
- Effort estimates provided

### 4. Implement P1 Critical features first (32 hours estimated):
- **Issue #1**: Provider selection persistence (3 hours)
- **Issue #2**: Provider backend routing (5 hours)
- **Issue #3**: Prompt management CRUD UI (16 hours)
- **Issue #4**: Session delete/rename (8 hours)

---

## Important Notes

**Tech Stack:**
- Tauri 2.0 + Svelte 5 + Rust
- whisper.cpp for transcription
- SQLite database
- OpenAI GPT-4 + Claude API

**Current State:**
- ✅ Build works: App compiles and runs successfully
- ✅ Core features work: Recording, transcription, chat, export
- ⚠️  Tests missing: No test suite exists yet - create as you implement
- ⚠️  60% feature-complete: 14 features missing

**Code Conventions:**
- **Svelte 5 runes**: Use `$props()`, `$bindable()`, `$derived()`
- **NOT**: `export let` or `$:` (Svelte 4 syntax)
- **Rust**: Follow existing patterns in codebase
- **Testing**: Create tests as you implement features

**Branch:**
- Work on: `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`
- Create PR to: `main` when ready

---

## Success Criteria

**For v1.0 Release:**
- ✅ All P1 (critical) issues implemented and tested
- ✅ All P2 (high) issues implemented and tested
- ✅ Test coverage > 60%
- ✅ Manual QA checklist complete
- ✅ CI pipeline passing
- ✅ Documentation updated
- ✅ Create PR to main when ready

---

## Priority Breakdown

### P1 Critical (Must Complete - 32 hours)
**Blocking v1.0 release:**
1. Provider selection doesn't persist (3h)
2. Chat always uses Claude regardless of UI selection (5h)
3. No prompt management CRUD UI (16h)
4. Can't delete/rename sessions (8h)

### P2 High (Should Complete - 46 hours)
**Important for UX:**
5. No visual feedback during recording (8h)
6. No chat session search (12h)
7. Export button hidden in ChatPanel (4h)

### P3 Medium (Nice to Have - 28 hours)
**Quality improvements:**
8. Settings panel not integrated in App.svelte (4h)
9. No error recovery UI (12h)

### P4 Low (Future - 60 hours)
**Enhancements:**
10. No usage statistics (16h)
11. No keyboard shortcuts (8h)
12. No multi-language support (20h)
13. No session tagging (8h)
14. No auto-backup (8h)

---

## Quick Development Setup

```bash
# Install dependencies
npm install

# Install Rust toolchain (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install whisper.cpp (macOS)
brew install whisper-cpp

# Download Whisper model
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# Run development server
npm run tauri:dev

# Run tests (when you create them)
npm run test
cd src-tauri && cargo test
```

---

## File Structure (Key Areas)

```
src/
├── App.svelte                          # Main app (integrate ChatView here)
├── components/
│   ├── ChatPanel.svelte               # Legacy chat (replace with ChatView)
│   ├── SettingsPanel.svelte           # Provider settings (needs integration)
│   └── RecordButton.svelte            # Recording UI (add visual feedback)
└── lib/
    ├── components/
    │   ├── ChatView.svelte            # NEW: Complete chat interface
    │   ├── SessionsList.svelte        # NEW: Sessions sidebar (add search)
    │   ├── MessageThread.svelte       # NEW: Message display
    │   └── ToastContainer.svelte      # NEW: Notifications
    └── utils/
        └── toast.js                   # Toast notification system

src-tauri/src/
├── commands.rs                        # Tauri commands (add CRUD operations)
├── services/
│   ├── openai_api.rs                 # OpenAI client
│   └── claude_api.rs                 # Claude client
├── prompts.rs                        # Prompt template loader
├── export.rs                         # Markdown export
└── db/
    ├── models.rs                     # Database models
    └── repository.rs                 # Database operations (add missing CRUD)
```

---

## Common Tasks

### Add a new Tauri command:
```rust
// src-tauri/src/commands.rs
#[tauri::command]
pub async fn my_new_command(param: String) -> Result<String, BrainDumpError> {
    // Implementation
    Ok("result".to_string())
}

// src-tauri/src/main.rs (register command)
.invoke_handler(tauri::generate_handler![
    commands::my_new_command,  // Add this line
    // ... other commands
])
```

### Call from frontend:
```javascript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke('my_new_command', { param: 'value' });
```

### Create a Svelte 5 component:
```svelte
<script>
  // Use Svelte 5 runes
  let count = $state(0);
  let doubled = $derived(count * 2);

  $effect(() => {
    console.log('Count changed:', count);
  });
</script>

<button onclick={() => count++}>
  Count: {count} (Doubled: {doubled})
</button>
```

---

## Testing Guidelines

### Rust tests:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_my_function() {
        let result = my_function("input");
        assert_eq!(result, "expected");
    }
}
```

### Frontend tests (create):
```javascript
// Use Vitest or your preferred framework
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import MyComponent from './MyComponent.svelte';

describe('MyComponent', () => {
  it('renders correctly', () => {
    const { getByText } = render(MyComponent);
    expect(getByText('Hello')).toBeTruthy();
  });
});
```

---

## Questions?

All documentation is in the repository:

1. **Quick Overview**: `README.md`
2. **Current Status**: `docs/dev/PROJECT_STATUS_2025-11-16.md`
3. **What to Build**: `docs/dev/GITHUB_ISSUES_FOR_WEB_TEAM.md`
4. **How to Build**: `docs/dev/HANDOFF_TO_WEB_TEAM.md`
5. **Architecture**: `docs/dev/HANDOVER_MVP_v3.0.md`
6. **For Leadership**: `docs/pm/CTO_HANDOVER_MVP_v3.0.md`

---

## Deployment Workflow

```bash
# 1. Create feature branch
git checkout -b feature/issue-1-provider-persistence

# 2. Implement feature + tests
# ... code ...

# 3. Commit with conventional commits
git commit -m "feat: Add provider selection persistence

- Store selected provider in database
- Load on app startup
- Add migration for provider_settings table

Fixes #1"

# 4. Push and create PR
git push origin feature/issue-1-provider-persistence
gh pr create --base claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54

# 5. After all P1 issues complete, create final PR to main
gh pr create --base main --title "feat: BrainDump v3.1 - Complete MVP features"
```

---

## Let's Ship v3.1! 🚀

You have all the tools, documentation, and unlimited resources. The foundation is solid - now complete the missing features and ship a production-ready MVP.

**Start with P1 Critical issues and work your way through the priorities.**

Good luck! 💪
