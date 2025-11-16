<script>
  import { invoke } from '@tauri-apps/api/core';
  import { showError, showSuccess } from '../utils/toast.js';

  let stats = $state(null);
  let isLoading = $state(true);
  let isExporting = $state(false);

  // Load stats on mount
  $effect(() => {
    loadStats();
  });

  async function loadStats() {
    isLoading = true;
    try {
      stats = await invoke('get_usage_stats');
      console.log('Loaded stats:', stats);
    } catch (e) {
      showError(`Failed to load stats: ${e}`);
      console.error('Stats loading error:', e);
    } finally {
      isLoading = false;
    }
  }

  function formatDuration(ms) {
    if (!ms) return '0m 0s';
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m ${seconds}s`;
  }

  function exportStats() {
    if (!stats) return;

    isExporting = true;

    try {
      // Generate CSV content
      const csv = generateCSV(stats);

      // Create blob and download
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `braindump-stats-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showSuccess('Statistics exported successfully');
    } catch (e) {
      showError(`Export failed: ${e}`);
      console.error('Export error:', e);
    } finally {
      isExporting = false;
    }
  }

  function generateCSV(stats) {
    const lines = [];

    lines.push('BrainDump Usage Statistics');
    lines.push(`Generated: ${new Date().toISOString()}`);
    lines.push('');

    lines.push('Overall Statistics');
    lines.push('Metric,Value');
    lines.push(`Total Sessions,${stats.total_sessions}`);
    lines.push(`Sessions This Week,${stats.sessions_this_week}`);
    lines.push(`Sessions This Month,${stats.sessions_this_month}`);
    lines.push(`Total Messages,${stats.total_messages}`);
    lines.push(`Total Recordings,${stats.total_recordings}`);
    lines.push(`Total Recording Time,${formatDuration(stats.total_recording_time_ms)}`);
    lines.push(`Estimated API Cost,$${stats.estimated_cost.toFixed(4)}`);
    lines.push('');

    lines.push('Provider Usage');
    lines.push('Provider,Count,Percentage');
    lines.push(`OpenAI,${stats.provider_usage.openai_count},${stats.provider_usage.openai_percent.toFixed(1)}%`);
    lines.push(`Claude,${stats.provider_usage.claude_count},${stats.provider_usage.claude_percent.toFixed(1)}%`);
    lines.push('');

    if (stats.top_prompts && stats.top_prompts.length > 0) {
      lines.push('Top Prompts');
      lines.push('Prompt Name,Usage Count');
      stats.top_prompts.forEach(prompt => {
        lines.push(`${prompt.name},${prompt.count}`);
      });
    }

    return lines.join('\n');
  }
</script>

