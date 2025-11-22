<script>
  import { invoke } from '@tauri-apps/api/core';

  // Component props using Svelte 5 runes
  let { onInsert = null } = $props();

  // State
  let searchQuery = $state('');
  let results = $state([]);
  let loading = $state(false);
  let error = $state('');
  let connectionStatus = $state('unknown');
  let debounceTimer = $state(null);

  // Statistics
  let stats = $state({
    totalResults: 0,
    platforms: {}
  });

  // Test connection on mount
  $effect(() => {
    testConnection();
    loadStats();
  });

  async function testConnection() {
    try {
      const isConnected = await invoke('test_research_db_connection');
      connectionStatus = isConnected ? 'connected' : 'disconnected';
    } catch (e) {
      connectionStatus = 'error';
      console.error('Research DB connection test failed:', e);
    }
  }

  async function loadStats() {
    try {
      const dbStats = await invoke('get_research_stats');
      stats = dbStats;
    } catch (e) {
      console.error('Failed to load research stats:', e);
    }
  }

  async function performSearch() {
    if (searchQuery.length < 3) {
      results = [];
      return;
    }

    loading = true;
    error = '';

    try {
      const searchResults = await invoke('search_knowledge', {
        query: searchQuery,
        limit: 10
      });
      results = searchResults;
    } catch (e) {
      console.error('Search failed:', e);
      error = e.toString();
      results = [];
    } finally {
      loading = false;
    }
  }

  // Debounced search effect
  $effect(() => {
    if (searchQuery.length >= 3) {
      if (debounceTimer !== null) {
        clearTimeout(debounceTimer);
      }

      debounceTimer = setTimeout(() => {
        performSearch();
      }, 300);
    } else {
      results = [];
    }
  });

  function handleInsert(result) {
    if (onInsert) {
      // Format the content for insertion
      const formattedContent = `
**${result.title || 'Research Insight'}**
Source: ${result.author} (${result.platform})

${result.text_content}

---
Concepts: ${result.concepts ? result.concepts.join(', ') : 'N/A'}
Link: ${result.url}
`;
      onInsert(formattedContent.trim());
    }
  }

  function getPlatformIcon(platform) {
    const icons = {
      'twitter': '🐦',
      'youtube': '📺',
      'reddit': '🤖',
      'web': '🌐'
    };
    return icons[platform] || '📄';
  }

  function formatDate(dateStr) {
    if (!dateStr) return 'Unknown date';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function truncateText(text, maxLength = 200) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
</script>

<div class="research-panel">
  <div class="panel-header">
    <h3>Research Knowledge Base</h3>
    <div class="connection-status" class:connected={connectionStatus === 'connected'} class:disconnected={connectionStatus !== 'connected'}>
      {#if connectionStatus === 'connected'}
        <span class="status-dot"></span> Database Connected
      {:else if connectionStatus === 'disconnected'}
        <span class="status-dot"></span> Database Offline
      {:else if connectionStatus === 'error'}
        <span class="status-dot"></span> Connection Error
      {:else}
        <span class="status-dot"></span> Checking...
      {/if}
    </div>
  </div>

  {#if connectionStatus === 'connected' && stats.totalResults > 0}
    <div class="stats-bar">
      <span class="stat-item">📊 {stats.totalResults.toLocaleString()} insights available</span>
      {#if stats.platforms}
        {#each Object.entries(stats.platforms) as [platform, count]}
          <span class="stat-item">{getPlatformIcon(platform)} {count}</span>
        {/each}
      {/if}
    </div>
  {/if}

  <div class="search-container">
    <div class="search-input-wrapper">
      <span class="search-icon">🔍</span>
      <input
        type="search"
        bind:value={searchQuery}
        placeholder="Search knowledge base (e.g., 'content pillars', 'audience building'...)"
        class="search-input"
        disabled={connectionStatus !== 'connected'}
      />
    </div>
  </div>

  {#if error}
    <div class="error-message">
      <strong>Search Error:</strong> {error}
      <button class="retry-btn" onclick={performSearch}>Retry</button>
    </div>
  {/if}

  <div class="results-container">
    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <span>Searching knowledge base...</span>
      </div>
    {:else if results.length > 0}
      <div class="results-count">
        {results.length} result{results.length === 1 ? '' : 's'} found
      </div>

      {#each results as result}
        <div class="result-card">
          <div class="result-header">
            <div class="result-meta">
              <span class="platform-badge">{getPlatformIcon(result.platform)} {result.platform}</span>
              <span class="author-name">{result.author || 'Unknown Author'}</span>
            </div>
            <span class="similarity-score" title="Relevance score">
              {Math.round((result.similarity_score || 0) * 100)}% match
            </span>
          </div>

          {#if result.title}
            <h4 class="result-title">{result.title}</h4>
          {/if}

          <p class="result-content">
            {truncateText(result.text_content)}
          </p>

          {#if result.concepts && result.concepts.length > 0}
            <div class="concepts-tags">
              {#each result.concepts.slice(0, 5) as concept}
                <span class="concept-tag">{concept}</span>
              {/each}
            </div>
          {/if}

          <div class="result-footer">
            <div class="result-info">
              <span class="result-date">{formatDate(result.published_at)}</span>
              {#if result.word_count}
                <span class="word-count">{result.word_count} words</span>
              {/if}
            </div>
            <div class="result-actions">
              {#if result.url}
                <a href={result.url} target="_blank" class="action-btn" title="Open source">
                  🔗 Source
                </a>
              {/if}
              <button class="action-btn primary" onclick={() => handleInsert(result)}>
                ✨ Insert
              </button>
            </div>
          </div>
        </div>
      {/each}
    {:else if searchQuery.length >= 3}
      <div class="empty-state">
        <span class="empty-icon">🔍</span>
        <p>No results found for "{searchQuery}"</p>
        <p class="empty-hint">Try different keywords or check your spelling</p>
      </div>
    {:else if searchQuery.length > 0}
      <div class="hint-state">
        <span class="hint-icon">💡</span>
        <p>Type at least 3 characters to search</p>
      </div>
    {:else}
      <div class="welcome-state">
        <span class="welcome-icon">🎯</span>
        <h4>Search the Knowledge Base</h4>
        <p>Access insights from Dan Koe, Naval, Alex Hormozi, and more!</p>
        <ul class="suggestions">
          <li>Try: "content creation strategies"</li>
          <li>Try: "audience building tactics"</li>
          <li>Try: "personal branding tips"</li>
        </ul>
      </div>
    {/if}
  </div>
</div>

<style>
  .research-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1.5rem;
    height: 100%;
    background: var(--bg-primary, #ffffff);
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--border-color, #e5e7eb);
  }

  .panel-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary, #1f2937);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 500;
    padding: 0.375rem 0.75rem;
    border-radius: 1rem;
    background: var(--bg-secondary, #f9fafb);
  }

  .connection-status.connected {
    color: #10b981;
    background: #d1fae5;
  }

  .connection-status.disconnected,
  .connection-status[class*="error"] {
    color: #ef4444;
    background: #fee2e2;
  }

  .status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: currentColor;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .stats-bar {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    padding: 0.75rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 0.5rem;
    color: white;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .search-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 1rem;
    font-size: 1.125rem;
    opacity: 0.5;
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 0.875rem 1rem 0.875rem 3rem;
    border: 2px solid var(--border-color, #d1d5db);
    border-radius: 0.5rem;
    font-size: 0.9375rem;
    background: white;
    color: var(--text-primary, #1f2937);
    transition: all 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .search-input:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .search-input::placeholder {
    color: #9ca3af;
  }

  .error-message {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 0.5rem;
    color: #dc2626;
    font-size: 0.875rem;
  }

  .retry-btn {
    padding: 0.375rem 0.75rem;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  .retry-btn:hover {
    background: #b91c1c;
  }

  .results-container {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: #6b7280;
  }

  .spinner {
    width: 2.5rem;
    height: 2.5rem;
    border: 3px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .results-count {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
    background: #f9fafb;
    border-radius: 0.375rem;
  }

  .result-card {
    padding: 1.25rem;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 0.75rem;
    transition: all 0.2s;
  }

  .result-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .result-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .platform-badge {
    padding: 0.25rem 0.625rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
  }

  .author-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .similarity-score {
    padding: 0.25rem 0.625rem;
    background: #dcfce7;
    color: #166534;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .result-title {
    margin: 0 0 0.625rem;
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.4;
  }

  .result-content {
    margin: 0 0 0.75rem;
    font-size: 0.875rem;
    line-height: 1.6;
    color: #4b5563;
  }

  .concepts-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin-bottom: 0.75rem;
  }

  .concept-tag {
    padding: 0.25rem 0.5rem;
    background: #eff6ff;
    color: #1e40af;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .result-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.75rem;
    border-top: 1px solid #e5e7eb;
  }

  .result-info {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .result-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    padding: 0.5rem 1rem;
    background: #f3f4f6;
    color: #374151;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s;
  }

  .action-btn:hover {
    background: #e5e7eb;
    transform: translateY(-1px);
  }

  .action-btn.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .action-btn.primary:hover {
    background: linear-gradient(135deg, #5568d3 0%, #63408b 100%);
    box-shadow: 0 4px 6px -1px rgba(102, 126, 234, 0.3);
  }

  .empty-state, .hint-state, .welcome-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 3rem 1.5rem;
    text-align: center;
  }

  .empty-icon, .hint-icon, .welcome-icon {
    font-size: 3rem;
    opacity: 0.3;
  }

  .empty-state p, .hint-state p {
    margin: 0;
    color: #6b7280;
    font-size: 0.9375rem;
  }

  .empty-hint {
    font-size: 0.8125rem;
    color: #9ca3af;
  }

  .welcome-state h4 {
    margin: 0.5rem 0 0.25rem;
    font-size: 1.125rem;
    font-weight: 700;
    color: #1f2937;
  }

  .welcome-state p {
    margin: 0;
    color: #6b7280;
    font-size: 0.9375rem;
  }

  .suggestions {
    margin: 1rem 0 0;
    padding: 0;
    list-style: none;
    text-align: left;
    width: 100%;
    max-width: 300px;
  }

  .suggestions li {
    padding: 0.5rem;
    color: #6b7280;
    font-size: 0.875rem;
    font-style: italic;
  }

  .suggestions li:before {
    content: "💡 ";
    margin-right: 0.25rem;
  }

  /* Scrollbar styling */
  .results-container::-webkit-scrollbar {
    width: 8px;
  }

  .results-container::-webkit-scrollbar-track {
    background: #f3f4f6;
    border-radius: 4px;
  }

  .results-container::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 4px;
  }

  .results-container::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }
</style>
