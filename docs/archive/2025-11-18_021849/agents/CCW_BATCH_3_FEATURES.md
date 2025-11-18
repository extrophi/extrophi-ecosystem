# CCW Agent Batch 3 - Core Feature Implementation

**Date**: 2025-11-16
**Status**: PR MERGED - Now implementing features
**Credits to Burn**: $750 by Tuesday

---

## Context

PR #22 merged to main. CI passing. Core infrastructure stable. Time to implement real features.

---

## Agent 11: Audio Waveform Visualization

**Task**: Add real-time waveform display during recording

### Requirements:
- Canvas-based waveform renderer
- Real-time audio data from Rust backend
- Responsive design
- Export waveform as image

### Files to create/modify:
- `src/lib/components/Waveform.svelte`
- `src-tauri/src/audio/analyzer.rs`
- Add Tauri command for audio samples

### Implementation:
```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  let canvas: HTMLCanvasElement;
  let animationFrame: number;

  function drawWaveform(samples: Float32Array) {
    const ctx = canvas.getContext('2d')!;
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);
    ctx.beginPath();
    ctx.moveTo(0, height / 2);

    for (let i = 0; i < samples.length; i++) {
      const x = (i / samples.length) * width;
      const y = (samples[i] + 1) / 2 * height;
      ctx.lineTo(x, y);
    }

    ctx.strokeStyle = '#4CAF50';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  onMount(() => {
    // Subscribe to audio stream from Rust
  });

  onDestroy(() => {
    cancelAnimationFrame(animationFrame);
  });
</script>

<canvas bind:this={canvas} width="800" height="200" />
```

---

## Agent 12: Keyboard Shortcuts System

**Task**: Implement global keyboard shortcuts

### Shortcuts to implement:
- `Cmd+R` - Start/stop recording
- `Cmd+N` - New session
- `Cmd+E` - Export current session
- `Cmd+F` - Focus search
- `Cmd+,` - Open settings
- `Cmd+1-9` - Switch between sessions
- `Esc` - Close modal/cancel operation

### Files:
- `src/lib/stores/shortcuts.ts`
- `src/lib/components/ShortcutOverlay.svelte`
- Update App.svelte to register shortcuts

### Implementation:
```typescript
// src/lib/stores/shortcuts.ts
import { writable } from 'svelte/store';

interface Shortcut {
  key: string;
  meta: boolean;
  shift?: boolean;
  action: () => void;
  description: string;
}

export const shortcuts = writable<Shortcut[]>([]);

export function registerShortcuts(newShortcuts: Shortcut[]) {
  shortcuts.set(newShortcuts);

  const handler = (e: KeyboardEvent) => {
    if (e.metaKey || e.ctrlKey) {
      const shortcut = newShortcuts.find(s =>
        s.key === e.key &&
        s.meta &&
        (s.shift === undefined || s.shift === e.shiftKey)
      );

      if (shortcut) {
        e.preventDefault();
        shortcut.action();
      }
    }
  };

  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}
```

---

## Agent 13: Session Export Formats

**Task**: Export sessions to multiple formats

### Formats:
- **Markdown** - Clean text with headers
- **JSON** - Structured data
- **PDF** - Formatted document
- **Audio + Transcript** - ZIP bundle

### Files:
- `src/lib/components/ExportModal.svelte`
- `src-tauri/src/export.rs` (enhance existing)
- Add PDF generation using printpdf crate

