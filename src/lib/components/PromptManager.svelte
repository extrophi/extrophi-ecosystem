<script>
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from 'svelte';

  let prompts = $state([]);
  let selectedPrompt = $state(null);
  let isEditing = $state(false);
  let isCreating = $state(false);
  let isLoading = $state(false);
  let error = $state('');

  let editForm = $state({
    title: '',
    content: ''
  });

  onMount(async () => {
    await loadPrompts();
  });

  async function loadPrompts() {
    isLoading = true;
    error = '';

    try {
      prompts = await invoke('list_user_prompts');
      console.log('Loaded prompts:', prompts);
    } catch (e) {
      error = `Failed to load prompts: ${e}`;
      console.error('Failed to load prompts:', e);
    } finally {
      isLoading = false;
    }
  }

  function startCreate() {
    isCreating = true;
    isEditing = false;
    selectedPrompt = null;
    editForm = { title: '', content: '' };
  }

  async function createPrompt() {
    if (!editForm.title || !editForm.content) {
      error = 'Title and content are required';
      return;
    }

    error = '';
    isLoading = true;

    try {
      // Generate name from title
      const name = editForm.title.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');

      await invoke('create_user_prompt', {
        name,
        title: editForm.title,
        content: editForm.content
      });

      isCreating = false;
      await loadPrompts();
    } catch (e) {
      error = `Failed to create prompt: ${e}`;
      console.error('Failed to create prompt:', e);
    } finally {
      isLoading = false;
    }
  }

  function startEdit(prompt) {
    if (prompt.is_system) {
      error = 'Cannot edit system prompts';
      return;
    }

    selectedPrompt = prompt;
    isEditing = true;
    isCreating = false;
    editForm = {
      title: prompt.title,
      content: prompt.content
    };
    error = '';
  }

  async function updatePrompt() {
    if (!editForm.title || !editForm.content) {
      error = 'Title and content are required';
      return;
    }

    error = '';
    isLoading = true;

    try {
      await invoke('update_user_prompt', {
        id: selectedPrompt.id,
        title: editForm.title,
        content: editForm.content
      });

      isEditing = false;
      selectedPrompt = null;
      await loadPrompts();
    } catch (e) {
      error = `Failed to update prompt: ${e}`;
      console.error('Failed to update prompt:', e);
    } finally {
      isLoading = false;
    }
  }

  async function deletePrompt(prompt) {
    if (prompt.is_system) {
      error = 'Cannot delete system prompts';
      return;
    }

    if (!confirm(`Delete prompt "${prompt.title}"?`)) {
      return;
    }

    error = '';
    isLoading = true;

    try {
      await invoke('delete_user_prompt', { id: prompt.id });
      await loadPrompts();
    } catch (e) {
      error = `Failed to delete prompt: ${e}`;
      console.error('Failed to delete prompt:', e);
    } finally {
      isLoading = false;
    }
  }

  function cancel() {
    isEditing = false;
    isCreating = false;
    selectedPrompt = null;
    error = '';
  }
</script>

