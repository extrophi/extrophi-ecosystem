<script>
/**
 * Real-time Scraping Dashboard Component
 *
 * Displays live scraping progress via WebSocket connection.
 *
 * Features:
 * - Real-time progress updates
 * - Live content previews
 * - Success/error counts
 * - Platform breakdown
 * - Job-specific or global view
 */

import { onMount, onDestroy } from 'svelte';

// Props (Svelte 5 runes syntax)
let {
    apiUrl = 'ws://localhost:8000',
    jobId = $bindable(),
    autoConnect = true
} = $props();

// State (Svelte 5 runes syntax)
let connected = $state(false);
let activeJobs = $state([]);
let platformStats = $state({});
let recentPreviews = $state([]);
let errorMessage = $state(null);

// Derived state
let totalItemsScraped = $derived(
    Object.values(platformStats).reduce((sum, stats) => sum + (stats.total_items || 0), 0)
);

let totalSuccessCount = $derived(
    Object.values(platformStats).reduce((sum, stats) => sum + (stats.success_count || 0), 0)
);

let totalErrorCount = $derived(
    Object.values(platformStats).reduce((sum, stats) => sum + (stats.error_count || 0), 0)
);

// WebSocket connection
let ws;

onMount(() => {
    if (autoConnect) {
        connect();
    }
});

onDestroy(() => {
    disconnect();
});

