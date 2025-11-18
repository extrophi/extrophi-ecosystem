<script>
  import { createEventDispatcher } from 'svelte';

  let { isRecording = false, disabled = false } = $props();

  const dispatch = createEventDispatcher();

  function handleClick() {
    if (!disabled) {
      dispatch('record');
    }
  }
</script>

<button
  class="record-btn"
  class:recording={isRecording}
  class:disabled={disabled}
  {disabled}
  onclick={handleClick}
>
  <span class="pulse" class:active={isRecording}></span>
  <span class="icon">
    {#if isRecording}
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <rect x="6" y="6" width="12" height="12" rx="2"/>
      </svg>
    {:else}
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="12" r="8"/>
      </svg>
    {/if}
  </span>
  <span class="label">
    {isRecording ? 'Stop Recording' : 'Start Recording'}
  </span>
</button>

<style>
  .record-btn {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.25rem 2.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    overflow: hidden;
  }

  .record-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(102, 126, 234, 0.6);
  }

  .record-btn:active {
    transform: translateY(0);
  }

  .record-btn.recording {
    background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
    box-shadow: 0 4px 20px rgba(244, 67, 54, 0.4);
  }

  .record-btn.recording:hover {
    box-shadow: 0 6px 30px rgba(244, 67, 54, 0.6);
  }

  .record-btn:disabled,
  .record-btn.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: linear-gradient(135deg, #555 0%, #666 100%);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }

  .record-btn:disabled:hover,
  .record-btn.disabled:hover {
    transform: none;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }

  .pulse {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    height: 100%;
    border-radius: 12px;
    opacity: 0;
  }

  .pulse.active {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 0;
      transform: translate(-50%, -50%) scale(1);
    }
    50% {
      opacity: 0.3;
      transform: translate(-50%, -50%) scale(1.05);
    }
  }

  .icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .label {
    font-weight: 600;
  }
</style>
