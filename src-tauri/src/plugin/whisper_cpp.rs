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
        use rubato::{Resampler, SincFixedIn, SincInterpolationType, SincInterpolationParameters, WindowFunction};

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
            ).map_err(|e| PluginError::TranscriptionFailed(format!("Resample failed: {}", e)))?;

            let waves_in = vec![audio.samples.clone()];
            let mut waves_out = resampler.process(&waves_in, None)
                .map_err(|e| PluginError::TranscriptionFailed(format!("Resample failed: {}", e)))?;

            eprintln!("✓ Resampled: {} → {} samples", audio.samples.len(), waves_out[0].len());
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

            let text = unsafe {
                CStr::from_ptr(text_ptr)
                    .to_string_lossy()
                    .into_owned()
            };

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
}