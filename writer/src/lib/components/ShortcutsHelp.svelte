<script>
  import { shortcuts as globalShortcuts } from '../utils/shortcuts.js';

  // Props using Svelte 5 runes
  let {
    visible = $bindable(false)
  } = $props();

  // Close handler
  function close() {
    visible = false;
  }

  // Keyboard shortcuts organized by category
  const shortcutCategories = [
    {
      title: 'Recording',
      shortcuts: [
        { keys: ['⌘', 'R'], description: 'Start/stop recording' },
      ]
    },
    {
      title: 'Navigation',
      shortcuts: [
        { keys: ['⌘', '1'], description: 'Switch to Chat view' },
        { keys: ['⌘', '2'], description: 'Switch to Transcript view' },
        { keys: ['⌘', '3'], description: 'Switch to Prompts view' },
      ]
    },
    {
      title: 'Actions',
      shortcuts: [
        { keys: ['⌘', 'N'], description: 'New session' },
        { keys: ['⌘', 'E'], description: 'Export session' },
        { keys: ['⌘', 'F'], description: 'Focus search' },
        { keys: ['⌘', '⇧', 'P'], description: 'Toggle privacy panel' },
      ]
    },
    {
      title: 'General',
      shortcuts: [
        { keys: ['⌘', ','], description: 'Open settings' },
        { keys: ['⌘', '?'], description: 'Show this help' },
        { keys: ['Ctrl', '`'], description: 'Toggle terminal' },
        { keys: ['Esc'], description: 'Close dialogs' },
      ]
    }
  ];
</script>

{#if visible}
  <div class="shortcuts-overlay" onclick={close} role="dialog" aria-modal="true" aria-labelledby="shortcuts-title">
    <div class="shortcuts-modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h2 id="shortcuts-title">Keyboard Shortcuts</h2>
        <button class="close-btn" onclick={close} aria-label="Close shortcuts help">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="modal-content">
        {#each shortcutCategories as category}
          <div class="shortcuts-section">
            <h3>{category.title}</h3>
            <div class="shortcuts-list">
              {#each category.shortcuts as shortcut}
                <div class="shortcut-item">
                  <div class="shortcut-keys">
                    {#each shortcut.keys as key}
                      <kbd>{key}</kbd>
                    {/each}
                  </div>
                  <span class="shortcut-desc">{shortcut.description}</span>
                </div>
              {/each}
            </div>
          </div>
        {/each}

        <div class="shortcuts-footer">
          <p class="help-text">
            On Windows/Linux, replace <kbd>⌘</kbd> with <kbd>Ctrl</kbd>
          </p>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .shortcuts-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .shortcuts-modal {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 700px;
    width: 90%;
    max-height: 80vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    animation: slideUp 0.3s ease-out;
  }

  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 28px;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .modal-header h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #000000;
    margin: 0;
  }

  .close-btn {
    background: none;
    border: none;
    padding: 8px;
    cursor: pointer;
    color: #666666;
    border-radius: 6px;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-btn:hover {
    background: #e0e0e0;
    color: #000000;
  }

  .close-btn:active {
    transform: scale(0.95);
  }

  .modal-content {
    padding: 28px;
    overflow-y: auto;
  }

  .shortcuts-section {
    margin-bottom: 28px;
  }

  .shortcuts-section:last-child {
    margin-bottom: 0;
  }

  .shortcuts-section h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #333333;
    margin: 0 0 16px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.85rem;
  }

  .shortcuts-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .shortcut-item {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .shortcut-keys {
    display: flex;
    align-items: center;
    gap: 4px;
    min-width: 120px;
  }

  kbd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 32px;
    height: 28px;
    padding: 0 8px;
    background: linear-gradient(180deg, #ffffff 0%, #f5f5f5 100%);
    border: 1px solid #d0d0d0;
    border-bottom-width: 2px;
    border-radius: 5px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Courier New', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    color: #333333;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .shortcut-desc {
    flex: 1;
    font-size: 0.95rem;
    color: #666666;
    line-height: 1.5;
  }

  .shortcuts-footer {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e0e0e0;
  }

  .help-text {
    font-size: 0.875rem;
    color: #666666;
    line-height: 1.6;
    margin: 0;
    text-align: center;
  }

  .help-text kbd {
    min-width: auto;
    height: auto;
    padding: 2px 6px;
    font-size: 0.8rem;
    border-bottom-width: 1px;
  }

  /* Scrollbar styling */
  .modal-content::-webkit-scrollbar {
    width: 8px;
  }

  .modal-content::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 4px;
  }

  .modal-content::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 4px;
  }

  .modal-content::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }
</style>
