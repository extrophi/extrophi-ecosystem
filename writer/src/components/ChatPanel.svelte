<script>
  import { invoke } from '@tauri-apps/api/core';
  import ErrorBoundary from '../lib/components/ErrorBoundary.svelte';
  import { retryWithBackoff, isRetryableError } from '../lib/utils/retry.js';

  // Use $props() for component props in Svelte 5
  let { messages = $bindable([]), currentSession = $bindable(null), onSendMessage = null } = $props();

  let inputText = $state('');
  let isLoading = $state(false);
  let messagesContainer;
  let exportStatus = $state('');
  let errorMessage = $state(null);
  let pendingMessage = $state(null);

  // Auto-scroll to bottom when new messages arrive
  $effect(() => {
    if (messages && messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  async function handleSend() {
    if (!inputText.trim() || isLoading || !currentSession) return;

    const userMessage = inputText.trim();
    pendingMessage = userMessage;
    inputText = '';
    isLoading = true;
    errorMessage = null;

    try {
      // Save user message
      const userMsg = await invoke('save_message', {
        sessionId: currentSession.id,
        role: 'user',
        content: userMessage,
        recordingId: null
      });

      messages = [...messages, userMsg];

      // Send to Claude with retry logic
      const response = await retryWithBackoff(
        () => invoke('send_message_to_claude', {
          message: userMessage
        }),
        {
          maxRetries: 2,
          shouldRetry: isRetryableError,
          onRetry: (attempt) => {
            console.log(`Retrying message send, attempt ${attempt}`);
          }
        }
      );

      // Save Claude's response
      const assistantMsg = await invoke('save_message', {
        sessionId: currentSession.id,
        role: 'assistant',
        content: response,
        recordingId: null
      });

      messages = [...messages, assistantMsg];

      if (onSendMessage) {
        onSendMessage(assistantMsg);
      }

      pendingMessage = null;
    } catch (error) {
      console.error('Failed to send message:', error);
      // Restore input for retry
      inputText = pendingMessage;
      errorMessage = error;
    } finally {
      isLoading = false;
    }
  }

  function retryMessage() {
    if (pendingMessage) {
      inputText = pendingMessage;
      handleSend();
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
    else if (event.key === 'Escape') {
      event.preventDefault();
      inputText = '';
    }
  }

  function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  async function exportSession() {
    if (!currentSession) {
      exportStatus = 'error:No session selected';
      setTimeout(() => exportStatus = '', 3000);
      return;
    }

    if (messages.length === 0) {
      exportStatus = 'error:Cannot export empty session';
      setTimeout(() => exportStatus = '', 3000);
      return;
    }

    try {
      const filePath = await invoke('export_session', {
        sessionId: currentSession.id
      });
      exportStatus = `success:Exported to: ${filePath}`;
      setTimeout(() => exportStatus = '', 5000);
    } catch (error) {
      console.error('Export failed:', error);
      exportStatus = `error:Export failed: ${error}`;
      setTimeout(() => exportStatus = '', 5000);
    }
  }

  function handleGlobalKeydown(event) {
    // Cmd+E (Mac) or Ctrl+E (Windows/Linux) for export
    if ((event.metaKey || event.ctrlKey) && event.key === 'e') {
      event.preventDefault();
      if (currentSession && messages.length > 0) {
        exportSession();
      }
    }
  }
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="chat-panel">
  <div class="chat-header">
    <h3>Chat Session</h3>
    <div class="header-actions">
      {#if exportStatus}
        <div class="export-toast {exportStatus.startsWith('success') ? 'success' : 'error'}">
          {exportStatus.split(':')[1]}
        </div>
      {/if}
      <button
        onclick={exportSession}
        class="export-btn"
        disabled={!currentSession || messages.length === 0}
        title="Export session to Markdown (Cmd+E or Ctrl+E)"
        aria-label="Export session to Markdown"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Export to Markdown
      </button>
    </div>
  </div>
  <div class="messages-container" bind:this={messagesContainer}>
    {#if errorMessage}
      <ErrorBoundary
        bind:error={errorMessage}
        retry={retryMessage}
        context="message"
      />
    {/if}

    {#if messages.length === 0}
      <div class="empty-state">
        <div class="empty-icon">💬</div>
        <p>No messages yet</p>
        <p class="empty-hint">Record audio or type a message to start</p>
      </div>
    {:else}
      {#each messages as message}
        <div class="message-wrapper {message.role}">
          <div class="message-bubble">
            <div class="message-content">{message.content}</div>
            <div class="message-time">{formatTime(message.created_at)}</div>
          </div>
        </div>
      {/each}
    {/if}

    {#if isLoading}
      <div class="message-wrapper assistant">
        <div class="message-bubble loading">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class="input-container">
    <textarea
      bind:value={inputText}
      onkeydown={handleKeyDown}
      placeholder="Type a message or record audio..."
      class="message-input"
      rows="1"
      disabled={isLoading || !currentSession}
    ></textarea>
    <button
      onclick={handleSend}
      class="send-btn"
      disabled={!inputText.trim() || isLoading || !currentSession}
      aria-label="Send message"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
    </button>
  </div>
</div>

<style>
  .chat-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #ffffff;
  }

  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .chat-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #000000;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .export-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #007aff 0%, #0056b3 100%);
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.2);
    position: relative;
  }

  .export-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #0056b3 0%, #003d82 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 122, 255, 0.4);
  }

  .export-btn:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.2);
  }

  .export-btn:disabled {
    background: #cccccc;
    cursor: not-allowed;
    opacity: 0.5;
    box-shadow: none;
  }

  .export-btn svg {
    flex-shrink: 0;
  }

  .export-toast {
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    animation: slideIn 0.3s ease-out;
  }

  .export-toast.success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
  }

  .export-toast.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(10px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .messages-container::-webkit-scrollbar {
    width: 8px;
  }

  .messages-container::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 4px;
  }

  .messages-container::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 4px;
  }

  .messages-container::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #999999;
    text-align: center;
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .empty-state p {
    margin: 0.5rem 0;
    font-size: 1rem;
  }

  .empty-hint {
    font-size: 0.875rem;
    color: #bbbbbb;
  }

  .message-wrapper {
    display: flex;
    width: 100%;
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .message-wrapper.user {
    justify-content: flex-end;
  }

  .message-wrapper.assistant {
    justify-content: flex-start;
  }

  .message-bubble {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 16px;
    word-wrap: break-word;
    white-space: pre-wrap;
  }

  .message-wrapper.user .message-bubble {
    background: #007aff;
    color: #ffffff;
    border-bottom-right-radius: 4px;
  }

  .message-wrapper.assistant .message-bubble {
    background: #f0f0f0;
    color: #000000;
    border-bottom-left-radius: 4px;
  }

  .message-content {
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 4px;
  }

  .message-time {
    font-size: 0.75rem;
    opacity: 0.7;
    text-align: right;
  }

  .message-wrapper.assistant .message-time {
    text-align: left;
  }

  .message-bubble.loading {
    padding: 16px 20px;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: #999999;
    border-radius: 50%;
    animation: typing 1.4s infinite;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
      opacity: 0.7;
    }
    30% {
      transform: translateY(-8px);
      opacity: 1;
    }
  }

  .input-container {
    display: flex;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .message-input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #d0d0d0;
    border-radius: 20px;
    font-size: 0.95rem;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    resize: none;
    outline: none;
    transition: border-color 0.2s ease;
    max-height: 120px;
    line-height: 1.5;
  }

  .message-input:focus {
    border-color: #007aff;
  }

  .message-input:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }

  .send-btn {
    width: 44px;
    height: 44px;
    border: none;
    border-radius: 50%;
    background: #007aff;
    color: #ffffff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .send-btn:hover:not(:disabled) {
    background: #0056b3;
    transform: scale(1.05);
  }

  .send-btn:active:not(:disabled) {
    transform: scale(0.95);
  }

  .send-btn:disabled {
    background: #cccccc;
    cursor: not-allowed;
    opacity: 0.5;
  }
</style>
