<script lang="ts">
  /**
   * EditorIsland Usage Example
   *
   * This demonstrates how to integrate the EditorIsland component
   * into your application.
   */

  import EditorIsland from './EditorIsland.svelte';

  // Example session data
  let sessionId = $state('1');
  let initialContent = $state(`# My Journal Entry

Today I learned about Svelte 5 runes and the islands architecture.

## Key Learnings

- Islands architecture enables selective hydration
- Svelte 5 uses runes for reactive state
- CodeMirror 6 provides excellent vim mode support

## Next Steps

1. Implement more editor features
2. Add syntax highlighting
3. Test with real users
`);

  // Example with vim mode enabled
  let enableVim = $state(true);

  // Callback when content is saved
  function handleSave(content: string) {
    console.log('Content saved:', content);
  }

  // Toggle vim mode
  function toggleVim() {
    enableVim = !enableVim;
  }
</script>

<div class="example-container">
  <div class="example-header">
    <h1>EditorIsland Example</h1>
    <button onclick={toggleVim}>
      {enableVim ? 'Disable' : 'Enable'} Vim Mode
    </button>
  </div>

  <div class="editor-wrapper">
    <!-- Basic usage with all features enabled -->
    <EditorIsland
      {sessionId}
      {initialContent}
      {enableVim}
      onSave={handleSave}
    />
  </div>

  <div class="example-info">
    <h2>Features</h2>
    <ul>
      <li>✅ Auto-save with 500ms debounce</li>
      <li>✅ Cmd+S (Mac) / Ctrl+S (Windows/Linux) keyboard shortcut</li>
      <li>✅ Privacy scanner integration</li>
      <li>✅ Tauri backend persistence</li>
      <li>✅ Vim mode (optional)</li>
      <li>✅ Real-time privacy warnings</li>
      <li>✅ Visual save status feedback</li>
    </ul>

    <h2>Keyboard Shortcuts</h2>
    <ul>
      <li><kbd>Cmd</kbd>+<kbd>S</kbd> - Save immediately</li>
      {#if enableVim}
        <li><kbd>i</kbd> - Enter insert mode</li>
        <li><kbd>Esc</kbd> - Exit to normal mode</li>
        <li><kbd>h</kbd><kbd>j</kbd><kbd>k</kbd><kbd>l</kbd> - Navigate</li>
        <li><kbd>d</kbd><kbd>d</kbd> - Delete line</li>
        <li><kbd>y</kbd><kbd>y</kbd> - Yank (copy) line</li>
        <li><kbd>p</kbd> - Paste</li>
        <li><kbd>u</kbd> - Undo</li>
        <li><kbd>Ctrl</kbd>+<kbd>r</kbd> - Redo</li>
      {/if}
    </ul>

    <h2>Privacy Levels</h2>
    <ul>
      <li><span class="badge red">PRIVATE</span> - Personally Identifiable Information (SSN, email, credit cards)</li>
      <li><span class="badge orange">PERSONAL</span> - Emotional content, family references, health info</li>
      <li><span class="badge yellow">BUSINESS</span> - Client info, project details, financial data</li>
      <li><span class="badge green">IDEAS</span> - Generic content, publishable ideas</li>
    </ul>
  </div>
</div>

<style>
  .example-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .example-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .example-header h1 {
    font-size: 24px;
    font-weight: 600;
    margin: 0;
  }

  .example-header button {
    padding: 8px 16px;
    background: #007acc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }

  .example-header button:hover {
    background: #005a9e;
  }

  .editor-wrapper {
    height: 600px;
    margin-bottom: 40px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
  }

  .example-info {
    background: #f5f5f5;
    padding: 20px;
    border-radius: 8px;
  }

  .example-info h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 20px 0 10px 0;
  }

  .example-info h2:first-child {
    margin-top: 0;
  }

  .example-info ul {
    margin: 0;
    padding-left: 20px;
  }

  .example-info li {
    margin: 6px 0;
    line-height: 1.6;
  }

  kbd {
    background: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 2px 6px;
    font-family: monospace;
    font-size: 12px;
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.1);
  }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }

  .badge.red {
    background: #ffebee;
    color: #c62828;
  }

  .badge.orange {
    background: #ffe0b2;
    color: #e65100;
  }

  .badge.yellow {
    background: #fff9c4;
    color: #f57f17;
  }

  .badge.green {
    background: #e8f5e9;
    color: #2e7d32;
  }
</style>
