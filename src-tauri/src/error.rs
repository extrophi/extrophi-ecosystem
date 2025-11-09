// src-tauri/src/error.rs
use std::fmt;

/// Main error type for BrainDump
/// All errors in the app use this type
#[derive(Debug)]
pub enum BrainDumpError {
    /// Audio recording errors
    Audio(AudioError),
    /// Database operation errors
    Database(DatabaseError),
    /// Transcription/model errors
    Transcription(TranscriptionError),
    /// File I/O errors
    Io(std::io::Error),
    /// Generic errors with context
    Other(String),
}

/// Audio recording and device errors
#[derive(Debug)]
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
}

/// Database operation errors
#[derive(Debug)]
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
}

/// Transcription and model errors
#[derive(Debug)]
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
        BrainDumpError::Io(err)
    }
}

// Convenience type alias
pub type Result<T> = std::result::Result<T, BrainDumpError>;