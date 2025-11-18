<script>
  import { invoke } from '@tauri-apps/api/core';
  import { showError, showSuccess } from '../utils/toast.js';
  import TagBadge from './TagBadge.svelte';

  /**
   * TagManager Component - Modal for managing all tags
   *
   * Props:
   * - isOpen: boolean - Controls modal visibility
   * - onClose: callback when modal is closed
   * - onTagsChanged: callback when tags are modified
   */

  let { isOpen = $bindable(false), onClose, onTagsChanged } = $props();

  let tagUsages = $state([]);
  let editingTagId = $state(null);
  let editName = $state('');
  let editColor = $state('');
  let mergeMode = $state(false);
  let mergeSourceId = $state(null);
  let mergeTargetId = $state(null);

  // Color palette for editing
  const colorPalette = [
    '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B',
    '#EC4899', '#EF4444', '#14B8A6', '#6366F1',
  ];

  // Load tag usage data whenever modal opens
  $effect(() => {
    if (isOpen) {
      loadTagUsages();
    }
  });

  async function loadTagUsages() {
    try {
      tagUsages = await invoke('get_tag_usage_counts');
    } catch (e) {
      showError(`Failed to load tags: ${e}`);
    }
  }

  function startEdit(tag) {
    editingTagId = tag.id;
    editName = tag.name;
    editColor = tag.color;
  }

  function cancelEdit() {
    editingTagId = null;
    editName = '';
    editColor = '';
  }

  async function saveEdit(tagId) {
    if (!editName.trim()) {
      showError('Tag name cannot be empty');
      return;
    }

    try {
      await invoke('rename_tag', {
        tagId,
        newName: editName.trim()
      });

      if (editColor) {
        await invoke('update_tag_color', {
          tagId,
          color: editColor
        });
      }

      showSuccess('Tag updated');
      await loadTagUsages();

      if (onTagsChanged) {
        onTagsChanged();
      }

      cancelEdit();
    } catch (e) {
      showError(`Failed to update tag: ${e}`);
    }
  }

  async function deleteTag(tag, usageCount) {
    const message = usageCount > 0
      ? `Delete tag "${tag.name}"?\n\nThis tag is used in ${usageCount} session(s).`
      : `Delete tag "${tag.name}"?`;

    if (!confirm(message)) {
      return;
    }

    try {
      await invoke('delete_tag', { tagId: tag.id });
      showSuccess('Tag deleted');
      await loadTagUsages();

      if (onTagsChanged) {
        onTagsChanged();
      }
    } catch (e) {
      showError(`Failed to delete tag: ${e}`);
    }
  }

  function startMerge(tag) {
    mergeMode = true;
    mergeSourceId = tag.id;
    mergeTargetId = null;
  }

  function cancelMerge() {
    mergeMode = false;
    mergeSourceId = null;
    mergeTargetId = null;
  }

  async function executeMerge() {
    if (!mergeSourceId || !mergeTargetId) {
      showError('Please select both source and target tags');
      return;
    }

    const sourceTag = tagUsages.find(t => t.tag.id === mergeSourceId)?.tag;
    const targetTag = tagUsages.find(t => t.tag.id === mergeTargetId)?.tag;

    if (!confirm(`Merge "${sourceTag.name}" into "${targetTag.name}"?\n\nAll sessions tagged with "${sourceTag.name}" will be tagged with "${targetTag.name}" instead, and "${sourceTag.name}" will be deleted.`)) {
      return;
    }

    try {
      await invoke('merge_tags', {
        sourceTagId: mergeSourceId,
        targetTagId: mergeTargetId
      });

      showSuccess('Tags merged successfully');
      await loadTagUsages();

      if (onTagsChanged) {
        onTagsChanged();
      }

      cancelMerge();
    } catch (e) {
      showError(`Failed to merge tags: ${e}`);
    }
  }

  function handleClose() {
    cancelEdit();
    cancelMerge();
    if (onClose) {
      onClose();
    }
    isOpen = false;
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }
</script>

