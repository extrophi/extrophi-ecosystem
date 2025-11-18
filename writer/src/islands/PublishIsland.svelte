<script lang="ts">
  /**
   * Git Publish Island - One-click sync for BUSINESS + IDEAS cards
   * Privacy Filter: PRIVATE and PERSONAL cards stay local only
   */
  import { invoke } from '@tauri-apps/api/core';
  import { homeDir } from '@tauri-apps/api/path';

  // Props
  let {
    onPublishComplete = null,
  }: {
    onPublishComplete?: (() => void) | null;
  } = $props();

  // State
  let repoPath = $state<string>('');
  let publishableCount = $state<number>(0);
  let publishedCount = $state<number>(0);
  let lastPublishAt = $state<string | null>(null);
  let lastCommitSha = $state<string | null>(null);
  let isPublishing = $state<boolean>(false);
  let isLoading = $state<boolean>(false);
  let error = $state<string | null>(null);
  let commitMessage = $state<string>('Update published cards');
  let shouldPush = $state<boolean>(false);
  let remoteName = $state<string>('origin');
  let branch = $state<string>('main');

  interface PublishStatus {
    publishable_count: number;
    published_count: number;
    last_publish_at: string | null;
    last_commit_sha: string | null;
  }

  interface PublishResult {
    cards_published: number;
    commit_sha: string;
    pushed: boolean;
    timestamp: string;
  }

  /**
   * Load initial repo path
   */
  async function loadRepoPath() {
    try {
      const home = await homeDir();
      repoPath = `${home}.braindump-publish`;
    } catch (err) {
      console.error('Failed to get home directory:', err);
      repoPath = '';
    }
  }

  /**
   * Initialize repository
   */
  async function initializeRepository() {
    if (!repoPath) {
      error = 'Please set a repository path';
      return;
    }

    isLoading = true;
    error = null;

    try {
      await invoke('git_init_repository', { repoPath });
      await loadStatus();
    } catch (err) {
      error = `Failed to initialize repository: ${err}`;
      console.error('Initialize error:', err);
    } finally {
      isLoading = false;
    }
  }

  /**
   * Load publish status
   */
  async function loadStatus() {
    if (!repoPath) return;

    isLoading = true;
    error = null;

    try {
      const status = await invoke<PublishStatus>('git_get_publish_status', {
        repoPath,
      });

      publishableCount = status.publishable_count;
      publishedCount = status.published_count;
      lastPublishAt = status.last_publish_at;
      lastCommitSha = status.last_commit_sha;
    } catch (err) {
      error = `Failed to load status: ${err}`;
      console.error('Load status error:', err);
    } finally {
      isLoading = false;
    }
  }

  /**
   * Publish cards to Git
   */
  async function publishCards() {
    if (!repoPath) {
      error = 'Please set a repository path';
      return;
    }

    if (publishableCount === 0) {
      error = 'No publishable cards found';
      return;
    }

    isPublishing = true;
    error = null;

    try {
      const result = await invoke<PublishResult>('git_publish_cards', {
        repoPath,
        commitMessage,
        shouldPush,
        remoteName,
        branch,
      });

      // Update status
      lastCommitSha = result.commit_sha;
      lastPublishAt = result.timestamp;

      // Show success
      if (result.pushed) {
        error = null;
        console.log(`Published ${result.cards_published} cards and pushed to remote`);
      } else {
        error = null;
        console.log(`Published ${result.cards_published} cards (not pushed)`);
      }

      // Reload status
      await loadStatus();

      // Call callback
      if (onPublishComplete) {
        onPublishComplete();
      }
    } catch (err) {
      error = `Failed to publish: ${err}`;
      console.error('Publish error:', err);
    } finally {
      isPublishing = false;
    }
  }

  /**
   * Format timestamp
   */
  function formatTimestamp(timestamp: string | null): string {
    if (!timestamp) return 'Never';

    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return 'Invalid date';
    }
  }

  /**
   * Truncate commit SHA
   */
  function truncateSha(sha: string | null): string {
    if (!sha) return 'N/A';
    return sha.substring(0, 8);
  }

  // Load on mount
  $effect(() => {
    loadRepoPath();
  });

  // Auto-load status when repo path changes
  $effect(() => {
    if (repoPath) {
      loadStatus();
    }
  });
</script>