### Rust Implementation:
```rust
#[tauri::command]
pub async fn export_session(
    session_id: i64,
    format: String,
    output_path: String
) -> Result<String, String> {
    match format.as_str() {
        "markdown" => export_as_markdown(session_id, &output_path).await,
        "json" => export_as_json(session_id, &output_path).await,
        "pdf" => export_as_pdf(session_id, &output_path).await,
        "bundle" => export_as_bundle(session_id, &output_path).await,
        _ => Err("Unknown format".to_string()),
    }
}

async fn export_as_markdown(session_id: i64, path: &str) -> Result<String, String> {
    let session = get_session(session_id)?;
    let messages = get_session_messages(session_id)?;

    let mut md = String::new();
    md.push_str(&format!("# {}\n\n", session.title));
    md.push_str(&format!("*Created: {}*\n\n", session.created_at));
    md.push_str("---\n\n");

    for msg in messages {
        md.push_str(&format!("## {}\n\n", msg.role));
        md.push_str(&format!("{}\n\n", msg.content));
    }

    std::fs::write(path, md).map_err(|e| e.to_string())?;
    Ok(path.to_string())
}
```

---

## Agent 14: Dark Mode Theme

**Task**: Implement system-aware dark mode

### Requirements:
- Auto-detect system preference
- Manual toggle in settings
- Smooth transitions
- CSS variables for theming
- Persist preference

### Files:
- `src/lib/stores/theme.ts`
- `src/app.css` - Add CSS variables
- `src/lib/components/ThemeToggle.svelte`

### Implementation:
```typescript
// src/lib/stores/theme.ts
import { writable } from 'svelte/store';

type Theme = 'light' | 'dark' | 'system';

function createThemeStore() {
  const stored = localStorage.getItem('theme') as Theme || 'system';
  const { subscribe, set } = writable<Theme>(stored);

  function apply(theme: Theme) {
    const isDark = theme === 'dark' ||
      (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('theme', theme);
    set(theme);
  }

  // Listen for system changes
  window.matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', () => {
      const current = localStorage.getItem('theme') as Theme;
      if (current === 'system') apply('system');
    });

  return {
    subscribe,
    set: apply,
  };
}

export const theme = createThemeStore();
```

### CSS Variables:
```css
:root, [data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --accent: #4CAF50;
  --border: #e0e0e0;
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --accent: #66BB6A;
  --border: #404040;
}
```

---

## Agent 15: Notification System

**Task**: Toast notifications and alerts

### Types:
- Success (green)
- Error (red)
- Warning (yellow)
- Info (blue)

### Features:
- Auto-dismiss after timeout
- Stack multiple notifications
- Click to dismiss
- Action buttons

### Files:
- `src/lib/stores/notifications.ts`
- `src/lib/components/NotificationToast.svelte`
- `src/lib/components/NotificationContainer.svelte`

### Implementation:
```typescript
// src/lib/stores/notifications.ts
import { writable } from 'svelte/store';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timeout?: number;
  action?: { label: string; callback: () => void };
}

function createNotificationStore() {
  const { subscribe, update } = writable<Notification[]>([]);

  function add(notification: Omit<Notification, 'id'>) {
    const id = crypto.randomUUID();
    update(n => [...n, { ...notification, id }]);

    if (notification.timeout !== 0) {
      setTimeout(() => remove(id), notification.timeout || 5000);
    }
  }

  function remove(id: string) {
    update(n => n.filter(x => x.id !== id));
  }

  return {
    subscribe,
    success: (msg: string) => add({ type: 'success', message: msg }),
    error: (msg: string) => add({ type: 'error', message: msg }),
    warning: (msg: string) => add({ type: 'warning', message: msg }),
    info: (msg: string) => add({ type: 'info', message: msg }),
    remove,
  };
}

export const notifications = createNotificationStore();
```

---

## Git Workflow

```bash
git checkout main
git pull origin main
git checkout -b feature/[feature-name]
# Implement feature
git add -A
git commit -m "feat: [description]"
git push origin feature/[feature-name]
# Create PR to main
```

---

## Success Criteria

For each agent:
- [ ] Feature implemented and working
- [ ] Tests pass
- [ ] Code follows existing patterns
- [ ] No TypeScript errors
- [ ] Responsive design
- [ ] Accessible (keyboard nav, ARIA)

**SPAWN THESE AGENTS NOW. BURN THE CREDITS.**
