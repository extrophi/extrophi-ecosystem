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

// ===== User-Created Prompts (Issue #3) =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Prompt {
    pub id: Option<i64>,
    pub name: String,
    pub title: String,
    pub content: String,
    pub is_system: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

// ===== Usage Statistics (Issue #10) =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageEvent {
    pub id: Option<i64>,
    pub event_type: String,
    pub provider: Option<String>,
    pub prompt_name: Option<String>,
    pub token_count: Option<i64>,
    pub recording_duration_ms: Option<i64>,
    pub created_at: DateTime<Utc>,
}

// ===== Session Tagging System (Issue #13) =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tag {
    pub id: Option<i64>,
    pub name: String,
    pub color: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionTag {
    pub session_id: i64,
    pub tag_id: i64,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageStats {
    pub total_sessions: i64,
    pub total_messages: i64,
    pub total_recordings: i64,
    pub total_recording_time_ms: i64,
    pub estimated_cost: f64,
    pub provider_usage: ProviderUsage,
    pub top_prompts: Vec<PromptUsage>,
    pub sessions_this_week: i64,
    pub sessions_this_month: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderUsage {
    pub openai_count: i64,
    pub claude_count: i64,
    pub openai_percent: f64,
    pub claude_percent: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptUsage {
    pub name: String,
    pub count: i64,
}

// ===== Backup System (Issue #14) =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupSettings {
    pub id: Option<i64>,
    pub enabled: bool,
    pub frequency: String, // "daily", "weekly", "manual"
    pub backup_path: String,
    pub retention_count: i64,
    pub last_backup_at: Option<DateTime<Utc>>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupHistory {
    pub id: Option<i64>,
    pub file_path: String,
    pub file_size_bytes: i64,
    pub created_at: DateTime<Utc>,
    pub is_automatic: bool,
    pub status: String, // "success" or "failed"
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupStatus {
    pub enabled: bool,
    pub last_backup_at: Option<DateTime<Utc>>,
    pub next_backup_due: Option<DateTime<Utc>>,
    pub total_backups: i64,
    pub total_backup_size_bytes: i64,
    pub is_overdue: bool,
}
