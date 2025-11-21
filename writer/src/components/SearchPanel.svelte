<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';

  // Types
  interface SearchResult {
    result_type: string;
    session_id: number;
    session_title: string | null;
    content: string;
    created_at: string;
    highlight: string | null;
  }

  interface Tag {
    id: number;
    name: string;
    color: string;
    created_at: string;
  }

  // State
  let searchQuery = $state('');
  let results = $state<SearchResult[]>([]);
  let loading = $state(false);
  let showFilters = $state(false);

  // Filter state
  let selectedTags = $state<number[]>([]);
  let startDate = $state('');
  let endDate = $state('');
  let availableTags = $state<Tag[]>([]);

  // Debounce timer
  let debounceTimer: number | null = null;

  // Load tags when component mounts
  $effect(() => {
    loadTags();
  });

  async function loadTags() {
    try {
      availableTags = await invoke('get_all_tags');
    } catch (e) {
      console.error('Failed to load tags:', e);
    }
  }

  async function performSearch() {
    if (searchQuery.length < 2) {
      results = [];
      return;
    }

    loading = true;
    try {
      results = await invoke('search_all', {
        query: searchQuery,
        tags: selectedTags.length > 0 ? selectedTags : null,
        startDate: startDate || null,
        endDate: endDate || null,
      });
    } catch (e) {
      console.error('Search failed:', e);
      results = [];
    } finally {
      loading = false;
    }
  }

  // Debounced search effect
  $effect(() => {
    // Trigger on search query or filter changes
    if (searchQuery || selectedTags.length > 0 || startDate || endDate) {
      if (debounceTimer !== null) {
        clearTimeout(debounceTimer);
      }

      debounceTimer = setTimeout(() => {
        performSearch();
      }, 300);
    }
  });

  function toggleTag(tagId: number) {
    if (selectedTags.includes(tagId)) {
      selectedTags = selectedTags.filter(id => id !== tagId);
    } else {
      selectedTags = [...selectedTags, tagId];
    }
  }

  function clearFilters() {
    selectedTags = [];
    startDate = '';
    endDate = '';
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function getResultIcon(type: string): string {
    switch (type) {
      case 'session':
        return '📁';
      case 'message':
        return '💬';
      case 'transcript':
        return '🎤';
      default:
        return '📄';
    }
  }

  function getResultTypeLabel(type: string): string {
    switch (type) {
      case 'session':
        return 'Session';
      case 'message':
        return 'Message';
      case 'transcript':
        return 'Transcript';
      default:
        return 'Result';
    }
  }

  function openSession(sessionId: number) {
    // Emit event to open session (can be handled by parent component)
    window.dispatchEvent(new CustomEvent('open-session', { detail: { sessionId } }));
  }
</script>

<div class="search-panel">
  <div class="search-header">
    <div class="search-input-container">
      <span class="search-icon">🔍</span>
      <input
        type="search"
        bind:value={searchQuery}
        placeholder="Search sessions, transcripts, conversations..."
        class="search-input"
      />
    </div>

    <button
      class="filter-toggle"
      class:active={showFilters}
      onclick={() => showFilters = !showFilters}
    >
      <span class="filter-icon">⚙️</span>
      Filters
      {#if selectedTags.length > 0 || startDate || endDate}
        <span class="filter-badge">{selectedTags.length + (startDate ? 1 : 0) + (endDate ? 1 : 0)}</span>
      {/if}
    </button>
  </div>

  {#if showFilters}
    <div class="filters">
      <div class="filter-section">
        <label class="filter-label">Tags</label>
        <div class="tag-filters">
          {#each availableTags as tag}
            <button
              class="tag-filter"
              class:selected={selectedTags.includes(tag.id)}
              style="--tag-color: {tag.color}"
              onclick={() => toggleTag(tag.id)}
            >
              {tag.name}
            </button>
          {/each}
        </div>
      </div>

      <div class="filter-section">
        <label class="filter-label">Date Range</label>
        <div class="date-filters">
          <input
            type="date"
            bind:value={startDate}
            placeholder="Start Date"
            class="date-input"
          />
          <span class="date-separator">→</span>
          <input
            type="date"
            bind:value={endDate}
            placeholder="End Date"
            class="date-input"
          />
        </div>
      </div>

      {#if selectedTags.length > 0 || startDate || endDate}
        <button class="clear-filters" onclick={clearFilters}>
          Clear Filters
        </button>
      {/if}
    </div>
  {/if}

  <div class="results">
    {#if loading}
      <div class="loading">
        <div class="spinner"></div>
        <span>Searching...</span>
      </div>
    {:else if results.length > 0}
      <div class="results-count">
        {results.length} result{results.length === 1 ? '' : 's'}
      </div>

      {#each results as result}
        <div class="result-item" onclick={() => openSession(result.session_id)}>
          <div class="result-header">
            <span class="result-icon">{getResultIcon(result.result_type)}</span>
            <div class="result-meta">
              <div class="result-title-row">
                <span class="result-type">{getResultTypeLabel(result.result_type)}</span>
                {#if result.session_title}
                  <span class="result-session">{result.session_title}</span>
                {/if}
              </div>
              <span class="result-date">{formatDate(result.created_at)}</span>
            </div>
          </div>

          {#if result.highlight}
            <p class="result-preview">
              {result.highlight}
            </p>
          {/if}
        </div>
      {/each}
    {:else if searchQuery.length >= 2}
      <div class="no-results">
        <span class="no-results-icon">🔍</span>
        <p>No results found for "{searchQuery}"</p>
        {#if selectedTags.length > 0 || startDate || endDate}
          <button class="try-clear-filters" onclick={clearFilters}>
            Try clearing filters
          </button>
        {/if}
      </div>
    {:else if searchQuery.length > 0}
      <div class="hint">
        <span class="hint-icon">💡</span>
        <p>Type at least 2 characters to search</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .search-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    height: 100%;
    overflow: hidden;
  }

  .search-header {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .search-input-container {
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 0.75rem;
    font-size: 1.25rem;
    opacity: 0.5;
  }

  .search-input {
    width: 100%;
    padding: 0.75rem 0.75rem 0.75rem 2.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    font-size: 1rem;
    transition: all 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .filter-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
    position: relative;
  }

  .filter-toggle:hover {
    background: #f9fafb;
    border-color: #9ca3af;
  }

  .filter-toggle.active {
    background: #eff6ff;
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .filter-icon {
    font-size: 1rem;
  }

  .filter-badge {
    position: absolute;
    top: -0.5rem;
    right: -0.5rem;
    background: #ef4444;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.125rem 0.5rem;
    border-radius: 999px;
    min-width: 1.25rem;
    text-align: center;
  }

  .filters {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
  }

  .filter-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .filter-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .tag-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag-filter {
    padding: 0.5rem 1rem;
    background: white;
    border: 2px solid var(--tag-color);
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    transition: all 0.2s;
  }

  .tag-filter:hover {
    background: var(--tag-color);
    color: white;
  }

  .tag-filter.selected {
    background: var(--tag-color);
    color: white;
  }

  .date-filters {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .date-input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }

  .date-separator {
    color: #9ca3af;
    font-weight: 600;
  }

  .clear-filters {
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #ef4444;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    color: #ef4444;
    transition: all 0.2s;
  }

  .clear-filters:hover {
    background: #ef4444;
    color: white;
  }

  .results {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: #6b7280;
  }

  .spinner {
    width: 2rem;
    height: 2rem;
    border: 3px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .results-count {
    padding: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
  }

  .result-item {
    padding: 1rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .result-item:hover {
    background: #f9fafb;
    border-color: #3b82f6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  .result-header {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .result-icon {
    font-size: 1.5rem;
  }

  .result-meta {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .result-title-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .result-type {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .result-session {
    font-size: 0.875rem;
    font-weight: 600;
    color: #111827;
  }

  .result-date {
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .result-preview {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.5;
    color: #4b5563;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .no-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    text-align: center;
  }

  .no-results-icon {
    font-size: 3rem;
    opacity: 0.3;
  }

  .no-results p {
    margin: 0;
    color: #6b7280;
    font-size: 0.875rem;
  }

  .try-clear-filters {
    padding: 0.5rem 1rem;
    background: #eff6ff;
    border: 1px solid #3b82f6;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    color: #3b82f6;
    transition: all 0.2s;
  }

  .try-clear-filters:hover {
    background: #3b82f6;
    color: white;
  }

  .hint {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: #fef3c7;
    border: 1px solid #fbbf24;
    border-radius: 0.5rem;
  }

  .hint-icon {
    font-size: 1.5rem;
  }

  .hint p {
    margin: 0;
    color: #92400e;
    font-size: 0.875rem;
    font-weight: 500;
  }
</style>
