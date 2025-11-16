<script>
  import { invoke } from '@tauri-apps/api/core';
  import SessionsList from './SessionsList.svelte';
  import MessageThread from './MessageThread.svelte';
  import ErrorBoundary from './ErrorBoundary.svelte';
  import LoadingState from './LoadingState.svelte';
  import { showError, showSuccess } from '../utils/toast.js';
  import { retryWithBackoff, isRetryableError } from '../utils/retry.js';

  let sessions = $state([]);
  let currentSessionId = $state(null);
  let messages = $state([]);
  let inputMessage = $state('');
  let selectedPrompt = $state('brain_dump');
  let isLoading = $state(false);
  let availablePrompts = $state([]);

  // Loading and error states
  let loadingState = $state('idle'); // 'idle', 'loading', 'success', 'error'
  let errorMessage = $state(null);
  let errorContext = $state('general');

  // Load sessions on mount
  $effect(() => {
    loadSessions();
    loadPrompts();
  });

  // Load messages when session changes
  $effect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId);
    } else {
      messages = [];
    }
  });

  async function loadSessions() {
    loadingState = 'loading';
    errorMessage = null;

    try {
      const loadedSessions = await retryWithBackoff(
        () => invoke('list_chat_sessions', { limit: 50 }),
        {
          maxRetries: 2,
          shouldRetry: isRetryableError,
          onRetry: (attempt) => {
            console.log(`Retrying session load, attempt ${attempt}`);
          }
        }
      );

      sessions = loadedSessions;

      // Select first session if available and no session is currently selected
      if (loadedSessions.length > 0 && !currentSessionId) {
        currentSessionId = loadedSessions[0].id;
      }

      loadingState = 'success';
    } catch (e) {
      loadingState = 'error';
      errorMessage = e;
      errorContext = 'session';
      showError('Failed to load sessions: ' + e);
    }
  }

  async function loadMessages(sessionId) {
    try {
      const loadedMessages = await retryWithBackoff(
        () => invoke('get_messages', { sessionId }),
        {
          maxRetries: 2,
          shouldRetry: isRetryableError
        }
      );
      messages = loadedMessages;
    } catch (e) {
      errorMessage = e;
      errorContext = 'session';
      showError('Failed to load messages: ' + e);
    }
  }

  async function loadPrompts() {
    try {
      const templates = await invoke('list_prompt_templates');
      availablePrompts = templates.map(t => t.name);

      // Set default if available
      const defaultTemplate = templates.find(t => t.is_default);
      if (defaultTemplate) {
        selectedPrompt = defaultTemplate.name;
      }
    } catch (e) {
      console.warn('Failed to load prompts:', e);
      // Fallback to basic prompts
      availablePrompts = ['brain_dump', 'general'];
    }
  }

  async function sendMessage() {
    if (!inputMessage.trim()) return;
    if (!currentSessionId) {
      showError('No session selected. Please create a new session.');
      return;
    }

    const messageText = inputMessage.trim();
    const tempInputMessage = inputMessage; // Save for retry
    inputMessage = '';
    isLoading = true;
    errorMessage = null;

    try {
      // Save user message
      const userMsg = await invoke('save_message', {
        sessionId: currentSessionId,
        role: 'user',
        content: messageText,
        recordingId: null
      });

      messages = [...messages, userMsg];

      // Send to AI with retry logic
      const response = await retryWithBackoff(
        () => invoke('send_ai_message', {
          messages: [['user', messageText]],
          systemPrompt: null
        }),
        {
          maxRetries: 2,
          shouldRetry: isRetryableError,
          onRetry: (attempt, delay) => {
            showError(`Retrying message send (attempt ${attempt})...`);
          }
        }
      );

      // Save assistant response
      const assistantMsg = await invoke('save_message', {
        sessionId: currentSessionId,
        role: 'assistant',
        content: response,
        recordingId: null
      });

      messages = [...messages, assistantMsg];
      showSuccess('Message sent');
    } catch (e) {
      // Restore input message for retry
      inputMessage = tempInputMessage;
      errorMessage = e;
      errorContext = 'message';
      showError('Failed to send message: ' + e);
    } finally {
      isLoading = false;
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function handleNewSession(newSession) {
    // Session already added to list and selected in SessionsList
    messages = [];
  }

  function retryLoadSessions() {
    loadSessions();
  }
</script>

<div class="chat-container">
  {#if loadingState === 'loading'}
    <LoadingState message="Loading sessions..." submessage="This should only take a moment" fullScreen={true} />
  {:else if loadingState === 'error'}
    <ErrorBoundary
      bind:error={errorMessage}
      retry={retryLoadSessions}
      context={errorContext}
      fullScreen={true}
    />
  {:else}
    <SessionsList
      bind:sessions={sessions}
      bind:currentSessionId={currentSessionId}
      onNewSession={handleNewSession}
    />

    <div class="chat-main">
      {#if !currentSessionId}
        <div class="no-session-state">
          <div class="no-session-icon">💬</div>
          <p>No session selected</p>
          <p class="no-session-hint">Create a new session to start chatting</p>
        </div>
      {:else}
        {#if errorMessage && errorContext === 'message'}
          <ErrorBoundary
            bind:error={errorMessage}
            retry={sendMessage}
            context="message"
          />
        {/if}

        <MessageThread {messages} {isLoading} />

        <div class="input-area">
          <div class="input-controls">
            <select bind:value={selectedPrompt} class="prompt-select">
              {#each availablePrompts as prompt}
                <option value={prompt}>{prompt.replace(/_/g, ' ')}</option>
              {/each}
            </select>

            <textarea
              bind:value={inputMessage}
              onkeydown={handleKeyDown}
              placeholder="Type your message... (Shift+Enter for new line)"
              disabled={isLoading}
              class="message-input"
              rows="1"
            />

            <button
              onclick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
              class="send-btn"
              aria-label="Send message"
            >
              {#if isLoading}
                <div class="spinner"></div>
              {:else}
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              {/if}
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .chat-container {
    display: flex;
    height: 100%;
    background: #ffffff;
  }
  
  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .no-session-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #999999;
    text-align: center;
    padding: 60px 20px;
  }

  .no-session-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .no-session-state p {
    margin: 0.5rem 0;
    font-size: 1.1rem;
  }

  .no-session-hint {
    font-size: 0.9rem;
    color: #bbbbbb;
  }
  
  .input-area {
    padding: 16px 20px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
    flex-shrink: 0;
  }

  .input-controls {
    display: flex;
    gap: 12px;
    align-items: flex-end;
  }

  .prompt-select {
    padding: 10px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    font-size: 0.875rem;
    background: #ffffff;
    color: #333333;
    cursor: pointer;
    outline: none;
    transition: border-color 0.2s ease;
    flex-shrink: 0;
  }

  .prompt-select:focus {
    border-color: #007aff;
  }

  .message-input {
    flex: 1;
    padding: 10px 16px;
    border: 1px solid #d0d0d0;
    border-radius: 20px;
    font-size: 0.95rem;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    resize: none;
    outline: none;
    transition: border-color 0.2s ease;
    max-height: 120px;
    line-height: 1.5;
    background: #ffffff;
  }

  .message-input:focus {
    border-color: #007aff;
  }

  .message-input:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
    opacity: 0.6;
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

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
