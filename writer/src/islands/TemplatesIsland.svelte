<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import type { CardTemplate } from '../lib/templates/templates';
  import { substituteVariables, TEMPLATE_VARIABLES, formatTemplateName } from '../lib/templates/templates';
  import type { CardCategory } from '../lib/card-types';

  // Props using Svelte 5 runes
  let {
    onTemplateSelect = null,
  }: {
    onTemplateSelect?: ((template: CardTemplate) => void) | null;
  } = $props();

  // State
  let templates = $state<CardTemplate[]>([]);
  let selectedTemplate = $state<CardTemplate | null>(null);
  let isLoading = $state(true);
  let errorMessage = $state('');
  let showCreateForm = $state(false);
  let previewContent = $state('');

  // Form state
  let formName = $state('');
  let formTitle = $state('');
  let formContent = $state('');
  let formCategory = $state<CardCategory | ''>('');

  // Filter state
  let showSystemOnly = $state(false);
  let showUserOnly = $state(false);

  // Derived filtered templates
  let filteredTemplates = $derived(() => {
    let result = templates;
    if (showSystemOnly) {
      result = result.filter(t => t.is_system);
    } else if (showUserOnly) {
      result = result.filter(t => !t.is_system);
    }
    return result;
  });

  /**
   * Load templates from database
   */
  async function loadTemplates(): Promise<void> {
    try {
      isLoading = true;
      errorMessage = '';
      templates = await invoke('list_card_templates');

      // Select first template if none selected
      if (!selectedTemplate && templates.length > 0) {
        selectTemplate(templates[0]);
      }
    } catch (error) {
      console.error('Failed to load card templates:', error);
      errorMessage = error instanceof Error ? error.message : 'Failed to load templates';
    } finally {
      isLoading = false;
    }
  }

  /**
   * Select a template
   */
  function selectTemplate(template: CardTemplate): void {
    selectedTemplate = template;
    previewContent = substituteVariables(template.content);

    if (onTemplateSelect) {
      onTemplateSelect(template);
    }
  }

  /**
   * Use the selected template
   */
  function useTemplate(): void {
    if (!selectedTemplate) return;

    const content = substituteVariables(selectedTemplate.content);

    // Emit event or call callback with substituted content
    if (onTemplateSelect) {
      onTemplateSelect({
        ...selectedTemplate,
        content,
      });
    }
  }

  /**
   * Create a new custom template
   */
  async function createTemplate(): Promise<void> {
    if (!formName || !formTitle || !formContent) {
      errorMessage = 'Please fill in all required fields';
      return;
    }

    try {
      errorMessage = '';
      const templateId = await invoke('create_card_template', {
        name: formName,
        title: formTitle,
        content: formContent,
        category: formCategory || null,
      });

      // Reset form
      formName = '';
      formTitle = '';
      formContent = '';
      formCategory = '';
      showCreateForm = false;

      // Reload templates
      await loadTemplates();
    } catch (error) {
      console.error('Failed to create template:', error);
      errorMessage = error instanceof Error ? error.message : 'Failed to create template';
    }
  }

  /**
   * Delete a template
   */
  async function deleteTemplate(template: CardTemplate): Promise<void> {
    if (template.is_system) {
      errorMessage = 'Cannot delete system templates';
      return;
    }

    if (!template.id) return;

    if (!confirm(`Delete template "${template.title}"?`)) {
      return;
    }

    try {
      errorMessage = '';
      await invoke('delete_card_template', { id: template.id });

      // Clear selection if deleted template was selected
      if (selectedTemplate?.id === template.id) {
        selectedTemplate = null;
      }

      // Reload templates
      await loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
      errorMessage = error instanceof Error ? error.message : 'Failed to delete template';
    }
  }

  // Load templates on mount
  onMount(() => {
    loadTemplates();
  });
</script>

