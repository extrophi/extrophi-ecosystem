<script>
  import { invoke } from '@tauri-apps/api/core';
  import { showError } from '../utils/toast.js';
  import TagBadge from './TagBadge.svelte';

  /**
   * SessionTagInput Component
   * Displays and manages tags for a specific session
   *
   * Props:
   * - sessionId: number - The session to manage tags for
   * - tags: Array<{ id: number; name: string; color: string }> - Current tags assigned to this session
   * - onTagsChange: callback when tags are modified
   */

  /** @type {{ sessionId: number; tags?: Array<{ id: number; name: string; color: string }>; onTagsChange?: (tags: Array<{ id: number; name: string; color: string }>) => void }} */
  let { sessionId, tags = [], onTagsChange } = $props();

  let inputValue = $state('');
  let availableTags = $state([]);
  let showSuggestions = $state(false);
  let selectedIndex = $state(0);

  // Filter suggestions based on input - fixed line 27
  let suggestions = $derived(() => {
    const existingIds = new Set(tags.map(tag => tag.id));
    const query = inputValue.toLowerCase().trim();

    return availableTags
      .filter(tag => !existingIds.has(tag.id))
      .filter(tag => tag.name.toLowerCase().includes(query))
      .slice(0, 5);
  });

  $effect(() => {
    loadAvailableTags();
  });

  async function loadAvailableTags() {
    try {
      availableTags = await invoke('get_all_tags');
    } catch (e) {
      console.error('Failed to load tags:', e);
      showError('Failed to load available tags');
    }
  }

  async function addTag(tag) {
    try {
      await invoke('add_tag_to_session', {
        sessionId,
        tagId: tag.id
      });

      const updatedTags = [...tags, tag];
      if (onTagsChange) {
        onTagsChange(updatedTags);
      }

      inputValue = '';
      showSuggestions = false;
    } catch (e) {
      showError(`Failed to add tag: ${e}`);
    }
  }

  async function removeTag(tagToRemove) {
    try {
      await invoke('remove_tag_from_session', {
        sessionId,
        tagId: tagToRemove.id
      });

      const updatedTags = tags.filter(tag => tag.id !== tagToRemove.id);
      if (onTagsChange) {
        onTagsChange(updatedTags);
      }
    } catch (e) {
      showError(`Failed to remove tag: ${e}`);
    }
  }

  function handleInput() {
    showSuggestions = inputValue.length > 0;
    selectedIndex = 0;
  }

  function handleKeydown(event) {
    if (!showSuggestions || suggestions().length === 0) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        selectedIndex = (selectedIndex + 1) % suggestions().length;
        break;

      case 'ArrowUp':
        event.preventDefault();
        selectedIndex = (selectedIndex - 1 + suggestions().length) % suggestions().length;
        break;

      case 'Enter':
        event.preventDefault();
        if (suggestions()[selectedIndex]) {
          addTag(suggestions()[selectedIndex]);
        }
        break;

      case 'Escape':
        event.preventDefault();
        showSuggestions = false;
        inputValue = '';
        break;
    }
  }

  function handleBlur() {
    setTimeout(() => {
      showSuggestions = false;
    }, 150);
  }
</script>

<div class="session-tag-input">
  <div class="current-tags">
    {#each tags as tag (tag.id)}
      <TagBadge
        {tag}
        removable={true}
        onRemove={() => removeTag(tag)}
      />
    {/each}
  </div>

  <div class="input-wrapper">
    <input
      type="text"
      bind:value={inputValue}
      oninput={handleInput}
      onkeydown={handleKeydown}
      onblur={handleBlur}
      onfocus={() => inputValue.length > 0 && (showSuggestions = true)}
      placeholder="Add tag..."
      class="tag-input"
      autocomplete="off"
    />

    {#if showSuggestions && suggestions().length > 0}
      <div class="suggestions">
        {#each suggestions() as suggestion, index}
          <button
            class="suggestion-item"
            class:selected={index === selectedIndex}
            onclick={() => addTag(suggestion)}
            type="button"
          >
            <span class="tag-color" style:background-color={suggestion.color}></span>
            <span>{suggestion.name}</span>
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .session-tag-input {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .current-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .input-wrapper {
    position: relative;
  }

  .tag-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.875rem;
    font-family: inherit;
    background: #fafafa;
    outline: none;
    transition: all 0.2s ease;
  }

  .tag-input:focus {
    border-color: #007aff;
    background: #ffffff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }

  .tag-input::placeholder {
    color: #999999;
  }

  .suggestions {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 100;
    overflow: hidden;
  }

  .suggestion-item {
    width: 100%;
    padding: 10px 12px;
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    color: #333333;
    transition: background-color 0.15s ease;
  }

  .suggestion-item:hover,
  .suggestion-item.selected {
    background: #f0f0f0;
  }

  .tag-color {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    flex-shrink: 0;
  }
</style>
