//! Pure Rust Candle transcription plugin
//!
//! This plugin uses HuggingFace Candle for 100% Rust ML inference.
//! Zero FFI, zero C++ dependencies - just safe Rust code.
//!
//! NOTE: This is a simplified implementation demonstrating the plugin architecture.
//! Full Whisper model integration requires additional work to match the Candle API.

use super::{AudioData, PluginError, Transcript, TranscriptSegment, TranscriptionPlugin};
use candle_core::Device;
use std::path::PathBuf;

/// CandlePlugin - Pure Rust transcription using HuggingFace Candle
///
/// This implementation provides the plugin structure and demonstrates
/// Metal GPU acceleration support. Full Whisper model integration is
/// deferred to the next iteration when the Candle Whisper API stabilizes.
pub struct CandlePlugin {
    model_path: PathBuf,
    device: Device,
    initialized: bool,
}

impl CandlePlugin {
    /// Create a new Candle plugin instance
    ///
    /// # Arguments
    /// * `model_path` - Path to the Whisper model in safetensors format
    ///
    /// # Example
    /// ```no_run
    /// use std::path::PathBuf;
    /// use braindump::plugin::candle::CandlePlugin;
    ///
    /// let plugin = CandlePlugin::new(PathBuf::from("models/whisper-base.safetensors"));
    /// ```
    pub fn new(model_path: PathBuf) -> Self {
        // Try to use Metal GPU on macOS, fallback to CPU
        let device = Device::new_metal(0).unwrap_or_else(|_| {
            eprintln!("⚠️  Metal GPU not available, falling back to CPU");
            Device::Cpu
        });

        Self {
            model_path,
            device,
            initialized: false,
        }
    }

    /// Get the device being used (for testing/diagnostics)
    pub fn device(&self) -> &Device {
        &self.device
    }

    /// Validate audio format
    fn validate_audio(&self, audio: &AudioData) -> Result<(), PluginError> {
        // Whisper expects 16kHz mono audio
        if audio.sample_rate != 16000 {
            return Err(PluginError::InvalidAudioFormat(format!(
                "Expected 16kHz audio, got {}Hz. Please resample before transcription.",
                audio.sample_rate
            )));
        }

        if audio.channels != 1 {
            return Err(PluginError::InvalidAudioFormat(format!(
                "Expected mono audio, got {} channels. Please convert to mono first.",
                audio.channels
            )));
        }

        Ok(())
    }
}

impl TranscriptionPlugin for CandlePlugin {
    fn name(&self) -> &str {
        "candle"
    }

    fn version(&self) -> &str {
        "0.8.0"
    }

    fn initialize(&mut self) -> Result<(), PluginError> {
        if self.initialized {
            return Ok(());
        }

        // Check model file exists
        if !self.model_path.exists() {
            return Err(PluginError::ModelNotFound(
                self.model_path.display().to_string(),
            ));
        }

        // Check device capabilities
        match &self.device {
            Device::Metal(_) => {
                println!("✅ Candle Plugin: Metal GPU acceleration enabled");
            }
            Device::Cpu => {
                println!("⚠️  Candle Plugin: Running on CPU (slower, no GPU available)");
            }
            _ => {}
        }

        // NOTE: Full model loading would happen here
        // For now, we validate the setup is correct
        self.initialized = true;

        println!("✅ Candle Plugin initialized successfully");
        println!("   Model: {}", self.model_path.display());
        println!("   Device: {:?}", self.device);

        Ok(())
    }

    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError> {
        if !self.initialized {
            return Err(PluginError::NotInitialized(self.name().to_string()));
        }

        // Validate audio format
        self.validate_audio(audio)?;

        // Calculate audio duration
        let duration_ms = (audio.samples.len() as u64 * 1000) / audio.sample_rate as u64;

        // NOTE: Full Whisper transcription would happen here
        // This is a placeholder showing the plugin architecture works
        println!("🎤 Transcribing {} seconds of audio...", duration_ms / 1000);

        // Return a mock transcript demonstrating the structure
        Ok(Transcript {
            text: format!(
                "[Candle Plugin v{}] Audio transcription placeholder ({:.1}s)",
                self.version(),
                duration_ms as f64 / 1000.0
            ),
            language: Some("en".to_string()),
            segments: vec![TranscriptSegment {
                start_ms: 0,
                end_ms: duration_ms,
                text: "Candle plugin architecture validated. Full Whisper model integration pending.".to_string(),
                confidence: 1.0,
            }],
        })
    }

    fn shutdown(&mut self) -> Result<(), PluginError> {
        self.initialized = false;
        println!("✅ Candle Plugin shutdown successfully");
        Ok(())
    }

    fn is_initialized(&self) -> bool {
        self.initialized
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_candle_plugin_creation() {
        let plugin = CandlePlugin::new(PathBuf::from("models/whisper-base.safetensors"));
        assert_eq!(plugin.name(), "candle");
        assert_eq!(plugin.version(), "0.8.0");
        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_device_selection() {
        let plugin = CandlePlugin::new(PathBuf::from("models/whisper-base.safetensors"));

        // Device should be either Metal (macOS) or CPU
        match plugin.device() {
            Device::Metal(_) => {
                println!("✅ Metal GPU detected and selected");
            }
            Device::Cpu => {
                println!("ℹ️  Running on CPU");
            }
            _ => {}
        }
    }

    #[test]
    fn test_invalid_audio_format() {
        let mut plugin = CandlePlugin::new(PathBuf::from("models/whisper-base.safetensors"));

        // Don't need model file to test format validation
        plugin.initialized = true;

        let bad_audio_rate = AudioData {
            samples: vec![0.0; 44100],
            sample_rate: 44100, // Wrong! Should be 16000
            channels: 1,
        };

        let result = plugin.transcribe(&bad_audio_rate);
        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            PluginError::InvalidAudioFormat(_)
        ));

        let bad_audio_channels = AudioData {
            samples: vec![0.0; 16000],
            sample_rate: 16000,
            channels: 2, // Wrong! Should be 1
        };

        let result = plugin.transcribe(&bad_audio_channels);
        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            PluginError::InvalidAudioFormat(_)
        ));
    }

    #[test]
    fn test_transcribe_without_init() {
        let plugin = CandlePlugin::new(PathBuf::from("models/whisper-base.safetensors"));

        let audio = AudioData {
            samples: vec![0.0; 16000],
            sample_rate: 16000,
            channels: 1,
        };

        let result = plugin.transcribe(&audio);
        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            PluginError::NotInitialized(_)
        ));
    }

    #[test]
    fn test_lifecycle() {
        let mut plugin = CandlePlugin::new(PathBuf::from("models/whisper-base.safetensors"));

        assert!(!plugin.is_initialized());

        // Skip actual initialization if model doesn't exist (CI environment)
        if plugin.model_path.exists() {
            assert!(plugin.initialize().is_ok());
            assert!(plugin.is_initialized());

            assert!(plugin.shutdown().is_ok());
            assert!(!plugin.is_initialized());
        }
    }
}
