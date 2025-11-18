<script lang="ts">
  /**
   * Privacy Scanner Island Demo
   * Demonstrates the 4-level privacy classification system
   *
   * Usage: Can be used standalone or as an Astro island
   */

  import PrivacyScannerIsland from './PrivacyScannerIsland.svelte';

  // Demo content examples
  let currentExample = $state('private');

  const examples = {
    private: `
Today I had a great meeting. Here's my contact info:
Email: john.doe@example.com
Phone: (555) 123-4567
SSN: 123-45-6789

I live at 123 Main Street, and my credit card is 4532-1234-5678-9010.
    `.trim(),

    personal: `
I feel really grateful today. My wife surprised me with breakfast and it made me so happy.
I've been working on my mental health and therapy is really helping.

When I was younger, I struggled with anxiety, but now I think I'm in a much better place.
My family has been incredibly supportive through this journey.
    `.trim(),

    business: `
Meeting notes from client discussion:
- Project Phoenix deadline: Q2 2024
- Revenue forecast shows 25% growth
- Budget allocation: $50,000 for development
- Competitor analysis reveals market opportunity
- Strategy: focus on enterprise customers
- Internal roadmap requires board approval
    `.trim(),

    ideas: `
Success in business comes from consistent daily action.
Focus on providing genuine value to others before expecting returns.

Building systems that scale beyond your personal time is the key to leverage.
The best ideas emerge from the intersection of curiosity and discipline.

Think long-term. Act short-term. Iterate constantly.
    `.trim()
  };

  let content = $state(examples['private']);
  let showDetails = $state(true);

  // Update content when example changes
  $effect(() => {
    content = examples[currentExample];
  });

  function selectExample(example: keyof typeof examples) {
    currentExample = example;
    content = examples[example];
  }
</script>

<div class="demo-container">
  <div class="demo-header">
    <h2>Privacy Scanner Demo</h2>
    <p>Test the 4-level privacy classification system</p>
  </div>

  <!-- Example Selector -->
  <div class="example-buttons">
    <button
      class="example-btn"
      class:active={currentExample === 'private'}
      onclick={() => selectExample('private')}
    >
      🔴 Private
    </button>
    <button
      class="example-btn"
      class:active={currentExample === 'personal'}
      onclick={() => selectExample('personal')}
    >
      🟠 Personal
    </button>
    <button
      class="example-btn"
      class:active={currentExample === 'business'}
      onclick={() => selectExample('business')}
    >
      🟡 Business
    </button>
    <button
      class="example-btn"
      class:active={currentExample === 'ideas'}
      onclick={() => selectExample('ideas')}
    >
      🟢 Ideas
    </button>
  </div>

  <!-- Content Editor -->
  <div class="content-section">
    <label for="content-textarea">Content to Scan:</label>
    <textarea
      id="content-textarea"
      bind:value={content}
      placeholder="Type or paste content here..."
      rows={12}
    ></textarea>
  </div>

  <!-- Privacy Scanner Island -->
  <div class="scanner-section">
    <div class="scanner-controls">
      <label>
        <input type="checkbox" bind:checked={showDetails} />
        Show detailed breakdown
      </label>
    </div>

    <PrivacyScannerIsland
      content={content}
      showDetails={showDetails}
      debounceMs={300}
      onLevelChange={(level) => console.log('Privacy level changed:', level)}
    />
  </div>

  <!-- Instructions -->
  <div class="instructions">
    <h3>How It Works</h3>
    <ul>
      <li><strong>🔴 PRIVATE:</strong> PII data (emails, SSN, credit cards, phone numbers, addresses)</li>
      <li><strong>🟠 PERSONAL:</strong> Emotional content, family references, health info</li>
      <li><strong>🟡 BUSINESS:</strong> Client names, projects, strategies, financial info</li>
      <li><strong>🟢 IDEAS:</strong> General thoughts and philosophies - safe to publish</li>
    </ul>
    <p><strong>Priority:</strong> PRIVATE → PERSONAL → BUSINESS → IDEAS (most restrictive wins)</p>
  </div>
</div>

<style>
  .demo-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
    font-family: system-ui, -apple-system, sans-serif;
  }

  .demo-header {
    text-align: center;
    margin-bottom: 32px;
  }

  .demo-header h2 {
    margin: 0 0 8px 0;
    font-size: 2rem;
    font-weight: 700;
    color: #333333;
  }

  .demo-header p {
    margin: 0;
    font-size: 1.125rem;
    color: #666666;
  }

  .example-buttons {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }

  .example-btn {
    flex: 1;
    min-width: 120px;
    padding: 12px 20px;
    background: #f5f5f5;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .example-btn:hover {
    background: #e8e8e8;
    border-color: #cccccc;
  }

  .example-btn.active {
    background: #007aff;
    border-color: #007aff;
    color: #ffffff;
  }

  .content-section {
    margin-bottom: 24px;
  }

  .content-section label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #333333;
  }

  textarea {
    width: 100%;
    padding: 12px;
    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.6;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    resize: vertical;
    transition: border-color 0.2s ease;
  }

  textarea:focus {
    outline: none;
    border-color: #007aff;
  }

  .scanner-section {
    margin-bottom: 32px;
  }

  .scanner-controls {
    margin-bottom: 16px;
  }

  .scanner-controls label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.95rem;
    color: #666666;
    cursor: pointer;
  }

  .scanner-controls input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  .instructions {
    padding: 20px;
    background: #f9f9f9;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
  }

  .instructions h3 {
    margin: 0 0 16px 0;
    font-size: 1.25rem;
    color: #333333;
  }

  .instructions ul {
    margin: 0 0 16px 0;
    padding-left: 24px;
  }

  .instructions li {
    margin-bottom: 8px;
    line-height: 1.6;
    color: #555555;
  }

  .instructions p {
    margin: 0;
    padding: 12px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    font-size: 0.95rem;
    color: #856404;
  }

  @media (max-width: 640px) {
    .demo-container {
      padding: 16px;
    }

    .example-buttons {
      flex-direction: column;
    }

    .example-btn {
      width: 100%;
    }
  }
</style>
