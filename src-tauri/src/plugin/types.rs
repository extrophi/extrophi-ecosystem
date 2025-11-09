//! Shared types used across the plugin system
//!
//! This module re-exports common types and provides convenience type aliases
//! for plugin operations.

pub use super::{AudioData, Transcript, TranscriptSegment, PluginError};

/// Result type alias for plugin operations
pub type PluginResult<T> = Result<T, PluginError>;

/// Helper function to convert stereo audio to mono
///
/// Averages the left and right channels for each sample.
///
/// # Arguments
///
/// * `stereo_samples` - Interleaved stereo samples (L, R, L, R, ...)
///
/// # Returns
///
/// Vector of mono samples (averaged)
pub fn stereo_to_mono(stereo_samples: &[f32]) -> Vec<f32> {
    stereo_samples
        .chunks_exact(2)
        .map(|chunk| (chunk[0] + chunk[1]) / 2.0)
        .collect()
}

/// Helper function to resample audio (simple linear interpolation)
///
/// This is a basic resampling implementation. For production use, consider
/// a dedicated audio resampling library like `rubato` or `samplerate`.
///
/// # Arguments
///
/// * `samples` - Input audio samples
/// * `from_rate` - Source sample rate in Hz
/// * `to_rate` - Target sample rate in Hz
///
/// # Returns
///
/// Resampled audio
pub fn resample_audio(samples: &[f32], from_rate: u32, to_rate: u32) -> Vec<f32> {
    if from_rate == to_rate {
        return samples.to_vec();
    }

    let ratio = from_rate as f64 / to_rate as f64;
    let output_len = (samples.len() as f64 / ratio).ceil() as usize;
    let mut output = Vec::with_capacity(output_len);

    for i in 0..output_len {
        let src_pos = i as f64 * ratio;
        let src_idx = src_pos.floor() as usize;
        let frac = src_pos - src_idx as f64;

        if src_idx + 1 < samples.len() {
            // Linear interpolation
            let sample = samples[src_idx] * (1.0 - frac) as f32
                + samples[src_idx + 1] * frac as f32;
            output.push(sample);
        } else if src_idx < samples.len() {
            output.push(samples[src_idx]);
        }
    }

    output
}

/// Normalize audio samples to [-1.0, 1.0] range
///
/// # Arguments
///
/// * `samples` - Audio samples to normalize
///
/// # Returns
///
/// Normalized samples
pub fn normalize_audio(samples: &[f32]) -> Vec<f32> {
    if samples.is_empty() {
        return vec![];
    }

    let max_val = samples.iter()
        .map(|s| s.abs())
        .fold(0.0f32, f32::max);

    if max_val == 0.0 || max_val == 1.0 {
        return samples.to_vec();
    }

    samples.iter()
        .map(|s| s / max_val)
        .collect()
}

