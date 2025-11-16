<script>
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { onMount } from 'svelte';

  // Model state
  let availableModels = $state([]);
  let installedModels = $state([]);
  let selectedModel = $state('');
  let downloadProgress = $state({});
  let isLoading = $state(true);
  let error = $state('');

  // VAD settings state
  let vadEnabled = $state(false);
  let silenceThreshold = $state(-50);
  let minSilenceDuration = $state(500);

  // Format file size to human-readable format
  const formatSize = (sizeInMB) => {
    if (sizeInMB >= 1024) {
      return `${(sizeInMB / 1024).toFixed(1)} GB`;
    }
    return `${sizeInMB} MB`;
  };

  // Check if model is installed
  const isInstalled = (modelName) => {
    return installedModels.some(m => m.name === modelName);
  };

  // Check if model is currently downloading
  const isDownloading = (modelName) => {
    return downloadProgress[modelName] !== undefined && downloadProgress[modelName] < 100;
  };

  // Get accuracy rating display
  const getAccuracyStars = (accuracy) => {
    const stars = Math.round(accuracy / 20);
    return '★'.repeat(stars) + '☆'.repeat(5 - stars);
  };

  // Get speed rating display
  const getSpeedLabel = (speed) => {
    if (speed >= 80) return 'Very Fast';
    if (speed >= 60) return 'Fast';
    if (speed >= 40) return 'Medium';
    if (speed >= 20) return 'Slow';
    return 'Very Slow';
  };

  // Load available and installed models
  async function loadModels() {
    isLoading = true;
    error = '';

    try {
      const [available, installed, settings] = await Promise.all([
        invoke('get_available_models'),
        invoke('get_installed_models'),
        invoke('get_vad_settings')
      ]);

      availableModels = available;
      installedModels = installed;

      // Load VAD settings
      if (settings) {
        vadEnabled = settings.enabled || false;
        silenceThreshold = settings.silence_threshold || -50;
        minSilenceDuration = settings.min_silence_duration || 500;
      }

      // Get currently selected model
      const currentModel = await invoke('get_selected_model');
      selectedModel = currentModel || '';
    } catch (e) {
      error = `Failed to load models: ${e}`;
      console.error('Failed to load models:', e);
    } finally {
      isLoading = false;
    }
  }

  // Download a model
  async function downloadModel(modelName) {
    error = '';
    downloadProgress[modelName] = 0;

    try {
      await invoke('download_model', { modelName });
      // Progress will be updated via event listener
      await loadModels();
    } catch (e) {
      error = `Failed to download ${modelName}: ${e}`;
      console.error('Failed to download model:', e);
      delete downloadProgress[modelName];
    }
  }

  // Select a model for use
  async function selectModel(modelName) {
    error = '';

    try {
      await invoke('select_model', { modelName });
      selectedModel = modelName;
    } catch (e) {
      error = `Failed to select model: ${e}`;
      console.error('Failed to select model:', e);
    }
  }

  // Delete an installed model
  async function deleteModel(modelName) {
    if (modelName === 'base') {
      error = 'Cannot delete the base model';
      return;
    }

    if (!confirm(`Delete model "${modelName}"? You will need to download it again to use it.`)) {
      return;
    }

    error = '';

    try {
      await invoke('delete_model', { modelName });
      await loadModels();

      // If the deleted model was selected, clear selection
      if (selectedModel === modelName) {
        selectedModel = '';
      }
    } catch (e) {
      error = `Failed to delete model: ${e}`;
      console.error('Failed to delete model:', e);
    }
  }

  // Save VAD settings
  async function saveVadSettings() {
    error = '';

    try {
      await invoke('update_vad_settings', {
        settings: {
          enabled: vadEnabled,
          silence_threshold: silenceThreshold,
          min_silence_duration: minSilenceDuration
        }
      });
    } catch (e) {
      error = `Failed to save VAD settings: ${e}`;
      console.error('Failed to save VAD settings:', e);
    }
  }

  onMount(async () => {
    await loadModels();

    // Listen for download progress events
    const unlisten = await listen('model-download-progress', (event) => {
      const { model_name, progress } = event.payload;
      downloadProgress[model_name] = progress;

      // When download completes, reload models
      if (progress >= 100) {
        setTimeout(() => {
          delete downloadProgress[model_name];
          loadModels();
        }, 500);
      }
    });

    // Cleanup on unmount
    return () => {
      unlisten();
    };
  });
