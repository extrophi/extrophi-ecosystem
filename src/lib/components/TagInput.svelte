<script>
  import { invoke } from '@tauri-apps/api/core';
  import { showError } from '../utils/toast.js';

  /**
   * TagInput Component
   * Autocomplete input for adding tags to a session
   *
   * Props:
   * - sessionId: number - The session to add tags to
   * - existingTags: Tag[] - Tags already assigned to this session
   * - onTagAdded: callback when a tag is successfully added
   */

  let { sessionId, existingTags = [], onTagAdded } = $props();

  let allTags = $state([]);
  let inputValue = $state('');
  let showDropdown = $state(false);
  let selectedIndex = $state(0);
  let inputRef = $state(null);
  let showColorPicker = $state(false);
  let newTagColor = $state('#3B82F6');

  // Predefined colors (Tailwind palette)
  const colorPalette = [
    { name: 'Blue', value: '#3B82F6' },
    { name: 'Green', value: '#10B981' },
    { name: 'Purple', value: '#8B5CF6' },
    { name: 'Amber', value: '#F59E0B' },
    { name: 'Pink', value: '#EC4899' },
    { name: 'Red', value: '#EF4444' },
    { name: 'Teal', value: '#14B8A6' },
    { name: 'Indigo', value: '#6366F1' },
  ];

  // Filtered tags (exclude already assigned tags and filter by input)
  let filteredTags = $derived(() => {
    const existingTagIds = new Set(existingTags.map(t => t.id));
    const query = inputValue.toLowerCase().trim();

    return allTags
      .filter(tag => !existingTagIds.has(tag.id))
      .filter(tag => tag.name.toLowerCase().includes(query))
      .slice(0, 10);
  });

  // Check if input matches an existing tag exactly (for creating new)
  let canCreateNew = $derived(() => {
    const query = inputValue.trim();
    if (!query) return false;

    const exactMatch = allTags.find(t => t.name.toLowerCase() === query.toLowerCase());
    return !exactMatch;
  });

  // Load all tags on mount
  $effect(() => {
    loadAllTags();
  });

  async function loadAllTags() {
    try {
      allTags = await invoke('get_all_tags');
    } catch (e) {
      console.error('Failed to load tags:', e);
      showError('Failed to load tags');
    }
  }

  function handleInput() {
    showDropdown = inputValue.length > 0;
    selectedIndex = 0;
  }

  function handleFocus() {
    if (inputValue.length > 0) {
      showDropdown = true;
    }
  }

  function handleBlur() {
    // Delay to allow click events to register
    setTimeout(() => {
      showDropdown = false;
      showColorPicker = false;
    }, 200);
  }

  async function selectTag(tag) {
    try {
      await invoke('add_tag_to_session', {
        sessionId,
        tagId: tag.id
      });

      if (onTagAdded) {
        onTagAdded(tag);
      }

      inputValue = '';
      showDropdown = false;
      inputRef?.focus();
    } catch (e) {
      showError(`Failed to add tag: ${e}`);
    }
  }

  async function createNewTag() {
    const tagName = inputValue.trim();
    if (!tagName) return;

    try {
      const newTag = await invoke('create_tag', {
        name: tagName,
        color: newTagColor
      });

      // Reload tags list
      await loadAllTags();

      // Add to session
      await selectTag(newTag);

      showColorPicker = false;
      newTagColor = '#3B82F6'; // Reset to default
    } catch (e) {
      showError(`Failed to create tag: ${e}`);
    }
  }

  function handleKeydown(event) {
    if (!showDropdown) {
      if (event.key === 'Enter' && canCreateNew()) {
        event.preventDefault();
        showColorPicker = true;
      }
      return;
    }

    const itemCount = filteredTags().length + (canCreateNew() ? 1 : 0);

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        selectedIndex = (selectedIndex + 1) % itemCount;
        break;

      case 'ArrowUp':
        event.preventDefault();
        selectedIndex = (selectedIndex - 1 + itemCount) % itemCount;
        break;

      case 'Enter':
        event.preventDefault();
        if (selectedIndex < filteredTags().length) {
          selectTag(filteredTags()[selectedIndex]);
        } else if (canCreateNew()) {
          showColorPicker = true;
        }
        break;

      case 'Escape':
        event.preventDefault();
        showDropdown = false;
        showColorPicker = false;
        inputValue = '';
        break;
    }
  }

  function handleColorSelect(color) {
    newTagColor = color;
    createNewTag();
  }
