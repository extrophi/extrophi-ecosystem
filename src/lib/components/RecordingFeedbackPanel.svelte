<script>
  /**
   * RecordingFeedbackPanel - Complete visual feedback during recording
   *
   * This component combines all visual feedback features:
   * - Pulsing recording indicator
   * - Audio level meter
   * - Recording timer
   * - Waveform visualization
   *
   * Usage:
   *   <RecordingFeedbackPanel
   *     {isRecording}
   *     {peakLevel}
   *     {recordingTime}
   *     showWaveform={true}
   *   />
   */

  import VolumeIndicator from './VolumeIndicator.svelte';
  import WaveformVisualizer from './WaveformVisualizer.svelte';

  let {
    isRecording = false,
    peakLevel = 0,
    recordingTime = 0,
    showWaveform = false
  } = $props();

  // Format seconds to MM:SS
  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
</script>

{#if isRecording}
  <div class="recording-feedback-panel">
    <!-- Pulsing Recording Indicator -->
    <div class="recording-indicator">
      <div class="pulse-dot"></div>
      <span class="recording-text">Recording</span>
    </div>

    <!-- Recording Timer -->
    <div class="recording-timer">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
      </svg>
      <span class="timer-text">{formatTime(recordingTime)}</span>
    </div>

    <!-- Audio Level Meter -->
    <VolumeIndicator level={peakLevel} visible={isRecording} />

    <!-- Optional Waveform Visualization -->
    {#if showWaveform}
      <WaveformVisualizer level={peakLevel} visible={isRecording} width={300} height={60} />
    {/if}

    <!-- Recording Hint -->
    <p class="recording-hint">Speak clearly into your microphone</p>
  </div>
{/if}

<style>
  .recording-feedback-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(255, 59, 48, 0.05) 0%, rgba(244, 67, 54, 0.05) 100%);
    border-radius: 12px;
    border: 1px solid rgba(255, 59, 48, 0.2);
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Pulsing Recording Indicator */
  .recording-indicator {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .pulse-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #ff3b30;
    box-shadow: 0 0 8px rgba(255, 59, 48, 0.5);
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.6;
      transform: scale(1.2);
      box-shadow: 0 0 16px rgba(255, 59, 48, 0.8);
    }
  }

  .recording-text {
    font-size: 1.1rem;
    font-weight: 600;
    color: #ff3b30;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Recording Timer */
  .recording-timer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .recording-timer svg {
    color: #666666;
  }

  .timer-text {
    font-size: 1.25rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: #000000;
    letter-spacing: 0.05em;
    min-width: 60px;
    text-align: center;
  }

  /* Recording Hint */
  .recording-hint {
    margin: 0;
    font-size: 0.875rem;
    color: #666666;
    font-style: italic;
  }
</style>
