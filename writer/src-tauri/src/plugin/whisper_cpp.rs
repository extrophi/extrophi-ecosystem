//! Whisper.cpp Direct FFI Plugin
//!
//! Calls whisper.cpp library directly (no Stage A wrapper)
//!
//! Flow:
//! 1. Load model: whisper_init_from_file()
//! 2. Process audio: whisper_full() with f32 samples
//! 3. Extract text: whisper_full_get_segment_text()
//! 4. Clean up: whisper_free()

use super::{AudioData, PluginError, Transcript, TranscriptSegment, TranscriptionPlugin};
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

// ============================================================================
// WHISPER.CPP C API BINDINGS
// ============================================================================

/// Opaque whisper context (C++ object)
#[repr(C)]
struct WhisperContext {
    _private: [u8; 0],
}

/// Whisper parameters struct (opaque, we get from whisper_full_default_params)
#[repr(C)]
#[derive(Clone, Copy)]
struct WhisperFullParams {
    _data: [u8; 512], // Large enough for the C struct
}

extern "C" {
    /// Load model from file, returns context or null on failure
    fn whisper_init_from_file(path_model: *const c_char) -> *mut WhisperContext;

    /// Get default transcription parameters
    fn whisper_full_default_params(strategy: i32) -> WhisperFullParams;

    /// Run full transcription on audio samples
    /// Returns 0 on success, non-zero on error
    fn whisper_full(
        ctx: *mut WhisperContext,
        params: WhisperFullParams,
        samples: *const f32,
        n_samples: i32,
    ) -> i32;

    /// Get number of text segments after transcription
    fn whisper_full_n_segments(ctx: *mut WhisperContext) -> i32;

    /// Get text for segment i (0-indexed)
    /// Returns pointer to internal string (don't free)
    fn whisper_full_get_segment_text(ctx: *mut WhisperContext, i_segment: i32) -> *const c_char;

    /// Get start time of segment i in milliseconds
    fn whisper_full_get_segment_t0(ctx: *mut WhisperContext, i_segment: i32) -> i64;

    /// Get end time of segment i in milliseconds  
    fn whisper_full_get_segment_t1(ctx: *mut WhisperContext, i_segment: i32) -> i64;

    /// Free whisper context
    fn whisper_free(ctx: *mut WhisperContext);
}

/// Whisper sampling strategy (greedy is fastest/simplest)
const WHISPER_SAMPLING_GREEDY: i32 = 0;

// ============================================================================
// PLUGIN IMPLEMENTATION
// ============================================================================

/// Whisper.cpp plugin - calls whisper.cpp directly via FFI
pub struct WhisperCppPlugin {
    context: Option<*mut WhisperContext>,
    model_path: String,
    initialized: bool,
}

impl WhisperCppPlugin {
    /// Create new plugin with model path
    pub fn new(model_path: String) -> Self {
        Self {
            context: None,
            model_path,
            initialized: false,
        }
    }
}

// SAFETY: whisper.cpp is thread-safe (uses internal mutexes)
unsafe impl Send for WhisperCppPlugin {}
unsafe impl Sync for WhisperCppPlugin {}

impl TranscriptionPlugin for WhisperCppPlugin {
    fn name(&self) -> &str {
        "whisper-cpp"
    }

    fn version(&self) -> &str {
        "1.8.2"
    }

