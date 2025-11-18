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
   * Handle content changes
   */
  function handleContentChange(content: string): void {
    // Update privacy scanning
    updatePrivacyScanning(content);

    // Trigger auto-save
    autoSave(content);
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

    // Initial privacy scan
    updatePrivacyScanning(initialContent);
  }

  /**
   * Cleanup editor on destroy
   */
  function destroyEditor(): void {
    if (editorView) {
      editorView.destroy();
      editorView = null;
    }
    // Cancel pending auto-saves
    autoSave.cancel();
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

  <div class="editor-container" bind:this={editorContainer}></div>

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

  .editor-container {
    flex: 1;
    overflow: auto;
    position: relative;
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
