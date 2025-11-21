<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';
  import { save } from '@tauri-apps/api/dialog';

  let { sessionIds = [], onClose = () => {} } = $props();

  let selectedFormat = $state('pdf');
  let includeMetadata = $state(true);
  let includeChat = $state(true);
  let customTemplate = $state('');
  let exporting = $state(false);
  let errorMessage = $state('');

  async function handleExport() {
    exporting = true;
    errorMessage = '';

    try {
      if (sessionIds.length === 1) {
        // Single export
        const extensions = {
          pdf: ['pdf'],
          docx: ['docx'],
          html: ['html'],
          markdown: ['md']
        };

        const filePath = await save({
          filters: [{
            name: selectedFormat.toUpperCase(),
            extensions: extensions[selectedFormat as keyof typeof extensions]
          }]
        });

        if (filePath) {
          await invokeExport(sessionIds[0], filePath);
        }
      } else {
        // Batch export
        const filePath = await save({
          filters: [{ name: 'ZIP', extensions: ['zip'] }]
        });

        if (filePath) {
          await invoke('export_batch', {
            sessionIds,
            outputZip: filePath,
            format: selectedFormat
          });
        }
      }

      onClose();
    } catch (e) {
      console.error('Export failed:', e);
      errorMessage = String(e);
    } finally {
      exporting = false;
    }
  }

  async function invokeExport(sessionId: number, path: string) {
    switch (selectedFormat) {
      case 'pdf':
        await invoke('export_session_pdf', { sessionId, outputPath: path });
        break;
      case 'docx':
        await invoke('export_session_docx', { sessionId, outputPath: path });
        break;
      case 'html':
        await invoke('export_session_html', {
          sessionId,
          outputPath: path,
          template: customTemplate || null
        });
        break;
      case 'markdown':
        await invoke('export_session', { sessionId });
        break;
    }
  }
</script>