<div class="publish-island">
  <div class="header">
    <h2>Git Publish</h2>
    <p class="subtitle">Sync BUSINESS + IDEAS cards (PRIVATE/PERSONAL stay local)</p>
  </div>

  <!-- Configuration -->
  <div class="config-section">
    <div class="form-group">
      <label for="repo-path">Repository Path</label>
      <div class="input-with-button">
        <input
          id="repo-path"
          type="text"
          bind:value={repoPath}
          placeholder="e.g., /Users/you/.braindump-publish"
          disabled={isPublishing || isLoading}
        />
        <button
          type="button"
          onclick={initializeRepository}
          disabled={isPublishing || isLoading || !repoPath}
          class="btn-secondary"
        >
          {#if isLoading}
            Initializing...
          {:else}
            Init Repo
          {/if}
        </button>
      </div>
    </div>
  </div>

  <!-- Status Display -->
  <div class="status-section">
    <div class="status-grid">
      <div class="status-item">
        <span class="status-label">Publishable Cards</span>
        <span class="status-value">{publishableCount}</span>
      </div>
      <div class="status-item">
        <span class="status-label">Published Cards</span>
        <span class="status-value">{publishedCount}</span>
      </div>
      <div class="status-item">
        <span class="status-label">Last Publish</span>
        <span class="status-value">{formatTimestamp(lastPublishAt)}</span>
      </div>
      <div class="status-item">
        <span class="status-label">Commit SHA</span>
        <span class="status-value">{truncateSha(lastCommitSha)}</span>
      </div>
    </div>
  </div>

  <!-- Publish Options -->
  <div class="options-section">
    <div class="form-group">
      <label for="commit-message">Commit Message</label>
      <input
        id="commit-message"
        type="text"
        bind:value={commitMessage}
        placeholder="Update published cards"
        disabled={isPublishing || isLoading}
      />
    </div>

    <div class="checkbox-group">
      <label>
        <input
          type="checkbox"
          bind:checked={shouldPush}
          disabled={isPublishing || isLoading}
        />
        <span>Push to remote</span>
      </label>
    </div>

    {#if shouldPush}
      <div class="remote-config">
        <div class="form-group inline">
          <label for="remote-name">Remote</label>
          <input
            id="remote-name"
            type="text"
            bind:value={remoteName}
            placeholder="origin"
            disabled={isPublishing || isLoading}
          />
        </div>
        <div class="form-group inline">
          <label for="branch">Branch</label>
          <input
            id="branch"
            type="text"
            bind:value={branch}
            placeholder="main"
            disabled={isPublishing || isLoading}
          />
        </div>
      </div>
    {/if}
  </div>

  <!-- Error Display -->
  {#if error}
    <div class="error-message">
      {error}
    </div>
  {/if}

  <!-- Publish Button -->
  <div class="actions">
    <button
      type="button"
      onclick={publishCards}
      disabled={isPublishing || isLoading || publishableCount === 0 || !repoPath}
      class="btn-primary btn-publish"
    >
      {#if isPublishing}
        Publishing...
      {:else if publishableCount === 0}
        No Cards to Publish
      {:else}
        Publish {publishableCount} Card{publishableCount !== 1 ? 's' : ''}
      {/if}
    </button>

    <button
      type="button"
      onclick={loadStatus}
      disabled={isPublishing || isLoading || !repoPath}
      class="btn-secondary"
    >
      Refresh Status
    </button>
  </div>

  <!-- Privacy Notice -->
  <div class="privacy-notice">
    <strong>Privacy Filter Active:</strong>
    <ul>
      <li>✅ BUSINESS cards → Published</li>
      <li>✅ IDEAS cards → Published</li>
      <li>🔒 PRIVATE cards → Stay local only</li>
      <li>🔒 PERSONAL cards → Stay local only</li>
    </ul>
  </div>
</div>

<style>
  .publish-island {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 24px;
    margin: 16px 0;
  }

  .header {
    margin-bottom: 24px;
  }

  .header h2 {
    margin: 0 0 8px 0;
    font-size: 20px;
    font-weight: 600;
    color: #111827;
  }

  .subtitle {
    margin: 0;
    font-size: 14px;
    color: #6b7280;
  }

  .config-section,
  .status-section,
  .options-section {
    margin-bottom: 24px;
  }

  .form-group {
    margin-bottom: 16px;
  }

  .form-group label {
    display: block;
    margin-bottom: 8px;
    font-size: 14px;
    font-weight: 500;
    color: #374151;
  }

  .form-group input[type='text'] {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 14px;
  }

  .form-group input[type='text']:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }

  .input-with-button {
    display: flex;
    gap: 8px;
  }

  .input-with-button input {
    flex: 1;
  }

  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
  }

  .status-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .status-label {
    font-size: 12px;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 500;
  }

  .status-value {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
  }

  .checkbox-group {
    margin-bottom: 16px;
  }

  .checkbox-group label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #374151;
    cursor: pointer;
  }

  .checkbox-group input[type='checkbox'] {
    width: 16px;
    height: 16px;
    cursor: pointer;
  }

  .checkbox-group input[type='checkbox']:disabled {
    cursor: not-allowed;
  }

  .remote-config {
    display: flex;
    gap: 16px;
    margin-top: 12px;
  }

  .form-group.inline {
    flex: 1;
    margin-bottom: 0;
  }

  .form-group.inline input {
    width: 100%;
  }

  .error-message {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
    padding: 12px 16px;
    border-radius: 4px;
    margin-bottom: 16px;
    font-size: 14px;
  }

  .actions {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
  }

  .btn-primary,
  .btn-secondary {
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn-primary {
    background: #2563eb;
    color: white;
    flex: 1;
  }

  .btn-primary:hover:not(:disabled) {
    background: #1d4ed8;
  }

  .btn-primary:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #e5e7eb;
  }

  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .privacy-notice {
    background: #f0f9ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 16px;
  }

  .privacy-notice strong {
    display: block;
    margin-bottom: 8px;
    color: #1e40af;
    font-size: 14px;
  }

  .privacy-notice ul {
    margin: 0;
    padding-left: 20px;
    list-style: none;
  }

  .privacy-notice li {
    font-size: 13px;
    color: #1e40af;
    margin-bottom: 4px;
  }

  .privacy-notice li:last-child {
    margin-bottom: 0;
  }
</style>
