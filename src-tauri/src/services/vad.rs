//! Voice Activity Detection (VAD) Preprocessing Service
//! Handles audio preprocessing to remove silence and detect speech segments

use std::path::PathBuf;
use std::process::Command;

/// Configuration for Voice Activity Detection preprocessing
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct VADConfig {
    /// Whether VAD preprocessing is enabled
    pub enabled: bool,
    /// Silence threshold in decibels (default: -50.0 dB)
    pub silence_threshold_db: f32,
    /// Minimum duration of silence to remove in milliseconds (default: 500 ms)
    pub min_silence_duration_ms: u32,
    /// Padding to add around speech segments in milliseconds (default: 100 ms)
    pub padding_ms: u32,
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

/// Preprocess audio file with VAD to remove silence
///
/// Uses ffmpeg's silenceremove filter to strip silence from audio.
/// If VAD is disabled, returns the input path unchanged.
#[tauri::command]
pub async fn preprocess_audio_with_vad(
    input_path: String,
    config: VADConfig,
) -> Result<String, String> {
    // If VAD is disabled, return input path unchanged
    if !config.enabled {
        return Ok(input_path);
    }

    let input = PathBuf::from(&input_path);

    // Verify input file exists
    if !input.exists() {
        return Err(format!("Input file does not exist: {}", input_path));
    }

    // Generate output path with "_vad" suffix
    let stem = input
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or_else(|| "Invalid input file name".to_string())?;
    let extension = input
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("wav");
    let parent = input
        .parent()
        .ok_or_else(|| "Invalid input file path".to_string())?;

    let output_path = parent.join(format!("{}_vad.{}", stem, extension));
    let output_path_str = output_path
        .to_str()
        .ok_or_else(|| "Invalid output path".to_string())?
        .to_string();

    // Convert threshold from dB to amplitude ratio for ffmpeg
    // ffmpeg silenceremove uses amplitude ratio, not dB
    // For -50dB: 10^(-50/20) = 0.00316
    let amplitude_threshold = 10_f32.powf(config.silence_threshold_db / 20.0);

    // Convert min_silence_duration from ms to seconds
    let min_silence_seconds = config.min_silence_duration_ms as f32 / 1000.0;

    // Build ffmpeg silenceremove filter
    // Format: silenceremove=start_periods=1:start_duration=0:start_threshold={threshold}:
    //         detection=peak:stop_periods=-1:stop_duration={duration}:stop_threshold={threshold}
    let filter = format!(
        "silenceremove=start_periods=1:start_duration=0:start_threshold={}:\
         detection=peak:stop_periods=-1:stop_duration={}:stop_threshold={}",
        amplitude_threshold, min_silence_seconds, amplitude_threshold
    );

    // Execute ffmpeg command
    let output = Command::new("ffmpeg")
        .args([
            "-i",
            &input_path,
            "-af",
            &filter,
            "-y", // Overwrite output file if exists
            &output_path_str,
        ])
        .output()
        .map_err(|e| format!("Failed to execute ffmpeg: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("ffmpeg silenceremove failed: {}", stderr));
    }

    // Verify output file was created
    if !output_path.exists() {
        return Err("VAD processing completed but output file was not created".to_string());
    }

    Ok(output_path_str)
}

/// Detect speech segments in an audio file
///
/// Returns a list of (start_time, end_time) tuples indicating
/// where speech was detected in the audio.
///
/// Note: This is currently a placeholder implementation.
/// Future versions will use actual VAD detection algorithms.
#[tauri::command]
pub async fn detect_speech_segments(audio_path: String) -> Result<Vec<(f32, f32)>, String> {
    let path = PathBuf::from(&audio_path);

    // Verify file exists
    if !path.exists() {
        return Err(format!("Audio file does not exist: {}", audio_path));
    }

    // Placeholder implementation
    // In a real implementation, this would analyze the audio file
    // and return actual speech segment timestamps
    Ok(vec![(0.0, 10.0)])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vad_config_default() {
        let config = VADConfig::default();
        assert!(config.enabled);
        assert_eq!(config.silence_threshold_db, -50.0);
        assert_eq!(config.min_silence_duration_ms, 500);
        assert_eq!(config.padding_ms, 100);
    }

    #[test]
    fn test_vad_config_serialization() {
        let config = VADConfig::default();
        let json = serde_json::to_string(&config).expect("Failed to serialize");
        assert!(json.contains("\"enabled\":true"));
        assert!(json.contains("\"silence_threshold_db\":-50.0"));
        assert!(json.contains("\"min_silence_duration_ms\":500"));
        assert!(json.contains("\"padding_ms\":100"));
    }

    #[test]
    fn test_vad_config_deserialization() {
        let json = r#"{
            "enabled": false,
            "silence_threshold_db": -40.0,
            "min_silence_duration_ms": 1000,
            "padding_ms": 200
        }"#;
        let config: VADConfig = serde_json::from_str(json).expect("Failed to deserialize");
        assert!(!config.enabled);
        assert_eq!(config.silence_threshold_db, -40.0);
        assert_eq!(config.min_silence_duration_ms, 1000);
        assert_eq!(config.padding_ms, 200);
    }

    #[test]
    fn test_amplitude_threshold_calculation() {
        // Test that -50dB converts correctly
        let db = -50.0_f32;
        let amplitude = 10_f32.powf(db / 20.0);
        // -50dB should be approximately 0.00316
        assert!((amplitude - 0.00316).abs() < 0.0001);
    }
}
