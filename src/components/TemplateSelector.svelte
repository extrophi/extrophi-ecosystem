<script>
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from 'svelte';

  let templates = $state([]);

  // Make selectedTemplate bindable from parent
  let { selectedTemplate = $bindable(null) } = $props();

  onMount(async () => {
    try {
      templates = await invoke('list_prompt_templates');
      // Select default template
      selectedTemplate = templates.find(t => t.is_default) || templates[0];
    } catch (error) {
      console.error('Failed to load prompt templates:', error);
    }
  });

  function selectTemplate(template) {
    selectedTemplate = template;
  }

  function formatTemplateName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
</script>

<div class="template-selector">
  <label for="template-select">AI Template:</label>
  <select id="template-select" bind:value={selectedTemplate}>
    {#each templates as template}
      <option value={template}>
        {formatTemplateName(template.name)}
        {#if template.is_default}(default){/if}
      </option>
    {/each}
  </select>

  {#if selectedTemplate}
    <p class="template-description">{selectedTemplate.description || 'No description available'}</p>
  {/if}
</div>

<style>
  .template-selector {
    padding: 12px;
    background: #f9f9f9;
    border-radius: 8px;
    margin-bottom: 16px;
  }

  label {
    display: block;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 8px;
    color: #333;
  }

  select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    background: white;
    font-size: 0.9rem;
    cursor: pointer;
    transition: border-color 0.2s ease;
  }

  select:hover {
    border-color: #007aff;
  }

  select:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }

  .template-description {
    margin-top: 8px;
    font-size: 0.85rem;
    color: #666;
    font-style: italic;
    line-height: 1.4;
  }
</style>
