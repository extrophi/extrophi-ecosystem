<script>
  import { toasts } from '../utils/toast.js';
</script>

{#if $toasts.length > 0}
  <div class="toast-container">
    {#each $toasts as toast (toast.id)}
      <div class="toast toast-{toast.type}" role="alert">
        <div class="toast-content">
          {#if toast.type === 'error'}
            <div class="toast-icon">⚠️</div>
          {:else if toast.type === 'success'}
            <div class="toast-icon">✓</div>
          {:else if toast.type === 'info'}
            <div class="toast-icon">ℹ️</div>
          {/if}
          <div class="toast-message">{toast.message}</div>
        </div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 12px;
    pointer-events: none;
  }

  .toast {
    padding: 14px 18px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    max-width: 400px;
    animation: slideIn 0.3s ease-out;
    pointer-events: auto;
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .toast-error {
    background: #fee;
    border: 1px solid #fcc;
    color: #c33;
  }

  .toast-success {
    background: #efe;
    border: 1px solid #cfc;
    color: #3c3;
  }

  .toast-info {
    background: #eef;
    border: 1px solid #ccf;
    color: #33c;
  }

  .toast-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .toast-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
  }

  .toast-message {
    font-size: 0.9rem;
    line-height: 1.4;
    word-wrap: break-word;
  }
</style>
