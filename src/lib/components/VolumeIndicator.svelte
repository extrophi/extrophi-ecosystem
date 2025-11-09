<script>
  let { level = 0, visible = false } = $props();

  // Normalize level to percentage (0-100)
  const percentage = $derived(Math.min(100, Math.max(0, level * 100)));

  // Color based on volume level
  const barColor = $derived(
    percentage > 80 ? '#f44336' :
    percentage > 50 ? '#ff9800' :
    '#4caf50'
  );
</script>

{#if visible}
  <div class="volume-indicator">
    <div class="volume-label">Volume</div>
    <div class="volume-bar-container">
      <div
        class="volume-bar"
        style="width: {percentage}%; background-color: {barColor};"
      ></div>
    </div>
    <div class="volume-value">{Math.round(percentage)}%</div>
  </div>
{/if}

<style>
  .volume-indicator {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: #2a2a2a;
    border-radius: 8px;
    min-width: 250px;
  }

  .volume-label {
    font-size: 0.85rem;
    color: #888;
    font-weight: 500;
  }

  .volume-bar-container {
    flex: 1;
    height: 8px;
    background: #1a1a1a;
    border-radius: 4px;
    overflow: hidden;
  }

  .volume-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.1s ease-out, background-color 0.3s;
  }

  .volume-value {
    font-size: 0.85rem;
    color: #aaa;
    min-width: 40px;
    text-align: right;
    font-weight: 600;
  }
</style>