function connect() {
    const endpoint = jobId
        ? `${apiUrl}/ws/scraping/${jobId}`
        : `${apiUrl}/ws/scraping`;

    try {
        ws = new WebSocket(endpoint);

        ws.onopen = () => {
            connected = true;
            errorMessage = null;
            console.log('WebSocket connected:', endpoint);
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            handleMessage(message);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            errorMessage = 'WebSocket connection error';
            connected = false;
        };

        ws.onclose = () => {
            connected = false;
            console.log('WebSocket disconnected');

            // Auto-reconnect after 3 seconds
            setTimeout(() => {
                if (autoConnect) {
                    connect();
                }
            }, 3000);
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        errorMessage = `Connection failed: ${error.message}`;
    }
}

function disconnect() {
    if (ws) {
        ws.close();
        ws = null;
    }
    connected = false;
}

function handleMessage(message) {
    const { type, data, timestamp } = message;

    switch (type) {
        case 'initial_state':
            // Set initial state from server
            if (data.active_jobs) {
                activeJobs = Object.values(data.active_jobs);
            }
            if (data.platform_stats) {
                platformStats = data.platform_stats;
            }
            break;

        case 'progress':
            // Update job progress
            updateJobProgress(data);
            break;

        case 'item_preview':
            // Add item preview
            addItemPreview(data);
            break;

        case 'job_complete':
            // Mark job as complete
            removeActiveJob(data.job_id);
            break;

        case 'job_error':
            // Handle job error
            updateJobError(data);
            break;

        case 'stats':
            // Update platform stats
            if (data.platform_stats) {
                platformStats = data.platform_stats;
            }
            if (data.active_jobs) {
                activeJobs = Object.values(data.active_jobs);
            }
            break;

        default:
            console.log('Unknown message type:', type, data);
    }
}

function updateJobProgress(data) {
    const index = activeJobs.findIndex(job => job.job_id === data.job_id);

    if (index >= 0) {
        activeJobs[index] = data;
    } else {
        activeJobs = [...activeJobs, data];
    }
}

function addItemPreview(data) {
    recentPreviews = [
        { ...data, timestamp: new Date() },
        ...recentPreviews.slice(0, 19) // Keep last 20 previews
    ];
}

function removeActiveJob(jobId) {
    activeJobs = activeJobs.filter(job => job.job_id !== jobId);
}

function updateJobError(data) {
    const index = activeJobs.findIndex(job => job.job_id === data.job_id);

    if (index >= 0) {
        activeJobs[index] = {
            ...activeJobs[index],
            status: 'failed',
            error_message: data.error_message
        };
    }
}

function formatElapsedTime(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
}

function getProgressPercentage(job) {
    if (!job.items_total) return 0;
    return Math.min(100, (job.items_scraped / job.items_total) * 100);
}
</script>

<div class="scraping-dashboard">
    <!-- Connection Status -->
    <div class="status-bar" class:connected class:disconnected={!connected}>
        <span class="status-indicator"></span>
        {#if connected}
            Connected to scraping stream
        {:else if errorMessage}
            {errorMessage}
        {:else}
            Disconnected - reconnecting...
        {/if}
    </div>

    <!-- Overall Statistics -->
    <div class="stats-overview">
        <div class="stat-card">
            <h3>Total Items</h3>
            <div class="stat-value">{totalItemsScraped}</div>
        </div>
        <div class="stat-card success">
            <h3>Success</h3>
            <div class="stat-value">{totalSuccessCount}</div>
        </div>
        <div class="stat-card error">
            <h3>Errors</h3>
            <div class="stat-value">{totalErrorCount}</div>
        </div>
        <div class="stat-card">
            <h3>Active Jobs</h3>
            <div class="stat-value">{activeJobs.length}</div>
        </div>
    </div>

    <!-- Platform Breakdown -->
    {#if Object.keys(platformStats).length > 0}
        <section class="platform-breakdown">
            <h2>Platform Breakdown</h2>
            <div class="platform-grid">
                {#each Object.entries(platformStats) as [platform, stats]}
                    <div class="platform-card">
                        <h4>{platform}</h4>
                        <div class="platform-stats">
                            <div>Items: <strong>{stats.total_items}</strong></div>
                            <div>Success: <strong class="success">{stats.success_count}</strong></div>
                            <div>Errors: <strong class="error">{stats.error_count}</strong></div>
                            <div>Avg Time: <strong>{stats.avg_processing_time?.toFixed(2)}s</strong></div>
                        </div>
                    </div>
                {/each}
            </div>
        </section>
    {/if}

    <!-- Active Jobs -->
    {#if activeJobs.length > 0}
        <section class="active-jobs">
            <h2>Active Jobs ({activeJobs.length})</h2>
            {#each activeJobs as job (job.job_id)}
                <div class="job-card" class:error={job.status === 'failed'}>
                    <div class="job-header">
                        <h3>{job.platform}</h3>
                        <span class="job-status status-{job.status}">{job.status}</span>
                    </div>

                    <div class="job-progress">
                        <div class="progress-bar">
                            <div
                                class="progress-fill"
                                style="width: {getProgressPercentage(job)}%"
                            ></div>
                        </div>
                        <div class="progress-text">
                            {job.items_scraped} / {job.items_total || '?'} items
                            ({getProgressPercentage(job).toFixed(0)}%)
                        </div>
                    </div>

                    <div class="job-stats">
                        <span class="success">✓ {job.success_count}</span>
                        <span class="error">✗ {job.error_count}</span>
                        <span class="elapsed">⏱ {formatElapsedTime(job.elapsed_seconds)}</span>
                    </div>

                    {#if job.error_message}
                        <div class="error-message">
                            Error: {job.error_message}
                        </div>
                    {/if}
                </div>
            {/each}
        </section>
    {/if}

    <!-- Recent Previews -->
    {#if recentPreviews.length > 0}
        <section class="recent-previews">
            <h2>Live Content Preview</h2>
            <div class="preview-list">
                {#each recentPreviews.slice(0, 10) as preview (preview.timestamp)}
                    <div class="preview-card">
                        <div class="preview-header">
                            <span class="preview-platform">{preview.platform}</span>
                            <span class="preview-time">
                                {new Date(preview.timestamp).toLocaleTimeString()}
                            </span>
                        </div>
                        <div class="preview-content">
                            <pre>{JSON.stringify(preview.item, null, 2)}</pre>
                        </div>
                    </div>
                {/each}
            </div>
        </section>
    {/if}
</div>

<style>
.scraping-dashboard {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.status-bar {
    padding: 12px 20px;
    border-radius: 8px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 500;
}

.status-bar.connected {
    background: #d4edda;
    color: #155724;
}

.status-bar.disconnected {
    background: #f8d7da;
    color: #721c24;
}

.status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
}

.stat-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.stat-card h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 500;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stat-value {
    font-size: 36px;
    font-weight: 700;
    color: #333;
}

.stat-card.success .stat-value {
    color: #28a745;
}

.stat-card.error .stat-value {
    color: #dc3545;
}

.platform-breakdown, .active-jobs, .recent-previews {
    margin-bottom: 32px;
}

h2 {
    margin: 0 0 16px 0;
    font-size: 20px;
    font-weight: 600;
}

.platform-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
}

.platform-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
}

.platform-card h4 {
    margin: 0 0 12px 0;
    text-transform: capitalize;
    color: #333;
}

.platform-stats {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 14px;
    color: #666;
}

.success {
    color: #28a745;
}

.error {
    color: #dc3545;
}

.job-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
}

.job-card.error {
    border-color: #dc3545;
    background: #fff5f5;
}

.job-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.job-header h3 {
    margin: 0;
    text-transform: capitalize;
}

.job-status {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.status-started, .status-processing {
    background: #cfe2ff;
    color: #084298;
}

.status-completed {
    background: #d1e7dd;
    color: #0f5132;
}

.status-failed {
    background: #f8d7da;
    color: #842029;
}

.job-progress {
    margin-bottom: 12px;
}

.progress-bar {
    width: 100%;
    height: 24px;
    background: #e9ecef;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 8px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #0d6efd, #0a58ca);
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 14px;
    color: #666;
}

.job-stats {
    display: flex;
    gap: 20px;
    font-size: 14px;
    font-weight: 500;
}

.error-message {
    margin-top: 12px;
    padding: 12px;
    background: #f8d7da;
    border-radius: 6px;
    color: #842029;
    font-size: 14px;
}

.preview-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.preview-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
}

.preview-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
    font-size: 14px;
}

.preview-platform {
    font-weight: 600;
    text-transform: capitalize;
}

.preview-time {
    color: #666;
}

.preview-content pre {
    margin: 0;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    font-size: 12px;
    overflow-x: auto;
    max-height: 200px;
    overflow-y: auto;
}
</style>
