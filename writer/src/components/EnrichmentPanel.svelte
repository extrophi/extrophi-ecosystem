<script>
  import { invoke } from '@tauri-apps/api/core';
  import ErrorBoundary from '../lib/components/ErrorBoundary.svelte';

  // Component props using Svelte 5 runes
  let { content = $bindable(''), onEnriched = null } = $props();

  let enrichmentType = $state('expand');
  let loading = $state(false);
  let enrichedContent = $state('');
  let error = $state('');
  let connectionStatus = $state('unknown');

  // Test connection on mount
  $effect(() => {
    testConnection();
  });

  async function testConnection() {
    try {
      const isConnected = await invoke('test_research_connection');
      connectionStatus = isConnected ? 'connected' : 'disconnected';
    } catch (e) {
      connectionStatus = 'error';
      console.error('Connection test failed:', e);
    }
  }

  async function handleEnrich() {
    if (!content.trim()) {
      error = 'Please provide content to enrich';
      return;
    }

    loading = true;
    error = '';
    enrichedContent = '';

    try {
      const result = await invoke('enrich_content', {
        content: content.trim(),
        enrichmentType
      });

      enrichedContent = result;

      // Call optional callback
      if (onEnriched) {
        onEnriched(result);
      }
    } catch (e) {
      console.error('Enrichment error:', e);
      error = e.toString();
    } finally {
      loading = false;
    }
  }

  function handleCopyEnriched() {
    if (enrichedContent) {
      navigator.clipboard.writeText(enrichedContent);
    }
  }

  function handleReplaceContent() {
    if (enrichedContent) {
      content = enrichedContent;
      enrichedContent = '';
    }
  }
</script>

<ErrorBoundary>
  <div class="enrichment-panel">
    <div class="panel-header">
      <h3>Content Enrichment</h3>
      <div class="connection-status" class:connected={connectionStatus === 'connected'} class:disconnected={connectionStatus !== 'connected'}>
        {#if connectionStatus === 'connected'}
          <span class="status-dot"></span> Research API Connected
        {:else if connectionStatus === 'disconnected'}
          <span class="status-dot"></span> Research API Offline
        {:else}
          <span class="status-dot"></span> Checking...
        {/if}
      </div>
    </div>

    <div class="enrichment-controls">
      <label for="enrichment-type">Enrichment Type:</label>
      <select id="enrichment-type" bind:value={enrichmentType} disabled={loading}>
        <option value="expand">Expand</option>
        <option value="summarize">Summarize</option>
        <option value="analyze">Analyze</option>
      </select>

      <button
        class="enrich-button"
        onclick={handleEnrich}
        disabled={loading || !content.trim() || connectionStatus !== 'connected'}
      >
        {loading ? 'Enriching...' : 'Enrich Content'}
      </button>

      <button
        class="test-button"
        onclick={testConnection}
        disabled={loading}
      >
        Test Connection
      </button>
    </div>

    {#if error}
      <div class="error-message">
        <strong>Error:</strong> {error}
      </div>
    {/if}

    {#if enrichedContent}
      <div class="result-container">
        <div class="result-header">
          <h4>Enriched Content:</h4>
          <div class="result-actions">
            <button class="action-button" onclick={handleCopyEnriched}>
              📋 Copy
            </button>
            <button class="action-button" onclick={handleReplaceContent}>
              ↩️ Replace Original
            </button>
          </div>
        </div>
        <div class="result-content">
          {enrichedContent}
        </div>
      </div>
    {/if}
  </div>
</ErrorBoundary>

<style>
  .enrichment-panel {
    padding: 1rem;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 0.5rem;
    border: 1px solid var(--border-color, #e0e0e0);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary, #1f2937);
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    background: var(--bg-tertiary, #f9fafb);
  }

  .connection-status.connected {
    color: #10b981;
  }

  .connection-status.disconnected {
    color: #ef4444;
  }

  .status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: currentColor;
  }

  .enrichment-controls {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
  }

  label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary, #6b7280);
  }

  select {
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border-color, #d1d5db);
    border-radius: 0.375rem;
    background: white;
    color: var(--text-primary, #1f2937);
    font-size: 0.875rem;
    cursor: pointer;
  }

  select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

  .enrich-button {
    background: #3b82f6;
    color: white;
  }

  .enrich-button:hover:not(:disabled) {
    background: #2563eb;
  }

  .enrich-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .test-button {
    background: #6b7280;
    color: white;
  }

  .test-button:hover:not(:disabled) {
    background: #4b5563;
  }

  .error-message {
    margin-top: 1rem;
    padding: 0.75rem;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 0.375rem;
    color: #dc2626;
    font-size: 0.875rem;
  }

  .result-container {
    margin-top: 1rem;
    padding: 1rem;
    background: white;
    border: 1px solid var(--border-color, #d1d5db);
    border-radius: 0.375rem;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .result-header h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary, #1f2937);
  }

  .result-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-button {
    padding: 0.375rem 0.75rem;
    background: var(--bg-secondary, #f3f4f6);
    color: var(--text-primary, #1f2937);
    font-size: 0.8125rem;
  }

  .action-button:hover {
    background: var(--bg-tertiary, #e5e7eb);
  }

  .result-content {
    padding: 0.75rem;
    background: var(--bg-tertiary, #f9fafb);
    border-radius: 0.375rem;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--text-primary, #1f2937);
    max-height: 400px;
    overflow-y: auto;
  }
</style>
