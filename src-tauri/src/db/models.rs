//! Database models

use chrono::{DateTime, Utc};

#[derive(Debug, Clone)]
pub struct Recording {
    pub id: Option<i64>,
    pub filepath: String,
    pub duration_ms: i64,
    pub sample_rate: i32,
    pub channels: i16,
    pub file_size_bytes: Option<i64>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone)]
pub struct Transcript {
    pub id: Option<i64>,
    pub recording_id: i64,
    pub text: String,
    pub language: Option<String>,
    pub confidence: f32,
    pub plugin_name: String,
    pub transcription_duration_ms: Option<i64>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone)]
pub struct Segment {
    pub id: Option<i64>,
    pub transcript_id: i64,
    pub start_ms: i64,
    pub end_ms: i64,
    pub text: String,
    pub confidence: f32,
}
