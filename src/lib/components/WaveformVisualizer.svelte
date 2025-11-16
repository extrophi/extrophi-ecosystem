<script>
  import { onMount, onDestroy } from 'svelte';

  let { level = 0, visible = false, width = 300, height = 60 } = $props();

  let canvas;
  let waveformData = [];
  let animationFrameId = null;
  const maxDataPoints = 150;

  // Add new level data point
  $effect(() => {
    if (visible && level !== undefined) {
      waveformData.push(level);
      if (waveformData.length > maxDataPoints) {
        waveformData.shift();
      }
    }
  });

  // Animation loop for smooth rendering
  function animate() {
    drawWaveform();
    animationFrameId = requestAnimationFrame(animate);
  }

  function drawWaveform() {
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    // Set canvas size accounting for device pixel ratio
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    if (waveformData.length === 0) return;

    const centerY = height / 2;
    const pointSpacing = width / maxDataPoints;

    // Draw background grid
    ctx.strokeStyle = 'rgba(200, 200, 200, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();

    // Draw waveform
    ctx.strokeStyle = '#4A90E2';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Create gradient for waveform
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, 'rgba(74, 144, 226, 0.3)');
    gradient.addColorStop(0.5, 'rgba(92, 189, 185, 0.8)');
    gradient.addColorStop(1, 'rgba(74, 144, 226, 1)');
    ctx.strokeStyle = gradient;

    // Draw top wave
    ctx.beginPath();
    waveformData.forEach((level, i) => {
      const x = i * pointSpacing;
      const amplitude = level * (height / 2) * 0.8; // 80% of half height
      const y = centerY - amplitude;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw bottom wave (mirror)
    ctx.beginPath();
    waveformData.forEach((level, i) => {
      const x = i * pointSpacing;
      const amplitude = level * (height / 2) * 0.8;
      const y = centerY + amplitude;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw fill between waves
    ctx.fillStyle = 'rgba(74, 144, 226, 0.1)';
    ctx.beginPath();

    // Top wave
    waveformData.forEach((level, i) => {
      const x = i * pointSpacing;
      const amplitude = level * (height / 2) * 0.8;
      const y = centerY - amplitude;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    // Bottom wave (reverse order)
    for (let i = waveformData.length - 1; i >= 0; i--) {
      const level = waveformData[i];
      const x = i * pointSpacing;
      const amplitude = level * (height / 2) * 0.8;
      const y = centerY + amplitude;
      ctx.lineTo(x, y);
    }

    ctx.closePath();
    ctx.fill();
  }

  onMount(() => {
    if (visible) {
      animationFrameId = requestAnimationFrame(animate);
    }
  });

  onDestroy(() => {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
  });

  // Start/stop animation based on visibility
  $effect(() => {
    if (visible && !animationFrameId) {
      animationFrameId = requestAnimationFrame(animate);
    } else if (!visible && animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
      waveformData = []; // Clear data when hidden
    }
  });
</script>

{#if visible}
  <div class="waveform-container">
    <canvas
      bind:this={canvas}
      style="width: {width}px; height: {height}px;"
      aria-label="Audio waveform visualization"
    ></canvas>
  </div>
{/if}

<style>
  .waveform-container {
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fafafa;
    border-radius: 8px;
    padding: 8px;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  canvas {
    display: block;
    border-radius: 4px;
  }
</style>
