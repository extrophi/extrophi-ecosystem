<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { EditorView, keymap } from '@codemirror/view';
  import { EditorState } from '@codemirror/state';
  import { markdown } from '@codemirror/lang-markdown';
  import { vim } from '@replit/codemirror-vim';
  import { defaultKeymap } from '@codemirror/commands';
  import { debounce } from 'lodash-es';
  import { scanText, type PrivacyMatch, type PrivacyLevel } from '../lib/privacy-rules';
  import { marked } from 'marked';
  import hljs from 'highlight.js';

  // Props using Svelte 5 runes
  let {
    sessionId = '',
    initialContent = '',
    messageId = null,
    onSave = null,
    enableVim = true,
  }: {
    sessionId: string;
    initialContent?: string;
    messageId?: number | null;
    onSave?: ((content: string) => void) | null;
    enableVim?: boolean;
  } = $props();

  // State using Svelte 5 runes
  let editorContainer: HTMLDivElement;
  let editorView: EditorView | null = null;
  let isSaving = $state(false);
  let lastSaved = $state<Date | null>(null);
  let saveStatus = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
  let errorMessage = $state<string>('');

  // Privacy scanning state
  let privacyMatches = $state<PrivacyMatch[]>([]);
  let privacyLevel = $state<PrivacyLevel | null>(null);

  // Markdown preview state
  let showPreview = $state(false);
  let previewHtml = $state('');
  let previewContainer: HTMLDivElement | undefined;
  let editorScroller: HTMLElement | null = null;

  // Configure marked with GFM and line breaks
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  // Derived state for privacy badge
  let privacyBadgeColor = $derived(() => {
    if (!privacyLevel) return 'green';
    switch (privacyLevel) {
      case 'PRIVATE':
        return 'red';
      case 'PERSONAL':
        return 'orange';
      case 'BUSINESS':
        return 'yellow';
      case 'IDEAS':
        return 'green';
      default:
        return 'green';
    }
  });

  let privacyBadgeText = $derived(() => {
    if (!privacyLevel) return 'Clean';
    return privacyLevel;
  });

  /**
   * Save content to Tauri backend
   */
  async function saveContent(content: string): Promise<void> {
    try {
      isSaving = true;
      saveStatus = 'saving';
      errorMessage = '';

      // Call Tauri command to save message
      await invoke('save_message', {
        sessionId: parseInt(sessionId),
        role: 'user',
        content,
        recordingId: null,
      });

      lastSaved = new Date();
      saveStatus = 'saved';

      // Call optional onSave callback
      if (onSave) {
        onSave(content);
      }

      // Reset status after 2 seconds
      setTimeout(() => {
        if (saveStatus === 'saved') {
          saveStatus = 'idle';
        }
      }, 2000);
    } catch (error) {
      console.error('Failed to save content:', error);
      saveStatus = 'error';
      errorMessage = error instanceof Error ? error.message : 'Failed to save';
    } finally {
      isSaving = false;
    }
  }

  /**
   * Debounced auto-save function (500ms delay)
   */
  const autoSave = debounce((content: string) => {
    saveContent(content);
  }, 500);

  /**
   * Update privacy scanning
   */
  function updatePrivacyScanning(text: string): void {
    privacyMatches = scanText(text);

    // Determine highest privacy level
    if (privacyMatches.length === 0) {
      privacyLevel = null;
    } else {
      const levels: PrivacyLevel[] = ['PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS'];
      privacyLevel = levels.find(level =>
        privacyMatches.some(match => match.level === level)
      ) || null;
    }
  }

  /**
   * Render markdown to HTML with syntax highlighting
   */
  function renderMarkdown(text: string): void {
    try {
      let html = marked.parse(text) as string;

      // Apply syntax highlighting to code blocks
      // Create a temporary div to parse the HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;

      // Find all code blocks and highlight them
      const codeBlocks = tempDiv.querySelectorAll('pre code');
      codeBlocks.forEach((block) => {
        const codeElement = block as HTMLElement;
        const language = Array.from(codeElement.classList)
          .find(cls => cls.startsWith('language-'))
          ?.replace('language-', '');

        if (language && hljs.getLanguage(language)) {
          try {
            const result = hljs.highlight(codeElement.textContent || '', { language });
            codeElement.innerHTML = result.value;
            codeElement.classList.add('hljs');
          } catch (err) {
            console.error('Highlighting error:', err);
          }
        } else {
          // Auto-detect language
          const result = hljs.highlightAuto(codeElement.textContent || '');
          codeElement.innerHTML = result.value;
          codeElement.classList.add('hljs');
        }
      });

      previewHtml = tempDiv.innerHTML;
    } catch (err) {
      console.error('Markdown parsing error:', err);
      previewHtml = '<p>Error parsing markdown</p>';
    }
  }

  /**
   * Toggle preview mode
   */
  function togglePreview(): void {
    showPreview = !showPreview;
    if (showPreview && editorView) {
      // Render current content
      const content = editorView.state.doc.toString();
      renderMarkdown(content);
    }
  }

  /**
   * Handle scroll sync between editor and preview
   */
  function handleEditorScroll(): void {
    if (!showPreview || !editorScroller || !previewContainer) return;

    const scrollPercentage = editorScroller.scrollTop / (editorScroller.scrollHeight - editorScroller.clientHeight);
    previewContainer.scrollTop = scrollPercentage * (previewContainer.scrollHeight - previewContainer.clientHeight);
  }

  /**
   * Debounced scroll handler
   */
  const debouncedScrollHandler = debounce(handleEditorScroll, 10);

  /**
   * Handle content changes
   */
  function handleContentChange(content: string): void {
    // Update privacy scanning
    updatePrivacyScanning(content);

    // Trigger auto-save
    autoSave(content);

    // Update markdown preview if enabled
    if (showPreview) {
      renderMarkdown(content);
    }
  }

  /**
   * Manual save handler (Cmd+S / Ctrl+S)
   */
  function handleManualSave(): boolean {
    if (editorView) {
      const content = editorView.state.doc.toString();
      // Cancel pending auto-save
      autoSave.cancel();
      // Save immediately
      saveContent(content);
    }
    return true; // Prevent default browser behavior
  }

  /**
   * Initialize CodeMirror editor
   */
  function initializeEditor(): void {
    if (!editorContainer) return;

    // Custom keymap for Cmd+S / Ctrl+S
    const saveKeymap = keymap.of([
      {
        key: 'Mod-s', // Cmd on Mac, Ctrl on Windows/Linux
        run: () => {
          handleManualSave();
          return true;
        },
        preventDefault: true,
      },
    ]);

    // Build extensions array
    const extensions = [
      markdown(),
      saveKeymap,
      keymap.of(defaultKeymap),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          const content = update.state.doc.toString();
          handleContentChange(content);
        }
      }),
      EditorView.theme({
        '&': {
          height: '100%',
          fontSize: '14px',
          fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", "Consolas", monospace',
        },
        '.cm-content': {
          padding: '16px',
          minHeight: '400px',
        },
        '.cm-scroller': {
          overflow: 'auto',
        },
        '.cm-line': {
          lineHeight: '1.6',
        },
      }),
    ];

    // Add vim mode if enabled
    if (enableVim) {
      extensions.push(vim());
    }

    // Create editor state
    const startState = EditorState.create({
      doc: initialContent,
      extensions,
    });

    // Create editor view
    editorView = new EditorView({
      state: startState,
      parent: editorContainer,
    });

    // Get editor scroller for scroll sync
    editorScroller = editorContainer.querySelector('.cm-scroller');
    if (editorScroller) {
      editorScroller.addEventListener('scroll', debouncedScrollHandler);
    }

    // Initial privacy scan
    updatePrivacyScanning(initialContent);

    // Initial markdown render if preview is enabled
    if (showPreview) {
      renderMarkdown(initialContent);
    }
  }

  /**
   * Cleanup editor on destroy
   */
  function destroyEditor(): void {
    if (editorView) {
      editorView.destroy();
      editorView = null;
    }
    // Remove scroll listener
    if (editorScroller) {
      editorScroller.removeEventListener('scroll', debouncedScrollHandler);
    }
    // Cancel pending auto-saves and scroll handlers
    autoSave.cancel();
    debouncedScrollHandler.cancel();
  }

  // Lifecycle: Initialize editor on mount
  onMount(() => {
    initializeEditor();
  });

  // Lifecycle: Cleanup on destroy
  onDestroy(() => {
    destroyEditor();
  });
