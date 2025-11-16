<script>
  import { invoke } from '@tauri-apps/api/core';
  import { showError, showSuccess } from '../utils/toast.js';

  let { sessions = $bindable([]), currentSessionId = $bindable(null), onNewSession } = $props();

  let editingSessionId = $state(null);
  let editTitle = $state('');
  let searchQuery = $state('');
  let searchInputRef = $state(null);

  // Derived state for filtered sessions
  let filteredSessions = $derived(filterSessions());

  function filterSessions() {
    if (!searchQuery.trim()) {
      return sessions;
    }

    const query = searchQuery.toLowerCase();
    return sessions.filter(session =>
      (session.title || 'Untitled Session').toLowerCase().includes(query)
    );
  }

  function clearSearch() {
    searchQuery = '';
  }

  function handleGlobalKeydown(event) {
    // Cmd+F (Mac) or Ctrl+F (Windows/Linux) to focus search
    if ((event.metaKey || event.ctrlKey) && event.key === 'f') {
      event.preventDefault();
      searchInputRef?.focus();
    }
  }

  async function createNewSession() {
    try {
      const now = new Date();
      const title = 'Chat Session ' + now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
      const newSession = await invoke('create_chat_session', { title });
      sessions = [newSession, ...sessions];
      currentSessionId = newSession.id;

      if (onNewSession) {
        onNewSession(newSession);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      showError('Failed to create session');
    }
  }

  function selectSession(sessionId) {
    currentSessionId = sessionId;
  }

  function startRename(session, event) {
    event.stopPropagation();
    editingSessionId = session.id;
    editTitle = session.title || '';
  }

  async function saveRename(sessionId) {
    if (!editTitle.trim()) {
      showError('Title cannot be empty');
      return;
    }

    try {
      await invoke('rename_session', {
        sessionId,
        newTitle: editTitle
      });

      // Update local state
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        session.title = editTitle;
      }

      showSuccess('Session renamed');
      editingSessionId = null;
    } catch (e) {
      showError(`Failed to rename: ${e}`);
    }
  }

  function cancelRename() {
    editingSessionId = null;
    editTitle = '';
  }

  async function deleteSessionHandler(sessionId, event) {
    event.stopPropagation();

    const session = sessions.find(s => s.id === sessionId);
    if (!confirm(`Delete session "${session?.title}"?\n\nThis will delete all messages in this session.`)) {
      return;
    }

    try {
      await invoke('delete_session', { sessionId });

      // Remove from local state
      sessions = sessions.filter(s => s.id !== sessionId);

      // If we deleted the current session, clear selection
      if (currentSessionId === sessionId) {
        currentSessionId = null;
      }

      showSuccess('Session deleted');
    } catch (e) {
      showError(`Failed to delete: ${e}`);
    }
  }

  function handleKeydown(event, sessionId) {
    if (event.key === 'Enter') {
      saveRename(sessionId);
    } else if (event.key === 'Escape') {
      cancelRename();
    }
  }

  function handleListKeydown(event) {
    // Only handle arrow keys when not editing
    if (editingSessionId !== null) return;

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      navigateSessions(-1);
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      navigateSessions(1);
    }
  }

  function navigateSessions(direction) {
    if (sessions.length === 0) return;

    const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
    let newIndex;

    if (currentIndex === -1) {
      // No session selected, select the first one
      newIndex = 0;
    } else {
      // Move up or down
      newIndex = currentIndex + direction;
      // Clamp to valid range
      newIndex = Math.max(0, Math.min(sessions.length - 1, newIndex));
    }

    if (newIndex !== currentIndex && sessions[newIndex]) {
      selectSession(sessions[newIndex].id);
    }
  }
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="sessions-sidebar">
  <div class="sidebar-header">
    <h3>Chat Sessions</h3>
    <button class="new-session-btn" onclick={createNewSession} aria-label="New session">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"></line>
        <line x1="5" y1="12" x2="19" y2="12"></line>
      </svg>
    </button>
  </div>

  <div class="search-box">
    <div class="search-input-wrapper">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <input
        type="text"
        bind:value={searchQuery}
        bind:this={searchInputRef}
        placeholder="Search sessions..."
        class="search-input"
        aria-label="Search sessions"
      />
      {#if searchQuery}
        <button onclick={clearSearch} class="clear-btn" title="Clear search" aria-label="Clear search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      {/if}
    </div>

    <div class="session-count">
      {filteredSessions.length} {#if filteredSessions.length !== sessions.length}of {sessions.length}{/if} session{sessions.length !== 1 ? 's' : ''}
    </div>
  </div>

  <div class="sessions-list" onkeydown={handleListKeydown} tabindex="0" role="listbox">
    {#if sessions.length === 0}
      <div class="empty-state">
        <p>No sessions yet</p>
        <button class="create-first-btn" onclick={createNewSession}>
          Create your first session
        </button>
      </div>
    {:else if filteredSessions.length === 0}
      <div class="no-results">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <p>No sessions found</p>
        <p class="search-hint">No results for "{searchQuery}"</p>
        <button onclick={clearSearch} class="clear-search-btn">Clear search</button>
      </div>
    {:else}
      {#each filteredSessions as session}
        <div
          class="session-item"
          class:active={currentSessionId === session.id}
          class:editing={editingSessionId === session.id}
          onclick={() => selectSession(session.id)}
          onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && selectSession(session.id)}
          role="button"
          tabindex="0"
        >
          {#if editingSessionId === session.id}
            <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
            <form class="edit-mode" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} onsubmit={(e) => { e.preventDefault(); saveRename(session.id); }}>
              <!-- svelte-ignore a11y_autofocus -->
              <input
                type="text"
                bind:value={editTitle}
                onkeydown={(e) => handleKeydown(e, session.id)}
                autofocus
                class="edit-input"
              />
              <div class="edit-actions">
                <button type="submit" title="Save" class="btn-save">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </button>
                <button type="button" onclick={cancelRename} title="Cancel" class="btn-cancel">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            </form>
          {:else}
            <div class="session-content">
              <div class="session-title">{session.title || 'Untitled Session'}</div>
              <div class="session-date">{new Date(session.created_at).toLocaleDateString()}</div>
            </div>

            <div class="session-actions">
              <button
                onclick={(e) => startRename(session, e)}
                title="Rename"
                class="icon-btn btn-rename"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button
                onclick={(e) => deleteSessionHandler(session.id, e)}
                title="Delete"
                class="icon-btn btn-delete"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .sessions-sidebar {
    width: 280px;
    border-right: 1px solid #e0e0e0;
    background: #fafafa;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid #e0e0e0;
    background: #ffffff;
  }

  .sidebar-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #000000;
  }

  .search-box {
    padding: 12px 16px;
    border-bottom: 1px solid #e0e0e0;
    background: #ffffff;
  }

  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 10px;
    color: #999999;
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 8px 32px 8px 36px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.875rem;
    font-family: inherit;
    background: #fafafa;
    transition: all 0.2s ease;
  }

  .search-input:focus {
    outline: none;
    border-color: #007aff;
    background: #ffffff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }

  .search-input::placeholder {
    color: #999999;
  }

  .clear-btn {
    position: absolute;
    right: 8px;
    padding: 4px;
    background: none;
    border: none;
    cursor: pointer;
    color: #999999;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .clear-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: #666666;
  }

  .session-count {
    margin-top: 8px;
    font-size: 0.75rem;
    color: #666666;
    text-align: center;
  }

  .no-results {
    padding: 60px 20px;
    text-align: center;
    color: #999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  .no-results svg {
    color: #d0d0d0;
    margin-bottom: 8px;
  }

  .no-results p {
    margin: 0;
    font-size: 0.9rem;
  }

  .no-results p:first-of-type {
    font-weight: 500;
    color: #666666;
  }

  .search-hint {
    font-size: 0.8rem;
    color: #999999;
    font-style: italic;
  }

  .clear-search-btn {
    margin-top: 8px;
    padding: 8px 16px;
    background: #f5f5f5;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.8rem;
    color: #666666;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .clear-search-btn:hover {
    background: #e0e0e0;
    border-color: #b0b0b0;
    color: #333333;
  }

  .new-session-btn {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 6px;
    background: #007aff;
    color: #ffffff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  }

  .new-session-btn:hover {
    background: #0056b3;
    transform: scale(1.05);
  }

  .new-session-btn:active {
    transform: scale(0.95);
  }

  .sessions-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
    outline: none;
  }

  .sessions-list:focus {
    outline: 2px solid rgba(0, 122, 255, 0.3);
    outline-offset: -2px;
  }

  .sessions-list::-webkit-scrollbar {
    width: 6px;
  }

  .sessions-list::-webkit-scrollbar-track {
    background: #f5f5f5;
  }

  .sessions-list::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 3px;
  }

  .sessions-list::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }

  .session-item {
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #ebebeb;
    transition: background-color 0.15s ease;
    background: #ffffff;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .session-item:hover {
    background: #f5f5f5;
  }

  .session-item.active {
    background: #e3f2fd;
    border-left: 3px solid #007aff;
    padding-left: 13px;
  }

  .session-item.editing {
    cursor: default;
  }

  .session-content {
    flex: 1;
    min-width: 0;
  }

  .session-title {
    font-size: 0.9rem;
    font-weight: 500;
    color: #333333;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .session-date {
    font-size: 0.75rem;
    color: #999999;
  }

  .session-actions {
    display: none;
    gap: 4px;
    align-items: center;
  }

  .session-item:hover .session-actions {
    display: flex;
  }

  .icon-btn {
    padding: 6px;
    border: none;
    background: transparent;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666666;
    transition: all 0.15s ease;
  }

  .icon-btn:hover {
    background: rgba(0, 0, 0, 0.1);
  }

  .btn-rename:hover {
    color: #007aff;
    background: rgba(0, 122, 255, 0.1);
  }

  .btn-delete:hover {
    color: #ff3b30;
    background: rgba(255, 59, 48, 0.1);
  }

  .edit-mode {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .edit-input {
    width: 100%;
    padding: 8px;
    border: 1px solid #007aff;
    border-radius: 4px;
    font-size: 0.9rem;
    font-family: inherit;
    outline: none;
    background: #ffffff;
  }

  .edit-input:focus {
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }

  .edit-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .edit-actions button {
    padding: 6px 12px;
    border: 1px solid #d0d0d0;
    background: #ffffff;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .btn-save {
    color: #007aff;
    border-color: #007aff;
  }

  .btn-save:hover {
    background: #007aff;
    color: #ffffff;
  }

  .btn-cancel {
    color: #666666;
  }

  .btn-cancel:hover {
    background: #f5f5f5;
    border-color: #999999;
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: #999999;
  }

  .empty-state p {
    margin: 0 0 16px 0;
    font-size: 0.9rem;
  }

  .create-first-btn {
    background: #007aff;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .create-first-btn:hover {
    background: #0056b3;
    transform: translateY(-1px);
  }

  .create-first-btn:active {
    transform: translateY(0);
  }
</style>
