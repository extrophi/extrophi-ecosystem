<script lang="ts">
  /**
   * Privacy Scanner Island Component
   * Svelte 5 runes implementation
   *
   * Features:
   * - 4-level privacy classification (PRIVATE, PERSONAL, BUSINESS, IDEAS)
   * - Real-time scanning with debouncing
   * - Performance monitoring (< 50ms target)
   * - Color-coded badge display
   * - Detailed match breakdown
   *
   * Integration:
   * - Works as Astro island component
   * - Persists level to SQLite via Tauri
   * - Updates in real-time as content changes
   */

  import {
    scanText,
    classifyText,
    getLevelColor,
    getLevelLabel,
    getLevelDescription,
    getMatchCountsByLevel,
    type PrivacyLevel,
    type PrivacyMatch
  } from '../lib/privacy-rules';

  // Props (Svelte 5 runes)
  let {
    content = '',
    showDetails = false,
    debounceMs = 300,
    onLevelChange = undefined
  }: {
    content?: string;
    showDetails?: boolean;
    debounceMs?: number;
    onLevelChange?: (level: PrivacyLevel) => void;
  } = $props();

  // State (Svelte 5 runes)
  let matches = $state<PrivacyMatch[]>([]);
  let level = $state<PrivacyLevel>('IDEAS');
  let scanTime = $state(0);
  let isScanning = $state(false);
  let debounceTimeout: number | undefined = $state(undefined);

  // Derived state (Svelte 5 runes)
  let matchCounts = $derived(getMatchCountsByLevel(matches));
  let levelColor = $derived(getLevelColor(level));
  let levelLabel = $derived(getLevelLabel(level));
  let levelDescription = $derived(getLevelDescription(level));
  let hasIssues = $derived(matches.length > 0);
  let isWithinPerformanceTarget = $derived(scanTime < 50);

  // Derived matches by level
  let privateMatches = $derived(matches.filter(m => m.level === 'PRIVATE'));
  let personalMatches = $derived(matches.filter(m => m.level === 'PERSONAL'));
  let businessMatches = $derived(matches.filter(m => m.level === 'BUSINESS'));

  /**
   * Perform privacy scan
   * Measures performance and updates state
   */
  function performScan(text: string): void {
    if (!text || text.trim().length === 0) {
      matches = [];
      level = 'IDEAS';
      scanTime = 0;
      return;
    }

    isScanning = true;
    const startTime = performance.now();

    // Scan and classify
    const foundMatches = scanText(text);
    const detectedLevel = classifyText(text);

    const endTime = performance.now();
    const duration = endTime - startTime;

    // Update state
    matches = foundMatches;
    level = detectedLevel;
    scanTime = duration;
    isScanning = false;

    // Callback if provided
    if (onLevelChange && level !== detectedLevel) {
      onLevelChange(detectedLevel);
    }
  }

  /**
   * Debounced scan function
   * Prevents excessive scanning during typing
   */
  function debouncedScan(text: string): void {
    // Clear existing timeout
    if (debounceTimeout !== undefined) {
      clearTimeout(debounceTimeout);
    }

    // Set new timeout
    debounceTimeout = window.setTimeout(() => {
      performScan(text);
    }, debounceMs);
  }

  /**
   * Effect: Scan content when it changes
   * Uses Svelte 5 $effect rune
   */
  $effect(() => {
    debouncedScan(content);
  });

  /**
   * Get badge emoji for privacy level
   */
  function getLevelEmoji(lvl: PrivacyLevel): string {
    const emojis: Record<PrivacyLevel, string> = {
      PRIVATE: '🔴',
      PERSONAL: '🟠',
      BUSINESS: '🟡',
      IDEAS: '🟢'
    };
    return emojis[lvl];
  }
</script>