<div class="stats-dashboard">
  <div class="dashboard-header">
    <h2>Usage Statistics</h2>
    <button class="export-btn" onclick={exportStats} disabled={isExporting || isLoading}>
      {#if isExporting}
        <div class="spinner-small"></div>
        Exporting...
      {:else}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"></path>
        </svg>
        Export CSV
      {/if}
    </button>
  </div>

  {#if isLoading}
    <div class="loading-container">
      <div class="spinner"></div>
      <p>Loading statistics...</p>
    </div>
  {:else if stats}
    <!-- Key Metrics Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{stats.total_sessions || 0}</div>
        <div class="stat-label">Total Sessions</div>
        <div class="stat-sublabel">
          <span class="highlight">{stats.sessions_this_week || 0}</span> this week,
          <span class="highlight">{stats.sessions_this_month || 0}</span> this month
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-value">{stats.total_messages || 0}</div>
        <div class="stat-label">Messages Sent</div>
        <div class="stat-sublabel">User messages to AI</div>
      </div>

      <div class="stat-card">
        <div class="stat-value">{stats.total_recordings || 0}</div>
        <div class="stat-label">Voice Recordings</div>
        <div class="stat-sublabel">{formatDuration(stats.total_recording_time_ms)}</div>
      </div>

      <div class="stat-card cost-card">
        <div class="stat-value">${stats.estimated_cost?.toFixed(4) || '0.0000'}</div>
        <div class="stat-label">Estimated API Cost</div>
        <div class="stat-sublabel">Based on average usage</div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-container">
      <!-- Provider Usage Chart -->
      <div class="chart-card">
        <h3>Provider Usage</h3>
        <div class="provider-breakdown">
          <div class="provider-item">
            <div class="provider-header">
              <span class="provider-name">OpenAI GPT-4</span>
              <span class="provider-count">{stats.provider_usage.openai_count} calls</span>
            </div>
            <div class="provider-bar-container">
              <div
                class="provider-bar openai"
                style="width: {stats.provider_usage.openai_percent || 0}%"
              >
                <span class="bar-label">{stats.provider_usage.openai_percent?.toFixed(1) || 0}%</span>
              </div>
            </div>
          </div>

          <div class="provider-item">
            <div class="provider-header">
              <span class="provider-name">Claude (Anthropic)</span>
              <span class="provider-count">{stats.provider_usage.claude_count} calls</span>
            </div>
            <div class="provider-bar-container">
              <div
                class="provider-bar claude"
                style="width: {stats.provider_usage.claude_percent || 0}%"
              >
                <span class="bar-label">{stats.provider_usage.claude_percent?.toFixed(1) || 0}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Prompts -->
      <div class="chart-card">
        <h3>Most Used Prompts</h3>
        {#if stats.top_prompts && stats.top_prompts.length > 0}
          <ul class="prompt-list">
            {#each stats.top_prompts as prompt, index}
              <li class="prompt-item">
                <span class="prompt-rank">#{index + 1}</span>
                <span class="prompt-name">{prompt.name}</span>
                <span class="prompt-count">{prompt.count} uses</span>
              </li>
            {/each}
          </ul>
        {:else}
          <div class="empty-state">
            <p>No prompt usage data yet</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Insights Section -->
    <div class="insights-card">
      <h3>Insights</h3>
      <ul class="insights-list">
        {#if stats.total_sessions > 0}
          <li>
            You've created an average of <strong>{(stats.total_messages / stats.total_sessions).toFixed(1)}</strong> messages per session
          </li>
        {/if}
        {#if stats.total_recordings > 0}
          <li>
            Average recording length: <strong>{formatDuration(stats.total_recording_time_ms / stats.total_recordings)}</strong>
          </li>
        {/if}
        {#if stats.provider_usage.openai_count > stats.provider_usage.claude_count}
          <li>
            You prefer <strong>OpenAI</strong> ({stats.provider_usage.openai_percent.toFixed(0)}% of API calls)
          </li>
        {:else if stats.provider_usage.claude_count > stats.provider_usage.openai_count}
          <li>
            You prefer <strong>Claude</strong> ({stats.provider_usage.claude_percent.toFixed(0)}% of API calls)
          </li>
        {/if}
      </ul>
    </div>
  {:else}
    <div class="error-container">
      <p>No statistics available</p>
    </div>
  {/if}
</div>

<style>
  .stats-dashboard {
    padding: 30px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
  }

  .dashboard-header h2 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 600;
    color: #000000;
  }

  .export-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 10px 18px;
    border: none;
    border-radius: 8px;
    background: #007aff;
    color: white;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .export-btn:hover:not(:disabled) {
    background: #0056b3;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  }

  .export-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .loading-container, .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: #666666;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e0e0e0;
    border-top-color: #007aff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 20px;
  }

  .spinner-small {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }

  .stat-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  }

  .stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #007aff;
    margin-bottom: 8px;
    line-height: 1;
  }

  .cost-card .stat-value {
    color: #34c759;
  }

  .stat-label {
    font-size: 1rem;
    font-weight: 600;
    color: #333333;
    margin-bottom: 4px;
  }

  .stat-sublabel {
    font-size: 0.875rem;
    color: #666666;
  }

  .stat-sublabel .highlight {
    font-weight: 600;
    color: #007aff;
  }

  .charts-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }

  .chart-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .chart-card h3 {
    margin: 0 0 20px 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #000000;
  }

  .provider-breakdown {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .provider-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .provider-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .provider-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #333333;
  }

  .provider-count {
    font-size: 0.875rem;
    color: #666666;
  }

  .provider-bar-container {
    width: 100%;
    height: 32px;
    background: #f5f5f5;
    border-radius: 6px;
    overflow: hidden;
    position: relative;
  }

  .provider-bar {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 0 12px;
    transition: width 0.6s ease;
    position: relative;
  }

  .provider-bar.openai {
    background: linear-gradient(90deg, #007aff 0%, #0056b3 100%);
  }

  .provider-bar.claude {
    background: linear-gradient(90deg, #ff6b6b 0%, #c92a2a 100%);
  }

  .bar-label {
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .prompt-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .prompt-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-bottom: 1px solid #e8e8e8;
    transition: background 0.2s ease;
  }

  .prompt-item:last-child {
    border-bottom: none;
  }

  .prompt-item:hover {
    background: #f9f9f9;
  }

  .prompt-rank {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: #007aff;
    color: white;
    border-radius: 50%;
    font-size: 0.875rem;
    font-weight: 600;
    flex-shrink: 0;
  }

  .prompt-name {
    flex: 1;
    font-size: 0.95rem;
    color: #333333;
    font-weight: 500;
  }

  .prompt-count {
    font-size: 0.875rem;
    color: #666666;
    font-weight: 600;
  }

  .insights-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 24px;
    border-radius: 12px;
    color: white;
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  }

  .insights-card h3 {
    margin: 0 0 16px 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .insights-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .insights-list li {
    padding: 8px 0;
    font-size: 0.95rem;
    line-height: 1.6;
  }

  .insights-list li::before {
    content: '💡';
    margin-right: 8px;
  }

  .insights-list strong {
    font-weight: 600;
    text-decoration: underline;
    text-decoration-color: rgba(255, 255, 255, 0.4);
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: #999999;
  }

  .empty-state p {
    margin: 0;
    font-size: 0.95rem;
  }
</style>
