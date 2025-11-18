# EditorIsland Component

A powerful, privacy-aware text editor component built with Svelte 5, CodeMirror 6, and optional vim mode support.

## Features

- ✅ **Auto-save** - Automatic saving with 500ms debounce
- ✅ **Keyboard Shortcuts** - Cmd+S (Mac) / Ctrl+S (Windows/Linux)
- ✅ **Privacy Scanner** - Real-time privacy issue detection
- ✅ **Vim Mode** - Optional vim keybindings (i/Esc/hjkl/dd/yy)
- ✅ **Tauri Backend** - Persistent storage via Rust backend
- ✅ **Visual Feedback** - Save status, privacy warnings, error messages
- ✅ **Markdown Support** - Syntax highlighting for markdown

## Installation

The component requires the following dependencies (already installed):

```bash
npm install codemirror @codemirror/lang-markdown @codemirror/view @codemirror/state @codemirror/commands @codemirror/language @replit/codemirror-vim lodash-es
```

## Usage

### Basic Example

```svelte
<script>
  import EditorIsland from './islands/EditorIsland.svelte';

  let sessionId = '1';
  let initialContent = 'Hello, World!';
</script>

<EditorIsland
  {sessionId}
  {initialContent}
/>
```

### With All Options

```svelte
<script>
  import EditorIsland from './islands/EditorIsland.svelte';

  let sessionId = '1';
  let initialContent = '# My Document\n\nStart writing...';
  let messageId = 123;
  let enableVim = true;

  function handleSave(content) {
    console.log('Content saved:', content);
  }
</script>

<EditorIsland
  {sessionId}
  {initialContent}
  {messageId}
  {enableVim}
  onSave={handleSave}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `sessionId` | `string` | **required** | Session ID for saving content |
| `initialContent` | `string` | `''` | Initial editor content |
| `messageId` | `number \| null` | `null` | Optional message ID for updates |
| `enableVim` | `boolean` | `true` | Enable/disable vim mode |
| `onSave` | `(content: string) => void \| null` | `null` | Callback after successful save |

## Features in Detail

### Auto-Save

The editor automatically saves content after 500ms of inactivity.

### Manual Save (Cmd+S / Ctrl+S)

Press `Cmd+S` (Mac) or `Ctrl+S` (Windows/Linux) to save immediately.

### Privacy Scanner Integration

Real-time privacy scanning detects sensitive information in your content.

**Privacy Levels:**
- **PRIVATE** (Red) - SSN, emails, credit cards
- **PERSONAL** (Orange) - Emotional content, family references
- **BUSINESS** (Yellow) - Client info, project details
- **IDEAS** (Green) - Generic content, publishable ideas

### Vim Mode

Optional vim keybindings: `i`, `Esc`, `h/j/k/l`, `dd`, `yy`, `p`, `u`, `Ctrl+r`

## Testing

```bash
npm test src/islands/EditorIsland.test.ts
```

## Examples

See `EditorIsland.example.svelte` for a complete working example.

---

**Version:** 1.0.0
**Author:** Agent DELTA
**Last Updated:** 2025-11-18
