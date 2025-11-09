<script>
  import { onMount, onDestroy } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';

  let isRecording = $state(false);
  let status = $state('Ready');
  let currentTranscript = $state('');
  let historyItems = $state([]);
  let peakLevel = $state(0);
  let peakInterval = $state(null);
  let recordingTime = $state(0);
  let recordingTimer = $state(null);

  // Model loading state
  let modelStatus = $state('loading'); // 'loading' | 'ready' | 'error'
  let modelMessage = $state('Initializing Whisper model...');
  let unlisten = $state(null);

  async function handleRecord() {
    console.log('🔵 BUTTON CLICKED! isRecording:', isRecording, 'modelStatus:', modelStatus);

    // Don't allow recording if model isn't ready
    if (modelStatus !== 'ready') {
      console.log('⚠️ Model not ready, status:', modelStatus);
      status = 'Please wait for model to load...';
      return;
    }

    if (!isRecording) {
      try {
        console.log('▶️ Starting recording...');
        await invoke('start_recording');
        console.log('✅ Recording started successfully');
        isRecording = true;
        status = 'Recording...';
        currentTranscript = '';
        recordingTime = 0;
        startPeakMonitoring();
        startRecordingTimer();
      } catch (error) {
        console.error('❌ Start recording error:', error);
        status = `Error: ${error}`;
        isRecording = false;
      }
    } else {
      try {
        console.log('🛑 STOP BUTTON CLICKED - handleStopRecording initiated');
        console.log('Current recording time:', formatTime(recordingTime));
        status = 'Transcribing...';
        stopPeakMonitoring();
        stopRecordingTimer();
        console.log('📤 Calling stop_recording command...');
        console.log('Timestamp:', new Date().toISOString());
        const text = await invoke('stop_recording');
        console.log('✅ RESPONSE RECEIVED from stop_recording command');
        console.log('Transcript length:', text?.length || 0, 'characters');
        console.log('Transcript preview:', text?.substring(0, 100) || 'NO TEXT');
        console.log('Full transcript:', text);
        isRecording = false;
        status = 'Ready';
        currentTranscript = text;
        await loadHistory();
      } catch (error) {
        console.error('❌ STOP RECORDING ERROR');
        console.error('Error type:', error?.constructor?.name);
        console.error('Error message:', error?.message);
        console.error('Full error:', error);
        console.error('Timestamp:', new Date().toISOString());
        status = `Error: ${error}`;
        isRecording = false;
      }
    }
  }

  function startRecordingTimer() {
    recordingTimer = setInterval(() => {
      recordingTime += 1;
    }, 1000);
  }

  function stopRecordingTimer() {
    if (recordingTimer) {
      clearInterval(recordingTimer);
      recordingTimer = null;
    }
  }

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  async function loadHistory() {
    try {
      const items = await invoke('get_transcripts', { limit: 10 });
      historyItems = items;
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  }

  function startPeakMonitoring() {
    peakInterval = setInterval(async () => {
      try {
        peakLevel = await invoke('get_peak_level');
      } catch (error) {
        console.error('Failed to get peak level:', error);
      }
    }, 100);
  }

  function stopPeakMonitoring() {
    if (peakInterval) {
      clearInterval(peakInterval);
      peakInterval = null;
      peakLevel = 0;
    }
  }

  onMount(async () => {
    // Set up listener for model-loading events
    unlisten = await listen('model-loading', (event) => {
      const payload = event.payload;
      modelStatus = payload.status;
      modelMessage = payload.message;
    });

    // Check if model is already loaded
    try {
      const loaded = await invoke('is_model_loaded');
      if (loaded) {
        modelStatus = 'ready';
        modelMessage = 'Model loaded successfully';
        status = 'Ready';
      }
    } catch (error) {
      console.error('Failed to check model status:', error);
    }

    loadHistory();
  });

  onDestroy(() => {
    stopPeakMonitoring();
    stopRecordingTimer();

    // Clean up event listener
    if (unlisten) {
      unlisten();
    }
  });
</script>

<div class="app-container">
  <!-- Loading Overlay -->
  {#if modelStatus === 'loading'}
    <div class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <p class="loading-text">{modelMessage}</p>
        <p class="loading-subtext">This may take up to 30 seconds...</p>
      </div>
    </div>
  {/if}

  <!-- Error Display -->
  {#if modelStatus === 'error'}
    <div class="error-banner">
      <div class="error-icon">⚠️</div>
      <div class="error-content">
        <strong>Failed to Load Whisper Model</strong>
        <p>{modelMessage}</p>
        <p class="error-hint">Please ensure the model file exists at: models/ggml-base.bin</p>
      </div>
    </div>
  {/if}

  <!-- Main 2-Column Layout -->
  <div class="main-layout">
    <!-- Left Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="app-title">BrainDump</h1>
      </div>

      <div class="search-container">
        <input type="text" placeholder="Search transcripts..." class="search-input" />
      </div>

      <div class="transcript-list">
        {#if historyItems.length === 0}
          <div class="empty-state">
            <p>No transcripts yet</p>
          </div>
        {:else}
          {#each historyItems as item}
            <div class="transcript-item">
              <div class="item-timestamp">{new Date(item.created_at).toLocaleString()}</div>
              <div class="item-preview">{item.text.substring(0, 60)}{item.text.length > 60 ? '...' : ''}</div>
            </div>
          {/each}
        {/if}
      </div>
    </aside>

    <!-- Right Content Area -->
    <main class="content-area">
      <!-- Record Section at Top -->
      <div class="record-toolbar">
        <!-- Record Button -->
        <button
          class="record-button {isRecording ? 'recording' : ''}"
          onclick={handleRecord}
          disabled={modelStatus !== 'ready'}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          <div class="button-inner">
            {#if isRecording}
              <div class="stop-icon"></div>
            {:else}
              <div class="record-icon"></div>
            {/if}
          </div>
        </button>

        <!-- Status Display -->
        <div class="status-section">
          {#if modelStatus === 'loading'}
            <p class="status-main">Loading Whisper model...</p>
            <p class="status-sub">This may take up to 30 seconds</p>
          {:else if modelStatus === 'error'}
            <p class="status-main error">Model failed to load</p>
            <p class="status-sub">{modelMessage}</p>
          {:else if isRecording}
            <p class="status-main recording-text">Recording</p>
            <p class="status-timer">{formatTime(recordingTime)}</p>
            <div class="audio-level-meter">
              <div class="level-bar" style="width: {peakLevel * 100}%"></div>
            </div>
            <p class="status-sub">Click button to stop</p>
          {:else if status === 'Transcribing...'}
            <p class="status-main">Transcribing...</p>
            <p class="status-sub">Processing your audio</p>
          {:else}
            <p class="status-main ready-text">Ready</p>
            <p class="status-sub">Click to start recording</p>
          {/if}
        </div>
      </div>

      <!-- Current Transcript Display -->
      <div class="transcript-display">
        {#if currentTranscript}
          <div class="transcript-header">
            <h2>Current Transcript</h2>
            <button class="copy-btn" onclick={() => navigator.clipboard.writeText(currentTranscript)}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M5.5 4.5h-2a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2m-5-6h5a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-5a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              Copy
            </button>
          </div>
          <div class="transcript-content">{currentTranscript}</div>
        {:else}
          <div class="empty-transcript">
            <p>Press the record button to start capturing audio</p>
            <p class="hint">Your transcription will appear here</p>
          </div>
        {/if}
      </div>
    </main>
  </div>
</div>

<style>
  /* ==================== Global Layout ==================== */
  .app-container {
    min-height: 100vh;
    background: #ffffff;
    color: #000000;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  }

  .main-layout {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  /* ==================== Left Sidebar ==================== */
  .sidebar {
    width: 300px;
    background: #f5f5f5;
    border-right: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }

  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
    background: #ffffff;
  }

  .app-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #000000;
    margin: 0;
    letter-spacing: -0.02em;
  }

  .search-container {
    padding: 16px;
    border-bottom: 1px solid #e0e0e0;
  }

  .search-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.9rem;
    background: #ffffff;
    color: #000000;
    outline: none;
    transition: border-color 0.2s ease;
  }

  .search-input:focus {
    border-color: #007aff;
  }

  .search-input::placeholder {
    color: #999999;
  }

  .transcript-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }

  .transcript-item {
    padding: 12px 16px;
    cursor: pointer;
    border-bottom: 1px solid #e8e8e8;
    transition: background-color 0.15s ease;
  }

  .transcript-item:hover {
    background: #ebebeb;
  }

  .transcript-item.selected {
    background: #e0e0e0;
  }

  .item-timestamp {
    font-size: 0.75rem;
    color: #666666;
    margin-bottom: 4px;
    font-weight: 500;
  }

  .item-preview {
    font-size: 0.875rem;
    color: #333333;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: #999999;
  }

  .empty-state p {
    margin: 0;
    font-size: 0.9rem;
  }

  /* ==================== Right Content Area ==================== */
  .content-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #ffffff;
    overflow: hidden;
  }

  /* ==================== Record Toolbar ==================== */
  .record-toolbar {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 20px 30px;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
    flex-shrink: 0;
  }

  /* ==================== Record Button ==================== */
  .record-button {
    position: relative;
    width: 140px;
    height: 140px;
    border: none;
    background: transparent;
    cursor: pointer;
    padding: 0;
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .record-button:hover:not(:disabled) {
    transform: scale(1.05);
  }

  .record-button:active:not(:disabled) {
    transform: scale(0.95);
  }

  .record-button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .button-inner {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    border: 2px solid transparent;
    background-image: linear-gradient(rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.08)),
                      linear-gradient(135deg, #5CBDB9, #4A90E2);
    background-origin: border-box;
    background-clip: padding-box, border-box;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }

  .record-button:hover:not(:disabled) .button-inner {
    background-image: linear-gradient(rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.12)),
                      linear-gradient(135deg, #5CBDB9, #4A90E2);
    box-shadow: 0 12px 40px rgba(74, 144, 226, 0.3);
  }

  .record-button.recording .button-inner {
    background: rgba(92, 189, 185, 0.2);
    border-color: #5CBDB9;
    box-shadow: 0 8px 32px rgba(92, 189, 185, 0.4);
  }

  .record-icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #5CBDB9 0%, #4A90E2 100%);
    transition: all 0.3s ease;
  }

  .record-button:hover:not(:disabled) .record-icon {
    background: linear-gradient(135deg, #4db0ac 0%, #3d7fd9 100%);
    transform: scale(1.1);
  }

  .stop-icon {
    width: 36px;
    height: 36px;
    background: #ffffff;
    border-radius: 6px;
    transition: all 0.3s ease;
  }

  .record-button.recording:hover .stop-icon {
    transform: scale(1.1);
  }

  /* Pulse Ring Animation */
  .pulse-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid #5CBDB9;
    animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse-ring {
    0% {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1);
    }
    100% {
      opacity: 0;
      transform: translate(-50%, -50%) scale(1.4);
    }
  }

  /* ==================== Status Display ==================== */
  .status-section {
    text-align: center;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
  }

  .status-main {
    font-size: 1.5rem;
    font-weight: 600;
    color: #000000;
    margin: 0;
    letter-spacing: -0.01em;
  }

  .status-main.error {
    color: #ff3b30;
  }

  .ready-text {
    color: #34c759;
  }

  .recording-text {
    color: #ff3b30;
  }

  .status-timer {
    font-size: 2rem;
    font-weight: 700;
    color: #000000;
    font-variant-numeric: tabular-nums;
    margin: 0;
    letter-spacing: 0.05em;
  }

  .status-sub {
    font-size: 0.95rem;
    color: #666666;
    margin: 0;
  }

  /* ==================== Audio Level Meter ==================== */
  .audio-level-meter {
    width: 280px;
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
    position: relative;
  }

  .level-bar {
    height: 100%;
    background: linear-gradient(90deg,
      #34c759 0%,
      #007aff 50%,
      #5856d6 100%
    );
    border-radius: 3px;
    transition: width 0.1s ease-out;
    box-shadow: 0 0 8px rgba(52, 199, 89, 0.3);
  }

  /* ==================== Transcript Display ==================== */
  .transcript-display {
    flex: 1;
    overflow-y: auto;
    padding: 30px;
  }

  .empty-transcript {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #999999;
    text-align: center;
  }

  .empty-transcript p {
    margin: 0.5rem 0;
    font-size: 1rem;
  }

  .empty-transcript .hint {
    font-size: 0.875rem;
    color: #bbbbbb;
  }

  /* ==================== Transcript Container ==================== */
  .transcript-container {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 2rem;
    animation: slideUp 0.3s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .transcript-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }

  .transcript-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #000000;
    margin: 0;
  }

  .copy-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    padding: 0.625rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s ease;
  }

  .copy-btn:hover {
    background: #f5f5f5;
    border-color: #007aff;
    color: #007aff;
  }

  .copy-btn:active {
    transform: scale(0.95);
  }

  .transcript-content {
    background: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    line-height: 1.7;
    color: #333333;
    font-size: 0.95rem;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #e8e8e8;
  }

  .transcript-content::-webkit-scrollbar {
    width: 8px;
  }

  .transcript-content::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 4px;
  }

  .transcript-content::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 4px;
  }

  .transcript-content::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }

  /* ==================== Loading Overlay ==================== */
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 22, 40, 0.95);
    backdrop-filter: blur(20px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
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

  .loading-content {
    text-align: center;
    padding: 3rem 4rem;
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px) saturate(180%);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  }

  .spinner {
    width: 56px;
    height: 56px;
    margin: 0 auto 2rem;
    border: 3px solid rgba(255, 255, 255, 0.1);
    border-top-color: #4A90E2;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .loading-text {
    font-size: 1.25rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.5rem;
  }

  .loading-subtext {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.5);
  }

  /* ==================== Error Banner ==================== */
  .error-banner {
    position: fixed;
    top: 24px;
    left: 50%;
    transform: translateX(-50%);
    max-width: 560px;
    width: 90%;
    background: rgba(255, 107, 107, 0.15);
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 107, 107, 0.3);
    color: #ffffff;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(255, 107, 107, 0.2);
    z-index: 999;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    animation: slideDown 0.3s ease-out;
  }

  @keyframes slideDown {
    from {
      transform: translateX(-50%) translateY(-20px);
      opacity: 0;
    }
    to {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  }

  .error-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .error-content {
    flex: 1;
  }

  .error-content strong {
    display: block;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #ff9999;
  }

  .error-content p {
    margin: 0.25rem 0;
    font-size: 0.9rem;
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.8);
  }

  .error-hint {
    font-size: 0.85rem;
    opacity: 0.7;
    margin-top: 0.75rem;
    font-style: italic;
    color: rgba(255, 255, 255, 0.6);
  }
</style>
