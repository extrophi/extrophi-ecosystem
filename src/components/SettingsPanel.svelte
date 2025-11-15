<script>
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from 'svelte';

  export let isOpen = $state(false);

  let apiKey = $state('');
  let hasKey = $state(false);
  let testStatus = $state('idle'); // 'idle' | 'testing' | 'success' | 'error'
  let errorMessage = $state('');
  let successMessage = $state('');

  onMount(async () => {
    await checkApiKey();
  });

  async function checkApiKey() {
    try {
      hasKey = await invoke('has_api_key');
    } catch (error) {
      console.error('Failed to check API key:', error);
    }
  }

  async function handleSave() {
    if (!apiKey || apiKey.trim().length === 0) {
      errorMessage = 'Please enter an API key';
      return;
    }

    try {
      await invoke('store_api_key', { key: apiKey.trim() });
      successMessage = 'API key saved successfully';
      errorMessage = '';
      hasKey = true;
      apiKey = ''; // Clear input after saving

      // Clear success message after 3 seconds
      setTimeout(() => {
        successMessage = '';
      }, 3000);
    } catch (error) {
      errorMessage = `Failed to save API key: ${error}`;
      successMessage = '';
    }
  }

  async function handleTest() {
    testStatus = 'testing';
    errorMessage = '';
    successMessage = '';

    try {
      const isValid = await invoke('test_api_key');
      if (isValid) {
        testStatus = 'success';
        successMessage = 'API key is valid! ✓';
        setTimeout(() => {
          testStatus = 'idle';
          successMessage = '';
        }, 3000);
      } else {
        testStatus = 'error';
        errorMessage = 'API key is invalid or expired';
        setTimeout(() => {
          testStatus = 'idle';
        }, 3000);
      }
    } catch (error) {
      testStatus = 'error';
      errorMessage = `Connection test failed: ${error}`;
      setTimeout(() => {
        testStatus = 'idle';
      }, 3000);
    }
  }

  async function handleDelete() {
    if (!confirm('Are you sure you want to delete your API key?')) {
      return;
    }

    try {
      await invoke('delete_api_key');
      hasKey = false;
      successMessage = 'API key deleted';
      errorMessage = '';

      setTimeout(() => {
        successMessage = '';
      }, 3000);
    } catch (error) {
      errorMessage = `Failed to delete API key: ${error}`;
    }
  }

  function handleClose() {
    isOpen = false;
    errorMessage = '';
    successMessage = '';
    apiKey = '';
  }
</script>

{#if isOpen}
  <div class="overlay" onclick={handleClose}></div>

  <div class="settings-panel">
    <div class="panel-header">
      <h2>Settings</h2>
      <button class="close-btn" onclick={handleClose} aria-label="Close settings">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="panel-content">
      <div class="section">
        <h3>Claude API Key</h3>
        <p class="section-description">
          Enter your Anthropic API key to enable AI-powered journaling features.
        </p>

        {#if hasKey}
          <div class="key-status">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="#34c759" stroke-width="2"/>
              <path d="M6 10l3 3 5-6" stroke="#34c759" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>API key is configured</span>
          </div>
        {:else}
          <div class="key-status warning">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="#ff9500" stroke-width="2"/>
              <path d="M10 6v5M10 14v.5" stroke="#ff9500" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span>No API key configured</span>
          </div>
        {/if}

        <div class="input-group">
          <label for="api-key-input">API Key</label>
          <input
            id="api-key-input"
            type="password"
            bind:value={apiKey}
            placeholder="sk-ant-..."
            class="api-key-input"
          />
          <p class="input-hint">
            Get your API key from <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer">console.anthropic.com</a>
          </p>
        </div>

        <div class="button-group">
          <button class="btn btn-primary" onclick={handleSave} disabled={!apiKey || apiKey.trim().length === 0}>
            Save API Key
          </button>

          {#if hasKey}
            <button
              class="btn btn-secondary"
              onclick={handleTest}
              disabled={testStatus === 'testing'}
            >
              {#if testStatus === 'testing'}
                Testing...
              {:else if testStatus === 'success'}
                ✓ Valid
              {:else if testStatus === 'error'}
                ✗ Invalid
              {:else}
                Test Connection
              {/if}
            </button>

            <button class="btn btn-danger" onclick={handleDelete}>
              Delete Key
            </button>
          {/if}
        </div>

        {#if successMessage}
          <div class="message success">
            {successMessage}
          </div>
        {/if}

        {#if errorMessage}
          <div class="message error">
            {errorMessage}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .settings-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90%;
    max-width: 500px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    z-index: 1001;
    animation: slideUp 0.3s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translate(-50%, -45%);
    }
    to {
      opacity: 1;
      transform: translate(-50%, -50%);
    }
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e0e0e0;
  }

  .panel-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #000000;
  }

  .close-btn {
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    color: #666666;
    transition: all 0.2s ease;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-btn:hover {
    background: #f5f5f5;
    color: #000000;
  }

  .panel-content {
    padding: 24px;
    max-height: 70vh;
    overflow-y: auto;
  }

  .section {
    margin-bottom: 24px;
  }

  .section h3 {
    margin: 0 0 8px 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #000000;
  }

  .section-description {
    margin: 0 0 16px 0;
    font-size: 0.9rem;
    color: #666666;
    line-height: 1.5;
  }

  .key-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: #f0f9f0;
    border: 1px solid #34c759;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 0.9rem;
    color: #1d7a2f;
  }

  .key-status.warning {
    background: #fff8e6;
    border-color: #ff9500;
    color: #8f5000;
  }

  .input-group {
    margin-bottom: 16px;
  }

  .input-group label {
    display: block;
    margin-bottom: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #333333;
  }

  .api-key-input {
    width: 100%;
    padding: 12px;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    font-size: 0.95rem;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    transition: border-color 0.2s ease;
  }

  .api-key-input:focus {
    outline: none;
    border-color: #007aff;
  }

  .input-hint {
    margin: 8px 0 0 0;
    font-size: 0.85rem;
    color: #999999;
  }

  .input-hint a {
    color: #007aff;
    text-decoration: none;
  }

  .input-hint a:hover {
    text-decoration: underline;
  }

  .button-group {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #007aff;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0056b3;
  }

  .btn-secondary {
    background: #f5f5f5;
    color: #333333;
    border: 1px solid #d0d0d0;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #e8e8e8;
  }

  .btn-danger {
    background: #ff3b30;
    color: white;
  }

  .btn-danger:hover:not(:disabled) {
    background: #d32f2f;
  }

  .message {
    margin-top: 16px;
    padding: 12px;
    border-radius: 8px;
    font-size: 0.9rem;
  }

  .message.success {
    background: #f0f9f0;
    border: 1px solid #34c759;
    color: #1d7a2f;
  }

  .message.error {
    background: #fff0f0;
    border: 1px solid #ff3b30;
    color: #c41e3a;
  }
</style>