{#if isOpen}
  <div class="modal-backdrop" onclick={handleBackdropClick} onkeydown={(e) => e.key === 'Escape' && handleClose()} role="dialog" aria-modal="true" aria-labelledby="tag-manager-title" tabindex="-1">
    <div class="modal-content">
      <div class="modal-header">
        <h2 id="tag-manager-title">Manage Tags</h2>
        <button onclick={handleClose} class="close-btn" aria-label="Close tag manager">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      {#if mergeMode}
        <div class="merge-panel">
          <div class="merge-header">
            <h3>Merge Tags</h3>
            <button onclick={cancelMerge} class="cancel-merge-btn">Cancel</button>
          </div>

          <div class="merge-instructions">
            <p>Select a target tag to merge "{tagUsages.find(t => t.tag.id === mergeSourceId)?.tag.name}" into:</p>
          </div>

          <div class="merge-list">
            {#each tagUsages as { tag, usage_count }}
              {#if tag.id !== mergeSourceId}
                <button
                  class="merge-option"
                  class:selected={mergeTargetId === tag.id}
                  onclick={() => mergeTargetId = tag.id}
                >
                  <TagBadge {tag} />
                  <span class="usage-count">{usage_count} session{usage_count !== 1 ? 's' : ''}</span>
                </button>
              {/if}
            {/each}
          </div>

          <div class="merge-actions">
            <button
              onclick={executeMerge}
              disabled={!mergeTargetId}
              class="merge-execute-btn"
            >
              Merge Tags
            </button>
          </div>
        </div>
      {:else}
        <div class="tag-list">
          {#each tagUsages as { tag, usage_count }}
            <div class="tag-item" class:editing={editingTagId === tag.id}>
              {#if editingTagId === tag.id}
                <div class="edit-form">
                  <!-- svelte-ignore a11y_autofocus -->
                  <input
                    type="text"
                    bind:value={editName}
                    class="edit-input"
                    placeholder="Tag name"
                    autofocus
                  />

                  <div class="color-selector">
                    {#each colorPalette as color}
                      <button
                        class="color-btn"
                        class:selected={editColor === color}
                        style:background-color={color}
                        onclick={() => editColor = color}
                        title="Select color"
                        aria-label={`Select color ${color}`}
                      >
                        {#if editColor === color}
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        {/if}
                      </button>
                    {/each}
                  </div>

                  <div class="edit-actions">
                    <button onclick={() => saveEdit(tag.id)} class="save-btn">Save</button>
                    <button onclick={cancelEdit} class="cancel-btn">Cancel</button>
                  </div>
                </div>
              {:else}
                <div class="tag-info">
                  <TagBadge {tag} />
                  <span class="usage-badge">{usage_count} session{usage_count !== 1 ? 's' : ''}</span>
                </div>

                <div class="tag-actions">
                  <button
                    onclick={() => startEdit(tag)}
                    class="action-btn edit-btn"
                    title="Edit tag"
                    aria-label={`Edit tag ${tag.name}`}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>

                  <button
                    onclick={() => startMerge(tag)}
                    class="action-btn merge-btn"
                    title="Merge tag"
                    aria-label={`Merge tag ${tag.name}`}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
                    </svg>
                  </button>

                  <button
                    onclick={() => deleteTag(tag, usage_count)}
                    class="action-btn delete-btn"
                    title="Delete tag"
                    aria-label={`Delete tag ${tag.name}`}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              {/if}
            </div>
          {/each}

          {#if tagUsages.length === 0}
            <div class="empty-state">
              <p>No tags yet</p>
              <p class="hint">Create tags by typing in the "Add tag" field on any session</p>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    padding: 20px;
  }

  .modal-content {
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    max-width: 600px;
    width: 100%;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e0e0e0;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #000000;
  }

  .close-btn {
    padding: 8px;
    background: none;
    border: none;
    cursor: pointer;
    color: #666666;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .close-btn:hover {
    background: #f0f0f0;
    color: #333333;
  }

  .tag-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px 24px;
  }

  .tag-list::-webkit-scrollbar {
    width: 6px;
  }

  .tag-list::-webkit-scrollbar-track {
    background: #f5f5f5;
  }

  .tag-list::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 3px;
  }

  .tag-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
    background: #fafafa;
    transition: all 0.15s ease;
  }

  .tag-item:hover:not(.editing) {
    background: #f0f0f0;
  }

  .tag-item.editing {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
    background: #ffffff;
    border: 2px solid #007aff;
  }

  .tag-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .usage-badge {
    padding: 4px 8px;
    background: #e0e0e0;
    border-radius: 12px;
    font-size: 0.75rem;
    color: #666666;
    font-weight: 500;
  }

  .tag-actions {
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  .tag-item:hover .tag-actions {
    opacity: 1;
  }

  .action-btn {
    padding: 8px;
    background: none;
    border: 1px solid transparent;
    border-radius: 6px;
    cursor: pointer;
    color: #666666;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .action-btn:hover {
    background: rgba(0, 0, 0, 0.05);
  }

  .edit-btn:hover {
    color: #007aff;
    background: rgba(0, 122, 255, 0.1);
    border-color: #007aff;
  }

  .merge-btn:hover {
    color: #8B5CF6;
    background: rgba(139, 92, 246, 0.1);
    border-color: #8B5CF6;
  }

  .delete-btn:hover {
    color: #EF4444;
    background: rgba(239, 68, 68, 0.1);
    border-color: #EF4444;
  }

  .edit-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .edit-input {
    padding: 10px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.9rem;
    font-family: inherit;
  }

  .edit-input:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }

  .color-selector {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .color-btn {
    width: 32px;
    height: 32px;
    border: 2px solid transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .color-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .color-btn.selected {
    border-color: #000000;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .edit-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .save-btn,
  .cancel-btn {
    padding: 8px 16px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.15s ease;
  }

  .save-btn {
    background: #007aff;
    color: white;
    border-color: #007aff;
  }

  .save-btn:hover {
    background: #0056b3;
  }

  .cancel-btn {
    background: white;
    color: #666666;
  }

  .cancel-btn:hover {
    background: #f0f0f0;
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: #999999;
  }

  .empty-state p {
    margin: 8px 0;
    font-size: 0.9rem;
  }

  .empty-state .hint {
    font-size: 0.8rem;
    font-style: italic;
  }

  /* Merge Panel Styles */
  .merge-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .merge-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #e0e0e0;
  }

  .merge-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #333333;
  }

  .cancel-merge-btn {
    padding: 6px 12px;
    background: #f0f0f0;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.15s ease;
  }

  .cancel-merge-btn:hover {
    background: #e0e0e0;
  }

  .merge-instructions {
    padding: 16px 24px;
    background: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
  }

  .merge-instructions p {
    margin: 0;
    font-size: 0.9rem;
    color: #666666;
  }

  .merge-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px 24px;
  }

  .merge-option {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: #fafafa;
    border: 2px solid transparent;
    border-radius: 8px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .merge-option:hover {
    background: #f0f0f0;
  }

  .merge-option.selected {
    background: #e3f2fd;
    border-color: #007aff;
  }

  .merge-actions {
    padding: 16px 24px;
    border-top: 1px solid #e0e0e0;
  }

  .merge-execute-btn {
    width: 100%;
    padding: 12px;
    background: #8B5CF6;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .merge-execute-btn:hover:not(:disabled) {
    background: #7C3AED;
  }

  .merge-execute-btn:disabled {
    background: #d0d0d0;
    cursor: not-allowed;
    opacity: 0.6;
  }
</style>