<div class="prompt-manager">
  <div class="header">
    <h2>Prompt Templates</h2>
    <button onclick={startCreate} class="btn-primary" disabled={isLoading}>
      + New Prompt
    </button>
  </div>

  {#if error}
    <div class="error-banner">
      {error}
    </div>
  {/if}

  {#if isCreating || isEditing}
    <div class="editor">
      <h3>{isCreating ? 'Create' : 'Edit'} Prompt</h3>

      <label>
        <span class="label-text">Title</span>
        <input
          type="text"
          bind:value={editForm.title}
          placeholder="e.g., Daily Reflection"
          disabled={isLoading}
        />
      </label>

      <label>
        <span class="label-text">Content (Markdown)</span>
        <textarea
          bind:value={editForm.content}
          rows="20"
          placeholder="Enter your prompt template in markdown format..."
          disabled={isLoading}
        ></textarea>
      </label>

      <div class="actions">
        <button
          onclick={isCreating ? createPrompt : updatePrompt}
          class="btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : (isCreating ? 'Create' : 'Save')}
        </button>
        <button onclick={cancel} class="btn-secondary" disabled={isLoading}>
          Cancel
        </button>
      </div>
    </div>
  {:else}
    <div class="prompt-list">
      {#if isLoading && prompts.length === 0}
        <div class="loading">Loading prompts...</div>
      {:else if prompts.length === 0}
        <div class="empty-state">
          <p>No prompts yet</p>
          <p class="hint">Click "New Prompt" to create your first custom prompt</p>
        </div>
      {:else}
        {#each prompts as prompt}
          <div class="prompt-card" class:system={prompt.is_system}>
            <div class="prompt-header">
              <h4>{prompt.title}</h4>
              {#if prompt.is_system}
                <span class="badge">System</span>
              {/if}
            </div>

            <div class="prompt-meta">
              <span class="meta-item">ID: {prompt.name}</span>
              <span class="meta-item">
                {new Date(prompt.created_at).toLocaleDateString()}
              </span>
            </div>

            <div class="prompt-preview">
              {prompt.content.substring(0, 200)}{prompt.content.length > 200 ? '...' : ''}
            </div>

            <div class="prompt-actions">
              <button
                onclick={() => startEdit(prompt)}
                disabled={prompt.is_system || isLoading}
                class="btn-edit"
              >
                Edit
              </button>
              <button
                onclick={() => deletePrompt(prompt)}
                disabled={prompt.is_system || isLoading}
                class="btn-delete"
              >
                Delete
              </button>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  {/if}
</div>

<style>
  .prompt-manager {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .header h2 {
    font-size: 1.75rem;
    font-weight: 600;
    color: #000000;
    margin: 0;
  }

  .btn-primary {
    background: #007aff;
    color: #ffffff;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0056b3;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  }

  .btn-primary:disabled {
    background: #cccccc;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .btn-secondary {
    background: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #f5f5f5;
    border-color: #007aff;
  }

  .btn-secondary:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .error-banner {
    background: #fff0f0;
    border: 1px solid #ff3b30;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    color: #c41e3a;
    font-size: 0.95rem;
  }

  .prompt-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .prompt-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 1.5rem;
    background: #ffffff;
    transition: all 0.2s ease;
  }

  .prompt-card:hover {
    border-color: #007aff;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  }

  .prompt-card.system {
    background: #f9f9f9;
    border-color: #d0d0d0;
  }

  .prompt-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .prompt-header h4 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #000000;
    margin: 0;
    flex: 1;
  }

  .badge {
    display: inline-block;
    background: #34c759;
    color: #ffffff;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.25rem 0.6rem;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .prompt-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.75rem;
    font-size: 0.8rem;
    color: #666666;
  }

  .meta-item {
    display: flex;
    align-items: center;
  }

  .prompt-preview {
    font-size: 0.9rem;
    color: #555555;
    line-height: 1.6;
    margin-bottom: 1rem;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .prompt-actions {
    display: flex;
    gap: 0.75rem;
  }

  .btn-edit,
  .btn-delete {
    flex: 1;
    padding: 0.625rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-edit {
    background: #ffffff;
    color: #007aff;
    border: 1px solid #007aff;
  }

  .btn-edit:hover:not(:disabled) {
    background: #007aff;
    color: #ffffff;
  }

  .btn-edit:disabled {
    background: #f5f5f5;
    color: #cccccc;
    border-color: #cccccc;
    cursor: not-allowed;
  }

  .btn-delete {
    background: #ffffff;
    color: #ff3b30;
    border: 1px solid #ff3b30;
  }

  .btn-delete:hover:not(:disabled) {
    background: #ff3b30;
    color: #ffffff;
  }

  .btn-delete:disabled {
    background: #f5f5f5;
    color: #cccccc;
    border-color: #cccccc;
    cursor: not-allowed;
  }

  .editor {
    max-width: 800px;
    margin: 0 auto;
  }

  .editor h3 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #000000;
    margin-bottom: 1.5rem;
  }

  .editor label {
    display: block;
    margin-bottom: 1.5rem;
  }

  .label-text {
    display: block;
    font-size: 0.95rem;
    font-weight: 600;
    color: #333333;
    margin-bottom: 0.5rem;
  }

  .editor input,
  .editor textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    font-size: 0.95rem;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    background: #ffffff;
    color: #000000;
    outline: none;
    transition: border-color 0.2s ease;
  }

  .editor textarea {
    font-family: 'SF Mono', Monaco, 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    resize: vertical;
  }

  .editor input:focus,
  .editor textarea:focus {
    border-color: #007aff;
  }

  .editor input:disabled,
  .editor textarea:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }

  .actions {
    display: flex;
    gap: 1rem;
  }

  .loading,
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #999999;
  }

  .empty-state p {
    margin: 0.5rem 0;
    font-size: 1rem;
  }

  .empty-state .hint {
    font-size: 0.9rem;
    color: #bbbbbb;
  }

  @media (max-width: 768px) {
    .prompt-list {
      grid-template-columns: 1fr;
    }

    .prompt-manager {
      padding: 1rem;
    }
  }
</style>
