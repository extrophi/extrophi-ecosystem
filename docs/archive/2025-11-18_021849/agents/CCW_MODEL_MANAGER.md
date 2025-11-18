# CCW Agent Task: Whisper Model Manager + VAD

**Priority**: HIGH - Core Feature
**Estimated Effort**: 4-6 hours
**Credits to Burn**: Use these credits NOW

---

## Overview

Implement a complete Whisper model management system with:
1. Automatic base model download on first launch
2. Settings UI for model selection and download
3. Model quantization support (Q5_0)
4. Voice Activity Detection (VAD) preprocessing

---

## Task 1: Model Download Manager (Rust Backend)

### File: `src-tauri/src/services/model_manager.rs`

```rust
use std::path::PathBuf;
use tokio::fs;
use reqwest;

#[derive(Debug, Clone, serde::Serialize)]
pub struct WhisperModel {
    pub name: String,
    pub size_mb: u32,
    pub url: String,
    pub accuracy: String,
    pub speed: String,
}

pub const WHISPER_MODELS: &[WhisperModel] = &[
    WhisperModel {
        name: "tiny",
        size_mb: 39,
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
        accuracy: "~88%",
        speed: "Fastest",
    },
    WhisperModel {
        name: "base",
        size_mb: 141,
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
        accuracy: "~95%",
        speed: "Fast",
    },
    WhisperModel {
        name: "small",
        size_mb: 466,
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        accuracy: "~97%",
        speed: "Medium",
    },
    WhisperModel {
        name: "medium",
        size_mb: 1500,
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
        accuracy: "~98%",
        speed: "Slow",
    },
    WhisperModel {
        name: "large-v3-turbo",
        size_mb: 2900,
        url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin",
        accuracy: "~99.1%",
        speed: "8x faster than old Large",
    },
];

#[tauri::command]
pub async fn download_model(model_name: String, on_progress: tauri::Window) -> Result<String, String> {
    let model = WHISPER_MODELS.iter()
        .find(|m| m.name == model_name)
        .ok_or("Model not found")?;

    let models_dir = get_models_dir()?;
    let model_path = models_dir.join(format!("ggml-{}.bin", model_name));

    // Download with progress
    let client = reqwest::Client::new();
    let response = client.get(&model.url).send().await.map_err(|e| e.to_string())?;
    let total_size = response.content_length().unwrap_or(0);

    let mut downloaded = 0u64;
    let mut stream = response.bytes_stream();
    let mut file = fs::File::create(&model_path).await.map_err(|e| e.to_string())?;

    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| e.to_string())?;
        file.write_all(&chunk).await.map_err(|e| e.to_string())?;
        downloaded += chunk.len() as u64;

        let progress = (downloaded as f64 / total_size as f64) * 100.0;
        on_progress.emit("model-download-progress", progress).ok();
    }

    Ok(model_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn get_available_models() -> Vec<WhisperModel> {
    WHISPER_MODELS.to_vec()
}

#[tauri::command]
pub fn get_installed_models() -> Result<Vec<String>, String> {
    let models_dir = get_models_dir()?;
    let mut installed = vec![];

    for model in WHISPER_MODELS {
        let path = models_dir.join(format!("ggml-{}.bin", model.name));
        if path.exists() {
            installed.push(model.name.clone());
        }
    }

    Ok(installed)
}

#[tauri::command]
pub fn delete_model(model_name: String) -> Result<(), String> {
    let models_dir = get_models_dir()?;
    let model_path = models_dir.join(format!("ggml-{}.bin", model_name));
    std::fs::remove_file(model_path).map_err(|e| e.to_string())
}

fn get_models_dir() -> Result<PathBuf, String> {
    let app_dir = dirs::data_local_dir()
        .ok_or("Failed to get app data dir")?
        .join("com.iamcodio.braindump")
        .join("models");

    std::fs::create_dir_all(&app_dir).map_err(|e| e.to_string())?;
    Ok(app_dir)
}
```

---

## Task 2: Quantization Support

### File: `src-tauri/src/services/quantize.rs`

```rust
use std::process::Command;
use std::path::PathBuf;

#[derive(Debug, Clone, serde::Serialize)]
pub enum QuantizationType {
    Q4_0,  // Smallest, ~93% accuracy
    Q5_0,  // Best balance, 98%+ accuracy
    Q8_0,  // Near original quality
}

#[tauri::command]
pub async fn quantize_model(
    model_name: String,
    quant_type: String
) -> Result<String, String> {
    let models_dir = get_models_dir()?;
    let input_path = models_dir.join(format!("ggml-{}.bin", model_name));
    let output_path = models_dir.join(format!("ggml-{}-{}.bin", model_name, quant_type.to_lowercase()));

    if !input_path.exists() {
        return Err("Source model not found".to_string());
    }

    // Use whisper.cpp quantize tool
    let output = Command::new("whisper-quantize")
        .arg(&input_path)
        .arg(&output_path)
        .arg(&quant_type.to_lowercase())
        .output()
        .map_err(|e| format!("Quantization failed: {}", e))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }

    Ok(output_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn get_quantized_models() -> Result<Vec<String>, String> {
    let models_dir = get_models_dir()?;
    let mut quantized = vec![];

    for entry in std::fs::read_dir(&models_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let name = entry.file_name().to_string_lossy().to_string();
        if name.contains("-q") && name.ends_with(".bin") {
            quantized.push(name);
        }
    }

    Ok(quantized)
}
```