/// Calculate audio duration in milliseconds
///
/// # Arguments
///
/// * `num_samples` - Total number of samples
/// * `sample_rate` - Sample rate in Hz
/// * `channels` - Number of audio channels
///
/// # Returns
///
/// Duration in milliseconds
pub fn calculate_duration_ms(num_samples: usize, sample_rate: u32, channels: u16) -> u64 {
    let samples_per_channel = num_samples as f64 / channels as f64;
    let duration_sec = samples_per_channel / sample_rate as f64;
    (duration_sec * 1000.0).round() as u64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stereo_to_mono() {
        let stereo = vec![0.5, -0.5, 0.8, 0.2, 1.0, -1.0];
        let mono = stereo_to_mono(&stereo);

        assert_eq!(mono.len(), 3);
        assert_eq!(mono[0], 0.0); // (0.5 + -0.5) / 2
        assert_eq!(mono[1], 0.5); // (0.8 + 0.2) / 2
        assert_eq!(mono[2], 0.0); // (1.0 + -1.0) / 2
    }

    #[test]
    fn test_stereo_to_mono_empty() {
        let stereo: Vec<f32> = vec![];
        let mono = stereo_to_mono(&stereo);
        assert_eq!(mono.len(), 0);
    }

    #[test]
    fn test_resample_audio_same_rate() {
        let samples = vec![0.1, 0.2, 0.3, 0.4];
        let resampled = resample_audio(&samples, 16000, 16000);

        assert_eq!(resampled, samples);
    }

    #[test]
    fn test_resample_audio_downsample() {
        let samples = vec![0.0, 0.25, 0.5, 0.75, 1.0];
        let resampled = resample_audio(&samples, 44100, 16000);

        // Should have fewer samples
        assert!(resampled.len() < samples.len());
        assert!(resampled.len() > 0);
    }

    #[test]
    fn test_resample_audio_upsample() {
        let samples = vec![0.0, 0.5, 1.0];
        let resampled = resample_audio(&samples, 16000, 44100);

        // Should have more samples
        assert!(resampled.len() > samples.len());
    }

    #[test]
    fn test_normalize_audio() {
        let samples = vec![0.5, -0.8, 0.2, -0.4];
        let normalized = normalize_audio(&samples);

        // Max value should be 1.0
        let max = normalized.iter().map(|s| s.abs()).fold(0.0f32, f32::max);
        assert!((max - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_normalize_audio_already_normalized() {
        let samples = vec![1.0, -1.0, 0.5, -0.5];
        let normalized = normalize_audio(&samples);

        assert_eq!(normalized, samples);
    }

    #[test]
    fn test_normalize_audio_empty() {
        let samples: Vec<f32> = vec![];
        let normalized = normalize_audio(&samples);

        assert_eq!(normalized.len(), 0);
    }

    #[test]
    fn test_normalize_audio_zeros() {
        let samples = vec![0.0, 0.0, 0.0];
        let normalized = normalize_audio(&samples);

        assert_eq!(normalized, samples);
    }

    #[test]
    fn test_calculate_duration_ms_mono() {
        // 16000 samples at 16kHz mono = 1 second = 1000ms
        let duration = calculate_duration_ms(16000, 16000, 1);
        assert_eq!(duration, 1000);
    }

    #[test]
    fn test_calculate_duration_ms_stereo() {
        // 32000 samples at 16kHz stereo (2 channels) = 1 second = 1000ms
        let duration = calculate_duration_ms(32000, 16000, 2);
        assert_eq!(duration, 1000);
    }

    #[test]
    fn test_calculate_duration_ms_partial_second() {
        // 8000 samples at 16kHz mono = 0.5 seconds = 500ms
        let duration = calculate_duration_ms(8000, 16000, 1);
        assert_eq!(duration, 500);
    }

    #[test]
    fn test_audio_data_creation() {
        let audio = AudioData {
            samples: vec![0.1, 0.2, 0.3],
            sample_rate: 44100,
            channels: 2,
        };

        assert_eq!(audio.samples.len(), 3);
        assert_eq!(audio.sample_rate, 44100);
        assert_eq!(audio.channels, 2);
    }

    #[test]
    fn test_transcript_creation() {
        let transcript = Transcript {
            text: "Hello world".to_string(),
            language: Some("en".to_string()),
            segments: vec![
                TranscriptSegment {
                    start_ms: 0,
                    end_ms: 1000,
                    text: "Hello".to_string(),
                    confidence: 0.95,
                },
                TranscriptSegment {
                    start_ms: 1000,
                    end_ms: 2000,
                    text: "world".to_string(),
                    confidence: 0.92,
                },
            ],
        };

        assert_eq!(transcript.text, "Hello world");
        assert_eq!(transcript.language, Some("en".to_string()));
        assert_eq!(transcript.segments.len(), 2);
    }

    #[test]
    fn test_plugin_result_ok() {
        let result: PluginResult<String> = Ok("success".to_string());
        assert!(result.is_ok());
    }

    #[test]
    fn test_plugin_result_err() {
        let result: PluginResult<String> = Err(PluginError::NotInitialized("test".to_string()));
        assert!(result.is_err());
    }
}
