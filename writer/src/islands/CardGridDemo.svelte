<script lang="ts">
  import CardGridIsland from './CardGridIsland.svelte';
  import type { Card, CardCategory } from '../lib/card-types';

  // Sample cards for demonstration
  let cards = $state<Card[]>([
    {
      id: '1',
      content: 'I need to build a better morning routine. Wake up at 6am, exercise, meditate.',
      category: 'UNASSIMILATED',
      privacy_level: 'PERSONAL',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '2',
      content: 'Client project deadline is Friday. Need to finish the API integration and deploy.',
      category: 'PROGRAM',
      privacy_level: 'BUSINESS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '3',
      content: 'The key to productivity is focus. Eliminate distractions, batch similar tasks.',
      category: 'CATEGORIZED',
      privacy_level: 'IDEAS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '4',
      content: 'Struggling with imposter syndrome. Feel like I\'m not good enough for this role.',
      category: 'GRIT',
      privacy_level: 'PERSONAL',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '5',
      content: 'Most people are lazy and make excuses. Winners do the work regardless of how they feel.',
      category: 'TOUGH',
      privacy_level: 'IDEAS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '6',
      content: 'Random thoughts about what to eat for lunch. Maybe pizza?',
      category: 'JUNK',
      privacy_level: 'IDEAS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '7',
      content: 'My email is john.doe@example.com and my phone is 555-123-4567.',
      category: 'UNASSIMILATED',
      privacy_level: 'PRIVATE',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: '8',
      content: 'System for tracking daily goals: 1) Set 3 priorities, 2) Time block, 3) Review at EOD.',
      category: 'PROGRAM',
      privacy_level: 'IDEAS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);

  /**
   * Handle card move between categories
   */
  function handleCardMove(cardId: string, newCategory: CardCategory): void {
    cards = cards.map((card) =>
      card.id === cardId
        ? { ...card, category: newCategory, updated_at: new Date().toISOString() }
        : card
    );
    console.log(`Moved card ${cardId} to ${newCategory}`);
  }

  /**
   * Handle card click
   */
  function handleCardClick(card: Card): void {
    console.log('Card clicked:', card);
    alert(`Card: ${card.content.substring(0, 50)}...\nCategory: ${card.category}\nPrivacy: ${card.privacy_level}`);
  }
</script>

<div class="demo-container">
  <div class="demo-header">
    <h1>Card Grid - 6-Category System</h1>
    <p>Drag and drop cards between categories. Click cards to view details.</p>
  </div>

  <CardGridIsland
    {cards}
    onCardMove={handleCardMove}
    onCardClick={handleCardClick}
  />
</div>

<style>
  .demo-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #fafafa;
  }

  .demo-header {
    padding: 24px;
    background: #ffffff;
    border-bottom: 2px solid #e0e0e0;
  }

  .demo-header h1 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 600;
    color: #333333;
  }

  .demo-header p {
    margin: 0;
    font-size: 14px;
    color: #666666;
  }
</style>
