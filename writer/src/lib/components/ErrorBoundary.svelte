<script>
  /**
   * ErrorBoundary Component
   * Provides graceful error handling for Svelte components
   * Usage: Wrap components that may throw errors
   */

  import { onMount, onDestroy } from 'svelte';

  // Props using Svelte 5 runes
  let { error = $bindable(null), retry = null, context = 'component' } = $props();

  // Internal state
  let hasError = $state(false);
  let errorDetails = $state(null);

  // Watch for external error changes
  $effect(() => {
    if (error) {
      hasError = true;
      errorDetails = formatError(error);
    }
  });

  function formatError(err) {
    if (typeof err === 'string') {
      return { message: err, type: 'Error' };
    }

    return {
      message: err.message || 'An unknown error occurred',
      type: err.name || err.type || 'Error',
      stack: err.stack
    };
  }

  function handleRetry() {
    hasError = false;
    errorDetails = null;
    error = null;

    if (retry) {
      retry();
    }
  }

  function handleDismiss() {
    hasError = false;
    errorDetails = null;
    error = null;
  }

  // Handle uncaught errors in this component's scope
  function handleGlobalError(event) {
    if (event.error && !hasError) {
      hasError = true;
      errorDetails = formatError(event.error);
      event.preventDefault();
    }
  }

  onMount(() => {
    window.addEventListener('error', handleGlobalError);
  });

  onDestroy(() => {
    window.removeEventListener('error', handleGlobalError);
  });
</script>

{#if hasError && errorDetails}
  <div class="error-boundary" role="alert">
    <div class="error-container">
      <div class="error-icon">⚠️</div>
      <div class="error-content">
        <h3 class="error-title">
          {errorDetails.type} in {context}
        </h3>
        <p class="error-message">{errorDetails.message}</p>

        {#if errorDetails.stack}
          <details class="error-stack">
            <summary>Error Details</summary>
            <pre>{errorDetails.stack}</pre>
          </details>
        {/if}

        <div class="error-actions">
          {#if retry}
            <button class="btn-retry" onclick={handleRetry}>
              🔄 Retry
            </button>
          {/if}
          <button class="btn-dismiss" onclick={handleDismiss}>
            Dismiss
          </button>
        </div>
      </div>
    </div>
  </div>
{:else}
  <slot></slot>
{/if}

<style>
  .error-boundary {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: var(--bg-error, #fff5f5);
    border: 2px solid #fee2e2;
    border-radius: 0.75rem;
    margin: 1rem 0;
  }

  .error-container {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    max-width: 600px;
    width: 100%;
  }

  .error-icon {
    font-size: 2rem;
    line-height: 1;
    flex-shrink: 0;
  }

  .error-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .error-title {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #991b1b;
  }

  .error-message {
    margin: 0;
    font-size: 0.9375rem;
    line-height: 1.5;
    color: #7f1d1d;
  }

  .error-stack {
    margin-top: 0.5rem;
    padding: 0.75rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.375rem;
  }

  .error-stack summary {
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    color: #991b1b;
    user-select: none;
  }

  .error-stack summary:hover {
    text-decoration: underline;
  }

  .error-stack pre {
    margin: 0.5rem 0 0;
    padding: 0.5rem;
    background: #450a0a;
    color: #fecaca;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .error-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-retry {
    background: #dc2626;
    color: white;
  }

  .btn-retry:hover {
    background: #b91c1c;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(220, 38, 38, 0.2);
  }

  .btn-dismiss {
    background: white;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  .btn-dismiss:hover {
    background: #fef2f2;
  }

  button:active {
    transform: translateY(0);
  }
</style>
