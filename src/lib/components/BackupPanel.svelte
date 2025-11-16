<script>
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from 'svelte';

  // Reactive state using Svelte 5 runes
  let backupSettings = $state(null);
  let backupStatus = $state(null);
  let backupHistory = $state([]);
  let isCreatingBackup = $state(false);
  let isLoading = $state(true);
  let showRestoreConfirmation = $state(false);
  let selectedBackupForRestore = $state(null);

  // Format file size to human-readable format
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  // Format date to readable format
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Calculate time ago
  const timeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    const weeks = Math.floor(days / 7);
    return `${weeks}w ago`;
  };

  // Load backup data
  async function loadBackupData() {
    try {
      isLoading = true;

      // Load settings and status in parallel
      const [settings, status, history] = await Promise.all([
        invoke('get_backup_settings'),
        invoke('get_backup_status'),
        invoke('list_backup_history', { limit: 50 })
      ]);

      backupSettings = settings;
      backupStatus = status;
      backupHistory = history;
    } catch (error) {
      console.error('Failed to load backup data:', error);
      showToast(`Failed to load backup settings: ${error}`, 'error');
    } finally {
      isLoading = false;
    }
  }

  // Create manual backup
  async function createManualBackup() {
    isCreatingBackup = true;
    try {
      const result = await invoke('create_backup');
      showToast(`Backup created successfully: ${result.file_name}`, 'success');
      await loadBackupData(); // Reload data
    } catch (error) {
      console.error('Backup creation failed:', error);
      showToast(`Backup failed: ${error}`, 'error');
    } finally {
      isCreatingBackup = false;
    }
  }

  // Delete backup
  async function deleteBackup(backupPath, backupName) {
    if (!confirm(`Delete backup "${backupName}"? This cannot be undone.`)) {
      return;
    }

    try {
      await invoke('delete_backup', { backupPath });
      showToast('Backup deleted successfully', 'success');
      await loadBackupData();
    } catch (error) {
      console.error('Failed to delete backup:', error);
      showToast(`Failed to delete backup: ${error}`, 'error');
    }
  }

  // Show restore confirmation
  function confirmRestore(backup) {
    selectedBackupForRestore = backup;
    showRestoreConfirmation = true;
  }

  // Restore backup
  async function restoreBackup() {
    if (!selectedBackupForRestore) return;

    try {
      const result = await invoke('restore_backup', {
        backupPath: selectedBackupForRestore.file_path
      });
      showToast(result, 'success');
      showRestoreConfirmation = false;
      selectedBackupForRestore = null;

      // Note: App needs restart after restore
      setTimeout(() => {
        alert('Database restored. Please restart the application to see the changes.');
      }, 1000);
    } catch (error) {
      console.error('Failed to restore backup:', error);
      showToast(`Restore failed: ${error}`, 'error');
    }
  }

  // Cancel restore
  function cancelRestore() {
    showRestoreConfirmation = false;
    selectedBackupForRestore = null;
  }

  // Update backup settings
  async function updateSettings() {
    try {
      await invoke('update_backup_settings', { settings: backupSettings });
      showToast('Backup settings updated successfully', 'success');
      await loadBackupData();
    } catch (error) {
      console.error('Failed to update settings:', error);
      showToast(`Failed to update settings: ${error}`, 'error');
    }
  }

  // Simple toast notification (implement or use existing toast system)
  function showToast(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // TODO: Integrate with existing toast system if available
  }

  // Load data on mount
  onMount(() => {
    loadBackupData();
  });
</script>

