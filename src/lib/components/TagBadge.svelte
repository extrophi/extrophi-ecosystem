<script>
  /**
   * TagBadge Component
   * Displays a tag with custom color and optional remove button
   *
   * Props:
   * - tag: Tag object {id, name, color}
   * - size: 'small' | 'medium' (default: 'medium')
   * - removable: boolean (default: false)
   * - onRemove: callback when remove button is clicked
   */

  let { tag, size = 'medium', removable = false, onRemove = undefined } = $props();

  function handleRemove(event) {
    event.stopPropagation();
    if (onRemove) {
      onRemove(tag);
    }
  }
</script>

<span
  class="tag-badge"
  class:size-small={size === 'small'}
  class:size-medium={size === 'medium'}
  class:removable={removable}
  style:background-color={tag.color}
  style:border-color={tag.color}
  role="status"
  aria-label={`Tag: ${tag.name}`}
>
  <span class="tag-name">{tag.name}</span>
  {#if removable}
    <button
      class="remove-btn"
      onclick={handleRemove}
      aria-label={`Remove tag ${tag.name}`}
      title="Remove tag"
    >
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  {/if}
</span>

<style>
  .tag-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 12px;
    font-weight: 500;
    transition: all 0.15s ease;
    white-space: nowrap;
    color: rgba(255, 255, 255, 0.95);
    border: 1px solid transparent;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .tag-badge.size-small {
    padding: 2px 8px;
    font-size: 0.7rem;
    height: 20px;
  }

  .tag-badge.size-medium {
    padding: 4px 10px;
    font-size: 0.75rem;
    height: 24px;
  }

  .tag-badge.removable {
    padding-right: 6px;
  }

  .tag-name {
    line-height: 1;
    text-shadow: 0 0.5px 1px rgba(0, 0, 0, 0.2);
  }

  .remove-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    color: white;
    transition: all 0.15s ease;
    width: 16px;
    height: 16px;
  }

  .remove-btn:hover {
    background: rgba(255, 255, 255, 0.35);
    transform: scale(1.1);
  }

  .remove-btn:active {
    transform: scale(0.95);
  }

  .remove-btn svg {
    display: block;
  }

  /* Ensure good contrast on light backgrounds */
  .tag-badge[style*="#F"] .tag-name,
  .tag-badge[style*="#E"] .tag-name {
    color: rgba(0, 0, 0, 0.8);
    text-shadow: 0 0.5px 1px rgba(255, 255, 255, 0.3);
  }

  .tag-badge[style*="#F"] .remove-btn,
  .tag-badge[style*="#E"] .remove-btn {
    color: rgba(0, 0, 0, 0.7);
    background: rgba(0, 0, 0, 0.1);
  }

  .tag-badge[style*="#F"] .remove-btn:hover,
  .tag-badge[style*="#E"] .remove-btn:hover {
    background: rgba(0, 0, 0, 0.2);
  }
</style>
