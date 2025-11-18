//! Whisper Model Manager Service
//! Handles downloading, installing, and managing Whisper models

use futures_util::StreamExt;
use std::path::PathBuf;
use tauri::{Emitter, Window};
use tokio::io::AsyncWriteExt;

/// Represents a Whisper model with its metadata
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct WhisperModel {
    pub name: String,
    pub size_mb: u32,
    pub url: String,
    pub accuracy: String,
    pub speed: String,
}

/// Available Whisper models for download
pub const WHISPER_MODELS: &[WhisperModel] = &[
    WhisperModel {
        name: String::new(), // Will be replaced at runtime
        size_mb: 39,
        url: String::new(),
        accuracy: String::new(),
        speed: String::new(),
    },
];

// Since we can't have String in const, we use a function to get models
fn get_whisper_models() -> Vec<WhisperModel> {
    vec![
        WhisperModel {
            name: "tiny".to_string(),
            size_mb: 39,
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin"
                .to_string(),
            accuracy: "88%".to_string(),
            speed: "Fastest".to_string(),
        },
        WhisperModel {
            name: "base".to_string(),
            size_mb: 141,
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
                .to_string(),
            accuracy: "95%".to_string(),
            speed: "Fast".to_string(),
        },
        WhisperModel {
            name: "small".to_string(),
            size_mb: 466,
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
                .to_string(),
            accuracy: "97%".to_string(),
            speed: "Medium".to_string(),
        },
        WhisperModel {
            name: "medium".to_string(),
            size_mb: 1500,
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin"
                .to_string(),
            accuracy: "98%".to_string(),
            speed: "Slow".to_string(),
        },
        WhisperModel {
            name: "large-v3-turbo".to_string(),
            size_mb: 2900,
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin"
                .to_string(),
            accuracy: "99.1%".to_string(),
            speed: "8x faster than old Large".to_string(),
        },
    ]
}

/// Progress event payload for model downloads
#[derive(Debug, Clone, serde::Serialize)]
pub struct DownloadProgress {
    pub model_name: String,
    pub downloaded_bytes: u64,
    pub total_bytes: u64,
    pub percentage: f32,
}

/// Get the models directory path, creating it if it doesn't exist
pub fn get_models_dir() -> Result<PathBuf, String> {
    let data_dir = dirs::data_local_dir()
        .ok_or_else(|| "Failed to get local data directory".to_string())?;

    let models_dir = data_dir.join("com.iamcodio.braindump").join("models");

    if !models_dir.exists() {
        std::fs::create_dir_all(&models_dir)
            .map_err(|e| format!("Failed to create models directory: {}", e))?;
    }

    Ok(models_dir)
}

/// Get all available Whisper models
#[tauri::command]
pub async fn get_available_models() -> Result<Vec<WhisperModel>, String> {
    Ok(get_whisper_models())
}

/// Get list of installed model names by checking the models directory
#[tauri::command]
pub async fn get_installed_models() -> Result<Vec<String>, String> {
    let models_dir = get_models_dir()?;

    let mut installed = Vec::new();

    let entries = tokio::fs::read_dir(&models_dir)
        .await
        .map_err(|e| format!("Failed to read models directory: {}", e))?;

    let mut entries = entries;
    while let Some(entry) = entries
        .next_entry()
        .await
        .map_err(|e| format!("Failed to read directory entry: {}", e))?
    {
        let path = entry.path();
        if path.is_file() {
            if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                // Extract model name from ggml-{name}.bin format
                if file_name.starts_with("ggml-") && file_name.ends_with(".bin") {
                    let model_name = file_name
                        .strip_prefix("ggml-")
                        .unwrap()
                        .strip_suffix(".bin")
                        .unwrap();
                    installed.push(model_name.to_string());
                }
            }
        }
    }

    Ok(installed)
}

/// Download a Whisper model from HuggingFace with progress events
#[tauri::command]
pub async fn download_model(model_name: String, window: Window) -> Result<String, String> {
    let models = get_whisper_models();

    let model = models
        .iter()
        .find(|m| m.name == model_name)
        .ok_or_else(|| format!("Unknown model: {}", model_name))?;

    let models_dir = get_models_dir()?;
    let file_path = models_dir.join(format!("ggml-{}.bin", model_name));

    // Check if already downloaded
    if file_path.exists() {
        return Ok(format!("Model {} is already installed", model_name));
    }

    // Create HTTP client
    let client = reqwest::Client::new();

    // Start download
    let response = client
        .get(&model.url)
        .send()
        .await
        .map_err(|e| format!("Failed to start download: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "Download failed with status: {}",
            response.status()
        ));
    }

    let total_size = response.content_length().unwrap_or(0);

    // Create temp file for download
    let temp_path = models_dir.join(format!("ggml-{}.bin.tmp", model_name));
    let mut file = tokio::fs::File::create(&temp_path)
        .await
        .map_err(|e| format!("Failed to create temp file: {}", e))?;

    let mut downloaded: u64 = 0;
    let mut stream = response.bytes_stream();

    // Download with progress events
    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| format!("Error downloading chunk: {}", e))?;

        file.write_all(&chunk)
            .await
            .map_err(|e| format!("Failed to write chunk: {}", e))?;

        downloaded += chunk.len() as u64;

        // Emit progress event
        let progress = DownloadProgress {
            model_name: model_name.clone(),
            downloaded_bytes: downloaded,
            total_bytes: total_size,
            percentage: if total_size > 0 {
                (downloaded as f32 / total_size as f32) * 100.0
            } else {
                0.0
            },
        };

        // Emit event to frontend
        let _ = window.emit("model-download-progress", progress);
    }

    // Flush and close file
    file.flush()
        .await
        .map_err(|e| format!("Failed to flush file: {}", e))?;

    // Rename temp file to final path
    tokio::fs::rename(&temp_path, &file_path)
        .await
        .map_err(|e| format!("Failed to finalize download: {}", e))?;

    Ok(format!(
        "Successfully downloaded model {} to {:?}",
        model_name, file_path
    ))
}

/// Delete a model file
#[tauri::command]
pub async fn delete_model(model_name: String) -> Result<String, String> {
    let models_dir = get_models_dir()?;
    let file_path = models_dir.join(format!("ggml-{}.bin", model_name));

    if !file_path.exists() {
        return Err(format!("Model {} is not installed", model_name));
    }

    tokio::fs::remove_file(&file_path)
        .await
        .map_err(|e| format!("Failed to delete model: {}", e))?;

    Ok(format!("Successfully deleted model {}", model_name))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_whisper_models() {
        let models = get_whisper_models();
        assert_eq!(models.len(), 5);
        assert_eq!(models[0].name, "tiny");
        assert_eq!(models[1].name, "base");
        assert_eq!(models[2].name, "small");
        assert_eq!(models[3].name, "medium");
        assert_eq!(models[4].name, "large-v3-turbo");
    }

    #[test]
    fn test_model_sizes() {
        let models = get_whisper_models();
        assert_eq!(models[0].size_mb, 39); // tiny
        assert_eq!(models[1].size_mb, 141); // base
        assert_eq!(models[2].size_mb, 466); // small
        assert_eq!(models[3].size_mb, 1500); // medium
        assert_eq!(models[4].size_mb, 2900); // large-v3-turbo
    }

    #[test]
    fn test_get_models_dir() {
        let result = get_models_dir();
        assert!(result.is_ok());
        let path = result.unwrap();
        assert!(path.to_string_lossy().contains("com.iamcodio.braindump"));
        assert!(path.to_string_lossy().contains("models"));
    }
}