<div class="templates-island">
  <div class="templates-header">
    <h2>Card Templates</h2>
    <div class="header-actions">
      <button class="btn-secondary" onclick={() => showCreateForm = !showCreateForm}>
        {showCreateForm ? 'Cancel' : '+ New Template'}
      </button>
      <button class="btn-primary" onclick={useTemplate} disabled={!selectedTemplate}>
        Use Template
      </button>
    </div>
  </div>

  {#if errorMessage}
    <div class="error-banner">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>{errorMessage}</span>
    </div>
  {/if}

  {#if showCreateForm}
    <div class="create-form">
      <h3>Create Custom Template</h3>
      <div class="form-group">
        <label for="template-name">Template Name (alphanumeric, no spaces)</label>
        <input
          id="template-name"
          type="text"
          bind:value={formName}
          placeholder="my_template"
          pattern="[a-zA-Z0-9_-]+"
        />
      </div>
      <div class="form-group">
        <label for="template-title">Display Title</label>
        <input
          id="template-title"
          type="text"
          bind:value={formTitle}
          placeholder="My Template"
        />
      </div>
      <div class="form-group">
        <label for="template-category">Category (optional)</label>
        <select id="template-category" bind:value={formCategory}>
          <option value="">None</option>
          <option value="UNASSIMILATED">Unassimilated</option>
          <option value="PROGRAM">Program</option>
          <option value="CATEGORIZED">Categorized</option>
          <option value="GRIT">Grit</option>
          <option value="TOUGH">Tough</option>
          <option value="JUNK">Junk</option>
        </select>
      </div>
      <div class="form-group">
        <label for="template-content">
          Template Content
          <span class="hint">Use variables: {TEMPLATE_VARIABLES.map(v => v.placeholder).join(', ')}</span>
        </label>
        <textarea
          id="template-content"
          bind:value={formContent}
          placeholder="# {{date}}&#10;&#10;Your template content here..."
          rows="8"
        ></textarea>
      </div>
      <div class="form-actions">
        <button class="btn-secondary" onclick={() => showCreateForm = false}>Cancel</button>
        <button class="btn-primary" onclick={createTemplate}>Create Template</button>
      </div>
    </div>
  {/if}

  <div class="templates-container">
    <div class="templates-sidebar">
      <div class="filter-buttons">
        <button
          class="filter-btn"
          class:active={!showSystemOnly && !showUserOnly}
          onclick={() => { showSystemOnly = false; showUserOnly = false; }}
        >
          All
        </button>
        <button
          class="filter-btn"
          class:active={showSystemOnly}
          onclick={() => { showSystemOnly = true; showUserOnly = false; }}
        >
          System
        </button>
        <button
          class="filter-btn"
          class:active={showUserOnly}
          onclick={() => { showSystemOnly = false; showUserOnly = true; }}
        >
          Custom
        </button>
      </div>

      {#if isLoading}
        <div class="loading">Loading templates...</div>
      {:else if filteredTemplates().length === 0}
        <div class="empty-state">No templates found</div>
      {:else}
        <div class="template-list">
          {#each filteredTemplates() as template}
            <div
              class="template-item"
              class:selected={selectedTemplate?.id === template.id}
              onclick={() => selectTemplate(template)}
            >
              <div class="template-item-header">
                <span class="template-title">{template.title}</span>
                {#if template.is_system}
                  <span class="badge badge-system">System</span>
                {:else}
                  <button
                    class="btn-delete"
                    onclick={(e) => { e.stopPropagation(); deleteTemplate(template); }}
                    title="Delete template"
                  >
                    ×
                  </button>
                {/if}
              </div>
              {#if template.category}
                <span class="template-category">{template.category}</span>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="template-preview">
      {#if selectedTemplate}
        <div class="preview-header">
          <h3>{selectedTemplate.title}</h3>
          {#if selectedTemplate.is_system}
            <span class="badge badge-system">System Template</span>
          {:else}
            <span class="badge badge-custom">Custom Template</span>
          {/if}
        </div>

        <div class="preview-info">
          <div class="info-item">
            <strong>Name:</strong> {selectedTemplate.name}
          </div>
          {#if selectedTemplate.category}
            <div class="info-item">
              <strong>Category:</strong> {selectedTemplate.category}
            </div>
          {/if}
        </div>

        <div class="preview-section">
          <h4>Template Variables</h4>
          <div class="variables-list">
            {#each TEMPLATE_VARIABLES as variable}
              <div class="variable-item">
                <code>{variable.placeholder}</code>
                <span>{variable.description}</span>
              </div>
            {/each}
          </div>
        </div>

        <div class="preview-section">
          <h4>Preview (with substitutions)</h4>
          <div class="preview-content">
            <pre>{previewContent}</pre>
          </div>
        </div>

        <div class="preview-section">
          <h4>Raw Template</h4>
          <div class="preview-content">
            <pre>{selectedTemplate.content}</pre>
          </div>
        </div>
      {:else}
        <div class="empty-preview">
          <p>Select a template to preview</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .templates-island {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
  }

  .templates-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: #fafafa;
    border-bottom: 1px solid #e0e0e0;
  }

  .templates-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333;
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }

  .error-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    background: #ffebee;
    color: #c62828;
    border-bottom: 1px solid #ffcdd2;
    font-size: 14px;
  }

  .create-form {
    padding: 20px;
    background: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
  }

  .create-form h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
  }

  .form-group {
    margin-bottom: 16px;
  }

  .form-group label {
    display: block;
    margin-bottom: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #555;
  }

  .form-group .hint {
    font-size: 11px;
    color: #888;
    font-weight: 400;
    margin-left: 8px;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    font-size: 14px;
    font-family: inherit;
  }

  .form-group textarea {
    font-family: 'Monaco', 'Menlo', monospace;
    resize: vertical;
  }

  .form-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .templates-container {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .templates-sidebar {
    width: 300px;
    border-right: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .filter-buttons {
    display: flex;
    padding: 12px;
    gap: 8px;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .filter-btn {
    flex: 1;
    padding: 6px 12px;
    border: 1px solid #d0d0d0;
    background: #ffffff;
    color: #666;
    border-radius: 4px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .filter-btn:hover {
    background: #f5f5f5;
    border-color: #007aff;
  }

  .filter-btn.active {
    background: #007aff;
    color: white;
    border-color: #007aff;
  }

  .template-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .template-item {
    padding: 12px;
    margin-bottom: 6px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .template-item:hover {
    background: #f5f5f5;
    border-color: #007aff;
  }

  .template-item.selected {
    background: #e3f2fd;
    border-color: #007aff;
  }

  .template-item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 4px;
  }

  .template-title {
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }

  .template-category {
    font-size: 11px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
  }

  .badge-system {
    background: #e0e0e0;
    color: #555;
  }

  .badge-custom {
    background: #e3f2fd;
    color: #1976d2;
  }

  .btn-delete {
    width: 20px;
    height: 20px;
    padding: 0;
    border: none;
    background: #ffebee;
    color: #c62828;
    border-radius: 50%;
    font-size: 18px;
    line-height: 1;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-delete:hover {
    background: #c62828;
    color: white;
  }

  .template-preview {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  .preview-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #e0e0e0;
  }

  .preview-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333;
  }

  .preview-info {
    margin-bottom: 20px;
    padding: 12px;
    background: #f5f5f5;
    border-radius: 6px;
  }

  .info-item {
    font-size: 13px;
    color: #666;
    margin-bottom: 6px;
  }

  .info-item:last-child {
    margin-bottom: 0;
  }

  .info-item strong {
    color: #333;
  }

  .preview-section {
    margin-bottom: 24px;
  }

  .preview-section h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #555;
  }

  .variables-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .variable-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background: #f5f5f5;
    border-radius: 4px;
    font-size: 13px;
  }

  .variable-item code {
    padding: 2px 6px;
    background: #333;
    color: #fff;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
  }

  .variable-item span {
    color: #666;
  }

  .preview-content {
    padding: 16px;
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    overflow-x: auto;
  }

  .preview-content pre {
    margin: 0;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #333;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .empty-state,
  .loading,
  .empty-preview {
    padding: 40px 20px;
    text-align: center;
    color: #888;
    font-size: 14px;
  }

  .empty-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }

  /* Button styles */
  .btn-primary,
  .btn-secondary {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-primary {
    background: #007aff;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0056cc;
  }

  .btn-primary:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: #f5f5f5;
    color: #333;
    border: 1px solid #d0d0d0;
  }

  .btn-secondary:hover {
    background: #e0e0e0;
  }
</style>