    fn initialize(&mut self) -> Result<(), PluginError> {
        if self.initialized {
            return Ok(());
        }

        // Convert Rust string to C string
        let model_path_c = CString::new(self.model_path.clone())
            .map_err(|e| PluginError::TranscriptionFailed(format!("Invalid model path: {}", e)))?;

        // Load model
        let ctx = unsafe { whisper_init_from_file(model_path_c.as_ptr()) };

        if ctx.is_null() {
            return Err(PluginError::TranscriptionFailed(format!(
                "Failed to load whisper model: {}",
                self.model_path
            )));
        }

        self.context = Some(ctx);
        self.initialized = true;

        eprintln!("✓ Whisper.cpp initialized: {}", self.model_path);
        Ok(())
    }

    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError> {
        if !self.initialized {
            return Err(PluginError::NotInitialized(self.name().to_string()));
        }

        let ctx = self.context.ok_or_else(|| {
            PluginError::NotInitialized("Whisper context not initialized".to_string())
        })?;

        // Resample to 16kHz if needed
        use rubato::{
            Resampler, SincFixedIn, SincInterpolationParameters, SincInterpolationType,
            WindowFunction,
        };

        let resampled_samples = if audio.sample_rate != 16000 {
            eprintln!("🔄 Resampling {}Hz → 16000Hz", audio.sample_rate);

            let params = SincInterpolationParameters {
                sinc_len: 256,
                f_cutoff: 0.95,
                interpolation: SincInterpolationType::Linear,
                oversampling_factor: 256,
                window: WindowFunction::BlackmanHarris2,
            };

            let mut resampler = SincFixedIn::<f32>::new(
                16000_f64 / audio.sample_rate as f64,
                2.0,
                params,
                audio.samples.len(),
                1,
            )
            .map_err(|e| PluginError::TranscriptionFailed(format!("Resample failed: {}", e)))?;

            let waves_in = vec![audio.samples.clone()];
            let mut waves_out = resampler
                .process(&waves_in, None)
                .map_err(|e| PluginError::TranscriptionFailed(format!("Resample failed: {}", e)))?;

            eprintln!(
                "✓ Resampled: {} → {} samples",
                audio.samples.len(),
                waves_out[0].len()
            );
            waves_out.remove(0)
        } else {
            audio.samples.clone()
        };

        let params = unsafe { whisper_full_default_params(WHISPER_SAMPLING_GREEDY) };

        eprintln!("🎙️  Transcribing {} samples...", resampled_samples.len());

        let result = unsafe {
            whisper_full(
                ctx,
                params,
                resampled_samples.as_ptr(),
                resampled_samples.len() as i32,
            )
        };

        if result != 0 {
            return Err(PluginError::TranscriptionFailed(format!(
                "Whisper transcription failed with code: {}",
                result
            )));
        }

        let n_segments = unsafe { whisper_full_n_segments(ctx) };

        if n_segments <= 0 {
            return Ok(Transcript {
                text: String::new(),
                language: Some("en".to_string()),
                segments: vec![],
            });
        }

        let mut segments = Vec::new();
        let mut full_text = String::new();

        for i in 0..n_segments {
            let text_ptr = unsafe { whisper_full_get_segment_text(ctx, i) };

            if text_ptr.is_null() {
                continue;
            }

            let text = unsafe { CStr::from_ptr(text_ptr).to_string_lossy().into_owned() };

            let start_ms = unsafe { whisper_full_get_segment_t0(ctx, i) * 10 };
            let end_ms = unsafe { whisper_full_get_segment_t1(ctx, i) * 10 };

            segments.push(TranscriptSegment {
                start_ms: start_ms as u64,
                end_ms: end_ms as u64,
                text: text.clone(),
                confidence: 1.0,
            });

            full_text.push_str(&text);
            full_text.push(' ');
        }

        eprintln!("✓ Transcribed {} segments", n_segments);

        Ok(Transcript {
            text: full_text.trim().to_string(),
            language: Some("en".to_string()),
            segments,
        })
    }

    fn shutdown(&mut self) -> Result<(), PluginError> {
        if let Some(ctx) = self.context.take() {
            unsafe { whisper_free(ctx) };
            eprintln!("✓ Whisper.cpp shut down");
        }
        self.initialized = false;
        Ok(())
    }

    fn is_initialized(&self) -> bool {
        self.initialized
    }
}

impl Drop for WhisperCppPlugin {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_plugin_creation() {
        let model_path = "models/ggml-base.bin".to_string();
        let plugin = WhisperCppPlugin::new(model_path);

