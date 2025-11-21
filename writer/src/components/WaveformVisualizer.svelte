<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import WaveSurfer from 'wavesurfer.js';

  let { audioStream = $bindable(null), isRecording = false, peakLevel = 0 } = $props();

  let waveformContainer = $state<HTMLDivElement>();
  let wavesurfer = $state<WaveSurfer | null>(null);
  let canvasRef = $state<HTMLCanvasElement>();
  let animationId = $state<number | null>(null);

  onMount(() => {
    // Initialize canvas for real-time waveform during recording
    if (canvasRef) {
      const ctx = canvasRef.getContext('2d');
      if (ctx) {
        // Set canvas dimensions
        canvasRef.width = canvasRef.offsetWidth;
        canvasRef.height = 80;
      }
    }
  });

  // Real-time waveform visualization during recording
  $effect(() => {
    if (isRecording && canvasRef && peakLevel !== undefined) {
      updateWaveform(peakLevel);
    }
  });

  function updateWaveform(level: number) {
    if (!canvasRef) return;

    const canvas = canvasRef;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Scroll existing waveform to the left
    const imageData = ctx.getImageData(1, 0, canvas.width - 1, canvas.height);
    ctx.putImageData(imageData, 0, 0);

    // Draw new bar on the right
    const barHeight = level * canvas.height;
    const x = canvas.width - 1;
    const y = (canvas.height - barHeight) / 2;

    // Clear the rightmost column
    ctx.fillStyle = '#1F2937';
    ctx.fillRect(x, 0, 1, canvas.height);

    // Draw the new bar with gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#4F46E5');
    gradient.addColorStop(0.5, '#818CF8');
    gradient.addColorStop(1, '#4F46E5');

    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, 1, barHeight);
  }

  function clearWaveform() {
    if (!canvasRef) return;

    const canvas = canvasRef;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#1F2937';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  // Clear waveform when recording stops
  $effect(() => {
    if (!isRecording) {
      clearWaveform();
    }
  });

  onDestroy(() => {
    wavesurfer?.destroy();
    if (animationId) {
      cancelAnimationFrame(animationId);
    }
  });
</script>

<div class="waveform-container">
  <div class="waveform-label">Audio Waveform</div>
  <canvas bind:this={canvasRef} class="waveform-canvas"></canvas>
</div>

<style>
  .waveform-container {
    width: 100%;
    padding: 1rem;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 0.5rem;
    border: 1px solid #e0e0e0;
  }

  .waveform-label {
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-secondary, #666666);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .waveform-canvas {
    width: 100%;
    height: 80px;
    border-radius: 4px;
    background: #1F2937;
  }
</style>
