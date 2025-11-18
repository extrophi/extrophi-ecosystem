<script>
  let { items = [] } = $props();
</script>

<section class="history-section">
  <h2>Recent Transcripts</h2>
  <div class="history-list">
    {#if items.length > 0}
      {#each items as [filename, text]}
        <div class="history-item">
          <div class="history-filename">{filename}</div>
          <div class="history-preview">
            {text.substring(0, 150)}{text.length > 150 ? '...' : ''}
          </div>
        </div>
      {/each}
    {:else}
      <p class="empty-state">No transcripts yet</p>
    {/if}
  </div>
</section>

<style>
  .history-section {
    margin-bottom: 2rem;
  }

  h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #fff;
  }

  .history-list {
    background: #2a2a2a;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    border: 1px solid #3a3a3a;
  }

  .history-item {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #3a3a3a;
    transition: background 0.2s;
  }

  .history-item:last-child {
    border-bottom: none;
  }

  .history-item:hover {
    background: #333;
  }

  .history-filename {
    color: #667eea;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .history-preview {
    color: #aaa;
    line-height: 1.6;
    font-size: 0.95rem;
  }

  .empty-state {
    color: #666;
    text-align: center;
    padding: 3rem 0;
    font-style: italic;
  }
</style>