        assert_eq!(plugin.name(), "whisper-cpp");
        assert_eq!(plugin.version(), "1.8.2");
        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_transcribe_without_init() {
        let plugin = WhisperCppPlugin::new("models/ggml-base.bin".to_string());

        let audio = AudioData {
            samples: vec![0.0; 16000],
            sample_rate: 16000,
            channels: 1,
        };

        let result = plugin.transcribe(&audio);
        assert!(result.is_err());
    }

    #[test]
    fn test_plugin_name_version() {
        let plugin = WhisperCppPlugin::new("test_model.bin".to_string());

        assert_eq!(plugin.name(), "whisper-cpp");
        assert_eq!(plugin.version(), "1.8.2");
    }

    #[test]
    fn test_plugin_not_initialized_by_default() {
        let plugin = WhisperCppPlugin::new("test_model.bin".to_string());

        assert!(!plugin.is_initialized());
        assert!(plugin.context.is_none());
    }

    #[test]
    fn test_plugin_shutdown_when_not_initialized() {
        let mut plugin = WhisperCppPlugin::new("test_model.bin".to_string());

        // Shutdown should work even when not initialized
        let result = plugin.shutdown();
        assert!(result.is_ok());
        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_audio_data_creation() {
        let samples = vec![0.1, 0.2, 0.3, 0.4, 0.5];
        let audio = AudioData {
            samples: samples.clone(),
            sample_rate: 16000,
            channels: 1,
        };

        assert_eq!(audio.samples.len(), 5);
        assert_eq!(audio.sample_rate, 16000);
        assert_eq!(audio.channels, 1);
        assert_eq!(audio.samples, samples);
    }

    #[test]
    fn test_audio_data_various_sample_rates() {
        let sample_rates = vec![8000, 16000, 22050, 44100, 48000];

        for rate in sample_rates {
            let audio = AudioData {
                samples: vec![0.0; 1000],
                sample_rate: rate,
                channels: 1,
            };

            assert_eq!(audio.sample_rate, rate);
        }
    }

    #[test]
    fn test_audio_data_empty_samples() {
        let audio = AudioData {
            samples: vec![],
            sample_rate: 16000,
            channels: 1,
        };

        assert_eq!(audio.samples.len(), 0);
    }

    #[test]
    fn test_audio_data_stereo() {
        let audio = AudioData {
            samples: vec![0.1, 0.2, 0.3, 0.4],
            sample_rate: 44100,
            channels: 2,
        };

        assert_eq!(audio.channels, 2);
    }

    #[test]
    fn test_transcribe_error_when_not_initialized() {
        let plugin = WhisperCppPlugin::new("nonexistent_model.bin".to_string());

        let audio = AudioData {
            samples: vec![0.0; 16000],
            sample_rate: 16000,
            channels: 1,
        };

        let result = plugin.transcribe(&audio);

        // Should error because plugin is not initialized
        assert!(result.is_err());
        if let Err(e) = result {
            match e {
                PluginError::NotInitialized(_) => {
                    // Expected error type
                }
                _ => panic!("Expected NotInitialized error"),
            }
        }
    }

    #[test]
    fn test_plugin_model_path_storage() {
        let model_path = "/path/to/custom/model.bin".to_string();
        let plugin = WhisperCppPlugin::new(model_path.clone());

        assert_eq!(plugin.model_path, model_path);
    }

    #[test]
    fn test_plugin_multiple_instances() {
        let plugin1 = WhisperCppPlugin::new("model1.bin".to_string());
        let plugin2 = WhisperCppPlugin::new("model2.bin".to_string());

        assert_eq!(plugin1.model_path, "model1.bin");
        assert_eq!(plugin2.model_path, "model2.bin");
        assert!(!plugin1.is_initialized());
        assert!(!plugin2.is_initialized());
    }

    #[test]
    fn test_transcript_segment_structure() {
        let segment = TranscriptSegment {
            start_ms: 0,
            end_ms: 1000,
            text: "Hello world".to_string(),
            confidence: 0.95,
        };

        assert_eq!(segment.start_ms, 0);
        assert_eq!(segment.end_ms, 1000);
        assert_eq!(segment.text, "Hello world");
        assert_eq!(segment.confidence, 0.95);
    }

    #[test]
    fn test_transcript_structure() {
        let segments = vec![
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
        ];

        let transcript = Transcript {
            text: "Hello world".to_string(),
            language: Some("en".to_string()),
            segments: segments.clone(),
        };

        assert_eq!(transcript.text, "Hello world");
        assert_eq!(transcript.language, Some("en".to_string()));
        assert_eq!(transcript.segments.len(), 2);
        assert_eq!(transcript.segments[0].text, "Hello");
        assert_eq!(transcript.segments[1].text, "world");
    }

    #[test]
    fn test_empty_transcript() {
        let transcript = Transcript {
            text: String::new(),
            language: Some("en".to_string()),
            segments: vec![],
        };

        assert!(transcript.text.is_empty());
        assert_eq!(transcript.segments.len(), 0);
    }

    #[test]
    fn test_plugin_error_types() {
        // Test that PluginError variants can be constructed
        let _not_init = PluginError::NotInitialized("test".to_string());
        let _trans_failed = PluginError::TranscriptionFailed("test".to_string());

        // These should compile without issues
        assert!(true);
    }

    #[test]
    fn test_whisper_sampling_constant() {
        // Verify the constant is defined correctly
        assert_eq!(WHISPER_SAMPLING_GREEDY, 0);
    }

    #[test]
    fn test_audio_data_large_samples() {
        // Test with a larger audio buffer (1 second at 16kHz)
        let samples = vec![0.0; 16000];
        let audio = AudioData {
            samples,
            sample_rate: 16000,
            channels: 1,
        };

        assert_eq!(audio.samples.len(), 16000);
    }

    #[test]
    fn test_audio_data_sample_values() {
        // Test with various sample values
        let samples = vec![-1.0, -0.5, 0.0, 0.5, 1.0];
        let audio = AudioData {
            samples: samples.clone(),
            sample_rate: 16000,
            channels: 1,
        };

        for (i, expected) in samples.iter().enumerate() {
            assert_eq!(audio.samples[i], *expected);
        }
    }

    #[test]
    fn test_plugin_send_sync_traits() {
        // WhisperCppPlugin should be Send and Sync
        // This test verifies that the unsafe impl is present
        fn assert_send<T: Send>() {}
        fn assert_sync<T: Sync>() {}

        assert_send::<WhisperCppPlugin>();
        assert_sync::<WhisperCppPlugin>();
    }

    #[test]
    fn test_transcription_plugin_trait_methods() {
        let plugin = WhisperCppPlugin::new("test.bin".to_string());

        // Test trait methods
        assert_eq!(plugin.name(), "whisper-cpp");
        assert_eq!(plugin.version(), "1.8.2");
        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_plugin_initialization_fails_with_invalid_path() {
        let mut plugin = WhisperCppPlugin::new("/nonexistent/path/model.bin".to_string());

        // Initialization should fail with invalid path
        let result = plugin.initialize();

        // Should error because file doesn't exist
        assert!(result.is_err());
        if let Err(e) = result {
            match e {
                PluginError::TranscriptionFailed(msg) => {
                    assert!(msg.contains("Failed to load"));
                }
                _ => panic!("Expected TranscriptionFailed error"),
            }
        }
    }

    #[test]
    fn test_double_shutdown() {
        let mut plugin = WhisperCppPlugin::new("test.bin".to_string());

        // First shutdown
        let result1 = plugin.shutdown();
        assert!(result1.is_ok());

        // Second shutdown should also be ok (idempotent)
        let result2 = plugin.shutdown();
        assert!(result2.is_ok());

        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_audio_duration_calculation() {
        let sample_rate = 16000;
        let duration_seconds = 5;
        let expected_samples = sample_rate * duration_seconds;

        let audio = AudioData {
            samples: vec![0.0; expected_samples],
            sample_rate: sample_rate as u32,
            channels: 1,
        };

        // Calculate duration from samples
        let actual_duration = audio.samples.len() as f64 / audio.sample_rate as f64;

        assert!((actual_duration - duration_seconds as f64).abs() < 0.001);
    }
}
