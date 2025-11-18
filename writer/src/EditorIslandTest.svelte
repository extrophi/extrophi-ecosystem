<script lang="ts">
  /**
   * Minimal test to verify EditorIsland compiles and works
   */
  import EditorIsland from './islands/EditorIsland.svelte';

  let sessionId = $state('1');
  let initialContent = $state('# Test Editor\n\nThis is a test of the EditorIsland with vim mode.');
  let enableVim = $state(true);

  function handleSave(content: string) {
    console.log('Content saved:', content);
  }
</script>

<div class="test-container">
  <h1>EditorIsland Test</h1>
  <div class="editor-wrapper">
    <EditorIsland
      {sessionId}
      {initialContent}
      {enableVim}
      onSave={handleSave}
    />
  </div>
</div>

<style>
  .test-container {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .editor-wrapper {
    height: 600px;
    margin-top: 20px;
  }
</style>
