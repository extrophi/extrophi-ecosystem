//! Plugin system for BrainDump transcription engines
//!
//! This module defines the plugin trait and common types used across
//! all transcription engine implementations.

use thiserror::Error;

// Module 5: Plugin System Core
pub mod manager;
pub mod types;

// Module 6: C++ FFI Plugin (whisper.cpp wrapper)
pub mod whisper_cpp;

// Module 7: Candle Plugin (pure Rust ML)
pub mod candle;

/// Audio data passed to transcription plugins
#[derive(Debug, Clone)]
pub struct AudioData {
    /// Raw audio samples (f32, -1.0 to 1.0 range)
    pub samples: Vec<f32>,
    /// Sample rate in Hz (e.g., 16000)
    pub sample_rate: u32,
    /// Number of channels (1 = mono, 2 = stereo)
    pub channels: u16,
}

/// Transcription result from a plugin
#[derive(Debug, Clone)]
pub struct Transcript {
    /// Full transcribed text
    pub text: String,
    /// Detected or specified language (ISO 639-1 code)
    pub language: Option<String>,
    /// Timestamped segments
    pub segments: Vec<TranscriptSegment>,
}

/// A single segment of transcribed audio with timing
#[derive(Debug, Clone)]
pub struct TranscriptSegment {
    /// Start time in milliseconds
    pub start_ms: u64,
    /// End time in milliseconds
    pub end_ms: u64,
    /// Text for this segment
    pub text: String,
    /// Confidence score (0.0 to 1.0)
    pub confidence: f32,
}

/// Plugin errors
#[derive(Debug, Error)]
pub enum PluginError {
    #[error("Plugin not found: {0}")]
    NotFound(String),

    #[error("Plugin not initialized: {0}")]
    NotInitialized(String),

    #[error("Transcription failed: {0}")]
    TranscriptionFailed(String),

    #[error("Plugin initialization failed: {0}")]
    InitializationFailed(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    // Legacy error variants (for compatibility with Module 7/8)
    #[error("Model file not found: {0}")]
    ModelNotFound(String),

    #[error("Invalid audio format: {0}")]
    InvalidAudioFormat(String),

    #[error("Device initialization failed: {0}")]
    DeviceInitFailed(String),
}

/// Result type alias for plugin operations
pub type PluginResult<T> = Result<T, PluginError>;

/// Trait that all transcription plugins must implement
pub trait TranscriptionPlugin: Send + Sync {
    /// Plugin name (e.g., "candle", "whisper-cpp")
    fn name(&self) -> &str;

    /// Plugin version
    fn version(&self) -> &str;

    /// Initialize the plugin (load models, etc.)
    fn initialize(&mut self) -> Result<(), PluginError>;

    /// Transcribe audio data
    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError>;

    /// Shutdown the plugin (cleanup resources)
    fn shutdown(&mut self) -> Result<(), PluginError>;

    /// Check if plugin is initialized
    fn is_initialized(&self) -> bool;
}
