<script>
  let {
    message = 'Loading...',
    submessage = null,
    size = 'medium',
    fullScreen = false
  } = $props();

  const sizeMap = {
    small: '24px',
    medium: '48px',
    large: '64px'
  };

  const spinnerSize = $derived(sizeMap[size] || sizeMap.medium);
</script>

<div class="loading-state" class:fullscreen={fullScreen}>
  <div class="loading-content">
    <div class="spinner" style="width: {spinnerSize}; height: {spinnerSize};"></div>
    <p class="loading-message">{message}</p>
    {#if submessage}
      <p class="loading-submessage">{submessage}</p>
    {/if}
  </div>
</div>

<style>
  .loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem;
  }

  .loading-state.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    z-index: 9998;
  }

  .loading-content {
    text-align: center;
    animation: fadeIn 0.3s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .spinner {
    margin: 0 auto 1.5rem;
    border: 3px solid #e0e0e0;
    border-top-color: #007aff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .loading-message {
    font-size: 1.1rem;
    font-weight: 600;
    color: #333333;
    margin: 0 0 0.5rem 0;
  }

  .loading-submessage {
    font-size: 0.9rem;
    color: #666666;
    margin: 0;
  }
</style>