</script>

<div class="model-settings">
  <div class="header">
    <h2>Whisper Model Settings</h2>
    <button onclick={loadModels} class="btn-refresh" disabled={isLoading}>
      {isLoading ? 'Loading...' : 'Refresh'}
    </button>
  </div>

  {#if error}
    <div class="error-banner">
      {error}
    </div>
  {/if}

  {#if isLoading && availableModels.length === 0}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading available models...</p>
    </div>
  {:else}
    <!-- Model Selection Grid -->
    <div class="section">
      <h3>Available Models</h3>
      <p class="section-description">
        Choose a Whisper model based on your accuracy and speed requirements. Larger models are more accurate but slower.
      </p>

      <div class="model-grid">
        {#each availableModels as model}
          <div class="model-card" class:selected={selectedModel === model.name} class:installed={isInstalled(model.name)}>
            <div class="model-header">
              <h4>{model.name}</h4>
              {#if isInstalled(model.name)}
                <span class="badge installed">Installed</span>
              {/if}
              {#if selectedModel === model.name}
                <span class="badge active">Active</span>
              {/if}
            </div>

            <div class="model-stats">
              <div class="stat">
                <span class="stat-label">Size</span>
                <span class="stat-value">{formatSize(model.size_mb)}</span>
              </div>
              <div class="stat">
                <span class="stat-label">Accuracy</span>
                <span class="stat-value stars">{getAccuracyStars(model.accuracy)}</span>
              </div>
              <div class="stat">
                <span class="stat-label">Speed</span>
                <span class="stat-value">{getSpeedLabel(model.speed)}</span>
              </div>
            </div>

            {#if model.description}
              <p class="model-description">{model.description}</p>
            {/if}

            {#if isDownloading(model.name)}
              <div class="progress-container">
                <div class="progress-bar">
                  <div class="progress-fill" style="width: {downloadProgress[model.name]}%"></div>
                </div>
                <span class="progress-text">{Math.round(downloadProgress[model.name])}%</span>
              </div>
            {:else}
              <div class="model-actions">
                {#if !isInstalled(model.name)}
                  <button
                    onclick={() => downloadModel(model.name)}
                    class="btn-download"
                    disabled={isLoading}
                  >
                    Download
                  </button>
                {:else}
                  <button
                    onclick={() => selectModel(model.name)}
                    class="btn-select"
                    disabled={selectedModel === model.name || isLoading}
                  >
                    {selectedModel === model.name ? 'Selected' : 'Use This'}
                  </button>
                  {#if model.name !== 'base'}
                    <button
                      onclick={() => deleteModel(model.name)}
                      class="btn-delete"
                      disabled={isLoading}
                    >
                      Delete
                    </button>
                  {/if}
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <!-- VAD Settings Section -->
    <div class="section vad-section">
      <h3>Voice Activity Detection (VAD)</h3>
      <p class="section-description">
        Configure automatic silence detection to improve transcription quality and reduce processing time.
      </p>

      <div class="vad-settings">
        <div class="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              bind:checked={vadEnabled}
              onchange={saveVadSettings}
            />
            Enable Voice Activity Detection
          </label>
          <span class="form-hint">
            Automatically detect and skip silent portions of audio
          </span>
        </div>

        <div class="form-group" class:disabled={!vadEnabled}>
          <label for="silence-threshold">
            Silence Threshold: <strong>{silenceThreshold} dB</strong>
          </label>
          <input
            id="silence-threshold"
            type="range"
            min="-70"
            max="-30"
            step="1"
            bind:value={silenceThreshold}
            onchange={saveVadSettings}
            disabled={!vadEnabled}
          />
          <div class="range-labels">
            <span>-70 dB (Sensitive)</span>
            <span>-30 dB (Less Sensitive)</span>
          </div>
          <span class="form-hint">
            Audio below this level will be considered silence
          </span>
        </div>

        <div class="form-group" class:disabled={!vadEnabled}>
          <label for="min-silence">
            Minimum Silence Duration: <strong>{minSilenceDuration} ms</strong>
          </label>
          <input
            id="min-silence"
            type="range"
            min="100"
            max="2000"
            step="50"
            bind:value={minSilenceDuration}
            onchange={saveVadSettings}
            disabled={!vadEnabled}
          />
          <div class="range-labels">
            <span>100 ms (Short)</span>
            <span>2000 ms (Long)</span>
          </div>
          <span class="form-hint">
            Minimum duration of silence before considering speech has stopped
          </span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .model-settings {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .header h2 {
    font-size: 1.75rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .btn-refresh {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-refresh:hover:not(:disabled) {
    background: #e5e7eb;
  }

  .btn-refresh:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .error-banner {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    color: #dc2626;
    font-size: 0.95rem;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 4rem 2rem;
    color: #6b7280;
  }

  .spinner {
    border: 3px solid #e5e7eb;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .section {
    margin-bottom: 2.5rem;
  }

  .section h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 0.5rem 0;
  }

  .section-description {
    color: #6b7280;
    font-size: 0.95rem;
    margin: 0 0 1.5rem 0;
    line-height: 1.5;
  }

  .model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
  }

  .model-card {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.2s ease;
  }

  .model-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
  }

  .model-card.selected {
    border-color: #10b981;
    background: #f0fdf4;
  }

  .model-card.installed {
    background: #fafafa;
  }

  .model-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .model-header h4 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    text-transform: capitalize;
  }

  .badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .badge.installed {
    background: #dbeafe;
    color: #1e40af;
  }

  .badge.active {
    background: #d1fae5;
    color: #065f46;
  }

  .model-stats {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .stat-label {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1f2937;
  }

  .stat-value.stars {
    color: #f59e0b;
    font-size: 1rem;
  }

  .model-description {
    font-size: 0.875rem;
    color: #6b7280;
    line-height: 1.5;
    margin: 0 0 1rem 0;
  }

  .progress-container {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #10b981);
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 0.875rem;
    font-weight: 600;
    color: #3b82f6;
    min-width: 3rem;
  }

  .model-actions {
    display: flex;
    gap: 0.75rem;
  }

  .btn-download,
  .btn-select,
  .btn-delete {
    flex: 1;
    padding: 0.625rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-download {
    background: #3b82f6;
    color: #ffffff;
    border: none;
  }

  .btn-download:hover:not(:disabled) {
    background: #2563eb;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  .btn-download:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .btn-select {
    background: #10b981;
    color: #ffffff;
    border: none;
  }

  .btn-select:hover:not(:disabled) {
    background: #059669;
  }

  .btn-select:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .btn-delete {
    background: #ffffff;
    color: #dc2626;
    border: 1px solid #dc2626;
  }

  .btn-delete:hover:not(:disabled) {
    background: #dc2626;
    color: #ffffff;
  }

  .btn-delete:disabled {
    background: #f5f5f5;
    color: #9ca3af;
    border-color: #9ca3af;
    cursor: not-allowed;
  }

  .vad-section {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .vad-settings {
    max-width: 600px;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-group.disabled {
    opacity: 0.5;
  }

  .form-group label {
    display: block;
    font-size: 0.95rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .checkbox-group label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .checkbox-group input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  .form-group input[type="range"] {
    width: 100%;
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    outline: none;
    -webkit-appearance: none;
    cursor: pointer;
  }

  .form-group input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    background: #3b82f6;
    border-radius: 50%;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .form-group input[type="range"]::-webkit-slider-thumb:hover {
    background: #2563eb;
  }

  .form-group input[type="range"]:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .form-group input[type="range"]:disabled::-webkit-slider-thumb {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .range-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #9ca3af;
    margin-top: 0.25rem;
  }

  .form-hint {
    display: block;
    font-size: 0.8rem;
    color: #6b7280;
    margin-top: 0.5rem;
    line-height: 1.4;
  }

  @media (max-width: 768px) {
    .model-settings {
      padding: 1rem;
    }

    .model-grid {
      grid-template-columns: 1fr;
    }

    .model-stats {
      grid-template-columns: 1fr;
      gap: 0.5rem;
    }

    .stat {
      flex-direction: row;
      justify-content: space-between;
    }
  }
</style>