</script>

<div class="editor-island">
  <div class="editor-header">
    <div class="editor-info">
      <span class="editor-mode">{enableVim ? 'VIM MODE' : 'NORMAL MODE'}</span>
      {#if enableVim}
        <span class="vim-hint">Press 'i' to insert, 'Esc' for normal mode</span>
      {/if}
      <button class="preview-toggle" class:active={showPreview} onclick={togglePreview} type="button">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        <span>{showPreview ? 'Hide Preview' : 'Show Preview'}</span>
      </button>
    </div>
    <div class="editor-status">
      <div class="privacy-badge" data-level={privacyBadgeColor()}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        </svg>
        <span>{privacyBadgeText()}</span>
      </div>
      <div class="save-status" data-status={saveStatus}>
        {#if saveStatus === 'saving'}
          <span class="status-text">Saving...</span>
        {:else if saveStatus === 'saved'}
          <span class="status-text">✓ Saved</span>
        {:else if saveStatus === 'error'}
          <span class="status-text error">✗ Error</span>
        {:else if lastSaved}
          <span class="status-text muted">Last saved: {lastSaved.toLocaleTimeString()}</span>
        {/if}
      </div>
    </div>
  </div>

  <div class="editor-content" class:split-view={showPreview}>
    <div class="editor-pane">
      <div class="editor-container" bind:this={editorContainer}></div>
    </div>

    {#if showPreview}
      <div class="preview-pane">
        <div class="preview-container" bind:this={previewContainer}>
          {@html previewHtml}
        </div>
      </div>
    {/if}
  </div>

  {#if errorMessage}
    <div class="error-message">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>{errorMessage}</span>
    </div>
  {/if}

  {#if privacyMatches.length > 0}
    <div class="privacy-warnings">
      <div class="warning-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        <span>{privacyMatches.length} privacy issue{privacyMatches.length !== 1 ? 's' : ''} detected</span>
      </div>
      <div class="warning-list">
        {#each privacyMatches.slice(0, 3) as match}
          <div class="warning-item" data-level={match.level.toLowerCase()}>
            <span class="warning-type">{match.type}</span>
            <span class="warning-description">{match.description}</span>
          </div>
        {/each}
        {#if privacyMatches.length > 3}
          <div class="warning-more">
            +{privacyMatches.length - 3} more
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .editor-island {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
  }

  .editor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #fafafa;
    border-bottom: 1px solid #e0e0e0;
  }

  .editor-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .editor-mode {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: #666;
    padding: 4px 8px;
    background: #e8e8e8;
    border-radius: 4px;
  }

  .vim-hint {
    font-size: 12px;
    color: #888;
    font-style: italic;
  }

  .preview-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    color: #666;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .preview-toggle:hover {
    background: #f6f8fa;
    border-color: #d0d0d0;
    color: #333;
  }

  .preview-toggle.active {
    background: #0366d6;
    border-color: #0366d6;
    color: #ffffff;
  }

  .preview-toggle.active:hover {
    background: #0256c2;
    border-color: #0256c2;
  }

  .preview-toggle svg {
    width: 16px;
    height: 16px;
  }

  .editor-status {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .privacy-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }

  .privacy-badge[data-level="green"] {
    background: #e8f5e9;
    color: #2e7d32;
  }

  .privacy-badge[data-level="yellow"] {
    background: #fff9c4;
    color: #f57f17;
  }

  .privacy-badge[data-level="orange"] {
    background: #ffe0b2;
    color: #e65100;
  }

  .privacy-badge[data-level="red"] {
    background: #ffebee;
    color: #c62828;
  }

  .save-status {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-text {
    font-size: 12px;
    font-weight: 500;
  }

  .status-text.muted {
    color: #888;
    font-weight: 400;
  }

  .status-text.error {
    color: #c62828;
  }

  .editor-content {
    flex: 1;
    display: flex;
    overflow: hidden;
    position: relative;
  }

  .editor-content.split-view {
    gap: 1px;
  }

  .editor-pane {
    flex: 1;
    overflow: auto;
    position: relative;
  }

  .editor-content:not(.split-view) .editor-pane {
    flex: 1;
  }

  .editor-container {
    height: 100%;
    overflow: auto;
    position: relative;
  }

  .preview-pane {
    flex: 1;
    overflow: auto;
    background: #ffffff;
    border-left: 1px solid #e0e0e0;
  }

  .preview-container {
    padding: 16px;
    height: 100%;
    overflow-y: auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    line-height: 1.6;
    color: #333;
  }

  /* Markdown preview styles */
  .preview-container :global(h1),
  .preview-container :global(h2),
  .preview-container :global(h3),
  .preview-container :global(h4),
  .preview-container :global(h5),
  .preview-container :global(h6) {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
  }

  .preview-container :global(h1) {
    font-size: 2em;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 0.3em;
  }

  .preview-container :global(h2) {
    font-size: 1.5em;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 0.3em;
  }

  .preview-container :global(h3) {
    font-size: 1.25em;
  }

  .preview-container :global(h4) {
    font-size: 1em;
  }

  .preview-container :global(h5) {
    font-size: 0.875em;
  }

  .preview-container :global(h6) {
    font-size: 0.85em;
    color: #666;
  }

  .preview-container :global(p) {
    margin-top: 0;
    margin-bottom: 16px;
  }

  .preview-container :global(a) {
    color: #0366d6;
    text-decoration: none;
  }

  .preview-container :global(a:hover) {
    text-decoration: underline;
  }

  .preview-container :global(code) {
    background: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
    font-size: 85%;
  }

  .preview-container :global(pre) {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
    margin-bottom: 16px;
  }

  .preview-container :global(pre code) {
    background: transparent;
    padding: 0;
    font-size: 100%;
  }

  .preview-container :global(blockquote) {
    margin: 0 0 16px 0;
    padding: 0 1em;
    color: #666;
    border-left: 4px solid #e0e0e0;
  }

  .preview-container :global(ul),
  .preview-container :global(ol) {
    margin-bottom: 16px;
    padding-left: 2em;
  }

  .preview-container :global(li) {
    margin-bottom: 4px;
  }

  .preview-container :global(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 16px;
  }

  .preview-container :global(table th),
  .preview-container :global(table td) {
    padding: 6px 13px;
    border: 1px solid #e0e0e0;
  }

  .preview-container :global(table th) {
    font-weight: 600;
    background: #f6f8fa;
  }

  .preview-container :global(table tr:nth-child(2n)) {
    background: #f6f8fa;
  }

  .preview-container :global(img) {
    max-width: 100%;
    height: auto;
  }

  .preview-container :global(hr) {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: #e0e0e0;
    border: 0;
  }

  /* Syntax highlighting (highlight.js default styles) */
  .preview-container :global(.hljs) {
    display: block;
    overflow-x: auto;
    padding: 0.5em;
    background: #f6f8fa;
  }

  .preview-container :global(.hljs-comment),
  .preview-container :global(.hljs-quote) {
    color: #6a737d;
    font-style: italic;
  }

  .preview-container :global(.hljs-keyword),
  .preview-container :global(.hljs-selector-tag),
  .preview-container :global(.hljs-subst) {
    color: #d73a49;
    font-weight: bold;
  }

  .preview-container :global(.hljs-number),
  .preview-container :global(.hljs-literal),
  .preview-container :global(.hljs-variable),
  .preview-container :global(.hljs-template-variable),
  .preview-container :global(.hljs-tag .hljs-attr) {
    color: #005cc5;
  }

  .preview-container :global(.hljs-string),
  .preview-container :global(.hljs-doctag) {
    color: #032f62;
  }

  .preview-container :global(.hljs-title),
  .preview-container :global(.hljs-section),
  .preview-container :global(.hljs-selector-id) {
    color: #6f42c1;
    font-weight: bold;
  }

  .preview-container :global(.hljs-type),
  .preview-container :global(.hljs-class .hljs-title) {
    color: #d73a49;
    font-weight: bold;
  }

  .preview-container :global(.hljs-tag),
  .preview-container :global(.hljs-name),
  .preview-container :global(.hljs-attribute) {
    color: #22863a;
    font-weight: normal;
  }

  .preview-container :global(.hljs-regexp),
  .preview-container :global(.hljs-link) {
    color: #032f62;
  }

  .preview-container :global(.hljs-symbol),
  .preview-container :global(.hljs-bullet) {
    color: #e36209;
  }

  .preview-container :global(.hljs-built_in),
  .preview-container :global(.hljs-builtin-name) {
    color: #005cc5;
  }

  .preview-container :global(.hljs-meta) {
    color: #6a737d;
  }

  .preview-container :global(.hljs-deletion) {
    background: #ffeef0;
  }

  .preview-container :global(.hljs-addition) {
    background: #e6ffed;
  }

  .preview-container :global(.hljs-emphasis) {
    font-style: italic;
  }

  .preview-container :global(.hljs-strong) {
    font-weight: bold;
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #ffebee;
    color: #c62828;
    border-top: 1px solid #ffcdd2;
    font-size: 13px;
  }

  .privacy-warnings {
    border-top: 1px solid #e0e0e0;
    background: #fffef5;
    max-height: 150px;
    overflow-y: auto;
  }

  .warning-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #f57f17;
    border-bottom: 1px solid #fff9c4;
  }

  .warning-list {
    padding: 8px 16px;
  }

  .warning-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px;
    margin-bottom: 6px;
    border-radius: 4px;
    font-size: 12px;
  }

  .warning-item[data-level="private"] {
    background: #ffebee;
    border-left: 3px solid #c62828;
  }

  .warning-item[data-level="personal"] {
    background: #ffe0b2;
    border-left: 3px solid #e65100;
  }

  .warning-item[data-level="business"] {
    background: #fff9c4;
    border-left: 3px solid #f57f17;
  }

  .warning-item[data-level="ideas"] {
    background: #e8f5e9;
    border-left: 3px solid #2e7d32;
  }

  .warning-type {
    font-weight: 600;
    color: #333;
  }

  .warning-description {
    color: #666;
    font-size: 11px;
  }

  .warning-more {
    padding: 6px 8px;
    text-align: center;
    font-size: 11px;
    color: #888;
    font-style: italic;
  }

  /* CodeMirror overrides */
  :global(.cm-editor) {
    height: 100%;
  }

  :global(.cm-focused) {
    outline: none;
  }
</style>
