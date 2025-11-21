<script lang="ts">
  let { audioLevel = 0, isPeaking = false } = $props();

  // Compute peaking state based on audio level
  $effect(() => {
    isPeaking = audioLevel > 90;
  });

  // Format audio level for display (convert 0-1 range to percentage)
  let levelPercentage = $derived(Math.min(100, Math.max(0, audioLevel * 100)));
</script>

<div class="audio-meter">
  <div class="meter-label">Input Level</div>
  <div class="meter-bar">
    <div
      class="meter-fill"
      class:peaking={isPeaking}
      style="width: {levelPercentage}%"
    ></div>
    <div class="meter-markers">
      <div class="marker" style="left: 25%"></div>
      <div class="marker" style="left: 50%"></div>
      <div class="marker" style="left: 75%"></div>
      <div class="marker" style="left: 90%"></div>
    </div>
  </div>
  <div class="meter-indicators">
    <span>-40</span>
    <span>-20</span>
    <span>-10</span>
    <span class="peak">0</span>
  </div>
  {#if isPeaking}
    <div class="peak-warning">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
      </svg>
      Audio level too high!
    </div>
  {/if}
</div>

<style>
  .audio-meter {
    padding: 1rem;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 0.5rem;
    border: 1px solid #e0e0e0;
  }

  .meter-label {
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-secondary, #666666);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .meter-bar {
    height: 24px;
    background: #1F2937;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
  }

  .meter-fill {
    height: 100%;
    background: linear-gradient(to right,
      #10B981 0%,
      #10B981 60%,
      #F59E0B 75%,
      #EF4444 90%,
      #EF4444 100%
    );
    transition: width 0.1s ease-out;
    position: relative;
    z-index: 1;
  }

  .meter-fill.peaking {
    animation: pulse 0.5s infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }

  .meter-markers {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  .marker {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: rgba(255, 255, 255, 0.3);
  }

  .meter-indicators {
    display: flex;
    justify-content: space-between;
    margin-top: 0.25rem;
    font-size: 0.7rem;
    color: var(--text-tertiary, #999999);
    font-family: monospace;
  }

  .peak {
    color: #EF4444;
    font-weight: 600;
  }

  .peak-warning {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.75rem;
    padding: 0.5rem 0.75rem;
    background: #FEF3C7;
    border: 1px solid #F59E0B;
    border-radius: 0.375rem;
    color: #92400E;
    font-size: 0.8rem;
    font-weight: 600;
    animation: slideDown 0.2s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .peak-warning svg {
    flex-shrink: 0;
    color: #F59E0B;
  }
</style>
