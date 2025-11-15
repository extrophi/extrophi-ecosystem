<script>
  import { scanText } from '../lib/privacy_scanner';

  export let text = '';
  export let visible = $state(false);

  $: matches = scanText(text);
  $: dangerMatches = matches.filter(m => m.severity === 'danger');
  $: cautionMatches = matches.filter(m => m.severity === 'caution');
</script>

<aside class="privacy-panel" class:visible>
  <div class="panel-header">
    <h3>Privacy Scan</h3>
    <button class="close-btn" onclick={() => visible = false}>×</button>
  </div>

  <div class="panel-content">
    {#if dangerMatches.length > 0}
      <div class="danger-section">
        <h4 class="section-title danger-title">Danger</h4>
        <div class="match-list">
          {#each dangerMatches as match}
            <div class="match-item danger-item">
              <div class="match-type">{match.type}</div>
              <div class="match-value">{match.value}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if cautionMatches.length > 0}
      <div class="caution-section">
        <h4 class="section-title caution-title">Caution</h4>
        <div class="match-list">
          {#each cautionMatches as match}
            <div class="match-item caution-item">
              <div class="match-type">{match.type}</div>
              <div class="match-value">{match.value}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if matches.length === 0}
      <div class="no-matches">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <p>No privacy issues detected</p>
      </div>
    {/if}

    <div class="disclaimer">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <span>This is non-blocking. You can proceed anyway.</span>
    </div>
  </div>
</aside>

<style>
  .privacy-panel {
    position: fixed;
    right: -320px;
    top: 0;
    width: 320px;
    height: 100vh;
    background: #ffffff;
    border-left: 1px solid #e0e0e0;
    transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    z-index: 100;
    display: flex;
    flex-direction: column;
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
  }

  .privacy-panel.visible {
    right: 0;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
    flex-shrink: 0;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #000000;
  }

  .close-btn {
    background: transparent;
    border: none;
    font-size: 2rem;
    line-height: 1;
    color: #666666;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s ease;
  }

  .close-btn:hover {
    background: #e0e0e0;
    color: #000000;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  .danger-section,
  .caution-section {
    margin-bottom: 24px;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 12px 0;
  }

  .danger-title::before {
    content: '🔴';
    font-size: 1rem;
  }

  .caution-title::before {
    content: '🟡';
    font-size: 1rem;
  }

  .danger-title {
    color: #dc3545;
  }

  .caution-title {
    color: #ffc107;
  }

  .match-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .match-item {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid;
  }

  .danger-item {
    background: #fff5f5;
    border-color: #f8d7da;
  }

  .caution-item {
    background: #fffbf0;
    border-color: #ffeeba;
  }

  .match-type {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
    color: #666666;
  }

  .match-value {
    font-size: 0.875rem;
    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
    color: #333333;
    word-break: break-all;
  }

  .no-matches {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    text-align: center;
    color: #34c759;
  }

  .no-matches svg {
    margin-bottom: 16px;
  }

  .no-matches p {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 500;
    color: #666666;
  }

  .disclaimer {
    margin-top: 24px;
    padding: 16px;
    background: #f0f8ff;
    border: 1px solid #d0e7ff;
    border-radius: 8px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 0.85rem;
    color: #333333;
    line-height: 1.5;
  }

  .disclaimer svg {
    flex-shrink: 0;
    margin-top: 2px;
    color: #007aff;
  }

  .disclaimer span {
    flex: 1;
  }

  /* Scrollbar styling */
  .panel-content::-webkit-scrollbar {
    width: 8px;
  }

  .panel-content::-webkit-scrollbar-track {
    background: #f5f5f5;
  }

  .panel-content::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 4px;
  }

  .panel-content::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }
</style>
