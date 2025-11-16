<script>
  let {
    error = $bindable(null),
    retry = null,
    onDismiss = null,
    fullScreen = false,
    context = 'general'
  } = $props();

  function getErrorInfo(error, context) {
    const errorStr = typeof error === 'string' ? error : error?.message || JSON.stringify(error);

    // API Key Errors
    if (errorStr.includes('API key') || errorStr.includes('api_key') || errorStr.includes('ANTHROPIC_API_KEY') || errorStr.includes('OPENAI_API_KEY')) {
      return {
        title: 'API Key Not Found',
        message: 'Your API key is missing or invalid. Please add your OpenAI or Claude API key in Settings.',
        icon: '🔑',
        action: 'Open Settings',
        actionVariant: 'primary',
        onAction: openSettings,
        showDismiss: true,
        showDetails: true
      };
    }

    // Network Errors
    if (errorStr.includes('Network') || errorStr.includes('network') || errorStr.includes('fetch') || errorStr.includes('ECONNREFUSED')) {
      return {
        title: 'Connection Error',
        message: 'Could not connect to the API. Please check your internet connection and try again.',
        icon: '📡',
        action: retry ? 'Retry' : null,
        actionVariant: 'primary',
        onAction: retry,
        showDismiss: true,
        showDetails: true
      };
    }

    // Transcription Errors
    if (errorStr.includes('Transcription') || errorStr.includes('Whisper') || errorStr.includes('ModelNotReady')) {
      return {
        title: 'Transcription Failed',
        message: 'The audio transcription service encountered an error. This might be due to the model loading or invalid audio.',
        icon: '🎤',
        action: retry ? 'Try Again' : null,
        actionVariant: 'primary',
        onAction: retry,
        showDismiss: true,
        showDetails: true
      };
    }

    // Database Errors
    if (errorStr.includes('Database') || errorStr.includes('database') || errorStr.includes('SQLite') || errorStr.includes('Locked')) {
      return {
        title: 'Database Error',
        message: 'There was an issue accessing the database. Try closing other instances of the app.',
        icon: '💾',
        action: retry ? 'Retry' : 'Reload App',
        actionVariant: 'primary',
        onAction: retry || (() => window.location.reload()),
        showDismiss: false,
        showDetails: true
      };
    }

    // Session Load Errors
    if (context === 'session' || errorStr.includes('session')) {
      return {
        title: 'Session Load Failed',
        message: 'Could not load the chat session. The session might be corrupted or deleted.',
        icon: '💬',
        action: 'Create New Session',
        actionVariant: 'primary',
        onAction: () => {
          error = null;
          // Emit event for parent to create new session
          window.dispatchEvent(new CustomEvent('create-new-session'));
        },
        showDismiss: true,
        showDetails: true
      };
    }

    // Message Send Errors
    if (context === 'message' || errorStr.includes('send_message')) {
      return {
        title: 'Message Send Failed',
        message: 'Could not send your message. Please check your connection and API key.',
        icon: '✉️',
        action: retry ? 'Retry' : null,
        actionVariant: 'primary',
        onAction: retry,
        showDismiss: true,
        showDetails: true
      };
    }

    // Generic Error
    return {
      title: 'Something Went Wrong',
      message: 'An unexpected error occurred. Please try again or contact support if the problem persists.',
      icon: '⚠️',
      action: retry ? 'Try Again' : null,
      actionVariant: 'primary',
      onAction: retry,
      showDismiss: true,
      showDetails: true
    };
  }

  function openSettings() {
    error = null;
    // Emit event for parent to open settings
    window.dispatchEvent(new CustomEvent('open-settings'));
  }

  function handleDismiss() {
    if (onDismiss) {
      onDismiss();
    } else {
      error = null;
    }
  }

  let showTechnicalDetails = $state(false);

  const errorInfo = $derived(error ? getErrorInfo(error, context) : null);
  const errorString = $derived(typeof error === 'string' ? error : error?.message || JSON.stringify(error, null, 2));
</script>

{#if error && errorInfo}
  <div class="error-boundary" class:fullscreen={fullScreen}>
    <div class="error-content">
      <div class="error-icon">{errorInfo.icon}</div>
      <h2 class="error-title">{errorInfo.title}</h2>
      <p class="error-message">{errorInfo.message}</p>

      <div class="error-actions">
        {#if errorInfo.action && errorInfo.onAction}
          <button
            onclick={errorInfo.onAction}
            class="error-btn {errorInfo.actionVariant}"
          >
            {errorInfo.action}
          </button>
        {/if}

        {#if errorInfo.showDismiss}
          <button onclick={handleDismiss} class="error-btn secondary">
            Dismiss
          </button>
        {/if}
      </div>

      {#if errorInfo.showDetails}
        <details class="error-details" bind:open={showTechnicalDetails}>
          <summary>Technical Details</summary>
          <pre class="error-stack">{errorString}</pre>
        </details>
      {/if}
    </div>
  </div>
{/if}

<style>
  .error-boundary {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: #fff5f5;
    border: 1px solid #feb2b2;
    border-radius: 8px;
    margin: 1rem 0;
  }

  .error-boundary.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    margin: 0;
    border-radius: 0;
    background: rgba(255, 245, 245, 0.98);
    backdrop-filter: blur(10px);
  }

  .error-content {
    max-width: 600px;
    text-align: center;
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .error-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    line-height: 1;
  }

  .error-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #c53030;
    margin: 0 0 1rem 0;
  }

  .error-message {
    font-size: 1rem;
    color: #742a2a;
    line-height: 1.6;
    margin: 0 0 2rem 0;
  }

  .error-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  .error-btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 120px;
  }

  .error-btn.primary {
    background: #007aff;
    color: #ffffff;
  }

  .error-btn.primary:hover {
    background: #0056b3;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  }

  .error-btn.primary:active {
    transform: translateY(0);
  }

  .error-btn.secondary {
    background: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
  }

  .error-btn.secondary:hover {
    background: #f5f5f5;
    border-color: #999999;
  }

  .error-details {
    margin-top: 2rem;
    text-align: left;
    border-top: 1px solid #feb2b2;
    padding-top: 1rem;
  }

  .error-details summary {
    cursor: pointer;
    font-weight: 600;
    color: #742a2a;
    padding: 0.5rem;
    user-select: none;
    font-size: 0.9rem;
  }

  .error-details summary:hover {
    color: #c53030;
  }

  .error-stack {
    background: #ffffff;
    padding: 1rem;
    border-radius: 4px;
    border: 1px solid #feb2b2;
    overflow-x: auto;
    font-size: 0.85rem;
    line-height: 1.5;
    color: #742a2a;
    margin-top: 0.5rem;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .error-stack::-webkit-scrollbar {
    height: 8px;
  }

  .error-stack::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 4px;
  }

  .error-stack::-webkit-scrollbar-thumb {
    background: #feb2b2;
    border-radius: 4px;
  }

  .error-stack::-webkit-scrollbar-thumb:hover {
    background: #fc8181;
  }
</style>