</script>

<div class="tag-input-container">
  <div class="input-wrapper">
    <svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
      <line x1="7" y1="7" x2="7.01" y2="7"></line>
    </svg>

    <input
      type="text"
      bind:value={inputValue}
      bind:this={inputRef}
      oninput={handleInput}
      onfocus={handleFocus}
      onblur={handleBlur}
      onkeydown={handleKeydown}
      placeholder="Add tag..."
      class="tag-input"
      autocomplete="off"
      role="combobox"
      aria-label="Add tag to session"
      aria-autocomplete="list"
      aria-controls="tag-dropdown"
      aria-expanded={showDropdown}
    />
  </div>

  {#if showDropdown && (filteredTags().length > 0 || canCreateNew())}
    <div id="tag-dropdown" class="dropdown" role="listbox">
      {#each filteredTags() as tag, index}
        <button
          class="dropdown-item"
          class:selected={index === selectedIndex}
          onclick={() => selectTag(tag)}
          role="option"
          aria-selected={index === selectedIndex}
        >
          <span class="tag-preview" style:background-color={tag.color}></span>
          <span class="tag-name">{tag.name}</span>
        </button>
      {/each}

      {#if canCreateNew()}
        <button
          class="dropdown-item create-new"
          class:selected={selectedIndex === filteredTags().length}
          onclick={() => showColorPicker = true}
          role="option"
          aria-selected={selectedIndex === filteredTags().length}
        >
          <svg class="create-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>Create "{inputValue}"</span>
        </button>
      {/if}
    </div>
  {/if}

  {#if showColorPicker}
    <div class="color-picker-modal">
      <div class="color-picker-header">
        <span>Choose color for "{inputValue}"</span>
        <button onclick={() => showColorPicker = false} class="close-btn" aria-label="Close color picker">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="color-grid">
        {#each colorPalette as color}
          <button
            class="color-option"
            class:selected={newTagColor === color.value}
            style:background-color={color.value}
            onclick={() => handleColorSelect(color.value)}
            title={color.name}
            aria-label={`Select ${color.name} color`}
          >
            {#if newTagColor === color.value}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .tag-input-container {
    position: relative;
    width: 100%;
  }

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .icon {
    position: absolute;
    left: 10px;
    color: #999999;
    pointer-events: none;
  }

  .tag-input {
    width: 100%;
    padding: 8px 12px 8px 32px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 0.875rem;
    font-family: inherit;
    background: #fafafa;
    transition: all 0.2s ease;
    outline: none;
  }

  .tag-input:focus {
    border-color: #007aff;
    background: #ffffff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }

  .tag-input::placeholder {
    color: #999999;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    max-height: 240px;
    overflow-y: auto;
    z-index: 1000;
  }

  .dropdown::-webkit-scrollbar {
    width: 6px;
  }

  .dropdown::-webkit-scrollbar-track {
    background: #f5f5f5;
  }

  .dropdown::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 3px;
  }

  .dropdown-item {
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

  .dropdown-item:first-child {
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
  }

  .dropdown-item:last-child {
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
  }

  .dropdown-item:hover,
  .dropdown-item.selected {
    background: #f0f0f0;
  }

  .tag-preview {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    flex-shrink: 0;
  }

  .tag-name {
    flex: 1;
  }

  .dropdown-item.create-new {
    color: #007aff;
    font-weight: 500;
    border-top: 1px solid #e0e0e0;
  }

  .create-icon {
    flex-shrink: 0;
  }

  .color-picker-modal {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 12px;
    z-index: 1001;
  }

  .color-picker-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #333333;
  }

  .close-btn {
    padding: 4px;
    background: none;
    border: none;
    cursor: pointer;
    color: #666666;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .close-btn:hover {
    background: #f0f0f0;
    color: #333333;
  }

  .color-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }

  .color-option {
    width: 100%;
    aspect-ratio: 1;
    border: 2px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .color-option:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .color-option.selected {
    border-color: #333333;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
</style>