---

## Task 3: Voice Activity Detection (VAD)

### File: `src-tauri/src/services/vad.rs`

```rust
use std::path::PathBuf;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct VADConfig {
    pub enabled: bool,
    pub silence_threshold_db: f32,  // Default: -50dB
    pub min_silence_duration_ms: u32,  // Default: 500ms
    pub padding_ms: u32,  // Keep some silence for context
}

impl Default for VADConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            silence_threshold_db: -50.0,
            min_silence_duration_ms: 500,
            padding_ms: 100,
        }
    }
}

#[tauri::command]
pub async fn preprocess_audio_with_vad(
    input_path: String,
    config: VADConfig
) -> Result<String, String> {
    if !config.enabled {
        return Ok(input_path);
    }

    let output_path = format!("{}_vad.wav", input_path.trim_end_matches(".wav"));

    // Use ffmpeg for silence removal
    let output = std::process::Command::new("ffmpeg")
        .args(&[
            "-i", &input_path,
            "-af", &format!(
                "silenceremove=start_periods=1:start_duration=0:start_threshold={}dB:detection=peak,areverse,silenceremove=start_periods=1:start_duration=0:start_threshold={}dB:detection=peak,areverse",
                config.silence_threshold_db,
                config.silence_threshold_db
            ),
            "-y",
            &output_path
        ])
        .output()
        .map_err(|e| format!("VAD preprocessing failed: {}", e))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }

    Ok(output_path)
}

// Alternative: Use Silero VAD (more accurate)
#[tauri::command]
pub async fn detect_speech_segments(audio_path: String) -> Result<Vec<(f32, f32)>, String> {
    // Returns list of (start_time, end_time) for speech segments
    // This would use Silero VAD model or similar

    // Placeholder - implement with actual VAD model
    Ok(vec![(0.0, 10.0)])  // Full audio for now
}
```

---

## Task 4: Frontend Settings UI

