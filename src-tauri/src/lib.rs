//! BrainDump Voice Processor - Stage B
//!
//! Module 7: Rust Candle Plugin (Pure Rust ML)
//! Module 8: Memory-safe audio recording using cpal and hound
//! Module 9: SQLite database with Repository pattern

use std::sync::Arc;
use parking_lot::Mutex;
use std::sync::mpsc;

pub mod audio;
pub mod db;
pub mod plugin;
pub mod error;
pub mod logging;
pub mod services;
pub mod export;
pub mod prompts;

pub use audio::{Recorder, RecorderError, RecorderResult, WavWriter};
pub use db::{initialize_db, models, repository, Recording, Repository, Segment, Transcript};
pub use plugin::{AudioData, PluginError, Transcript as PluginTranscript, TranscriptSegment, TranscriptionPlugin};
pub use error::{BrainDumpError, AudioError, DatabaseError, TranscriptionError, ClaudeApiError, OpenAiApiError};
pub use services::{ClaudeClient, OpenAiClient};

/// Commands sent to the audio thread
pub enum AudioCommand {
    StartRecording,
    StopRecording,
    GetPeakLevel,
    Shutdown,
}

/// Responses from the audio thread
pub enum AudioResponse {
    RecordingStarted,
    RecordingStopped { samples: Vec<f32>, sample_rate: u32 },
    PeakLevel(f32),
    Error(String),
}

/// Application state shared across Tauri commands
pub struct AppState {
    pub plugin_manager: Arc<Mutex<plugin::manager::PluginManager>>,
    pub db: Arc<Mutex<Repository>>,
    pub audio_tx: mpsc::Sender<(AudioCommand, mpsc::Sender<AudioResponse>)>,
    pub claude_client: Arc<Mutex<ClaudeClient>>,
    pub openai_client: Arc<OpenAiClient>,
}
