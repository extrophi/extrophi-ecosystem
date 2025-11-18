<script lang="ts">
  import type { Card, CardCategory } from '../lib/card-types';
  import { getAllCategories, getCategoryConfig } from '../lib/card-types';
  import { classifyText, getLevelColor } from '../lib/privacy-rules';
  import type { PrivacyLevel } from '../lib/privacy-rules';

  // Props using Svelte 5 runes
  let {
    cards = [],
    onCardMove = null,
    onCardClick = null,
  }: {
    cards: Card[];
    onCardMove?: ((cardId: string, newCategory: CardCategory) => void) | null;
    onCardClick?: ((card: Card) => void) | null;
  } = $props();

  // State using Svelte 5 runes
  let draggedCard = $state<Card | null>(null);
  let dragOverCategory = $state<CardCategory | null>(null);
  let activeFilters = $state<Set<CardCategory>>(new Set());

  // Derived state: cards grouped by category
  let cardsByCategory = $derived(() => {
    const grouped: Record<CardCategory, Card[]> = {
      UNASSIMILATED: [],
      PROGRAM: [],
      CATEGORIZED: [],
      GRIT: [],
      TOUGH: [],
      JUNK: [],
    };

    cards.forEach((card) => {
      if (activeFilters.size === 0 || activeFilters.has(card.category)) {
        grouped[card.category].push(card);
      }
    });

    return grouped;
  });

  /**
   * Handle drag start
   */
  function handleDragStart(card: Card): (event: DragEvent) => void {
    return (event: DragEvent) => {
      draggedCard = card;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', card.id);
      }
    };
  }

  /**
   * Handle drag end
   */
  function handleDragEnd(): void {
    draggedCard = null;
    dragOverCategory = null;
  }

  /**
   * Handle drag over category column
   */
  function handleDragOver(category: CardCategory): (event: DragEvent) => void {
    return (event: DragEvent) => {
      event.preventDefault();
      dragOverCategory = category;
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = 'move';
      }
    };
  }

  /**
   * Handle drag leave category column
   */
  function handleDragLeave(): void {
    dragOverCategory = null;
  }

  /**
   * Handle drop on category column
   */
  function handleDrop(category: CardCategory): (event: DragEvent) => void {
    return (event: DragEvent) => {
      event.preventDefault();

      if (draggedCard && draggedCard.category !== category) {
        // Call the onCardMove callback if provided
        if (onCardMove) {
          onCardMove(draggedCard.id, category);
        }
      }

      draggedCard = null;
      dragOverCategory = null;
    };
  }

  /**
   * Handle card click
   */
  function handleCardClick(card: Card): void {
    if (onCardClick) {
      onCardClick(card);
    }
  }

  /**
   * Toggle category filter
   */
  function toggleFilter(category: CardCategory): void {
    const newFilters = new Set(activeFilters);
    if (newFilters.has(category)) {
      newFilters.delete(category);
    } else {
      newFilters.add(category);
    }
    activeFilters = newFilters;
  }

  /**
   * Clear all filters
   */
  function clearFilters(): void {
    activeFilters = new Set();
  }

  /**
   * Get privacy badge color for a card
   */
  function getPrivacyBadgeColor(level: PrivacyLevel): string {
    return getLevelColor(level);
  }
</script>

