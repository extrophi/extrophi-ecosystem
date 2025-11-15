//! Database models

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

// ===== Stage B Models =====

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

// ===== C2 Models =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatSession {
    pub id: Option<i64>,
    pub title: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: Option<i64>,
    pub session_id: i64,
    pub recording_id: Option<i64>,
    pub role: MessageRole,
    pub content: String,
    pub privacy_tags: Option<Vec<String>>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum MessageRole {
    User,
    Assistant,
}

impl MessageRole {
    pub fn as_str(&self) -> &str {
        match self {
            MessageRole::User => "user",
            MessageRole::Assistant => "assistant",
        }
    }

    pub fn from_str(s: &str) -> Result<Self, String> {
        match s {
            "user" => Ok(MessageRole::User),
            "assistant" => Ok(MessageRole::Assistant),
            _ => Err(format!("Invalid message role: {}", s)),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptTemplate {
    pub id: Option<i64>,
    pub name: String,
    pub system_prompt: String,
    pub description: Option<String>,
    pub is_default: bool,
    pub created_at: DateTime<Utc>,
}
