<script>
  let { transcript = '' } = $props();
</script>

<section class="transcript-section">
  <h2>Current Transcript</h2>
  <div class="transcript-box">
    {#if transcript}
      <p class="transcript-text">{transcript}</p>
    {:else}
      <p class="empty-state">Click "Start Recording" to begin...</p>
    {/if}
  </div>
</section>

<style>
  .transcript-section {
    margin-bottom: 2rem;
  }

  h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #fff;
  }

  .transcript-box {
    background: #2a2a2a;
    padding: 2rem;
    border-radius: 12px;
    min-height: 200px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    border: 1px solid #3a3a3a;
  }

  .transcript-text {
    color: #e0e0e0;
    line-height: 1.8;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 1rem;
  }

  .empty-state {
    color: #666;
    text-align: center;
    padding: 3rem 0;
    font-style: italic;
  }
</style>