<div class="backup-panel">
  <h2>Database Backup</h2>

  {#if isLoading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading backup settings...</p>
    </div>
  {:else}
    <!-- Backup Status -->
    <div class="backup-status" class:overdue={backupStatus?.is_overdue}>
      <div class="status-header">
        <h3>Backup Status</h3>
        <span class="status-badge" class:healthy={!backupStatus?.is_overdue} class:overdue={backupStatus?.is_overdue}>
          {backupStatus?.is_overdue ? 'Overdue' : 'Healthy'}
        </span>
      </div>

      <div class="status-grid">
        <div class="status-item">
          <span class="label">Last Backup:</span>
          <span class="value">
            {backupStatus?.last_backup_at ? timeAgo(backupStatus.last_backup_at) : 'Never'}
          </span>
        </div>
        <div class="status-item">
          <span class="label">Total Backups:</span>
          <span class="value">{backupStatus?.total_backups || 0}</span>
        </div>
        <div class="status-item">
          <span class="label">Total Size:</span>
          <span class="value">{formatFileSize(backupStatus?.total_backup_size_bytes || 0)}</span>
        </div>
        <div class="status-item">
          <span class="label">Next Backup:</span>
          <span class="value">
            {backupStatus?.next_backup_due ? timeAgo(backupStatus.next_backup_due) : 'Manual only'}
          </span>
        </div>
      </div>
    </div>

    <!-- Backup Settings -->
    <div class="backup-settings">
      <h3>Backup Settings</h3>

      <div class="form-group">
        <label>
          <input
            type="checkbox"
            bind:checked={backupSettings.enabled}
            onchange={updateSettings}
          />
          Enable automatic backups
        </label>
      </div>

      <div class="form-group">
        <label for="frequency">Backup Frequency:</label>
        <select
          id="frequency"
          bind:value={backupSettings.frequency}
          onchange={updateSettings}
          disabled={!backupSettings.enabled}
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="manual">Manual only</option>
        </select>
      </div>

      <div class="form-group">
        <label for="retention">Keep Last N Backups:</label>
        <input
          id="retention"
          type="number"
          min="1"
          max="100"
          bind:value={backupSettings.retention_count}
          onchange={updateSettings}
        />
      </div>

      <div class="form-group">
        <label for="backup-path">Backup Location:</label>
        <input
          id="backup-path"
          type="text"
          bind:value={backupSettings.backup_path}
          onchange={updateSettings}
          readonly
        />
        <small>Backups are stored in: {backupSettings.backup_path}</small>
      </div>
    </div>

    <!-- Manual Backup -->
    <div class="manual-backup">
      <button
        class="btn-primary"
        onclick={createManualBackup}
        disabled={isCreatingBackup}
      >
        {isCreatingBackup ? 'Creating Backup...' : 'Create Backup Now'}
      </button>
    </div>

    <!-- Backup History -->
    <div class="backup-history">
      <h3>Backup History</h3>

      {#if backupHistory.length === 0}
        <p class="no-backups">No backups found. Create your first backup above.</p>
      {:else}
        <div class="backup-list">
          {#each backupHistory as backup (backup.id)}
            <div class="backup-item">
              <div class="backup-info">
                <div class="backup-name">
                  {backup.file_path.split('/').pop()}
                  {#if backup.is_automatic}
                    <span class="badge auto">Auto</span>
                  {:else}
                    <span class="badge manual">Manual</span>
                  {/if}
                </div>
                <div class="backup-meta">
                  <span>{formatDate(backup.created_at)}</span>
                  <span>•</span>
                  <span>{formatFileSize(backup.file_size_bytes)}</span>
                </div>
              </div>

              <div class="backup-actions">
                <button
                  class="btn-restore"
                  onclick={() => confirmRestore(backup)}
                  title="Restore this backup"
                >
                  Restore
                </button>
                <button
                  class="btn-delete"
                  onclick={() => deleteBackup(backup.file_path, backup.file_path.split('/').pop())}
                  title="Delete this backup"
                >
                  Delete
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Restore Confirmation Modal -->
  {#if showRestoreConfirmation}
    <div class="modal-overlay" onclick={cancelRestore}>
      <div class="modal-content" onclick={(e) => e.stopPropagation()}>
        <h3>Confirm Restore</h3>
        <p>
          Are you sure you want to restore from this backup?
        </p>
        <p class="warning">
          <strong>Warning:</strong> This will replace your current database with the backup.
          The current database will be saved as a safety backup before restoring.
        </p>
        {#if selectedBackupForRestore}
          <div class="restore-details">
            <div><strong>Backup:</strong> {selectedBackupForRestore.file_path.split('/').pop()}</div>
            <div><strong>Created:</strong> {formatDate(selectedBackupForRestore.created_at)}</div>
            <div><strong>Size:</strong> {formatFileSize(selectedBackupForRestore.file_size_bytes)}</div>
          </div>
        {/if}
        <div class="modal-actions">
          <button class="btn-secondary" onclick={cancelRestore}>Cancel</button>
          <button class="btn-danger" onclick={restoreBackup}>Restore Backup</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .backup-panel {
    padding: 20px;
    max-width: 800px;
  }

  h2 {
    margin-top: 0;
    color: #333;
  }

  h3 {
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: #555;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px;
  }

  .spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .backup-status {
    background: #f8f9fa;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
  }

  .backup-status.overdue {
    border-color: #f59e0b;
    background: #fffbeb;
  }

  .status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }

  .status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .status-badge.healthy {
    background: #d1fae5;
    color: #065f46;
  }

  .status-badge.overdue {
    background: #fed7aa;
    color: #92400e;
  }

  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
  }

  .status-item {
    display: flex;
    flex-direction: column;
  }

  .status-item .label {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 4px;
  }

  .status-item .value {
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
  }

  .backup-settings {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    color: #374151;
  }

  .form-group input[type="checkbox"] {
    margin-right: 8px;
  }

  .form-group input[type="number"],
  .form-group input[type="text"],
  .form-group select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
  }

  .form-group small {
    display: block;
    margin-top: 5px;
    color: #6b7280;
    font-size: 0.875rem;
  }

  .manual-backup {
    margin-bottom: 30px;
  }

  .btn-primary {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-primary:hover:not(:disabled) {
    background: #2563eb;
  }

  .btn-primary:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .backup-history {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
  }

  .no-backups {
    text-align: center;
    color: #6b7280;
    padding: 20px;
  }

  .backup-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .backup-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    transition: background 0.2s;
  }

  .backup-item:hover {
    background: #f9fafb;
  }

  .backup-info {
    flex: 1;
  }

  .backup-name {
    font-weight: 600;
    color: #111827;
    margin-bottom: 4px;
  }

  .backup-meta {
    font-size: 0.875rem;
    color: #6b7280;
  }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 8px;
  }

  .badge.auto {
    background: #dbeafe;
    color: #1e40af;
  }

  .badge.manual {
    background: #e0e7ff;
    color: #4338ca;
  }

  .backup-actions {
    display: flex;
    gap: 8px;
  }

  .btn-restore,
  .btn-delete {
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-restore {
    background: #10b981;
    color: white;
    border: none;
  }

  .btn-restore:hover {
    background: #059669;
  }

  .btn-delete {
    background: white;
    color: #dc2626;
    border: 1px solid #dc2626;
  }

  .btn-delete:hover {
    background: #dc2626;
    color: white;
  }

  /* Modal styles */
  .modal-overlay {
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
  }

  .modal-content {
    background: white;
    padding: 24px;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
  }

  .modal-content h3 {
    margin-top: 0;
  }

  .warning {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    padding: 12px;
    border-radius: 6px;
    margin: 16px 0;
  }

  .restore-details {
    background: #f3f4f6;
    padding: 12px;
    border-radius: 6px;
    margin: 16px 0;
  }

  .restore-details div {
    margin-bottom: 8px;
  }

  .restore-details div:last-child {
    margin-bottom: 0;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 20px;
  }

  .btn-secondary,
  .btn-danger {
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-secondary {
    background: white;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .btn-secondary:hover {
    background: #f9fafb;
  }

  .btn-danger {
    background: #dc2626;
    color: white;
    border: none;
  }

  .btn-danger:hover {
    background: #b91c1c;
  }
</style>