<div class="export-dialog-overlay" onclick={onClose}>
  <div class="export-dialog" onclick={(e) => e.stopPropagation()}>
    <div class="dialog-header">
      <h2>Export {sessionIds.length} Session{sessionIds.length > 1 ? 's' : ''}</h2>
      <button class="close-button" onclick={onClose} aria-label="Close">×</button>
    </div>

    <div class="dialog-content">
      <div class="format-selector">
        <h3>Export Format</h3>
        <div class="format-options">
          <label class="format-option">
            <input type="radio" bind:group={selectedFormat} value="pdf" />
            <div class="format-label">
              <span class="format-icon">📄</span>
              <span>PDF</span>
            </div>
          </label>
          <label class="format-option">
            <input type="radio" bind:group={selectedFormat} value="docx" />
            <div class="format-label">
              <span class="format-icon">📝</span>
              <span>Word (DOCX)</span>
            </div>
          </label>
          <label class="format-option">
            <input type="radio" bind:group={selectedFormat} value="html" />
            <div class="format-label">
              <span class="format-icon">🌐</span>
              <span>HTML</span>
            </div>
          </label>
          <label class="format-option">
            <input type="radio" bind:group={selectedFormat} value="markdown" />
            <div class="format-label">
              <span class="format-icon">📋</span>
              <span>Markdown</span>
            </div>
          </label>
        </div>
      </div>

      <div class="options-section">
        <h3>Export Options</h3>
        <label class="checkbox-option">
          <input type="checkbox" bind:checked={includeMetadata} />
          <span>Include metadata (creation date, message count)</span>
        </label>
        <label class="checkbox-option">
          <input type="checkbox" bind:checked={includeChat} />
          <span>Include AI chat history</span>
        </label>
      </div>

      {#if selectedFormat === 'html'}
        <div class="template-section">
          <h3>HTML Template</h3>
          <label>
            <span>Custom template name (optional):</span>
            <input
              type="text"
              bind:value={customTemplate}
              placeholder="session (default)"
              class="template-input"
            />
          </label>
          <p class="template-hint">Leave empty to use the default template</p>
        </div>
      {/if}

      {#if errorMessage}
        <div class="error-message">
          <strong>Export Error:</strong> {errorMessage}
        </div>
      {/if}
    </div>

    <div class="dialog-actions">
      <button class="button button-secondary" onclick={onClose} disabled={exporting}>
        Cancel
      </button>
      <button class="button button-primary" onclick={handleExport} disabled={exporting}>
        {exporting ? 'Exporting...' : 'Export'}
      </button>
    </div>
  </div>
</div>

<style>
  .export-dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }

  .export-dialog {
    background: white;
    border-radius: 1rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #E5E7EB;
  }

  .dialog-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #111827;
  }

  .close-button {
    background: none;
    border: none;
    font-size: 2rem;
    line-height: 1;
    color: #6B7280;
    cursor: pointer;
    padding: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.5rem;
    transition: all 0.2s;
  }

  .close-button:hover {
    background: #F3F4F6;
    color: #111827;
  }

  .dialog-content {
    padding: 1.5rem;
  }

  .format-selector h3,
  .options-section h3,
  .template-section h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
  }

  .format-options {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .format-option {
    display: block;
    cursor: pointer;
  }

  .format-option input[type="radio"] {
    position: absolute;
    opacity: 0;
  }

  .format-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border: 2px solid #E5E7EB;
    border-radius: 0.5rem;
    transition: all 0.2s;
    background: white;
  }

  .format-option input[type="radio"]:checked + .format-label {
    border-color: #4F46E5;
    background: #EEF2FF;
  }

  .format-option:hover .format-label {
    border-color: #C7D2FE;
  }

  .format-icon {
    font-size: 1.5rem;
  }

  .format-label span:last-child {
    font-weight: 500;
    color: #1F2937;
  }

  .options-section {
    margin-bottom: 1.5rem;
  }

  .checkbox-option {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 0;
    cursor: pointer;
  }

  .checkbox-option input[type="checkbox"] {
    width: 1.25rem;
    height: 1.25rem;
    cursor: pointer;
    accent-color: #4F46E5;
  }

  .checkbox-option span {
    color: #374151;
  }

  .template-section {
    margin-bottom: 1.5rem;
  }

  .template-section label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .template-section label span {
    font-weight: 500;
    color: #374151;
    font-size: 0.875rem;
  }

  .template-input {
    padding: 0.75rem;
    border: 1px solid #D1D5DB;
    border-radius: 0.5rem;
    font-size: 1rem;
    transition: all 0.2s;
  }

  .template-input:focus {
    outline: none;
    border-color: #4F46E5;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  }

  .template-hint {
    margin: 0.5rem 0 0 0;
    font-size: 0.875rem;
    color: #6B7280;
  }

  .error-message {
    padding: 1rem;
    background: #FEE2E2;
    border: 1px solid #FCA5A5;
    border-radius: 0.5rem;
    color: #991B1B;
    margin-top: 1rem;
  }

  .error-message strong {
    display: block;
    margin-bottom: 0.25rem;
  }

  .dialog-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
    padding: 1.5rem;
    border-top: 1px solid #E5E7EB;
  }

  .button {
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    border: none;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .button-secondary {
    background: white;
    color: #374151;
    border: 1px solid #D1D5DB;
  }

  .button-secondary:hover:not(:disabled) {
    background: #F9FAFB;
  }

  .button-primary {
    background: #4F46E5;
    color: white;
  }

  .button-primary:hover:not(:disabled) {
    background: #4338CA;
  }

  @media (max-width: 640px) {
    .export-dialog {
      width: 95%;
      max-height: 95vh;
    }

    .format-options {
      grid-template-columns: 1fr;
    }

    .dialog-header {
      padding: 1rem;
    }

    .dialog-content {
      padding: 1rem;
    }

    .dialog-actions {
      padding: 1rem;
      flex-direction: column;
    }

    .button {
      width: 100%;
    }
  }
</style>
