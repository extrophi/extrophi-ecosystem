//! BrainDump Voice Processor - Stage B
//!
//! Module 7: Rust Candle Plugin (Pure Rust ML)
//! Module 8: Memory-safe audio recording using cpal and hound
//! Module 9: SQLite database with Repository pattern

use parking_lot::Mutex;
use std::sync::mpsc;
use std::sync::Arc;

pub mod audio;
pub mod backup;
pub mod db;
pub mod error;
pub mod export;
pub mod git;
pub mod logging;
pub mod plugin;
pub mod prompts;
pub mod services;

pub use audio::{Recorder, RecorderError, RecorderResult, WavWriter};
pub use db::{initialize_db, models, repository, Recording, Repository, Segment, Transcript};
pub use error::{
    AudioError, BrainDumpError, ClaudeApiError, DatabaseError, GitError, OpenAiApiError,
    TranscriptionError,
};
pub use git::{GitPublisher, PublishResult, PublishStatus};
pub use plugin::{
    AudioData, PluginError, Transcript as PluginTranscript, TranscriptSegment, TranscriptionPlugin,
};
pub use services::{ClaudeClient, OpenAiClient};

/// Commands sent to the audio thread
pub enum AudioCommand {
    StartRecording,
    StopRecording,
    PauseRecording,
    ResumeRecording,
    GetPeakLevel,
    Shutdown,
}

/// Responses from the audio thread
pub enum AudioResponse {
    RecordingStarted,
    RecordingStopped { samples: Vec<f32>, sample_rate: u32 },
    RecordingPaused,
    RecordingResumed,
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
