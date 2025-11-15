<script>
  import { invoke } from '@tauri-apps/api/core';

  let { sessions = $bindable([]), currentSessionId = $bindable(null), onNewSession } = $props();

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
    }
  }

  function selectSession(sessionId) {
    currentSessionId = sessionId;
  }
</script>

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

  <div class="sessions-list">
    {#if sessions.length === 0}
      <div class="empty-state">
        <p>No sessions yet</p>
        <button class="create-first-btn" onclick={createNewSession}>
          Create your first session
        </button>
      </div>
    {:else}
      {#each sessions as session}
        <div
          class="session-item"
          class:active={currentSessionId === session.id}
          onclick={() => selectSession(session.id)}
          role="button"
          tabindex="0"
        >
          <div class="session-title">{session.title || 'Untitled Session'}</div>
          <div class="session-date">{new Date(session.created_at).toLocaleDateString()}</div>
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
  }

  .session-item:hover {
    background: #f5f5f5;
  }

  .session-item.active {
    background: #e3f2fd;
    border-left: 3px solid #007aff;
    padding-left: 13px;
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
