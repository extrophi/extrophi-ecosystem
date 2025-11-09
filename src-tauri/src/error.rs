// src-tauri/src/error.rs
use std::fmt;
use serde::Serialize;

/// Main error type for BrainDump
/// All errors in the app use this type
#[derive(Debug, Serialize)]
#[serde(tag = "type", content = "data")]
pub enum BrainDumpError {
    /// Audio recording errors
    Audio(AudioError),
    /// Database operation errors
    Database(DatabaseError),
    /// Transcription/model errors
    Transcription(TranscriptionError),
    /// File I/O errors (serialized as string)
    Io(String),
    /// Generic errors with context
    Other(String),
}

/// Audio recording and device errors
#[derive(Debug, Serialize)]
pub enum AudioError {
    /// Microphone permission denied by user
    PermissionDenied,
    /// No audio input device found
    NoDeviceFound,
    /// Failed to initialize audio device
    DeviceInitFailed(String),
    /// Recording already in progress
    AlreadyRecording,
    /// No active recording to stop
    NotRecording,
    /// Buffer overflow or other recording error
    RecordingFailed(String),
    /// Audio buffer overflow during recording
    BufferOverflow,
    /// Audio device disconnected during recording
    StreamDisconnected,
}

/// Database operation errors
#[derive(Debug, Serialize)]
pub enum DatabaseError {
    /// Failed to open/create database file
    ConnectionFailed(String),
    /// Database file corrupted
    Corrupted,
    /// Failed to write to database
    WriteFailed(String),
    /// Failed to read from database
    ReadFailed(String),
    /// Database locked by another process
    Locked,
    /// Not enough disk space for operation
    InsufficientDiskSpace,
    /// Transaction failed and was rolled back
    TransactionFailed(String),
}

/// Transcription and model errors
#[derive(Debug, Serialize)]
pub enum TranscriptionError {
    /// Model file not found at expected path
    ModelNotFound(String),
    /// Model file exists but failed to load
    ModelLoadFailed(String),
    /// Model not initialized yet
    ModelNotReady,
    /// Transcription process failed
    TranscriptionFailed(String),
    /// Transcription timeout (took too long)
    Timeout,
    /// Invalid audio data format
    InvalidAudioData,
    /// No speech detected in audio (blank/silent)
    BlankAudio,
    /// Metal GPU acceleration failed, falling back to CPU
    MetalGPUFailed,
}

// Implement Display trait for user-facing messages
impl fmt::Display for BrainDumpError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BrainDumpError::Audio(e) => write!(f, "Audio Error: {}", e),
            BrainDumpError::Database(e) => write!(f, "Database Error: {}", e),
            BrainDumpError::Transcription(e) => write!(f, "Transcription Error: {}", e),
            BrainDumpError::Io(e) => write!(f, "File Error: {}", e),
            BrainDumpError::Other(msg) => write!(f, "{}", msg),
        }
    }
}

impl fmt::Display for AudioError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AudioError::PermissionDenied => {
                write!(f, "Microphone permission denied. Please grant access in System Settings → Privacy & Security → Microphone")
            }
            AudioError::NoDeviceFound => {
                write!(f, "No microphone found. Please connect a microphone and try again")
            }
            AudioError::DeviceInitFailed(msg) => {
                write!(f, "Failed to initialize microphone: {}", msg)
            }
            AudioError::AlreadyRecording => {
                write!(f, "Recording already in progress")
            }
            AudioError::NotRecording => {
                write!(f, "No active recording to stop")
            }
            AudioError::RecordingFailed(msg) => {
                write!(f, "Recording failed: {}", msg)
            }
            AudioError::BufferOverflow => {
                write!(f, "Audio buffer overflow. Try reducing system load and try again")
            }
            AudioError::StreamDisconnected => {
                write!(f, "Audio device disconnected. Please reconnect your microphone and try again")
            }
        }
    }
}

impl fmt::Display for DatabaseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DatabaseError::ConnectionFailed(msg) => {
                write!(f, "Failed to open database: {}", msg)
            }
            DatabaseError::Corrupted => {
                write!(f, "Database file is corrupted. You may need to reset the app")
            }
            DatabaseError::WriteFailed(msg) => {
                write!(f, "Failed to save to database: {}", msg)
            }
            DatabaseError::ReadFailed(msg) => {
                write!(f, "Failed to read from database: {}", msg)
            }
            DatabaseError::Locked => {
                write!(f, "Database is locked. Close other BrainDump instances and try again")
            }
            DatabaseError::InsufficientDiskSpace => {
                write!(f, "Not enough disk space. Please free up at least 100MB and try again")
            }
            DatabaseError::TransactionFailed(msg) => {
                write!(f, "Database transaction failed: {}. Your data is safe, please try again", msg)
            }
        }
    }
}

impl fmt::Display for TranscriptionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TranscriptionError::ModelNotFound(path) => {
                write!(f, "Whisper AI model not found at: {}", path)
            }
            TranscriptionError::ModelLoadFailed(msg) => {
                write!(f, "Failed to load Whisper model: {}", msg)
            }
            TranscriptionError::ModelNotReady => {
                write!(f, "Whisper model is still loading. Please wait a moment")
            }
            TranscriptionError::TranscriptionFailed(msg) => {
                write!(f, "Transcription failed: {}", msg)
            }
            TranscriptionError::Timeout => {
                write!(f, "Transcription timed out. The audio may be too long")
            }
            TranscriptionError::InvalidAudioData => {
                write!(f, "Invalid audio data. Recording may be corrupted")
            }
            TranscriptionError::BlankAudio => {
                write!(f, "No speech detected. Please speak clearly and try again")
            }
            TranscriptionError::MetalGPUFailed => {
                write!(f, "GPU acceleration failed, using CPU instead (may be slower)")
            }
        }
    }
}

// Implement std::error::Error trait
impl std::error::Error for BrainDumpError {}
impl std::error::Error for AudioError {}
impl std::error::Error for DatabaseError {}
impl std::error::Error for TranscriptionError {}

// Conversions from specific errors to BrainDumpError
impl From<AudioError> for BrainDumpError {
    fn from(err: AudioError) -> Self {
        BrainDumpError::Audio(err)
    }
}

impl From<DatabaseError> for BrainDumpError {
    fn from(err: DatabaseError) -> Self {
        BrainDumpError::Database(err)
    }
}

impl From<TranscriptionError> for BrainDumpError {
    fn from(err: TranscriptionError) -> Self {
        BrainDumpError::Transcription(err)
    }
}

impl From<std::io::Error> for BrainDumpError {
    fn from(err: std::io::Error) -> Self {
        BrainDumpError::Io(err.to_string())
    }
}

// Convenience type alias
pub type Result<T> = std::result::Result<T, BrainDumpError>;