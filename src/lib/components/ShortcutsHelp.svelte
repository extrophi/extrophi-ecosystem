<script>
  import { shortcuts, contextShortcuts, formatShortcut, formatKeys } from '../utils/shortcuts.js';

  let { visible = $bindable(false) } = $props();

  function closeModal() {
    visible = false;
  }

  function handleKeydown(event) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      closeModal();
    }
  }

  // Group shortcuts by category
  const globalShortcuts = [
    shortcuts.record,
    shortcuts.newSession,
    shortcuts.export,
    shortcuts.settings,
    shortcuts.search,
    shortcuts.help
  ];

  const viewShortcuts = [
    shortcuts.chatView,
    shortcuts.transcriptView,
    shortcuts.promptsView,
    shortcuts.privacyView
  ];
</script>

{#if visible}
  <div
    class="shortcuts-modal"
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="shortcuts-title"
    tabindex="-1"
  >
    <div class="modal-content">
      <div class="modal-header">
        <h2 id="shortcuts-title">Keyboard Shortcuts</h2>
        <button
          class="close-btn"
          onclick={closeModal}
          aria-label="Close shortcuts help"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="shortcuts-list">
        <!-- Global Shortcuts -->
        <div class="shortcut-section">
          <h3>Global</h3>
          {#each globalShortcuts as shortcut}
            <div class="shortcut-item">
              <kbd class="shortcut-key">{formatShortcut(shortcut)}</kbd>
              <span class="shortcut-desc">{shortcut.description}</span>
            </div>
          {/each}
        </div>

        <!-- View Navigation -->
        <div class="shortcut-section">
          <h3>Navigation</h3>
          {#each viewShortcuts as shortcut}
            <div class="shortcut-item">
              <kbd class="shortcut-key">{formatShortcut(shortcut)}</kbd>
              <span class="shortcut-desc">{shortcut.description}</span>
            </div>
          {/each}
        </div>

        <!-- Chat Input -->
        <div class="shortcut-section">
          <h3>Chat Input</h3>
          {#each contextShortcuts.chat as shortcut}
            <div class="shortcut-item">
              <kbd class="shortcut-key">{formatKeys(shortcut.key)}</kbd>
              <span class="shortcut-desc">{shortcut.description}</span>
            </div>
          {/each}
        </div>

        <!-- Sessions List -->
        <div class="shortcut-section">
          <h3>Sessions</h3>
          {#each contextShortcuts.sessions as shortcut}
            <div class="shortcut-item">
              <kbd class="shortcut-key">{formatKeys(shortcut.key)}</kbd>
              <span class="shortcut-desc">{shortcut.description}</span>
            </div>
          {/each}
        </div>

        <!-- General -->
        <div class="shortcut-section">
          <h3>General</h3>
          {#each contextShortcuts.general as shortcut}
            <div class="shortcut-item">
              <kbd class="shortcut-key">{formatKeys(shortcut.key)}</kbd>
              <span class="shortcut-desc">{shortcut.description}</span>
            </div>
          {/each}
        </div>
      </div>

      <div class="modal-footer">
        <button class="primary-btn" onclick={closeModal}>
          Got it!
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .shortcuts-modal {
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
    z-index: 2000;
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

  .modal-content {
    background: #ffffff;
    border-radius: 16px;
    max-width: 700px;
    width: 90%;
    max-height: 85vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: slideUp 0.3s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 30px;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #000000;
  }

  .close-btn {
    width: 36px;
    height: 36px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #666666;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  }

  .close-btn:hover {
    background: #e0e0e0;
    color: #000000;
  }

  .close-btn:active {
    transform: scale(0.95);
  }

  .shortcuts-list {
    flex: 1;
    overflow-y: auto;
    padding: 30px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
  }

  .shortcuts-list::-webkit-scrollbar {
    width: 8px;
  }

  .shortcuts-list::-webkit-scrollbar-track {
    background: #f5f5f5;
  }

  .shortcuts-list::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 4px;
  }

  .shortcuts-list::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }

  .shortcut-section h3 {
    margin: 0 0 16px 0;
    font-size: 1rem;
    font-weight: 600;
    color: #333333;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.875rem;
    color: #007aff;
  }

  .shortcut-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    gap: 16px;
  }

  .shortcut-key {
    background: linear-gradient(180deg, #ffffff 0%, #f5f5f5 100%);
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #d0d0d0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.5);
    font-family: 'SF Mono', 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 0.875rem;
    font-weight: 500;
    color: #333333;
    white-space: nowrap;
    min-width: 80px;
    text-align: center;
  }

  .shortcut-desc {
    flex: 1;
    font-size: 0.9rem;
    color: #666666;
    line-height: 1.5;
  }

  .modal-footer {
    padding: 20px 30px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
    display: flex;
    justify-content: flex-end;
  }

  .primary-btn {
    background: #007aff;
    color: #ffffff;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .primary-btn:hover {
    background: #0056b3;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  }

  .primary-btn:active {
    transform: translateY(0);
  }

  /* Mobile responsive */
  @media (max-width: 768px) {
    .shortcuts-list {
      grid-template-columns: 1fr;
      gap: 24px;
      padding: 20px;
    }

    .modal-header {
      padding: 20px;
    }

    .modal-footer {
      padding: 16px 20px;
    }

    .shortcut-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .shortcut-key {
      min-width: auto;
    }
  }
</style>
