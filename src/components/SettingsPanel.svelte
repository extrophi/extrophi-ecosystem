<script>
  import { invoke } from '@tauri-apps/api/core';
  import { showError, showSuccess } from '../lib/utils/toast.js';

  export let isOpen = $state(false);

  let selectedProvider = $state('openai'); // 'openai' or 'claude'
  let openaiKey = $state('');
  let claudeKey = $state('');
  let isTestingOpenai = $state(false);
  let isTestingClaude = $state(false);
  let openaiStatus = $state(null); // 'success' | 'error' | null
  let claudeStatus = $state(null);

  // Load existing keys on mount
  $effect(() => {
    checkExistingKeys();
  });

  async function checkExistingKeys() {
    try {
      const hasOpenai = await invoke('has_openai_key');
      const hasClaude = await invoke('has_api_key');

      if (hasOpenai) openaiStatus = 'success';
      if (hasClaude) claudeStatus = 'success';
    } catch (e) {
      console.error('Failed to check keys:', e);
    }
  }

  function handleClose() {
    isOpen = false;
  }

  async function saveOpenaiKey() {
    if (!openaiKey.trim()) {
      showError('Please enter an API key');
      return;
    }

    if (!openaiKey.startsWith('sk-')) {
      showError('OpenAI keys start with sk-');
      return;
    }

    try {
      await invoke('store_openai_key', { key: openaiKey });
      showSuccess('OpenAI key saved');
      openaiStatus = 'success';
      openaiKey = ''; // Clear input for security
    } catch (e) {
      showError(`Failed to save key: ${e}`);
      openaiStatus = 'error';
    }
  }

  async function testOpenaiConnection() {
    isTestingOpenai = true;
    try {
      const success = await invoke('test_openai_connection');
      if (success) {
        showSuccess('OpenAI connection successful!');
        openaiStatus = 'success';
      } else {
        showError('OpenAI connection failed');
        openaiStatus = 'error';
      }
    } catch (e) {
      showError(`Connection test failed: ${e}`);
      openaiStatus = 'error';
    } finally {
      isTestingOpenai = false;
    }
  }

  async function saveClaudeKey() {
    if (!claudeKey.trim()) {
      showError('Please enter an API key');
      return;
    }

    if (!claudeKey.startsWith('sk-ant-')) {
      showError('Claude keys start with sk-ant-');
      return;
    }

    try {
      await invoke('store_api_key', { key: claudeKey });
      showSuccess('Claude key saved');
      claudeStatus = 'success';
      claudeKey = ''; // Clear input
    } catch (e) {
      showError(`Failed to save key: ${e}`);
      claudeStatus = 'error';
    }
  }

  async function testClaudeConnection() {
    isTestingClaude = true;
    try {
      const success = await invoke('test_api_key');
      if (success) {
        showSuccess('Claude connection successful!');
        claudeStatus = 'success';
      } else {
        showError('Claude connection failed');
        claudeStatus = 'error';
      }
    } catch (e) {
      showError(`Connection test failed: ${e}`);
      claudeStatus = 'error';
    } finally {
      isTestingClaude = false;
    }
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
      <section class="provider-section">
        <h3>AI Provider</h3>
        <p class="help-text">Choose which AI service to use for conversations</p>

        <div class="provider-choice">
          <label>
            <input
              type="radio"
              bind:group={selectedProvider}
              value="openai"
            />
            OpenAI (GPT-4) - $0.15/1M tokens
          </label>

          <label>
            <input
              type="radio"
              bind:group={selectedProvider}
              value="claude"
            />
            Claude (Anthropic) - $3/1M tokens
          </label>
        </div>
      </section>

      <section class="api-keys-section">
        <h3>API Keys</h3>

        <!-- OpenAI Section -->
        <div class="key-group">
          <h4>OpenAI API Key {#if openaiStatus === 'success'}✓{/if}</h4>
          <p class="help-text">
            Get your key from <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a>
          </p>

          <div class="input-row">
            <input
              type="password"
              bind:value={openaiKey}
              placeholder="sk-..."
              class:error={openaiStatus === 'error'}
              class:success={openaiStatus === 'success'}
            />
            <button onclick={saveOpenaiKey}>Save</button>
            <button
              onclick={testOpenaiConnection}
              disabled={isTestingOpenai || openaiStatus !== 'success'}
            >
              {isTestingOpenai ? 'Testing...' : 'Test'}
            </button>
          </div>

          {#if openaiStatus === 'success'}
            <div class="status-message success">✓ Key configured</div>
          {/if}
          {#if openaiStatus === 'error'}
            <div class="status-message error">⚠ Key invalid or not configured</div>
          {/if}
        </div>

        <!-- Claude Section -->
        <div class="key-group">
          <h4>Claude API Key {#if claudeStatus === 'success'}✓{/if}</h4>
          <p class="help-text">
            Get your key from <a href="https://console.anthropic.com/settings/keys" target="_blank">Anthropic Console</a>
          </p>

          <div class="input-row">
            <input
              type="password"
              bind:value={claudeKey}
              placeholder="sk-ant-..."
              class:error={claudeStatus === 'error'}
              class:success={claudeStatus === 'success'}
            />
            <button onclick={saveClaudeKey}>Save</button>
            <button
              onclick={testClaudeConnection}
              disabled={isTestingClaude || claudeStatus !== 'success'}
            >
              {isTestingClaude ? 'Testing...' : 'Test'}
            </button>
          </div>

          {#if claudeStatus === 'success'}
            <div class="status-message success">✓ Key configured</div>
          {/if}
          {#if claudeStatus === 'error'}
            <div class="status-message error">⚠ Key invalid or not configured</div>
          {/if}
        </div>
      </section>

      <section class="info-section">
        <h3>About</h3>
        <p>BrainDump v3.0 - Privacy-first voice journaling</p>
        <p>All data stored locally. API keys stored in system keychain.</p>
      </section>
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
    max-width: 600px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    z-index: 1001;
    animation: slideUp 0.3s ease-out;
    max-height: 85vh;
    overflow-y: auto;
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
    position: sticky;
    top: 0;
    background: white;
    border-radius: 12px 12px 0 0;
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
  }

  section {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #e0e0e0;
  }

  section:last-child {
    border-bottom: none;
  }

  section h3 {
    margin: 0 0 8px 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #000000;
  }

  .provider-choice {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-top: 1rem;
  }

  .provider-choice label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    border: 2px solid #d0d0d0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .provider-choice label:hover {
    border-color: #2196F3;
  }

  .provider-choice label:has(input:checked) {
    border-color: #2196F3;
    background: #e3f2fd;
  }

  .provider-choice input[type="radio"] {
    margin: 0;
  }

  .key-group {
    margin-bottom: 1.5rem;
  }

  .key-group:last-child {
    margin-bottom: 0;
  }

  .key-group h4 {
    margin: 0 0 8px 0;
    font-size: 1rem;
    font-weight: 600;
    color: #333333;
  }

  .input-row {
    display: flex;
    gap: 0.5rem;
    margin-top: 8px;
  }

  input[type="password"] {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.95rem;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    transition: border-color 0.2s ease;
  }

  input[type="password"]:focus {
    outline: none;
    border-color: #2196F3;
  }

  input.success {
    border-color: #4caf50;
    background: #f0f9f0;
  }

  input.error {
    border-color: #f44336;
    background: #fff0f0;
  }

  button {
    padding: 10px 18px;
    border: none;
    border-radius: 6px;
    background: #2196F3;
    color: white;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  button:hover:not(:disabled) {
    background: #1976D2;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .status-message {
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.875rem;
  }

  .status-message.success {
    background: #e8f5e9;
    color: #2e7d32;
    border: 1px solid #4caf50;
  }

  .status-message.error {
    background: #ffebee;
    color: #c62828;
    border: 1px solid #f44336;
  }

  .help-text {
    font-size: 0.875rem;
    color: #666666;
    margin: 4px 0;
    line-height: 1.4;
  }

  a {
    color: #2196F3;
    text-decoration: none;
  }

  a:hover {
    text-decoration: underline;
  }

  .info-section p {
    margin: 8px 0;
    font-size: 0.9rem;
    color: #666666;
  }
</style>
