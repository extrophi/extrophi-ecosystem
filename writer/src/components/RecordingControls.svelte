<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  let {
    isRecording = $bindable(false),
    isPaused = $bindable(false),
    recordingTime = $bindable(0),
    onStart = () => {},
    onStop = () => {},
    modelStatus = 'ready'
  } = $props();

  let timer = $state<NodeJS.Timeout | null>(null);

  async function startRecording() {
    try {
      await invoke('start_recording');
      isRecording = true;
      isPaused = false;
      recordingTime = 0;
      startTimer();
      onStart();
    } catch (e) {
      console.error('Failed to start recording:', e);
    }
  }

  async function pauseRecording() {
    try {
      await invoke('pause_recording');
      isPaused = true;
      stopTimer();
    } catch (e) {
      console.error('Failed to pause recording:', e);
      // If pause command doesn't exist yet, just update UI state
      isPaused = true;
      stopTimer();
    }
  }

  async function resumeRecording() {
    try {
      await invoke('resume_recording');
      isPaused = false;
      startTimer();
    } catch (e) {
      console.error('Failed to resume recording:', e);
      // If resume command doesn't exist yet, just update UI state
      isPaused = false;
      startTimer();
    }
  }

  async function stopRecording() {
    try {
      stopTimer();
      recordingTime = 0;
      await onStop();
      isRecording = false;
      isPaused = false;
    } catch (e) {
      console.error('Failed to stop recording:', e);
      isRecording = false;
      isPaused = false;
    }
  }

  function startTimer() {
    if (timer) clearInterval(timer);
    timer = setInterval(() => {
      recordingTime += 1;
    }, 1000);
  }

  function stopTimer() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<div class="recording-controls">
  <div class="time-display">
    {formatTime(recordingTime)}
  </div>

  <div class="controls">
    {#if !isRecording}
      <button class="btn-record" onclick={startRecording} disabled={modelStatus !== 'ready'}>
        <span class="icon">🎙️</span>
        Start Recording
      </button>
    {:else if isPaused}
      <button class="btn-resume" onclick={resumeRecording}>
        <span class="icon">▶️</span>
        Resume
      </button>
      <button class="btn-stop" onclick={stopRecording}>
        <span class="icon">⏹️</span>
        Stop
      </button>
    {:else}
      <button class="btn-pause" onclick={pauseRecording}>
        <span class="icon">⏸️</span>
        Pause
      </button>
      <button class="btn-stop" onclick={stopRecording}>
        <span class="icon">⏹️</span>
        Stop
      </button>
    {/if}
  </div>

  {#if modelStatus === 'loading'}
    <div class="status-message loading">Loading model...</div>
  {:else if modelStatus === 'error'}
    <div class="status-message error">Model failed to load</div>
  {:else if isPaused}
    <div class="status-message paused">Recording paused</div>
  {/if}
</div>

<style>
  .recording-controls {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1.5rem;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 0.5rem;
    border: 1px solid #e0e0e0;
  }

  .time-display {
    font-size: 2rem;
    font-weight: bold;
    text-align: center;
    font-family: monospace;
    color: var(--text-primary, #000000);
    letter-spacing: 0.1em;
  }

  .controls {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  button {
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    border: none;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s;
    font-size: 0.95rem;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  button:not(:disabled):hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  button:not(:disabled):active {
    transform: translateY(0);
  }

  .btn-record {
    background: #EF4444;
    color: white;
  }

  .btn-record:not(:disabled):hover {
    background: #DC2626;
  }

  .btn-pause {
    background: #F59E0B;
    color: white;
  }

  .btn-pause:hover {
    background: #D97706;
  }

  .btn-resume {
    background: #10B981;
    color: white;
  }

  .btn-resume:hover {
    background: #059669;
  }

  .btn-stop {
    background: #6B7280;
    color: white;
  }

  .btn-stop:hover {
    background: #4B5563;
  }

  .icon {
    font-size: 1.1em;
    line-height: 1;
  }

  .status-message {
    text-align: center;
    font-size: 0.875rem;
    padding: 0.5rem;
    border-radius: 0.375rem;
    font-weight: 500;
  }

  .status-message.loading {
    background: #DBEAFE;
    color: #1E40AF;
  }

  .status-message.error {
    background: #FEE2E2;
    color: #991B1B;
  }

  .status-message.paused {
    background: #FEF3C7;
    color: #92400E;
  }
</style>