### File: `src/lib/components/ModelSettings.svelte`

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { onMount } from 'svelte';

  interface WhisperModel {
    name: string;
    size_mb: number;
    accuracy: string;
    speed: string;
  }

  let availableModels: WhisperModel[] = [];
  let installedModels: string[] = [];
  let currentModel = 'base';
  let downloadProgress = 0;
  let isDownloading = false;
  let selectedModel = '';

  // VAD settings
  let vadEnabled = true;
  let silenceThreshold = -50;
  let minSilenceDuration = 500;

  onMount(async () => {
    availableModels = await invoke('get_available_models');
    installedModels = await invoke('get_installed_models');

    // Listen for download progress
    await listen('model-download-progress', (event) => {
      downloadProgress = event.payload as number;
    });
  });

  async function downloadModel(modelName: string) {
    isDownloading = true;
    selectedModel = modelName;
    downloadProgress = 0;

    try {
      await invoke('download_model', { modelName });
      installedModels = [...installedModels, modelName];
    } catch (e) {
      console.error('Download failed:', e);
    } finally {
      isDownloading = false;
    }
  }

  async function deleteModel(modelName: string) {
    if (modelName === 'base') {
      alert('Cannot delete base model');
      return;
    }

    try {
      await invoke('delete_model', { modelName });
      installedModels = installedModels.filter(m => m !== modelName);
    } catch (e) {
      console.error('Delete failed:', e);
    }
  }

  async function selectModel(modelName: string) {
    currentModel = modelName;
    localStorage.setItem('whisper_model', modelName);
  }

  function formatSize(mb: number): string {
    if (mb >= 1000) {
      return `${(mb / 1000).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  }
</script>

<div class="model-settings">
  <h2>Whisper Model Settings</h2>

  <div class="current-model">
    <strong>Current Model:</strong> {currentModel}
  </div>

  <div class="models-list">
    {#each availableModels as model}
      <div class="model-card" class:installed={installedModels.includes(model.name)} class:active={currentModel === model.name}>
        <div class="model-header">
          <h3>{model.name}</h3>
          <span class="size">{formatSize(model.size_mb)}</span>
        </div>

        <div class="model-stats">
          <span>Accuracy: {model.accuracy}</span>
          <span>Speed: {model.speed}</span>
        </div>

        <div class="model-actions">
          {#if installedModels.includes(model.name)}
            <button
              class="select-btn"
              class:selected={currentModel === model.name}
              on:click={() => selectModel(model.name)}
            >
              {currentModel === model.name ? '✓ Selected' : 'Use'}
            </button>

            {#if model.name !== 'base'}
              <button class="delete-btn" on:click={() => deleteModel(model.name)}>
                Delete
              </button>
            {/if}
          {:else}
            <button
              class="download-btn"
              disabled={isDownloading}
              on:click={() => downloadModel(model.name)}
            >
              {#if isDownloading && selectedModel === model.name}
                Downloading... {downloadProgress.toFixed(0)}%
              {:else}
                Download
              {/if}
            </button>
          {/if}
        </div>

        {#if isDownloading && selectedModel === model.name}
          <div class="progress-bar">
            <div class="progress" style="width: {downloadProgress}%"></div>
          </div>
        {/if}
      </div>
    {/each}
  </div>

  <div class="vad-settings">
    <h3>Voice Activity Detection (VAD)</h3>

    <label>
      <input type="checkbox" bind:checked={vadEnabled} />
      Enable VAD preprocessing (removes silence)
    </label>

    {#if vadEnabled}
      <div class="vad-options">
        <label>
          Silence Threshold: {silenceThreshold}dB
          <input
            type="range"
            min="-70"
            max="-30"
            bind:value={silenceThreshold}
          />
        </label>

        <label>
          Min Silence Duration: {minSilenceDuration}ms
          <input
            type="range"
            min="100"
            max="2000"
            step="100"
            bind:value={minSilenceDuration}
          />
        </label>
      </div>
    {/if}
  </div>
</div>

<style>
  .model-settings {
    padding: 1rem;
  }

  .models-list {
    display: grid;
    gap: 1rem;
    margin: 1rem 0;
  }

  .model-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    background: #f9f9f9;
  }

  .model-card.installed {
    border-color: #4CAF50;
  }

  .model-card.active {
    background: #e8f5e9;
  }

  .model-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .model-stats {
    display: flex;
    gap: 1rem;
    color: #666;
    font-size: 0.9rem;
    margin: 0.5rem 0;
  }

  .model-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .download-btn {
    background: #2196F3;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .select-btn {
    background: #4CAF50;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .delete-btn {
    background: #f44336;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .progress-bar {
    height: 4px;
    background: #ddd;
    border-radius: 2px;
    margin-top: 0.5rem;
    overflow: hidden;
  }

  .progress {
    height: 100%;
    background: #2196F3;
    transition: width 0.3s;
  }

  .vad-settings {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #ddd;
  }

  .vad-options {
    margin-top: 1rem;
  }

  .vad-options label {
    display: block;
    margin-bottom: 1rem;
  }

  .vad-options input[type="range"] {
    width: 100%;
  }
</style>
```

---

## Task 5: Auto-download Base Model on First Launch

### File: `src-tauri/src/main.rs` (add to setup)

```rust
async fn ensure_base_model() -> Result<(), Box<dyn std::error::Error>> {
    let models_dir = get_models_dir()?;
    let base_model_path = models_dir.join("ggml-base.bin");

    if !base_model_path.exists() {
        println!("First launch: downloading base Whisper model...");
        download_model("base".to_string(), /* window */).await?;
        println!("Base model downloaded successfully!");
    }

    Ok(())
}

// Call in setup
#[tokio::main]
async fn main() {
    // Ensure base model exists
    if let Err(e) = ensure_base_model().await {
        eprintln!("Failed to download base model: {}", e);
    }

    tauri::Builder::default()
        // ... rest of setup
}
```

---

## Task 6: Register Commands

### File: `src-tauri/src/lib.rs`

```rust
mod services {
    pub mod model_manager;
    pub mod quantize;
    pub mod vad;
}

// In run() function, add to invoke_handler:
.invoke_handler(tauri::generate_handler![
    // ... existing commands
    services::model_manager::download_model,
    services::model_manager::get_available_models,
    services::model_manager::get_installed_models,
    services::model_manager::delete_model,
    services::quantize::quantize_model,
    services::quantize::get_quantized_models,
    services::vad::preprocess_audio_with_vad,
    services::vad::detect_speech_segments,
])
```

---

## Success Criteria

- [ ] Base model auto-downloads on first launch
- [ ] Settings UI shows all available models
- [ ] Download progress bar works
- [ ] Can switch between installed models
- [ ] Can delete non-base models
- [ ] VAD preprocessing removes silence
- [ ] Quantized models supported
- [ ] Model selection persists across restarts

---

## Git Commands

```bash
git checkout claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
git pull
# Implement all tasks above
git add -A
git commit -m "feat: Add Whisper model manager with VAD and quantization support"
git push origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
```

**START IMPLEMENTING NOW. THIS IS A CORE FEATURE.**