<div class="card-grid-island">
  <!-- Filter Bar -->
  <div class="filter-bar">
    <div class="filter-label">Filter by category:</div>
    <div class="filter-buttons">
      {#each getAllCategories() as category}
        {@const config = getCategoryConfig(category)}
        {@const isActive = activeFilters.has(category)}
        <button
          class="filter-btn"
          class:active={isActive}
          style="--category-color: {config.color}; --category-bg: {config.bgColor}"
          onclick={() => toggleFilter(category)}
        >
          {config.label}
        </button>
      {/each}
      {#if activeFilters.size > 0}
        <button class="clear-filters-btn" onclick={clearFilters}>
          Clear All
        </button>
      {/if}
    </div>
  </div>

  <!-- Category Columns Grid -->
  <div class="category-grid">
    {#each getAllCategories() as category}
      {@const config = getCategoryConfig(category)}
      {@const categoryCards = cardsByCategory()[category]}
      {@const isDragOver = dragOverCategory === category}

      <div
        class="category-column"
        class:drag-over={isDragOver}
        style="--category-color: {config.color}; --category-bg: {config.bgColor}"
        ondragover={handleDragOver(category)}
        ondragleave={handleDragLeave}
        ondrop={handleDrop(category)}
      >
        <!-- Column Header -->
        <div class="column-header">
          <div class="column-title">
            <span class="category-badge" style="background-color: {config.bgColor}; color: {config.color}">
              {config.label}
            </span>
            <span class="card-count">{categoryCards.length}</span>
          </div>
          <div class="column-description">{config.description}</div>
        </div>

        <!-- Cards List -->
        <div class="cards-list">
          {#each categoryCards as card (card.id)}
            <div
              class="card"
              class:dragging={draggedCard?.id === card.id}
              draggable="true"
              ondragstart={handleDragStart(card)}
              ondragend={handleDragEnd}
              onclick={() => handleCardClick(card)}
            >
              <!-- Card Header with Privacy Badge -->
              <div class="card-header">
                <div
                  class="privacy-badge"
                  style="background-color: {getPrivacyBadgeColor(card.privacy_level)}10; color: {getPrivacyBadgeColor(card.privacy_level)}; border-color: {getPrivacyBadgeColor(card.privacy_level)}40"
                >
                  {card.privacy_level}
                </div>
              </div>

              <!-- Card Content -->
              <div class="card-content">
                {card.content.substring(0, 200)}
                {#if card.content.length > 200}
                  <span class="content-ellipsis">...</span>
                {/if}
              </div>

              <!-- Card Footer -->
              <div class="card-footer">
                <span class="card-date">
                  {new Date(card.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          {/each}

          {#if categoryCards.length === 0}
            <div class="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="9" y1="9" x2="15" y2="15"></line>
                <line x1="15" y1="9" x2="9" y2="15"></line>
              </svg>
              <p>No cards</p>
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .card-grid-island {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #fafafa;
    padding: 24px;
    gap: 24px;
  }

  /* Filter Bar */
  .filter-bar {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
  }

  .filter-label {
    font-size: 14px;
    font-weight: 600;
    color: #333333;
  }

  .filter-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .filter-btn {
    padding: 6px 12px;
    border: 2px solid var(--category-color);
    background: #ffffff;
    color: var(--category-color);
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .filter-btn:hover {
    background: var(--category-bg);
  }

  .filter-btn.active {
    background: var(--category-color);
    color: #ffffff;
  }

  .clear-filters-btn {
    padding: 6px 12px;
    border: 2px solid #dc2626;
    background: #ffffff;
    color: #dc2626;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .clear-filters-btn:hover {
    background: #dc2626;
    color: #ffffff;
  }

  /* Category Grid */
  .category-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    flex: 1;
    overflow: hidden;
  }

  /* Responsive: 3 columns on tablet */
  @media (max-width: 1280px) {
    .category-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  /* Responsive: 1 column on mobile */
  @media (max-width: 768px) {
    .category-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Category Column */
  .category-column {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.2s ease;
  }

  .category-column.drag-over {
    border-color: var(--category-color);
    background: var(--category-bg);
    box-shadow: 0 0 0 3px var(--category-bg);
  }

  /* Column Header */
  .column-header {
    padding: 16px;
    background: var(--category-bg);
    border-bottom: 2px solid var(--category-color);
  }

  .column-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .category-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .card-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    padding: 0 8px;
    background: var(--category-color);
    color: #ffffff;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
  }

  .column-description {
    font-size: 12px;
    color: #666666;
    line-height: 1.4;
  }

  /* Cards List */
  .cards-list {
    flex: 1;
    padding: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* Card */
  .card {
    display: flex;
    flex-direction: column;
    padding: 12px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    cursor: move;
    transition: all 0.2s ease;
  }

  .card:hover {
    border-color: #999999;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  .card.dragging {
    opacity: 0.5;
    transform: scale(0.95);
  }

  /* Card Header */
  .card-header {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 8px;
  }

  .privacy-badge {
    padding: 2px 8px;
    border: 1px solid;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  /* Card Content */
  .card-content {
    flex: 1;
    font-size: 14px;
    line-height: 1.5;
    color: #333333;
    margin-bottom: 8px;
    word-wrap: break-word;
  }

  .content-ellipsis {
    color: #999999;
    font-style: italic;
  }

  /* Card Footer */
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 8px;
    border-top: 1px solid #f0f0f0;
  }

  .card-date {
    font-size: 11px;
    color: #999999;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: #cccccc;
  }

  .empty-state svg {
    margin-bottom: 12px;
    opacity: 0.5;
  }

  .empty-state p {
    font-size: 14px;
    font-weight: 500;
  }

  /* Scrollbar Styling */
  .cards-list::-webkit-scrollbar {
    width: 6px;
  }

  .cards-list::-webkit-scrollbar-track {
    background: #f5f5f5;
    border-radius: 3px;
  }

  .cards-list::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 3px;
  }

  .cards-list::-webkit-scrollbar-thumb:hover {
    background: #b0b0b0;
  }
</style>