<div class="privacy-scanner-island">
  <!-- Privacy Badge -->
  <div
    class="privacy-badge"
    style:background-color={levelColor}
    title={levelDescription}
  >
    <span class="badge-emoji">{getLevelEmoji(level)}</span>
    <span class="badge-label">{levelLabel}</span>
    {#if hasIssues}
      <span class="badge-count">{matches.length}</span>
    {/if}
  </div>

  <!-- Performance Indicator -->
  {#if scanTime > 0}
    <div
      class="performance-indicator"
      class:warning={!isWithinPerformanceTarget}
      title={`Scan time: ${scanTime.toFixed(2)}ms`}
    >
      <span class="perf-time">{scanTime.toFixed(0)}ms</span>
      {#if !isWithinPerformanceTarget}
        <span class="perf-warning">⚠️</span>
      {/if}
    </div>
  {/if}

  <!-- Detailed Match Breakdown -->
  {#if showDetails && hasIssues}
    <div class="match-details">
      <div class="details-header">
        <h4>Privacy Issues Detected</h4>
        <p class="details-description">{levelDescription}</p>
      </div>

      <!-- PRIVATE Matches -->
      {#if privateMatches.length > 0}
        <div class="match-section private">
          <div class="section-header">
            <span class="section-emoji">🔴</span>
            <h5>Private ({matchCounts.PRIVATE})</h5>
          </div>
          <div class="match-list">
            {#each privateMatches as match}
              <div class="match-item">
                <div class="match-type">{match.type}</div>
                <div class="match-value">{match.value}</div>
                <div class="match-description">{match.description}</div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- PERSONAL Matches -->
      {#if personalMatches.length > 0}
        <div class="match-section personal">
          <div class="section-header">
            <span class="section-emoji">🟠</span>
            <h5>Personal ({matchCounts.PERSONAL})</h5>
          </div>
          <div class="match-list">
            {#each personalMatches as match}
              <div class="match-item">
                <div class="match-type">{match.type}</div>
                <div class="match-value">{match.value}</div>
                <div class="match-description">{match.description}</div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- BUSINESS Matches -->
      {#if businessMatches.length > 0}
        <div class="match-section business">
          <div class="section-header">
            <span class="section-emoji">🟡</span>
            <h5>Business ({matchCounts.BUSINESS})</h5>
          </div>
          <div class="match-list">
            {#each businessMatches as match}
              <div class="match-item">
                <div class="match-type">{match.type}</div>
                <div class="match-value">{match.value}</div>
                <div class="match-description">{match.description}</div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Stats Summary -->
      <div class="stats-summary">
        <div class="stat">
          <span class="stat-label">Total Issues</span>
          <span class="stat-value">{matches.length}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Scan Time</span>
          <span class="stat-value">{scanTime.toFixed(2)}ms</span>
        </div>
        <div class="stat">
          <span class="stat-label">Performance</span>
          <span class="stat-value" class:good={isWithinPerformanceTarget}>
            {isWithinPerformanceTarget ? '✅ Good' : '⚠️ Slow'}
          </span>
        </div>
      </div>
    </div>
  {/if}

  <!-- No Issues Message -->
  {#if showDetails && !hasIssues && content.trim().length > 0}
    <div class="no-issues">
      <span class="no-issues-emoji">✅</span>
      <p>No privacy issues detected. Content is safe to publish.</p>
    </div>
  {/if}
</div>

<style>
  .privacy-scanner-island {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  /* Privacy Badge */
  .privacy-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    color: #ffffff;
    font-weight: 600;
    font-size: 0.875rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    cursor: default;
    user-select: none;
    width: fit-content;
  }

  .badge-emoji {
    font-size: 1rem;
  }

  .badge-label {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .badge-count {
    background: rgba(255, 255, 255, 0.3);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
  }

  /* Performance Indicator */
  .performance-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: #e8f5e9;
    border-radius: 12px;
    font-size: 0.75rem;
    color: #2e7d32;
    font-weight: 600;
    width: fit-content;
  }

  .performance-indicator.warning {
    background: #fff3e0;
    color: #e65100;
  }

  .perf-time {
    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  }

  .perf-warning {
    font-size: 0.875rem;
  }

  /* Match Details */
  .match-details {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
    background: #f9f9f9;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
  }

  .details-header {
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 12px;
  }

  .details-header h4 {
    margin: 0 0 8px 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: #333333;
  }

  .details-description {
    margin: 0;
    font-size: 0.875rem;
    color: #666666;
    line-height: 1.5;
  }

  /* Match Sections */
  .match-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid;
  }

  .match-section.private {
    background: #fff5f5;
    border-color: #ffcdd2;
  }

  .match-section.personal {
    background: #fff8f0;
    border-color: #ffcc80;
  }

  .match-section.business {
    background: #fffbf0;
    border-color: #fff59d;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-emoji {
    font-size: 1.125rem;
  }

  .section-header h5 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #333333;
  }

  /* Match Items */
  .match-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .match-item {
    padding: 10px;
    background: #ffffff;
    border-radius: 4px;
    border: 1px solid #e0e0e0;
  }

  .match-type {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666666;
    margin-bottom: 4px;
  }

  .match-value {
    font-size: 0.875rem;
    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
    color: #333333;
    word-break: break-all;
    margin-bottom: 4px;
    padding: 4px 8px;
    background: #f5f5f5;
    border-radius: 3px;
  }

  .match-description {
    font-size: 0.75rem;
    color: #999999;
    font-style: italic;
  }

  /* Stats Summary */
  .stats-summary {
    display: flex;
    gap: 16px;
    padding: 12px;
    background: #ffffff;
    border-radius: 6px;
    border: 1px solid #e0e0e0;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
  }

  .stat-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #999999;
  }

  .stat-value {
    font-size: 1rem;
    font-weight: 700;
    color: #333333;
  }

  .stat-value.good {
    color: #2e7d32;
  }

  /* No Issues */
  .no-issues {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px;
    background: #e8f5e9;
    border-radius: 6px;
    text-align: center;
  }

  .no-issues-emoji {
    font-size: 3rem;
    margin-bottom: 12px;
  }

  .no-issues p {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 500;
    color: #2e7d32;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .privacy-scanner-island {
      padding: 8px;
    }

    .stats-summary {
      flex-direction: column;
      gap: 12px;
    }

    .badge-label {
      display: none;
    }
  }
</style>
