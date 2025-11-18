<script>
  let { messages = [], isLoading = false } = $props();
  
  let messagesEnd;
  
  // Auto-scroll to bottom when messages change
  $effect(() => {
    if (messagesEnd && messages.length > 0) {
      messagesEnd.scrollIntoView({ behavior: 'smooth' });
    }
  });

  function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="messages-container">
  {#if messages.length === 0}
    <div class="empty-state">
      <div class="empty-icon">💬</div>
      <p>No messages yet</p>
      <p class="empty-hint">Start a conversation by typing a message or recording audio</p>
    </div>
  {:else}
    {#each messages as message}
      <div class="message-wrapper {message.role}">
        <div class="message-bubble">
          <div class="message-header">
            <span class="message-role">{message.role === 'user' ? 'You' : 'Assistant'}</span>
            <span class="message-time">{formatTime(message.created_at)}</span>
          </div>
          <div class="message-content">{message.content}</div>
        </div>
      </div>
    {/each}
  {/if}
  
  {#if isLoading}
    <div class="message-wrapper assistant">
      <div class="message-bubble loading">
        <div class="message-header">
          <span class="message-role">Assistant</span>
        </div>
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  {/if}
  
  <div bind:this={messagesEnd}></div>
</div>

<style>
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: #ffffff;
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
    padding: 60px 20px;
  }

  .empty-icon {
    font-size: 4rem;
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
    max-width: 75%;
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

  .message-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
    gap: 12px;
  }

  .message-role {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.8;
  }

  .message-time {
    font-size: 0.7rem;
    opacity: 0.6;
  }

  .message-content {
    font-size: 0.95rem;
    line-height: 1.5;
  }

  .message-bubble.loading {
    padding: 16px 20px;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
    padding-top: 4px;
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
</style>
