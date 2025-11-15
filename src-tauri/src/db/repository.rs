//! Repository pattern for database access

use super::models::*;
use chrono::Utc;
use rusqlite::{Connection, Result as SqliteResult, params};

pub struct Repository {
    conn: Connection,
}

impl Repository {
    pub fn new(conn: Connection) -> Self {
        Self { conn }
    }

    // ===== Recordings =====

    pub fn create_recording(&self, rec: &Recording) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO recordings (filepath, duration_ms, sample_rate, channels, file_size_bytes, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                rec.filepath,
                rec.duration_ms,
                rec.sample_rate,
                rec.channels,
                rec.file_size_bytes,
                rec.created_at.to_rfc3339(),
                rec.updated_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn get_recording(&self, id: i64) -> SqliteResult<Recording> {
        self.conn.query_row(
            "SELECT id, filepath, duration_ms, sample_rate, channels, file_size_bytes, created_at, updated_at
             FROM recordings WHERE id = ?1",
            params![id],
            |row| {
                Ok(Recording {
                    id: Some(row.get(0)?),
                    filepath: row.get(1)?,
                    duration_ms: row.get(2)?,
                    sample_rate: row.get(3)?,
                    channels: row.get(4)?,
                    file_size_bytes: row.get(5)?,
                    created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    pub fn list_recordings(&self, limit: usize) -> SqliteResult<Vec<Recording>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, filepath, duration_ms, sample_rate, channels, file_size_bytes, created_at, updated_at
             FROM recordings ORDER BY created_at DESC LIMIT ?1"
        )?;

        let recordings = stmt.query_map(params![limit], |row| {
            Ok(Recording {
                id: Some(row.get(0)?),
                filepath: row.get(1)?,
                duration_ms: row.get(2)?,
                sample_rate: row.get(3)?,
                channels: row.get(4)?,
                file_size_bytes: row.get(5)?,
                created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        recordings.collect()
    }

    pub fn delete_recording(&self, id: i64) -> SqliteResult<()> {
        self.conn.execute("DELETE FROM recordings WHERE id = ?1", params![id])?;
        Ok(())
    }

    // ===== Transcripts =====

    pub fn create_transcript(&self, trans: &Transcript) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO transcripts (recording_id, text, language, confidence, plugin_name, transcription_duration_ms, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                trans.recording_id,
                trans.text,
                trans.language,
                trans.confidence,
                trans.plugin_name,
                trans.transcription_duration_ms,
                trans.created_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn get_transcript_by_recording(&self, recording_id: i64) -> SqliteResult<Transcript> {
        self.conn.query_row(
            "SELECT id, recording_id, text, language, confidence, plugin_name, transcription_duration_ms, created_at
             FROM transcripts WHERE recording_id = ?1 ORDER BY created_at DESC LIMIT 1",
            params![recording_id],
            |row| {
                Ok(Transcript {
                    id: Some(row.get(0)?),
                    recording_id: row.get(1)?,
                    text: row.get(2)?,
                    language: row.get(3)?,
                    confidence: row.get(4)?,
                    plugin_name: row.get(5)?,
                    transcription_duration_ms: row.get(6)?,
                    created_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    pub fn list_transcripts_by_recording(&self, recording_id: i64) -> SqliteResult<Vec<Transcript>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, recording_id, text, language, confidence, plugin_name, transcription_duration_ms, created_at
             FROM transcripts WHERE recording_id = ?1 ORDER BY created_at DESC"
        )?;

        let transcripts = stmt.query_map(params![recording_id], |row| {
            Ok(Transcript {
                id: Some(row.get(0)?),
                recording_id: row.get(1)?,
                text: row.get(2)?,
                language: row.get(3)?,
                confidence: row.get(4)?,
                plugin_name: row.get(5)?,
                transcription_duration_ms: row.get(6)?,
                created_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        transcripts.collect()
    }

    // ===== Segments =====

    pub fn create_segment(&self, seg: &Segment) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO segments (transcript_id, start_ms, end_ms, text, confidence)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                seg.transcript_id,
                seg.start_ms,
                seg.end_ms,
                seg.text,
                seg.confidence,
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn list_segments_by_transcript(&self, transcript_id: i64) -> SqliteResult<Vec<Segment>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, transcript_id, start_ms, end_ms, text, confidence
             FROM segments WHERE transcript_id = ?1 ORDER BY start_ms"
        )?;

        let segments = stmt.query_map(params![transcript_id], |row| {
            Ok(Segment {
                id: Some(row.get(0)?),
                transcript_id: row.get(1)?,
                start_ms: row.get(2)?,
                end_ms: row.get(3)?,
                text: row.get(4)?,
                confidence: row.get(5)?,
            })
        })?;

        segments.collect()
    }

    // ===== Chat Sessions (C2) =====

    pub fn create_chat_session(&self, session: &ChatSession) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO chat_sessions (title, created_at, updated_at)
             VALUES (?1, ?2, ?3)",
            params![
                session.title,
                session.created_at.to_rfc3339(),
                session.updated_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn get_chat_session(&self, id: i64) -> SqliteResult<ChatSession> {
        self.conn.query_row(
            "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?1",
            params![id],
            |row| {
                Ok(ChatSession {
                    id: Some(row.get(0)?),
                    title: row.get(1)?,
                    created_at: row.get::<_, String>(2)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    pub fn list_chat_sessions(&self, limit: usize) -> SqliteResult<Vec<ChatSession>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, title, created_at, updated_at
             FROM chat_sessions ORDER BY updated_at DESC LIMIT ?1"
        )?;

        let sessions = stmt.query_map(params![limit], |row| {
            Ok(ChatSession {
                id: Some(row.get(0)?),
                title: row.get(1)?,
                created_at: row.get::<_, String>(2)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        sessions.collect()
    }

    pub fn update_chat_session_title(&self, id: i64, title: &str) -> SqliteResult<()> {
        self.conn.execute(
            "UPDATE chat_sessions SET title = ?1, updated_at = ?2 WHERE id = ?3",
            params![title, Utc::now().to_rfc3339(), id],
        )?;
        Ok(())
    }

    pub fn delete_chat_session(&self, id: i64) -> SqliteResult<()> {
        self.conn.execute("DELETE FROM chat_sessions WHERE id = ?1", params![id])?;
        Ok(())
    }

    // ===== Messages (C2) =====

    pub fn create_message(&self, msg: &Message) -> SqliteResult<i64> {
        let privacy_tags_json = msg.privacy_tags.as_ref()
            .map(|tags| serde_json::to_string(tags).unwrap_or_default());

        self.conn.execute(
            "INSERT INTO messages (session_id, recording_id, role, content, privacy_tags, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                msg.session_id,
                msg.recording_id,
                msg.role.as_str(),
                msg.content,
                privacy_tags_json,
                msg.created_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn list_messages_by_session(&self, session_id: i64) -> SqliteResult<Vec<Message>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, session_id, recording_id, role, content, privacy_tags, created_at
             FROM messages WHERE session_id = ?1 ORDER BY created_at ASC"
        )?;

        let messages = stmt.query_map(params![session_id], |row| {
            let privacy_tags_str: Option<String> = row.get(5)?;
            let privacy_tags = privacy_tags_str
                .and_then(|s| serde_json::from_str(&s).ok());

            Ok(Message {
                id: Some(row.get(0)?),
                session_id: row.get(1)?,
                recording_id: row.get(2)?,
                role: MessageRole::from_str(&row.get::<_, String>(3)?).unwrap_or(MessageRole::User),
                content: row.get(4)?,
                privacy_tags,
                created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        messages.collect()
    }

    // ===== Prompt Templates (C2) =====

    pub fn create_prompt_template(&self, template: &PromptTemplate) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO prompt_templates (name, system_prompt, description, is_default, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                template.name,
                template.system_prompt,
                template.description,
                template.is_default as i32,
                template.created_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn get_prompt_template_by_name(&self, name: &str) -> SqliteResult<PromptTemplate> {
        self.conn.query_row(
            "SELECT id, name, system_prompt, description, is_default, created_at
             FROM prompt_templates WHERE name = ?1",
            params![name],
            |row| {
                Ok(PromptTemplate {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    system_prompt: row.get(2)?,
                    description: row.get(3)?,
                    is_default: row.get::<_, i32>(4)? != 0,
                    created_at: row.get::<_, String>(5)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    pub fn list_prompt_templates(&self) -> SqliteResult<Vec<PromptTemplate>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, system_prompt, description, is_default, created_at
             FROM prompt_templates ORDER BY name ASC"
        )?;

        let templates = stmt.query_map([], |row| {
            Ok(PromptTemplate {
                id: Some(row.get(0)?),
                name: row.get(1)?,
                system_prompt: row.get(2)?,
                description: row.get(3)?,
                is_default: row.get::<_, i32>(4)? != 0,
                created_at: row.get::<_, String>(5)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        templates.collect()
    }

    pub fn get_default_prompt_template(&self) -> SqliteResult<PromptTemplate> {
        self.conn.query_row(
            "SELECT id, name, system_prompt, description, is_default, created_at
             FROM prompt_templates WHERE is_default = 1 LIMIT 1",
            [],
            |row| {
                Ok(PromptTemplate {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    system_prompt: row.get(2)?,
                    description: row.get(3)?,
                    is_default: row.get::<_, i32>(4)? != 0,
                    created_at: row.get::<_, String>(5)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    // ===== Search =====

    pub fn search_recordings(&self, query: &str) -> SqliteResult<Vec<Recording>> {
        let search_pattern = format!("%{}%", query);
        let mut stmt = self.conn.prepare(
            "SELECT DISTINCT r.id, r.filepath, r.duration_ms, r.sample_rate, r.channels, r.file_size_bytes, r.created_at, r.updated_at
             FROM recordings r
             JOIN transcripts t ON r.id = t.recording_id
             WHERE t.text LIKE ?1
             ORDER BY r.created_at DESC"
        )?;

        let recordings = stmt.query_map(params![search_pattern], |row| {
            Ok(Recording {
                id: Some(row.get(0)?),
                filepath: row.get(1)?,
                duration_ms: row.get(2)?,
                sample_rate: row.get(3)?,
                channels: row.get(4)?,
                file_size_bytes: row.get(5)?,
                created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        recordings.collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::initialize_db;

    #[test]
    fn test_crud_operations() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create recording
        let recording = Recording {
            id: None,
            filepath: "test.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(160000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let rec_id = repo.create_recording(&recording).unwrap();
        assert!(rec_id > 0);

        // Read recording
        let fetched = repo.get_recording(rec_id).unwrap();
        assert_eq!(fetched.filepath, "test.wav");
        assert_eq!(fetched.duration_ms, 5000);

        // Create transcript
        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "Hello world".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1500),
            created_at: Utc::now(),
        };

        let trans_id = repo.create_transcript(&transcript).unwrap();
        assert!(trans_id > 0);

        // Fetch transcript
        let fetched_trans = repo.get_transcript_by_recording(rec_id).unwrap();
        assert_eq!(fetched_trans.text, "Hello world");
        assert_eq!(fetched_trans.plugin_name, "whisper-cpp");

        // Delete recording (should cascade to transcript)
        repo.delete_recording(rec_id).unwrap();

        // Verify deletion
        assert!(repo.get_recording(rec_id).is_err());
    }

    #[test]
    fn test_chat_sessions() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create session
        let session = ChatSession {
            id: None,
            title: Some("Test Session".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let session_id = repo.create_chat_session(&session).unwrap();
        assert!(session_id > 0);

        // Fetch session
        let fetched = repo.get_chat_session(session_id).unwrap();
        assert_eq!(fetched.title, Some("Test Session".to_string()));

        // Update title
        repo.update_chat_session_title(session_id, "Updated Title").unwrap();
        let updated = repo.get_chat_session(session_id).unwrap();
        assert_eq!(updated.title, Some("Updated Title".to_string()));

        // Delete session
        repo.delete_chat_session(session_id).unwrap();
        assert!(repo.get_chat_session(session_id).is_err());
    }

    #[test]
    fn test_messages() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create session first
        let session = ChatSession {
            id: None,
            title: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = repo.create_chat_session(&session).unwrap();

        // Create user message
        let user_msg = Message {
            id: None,
            session_id,
            recording_id: None,
            role: MessageRole::User,
            content: "Test user message".to_string(),
            privacy_tags: Some(vec!["email".to_string()]),
            created_at: Utc::now(),
        };

        let msg_id = repo.create_message(&user_msg).unwrap();
        assert!(msg_id > 0);

        // Create assistant message
        let assistant_msg = Message {
            id: None,
            session_id,
            recording_id: None,
            role: MessageRole::Assistant,
            content: "Test assistant response".to_string(),
            privacy_tags: None,
            created_at: Utc::now(),
        };

        repo.create_message(&assistant_msg).unwrap();

        // List messages
        let messages = repo.list_messages_by_session(session_id).unwrap();
        assert_eq!(messages.len(), 2);
        assert_eq!(messages[0].content, "Test user message");
        assert_eq!(messages[1].content, "Test assistant response");
    }

    #[test]
    fn test_prompt_templates() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Default templates should exist
        let templates = repo.list_prompt_templates().unwrap();
        assert_eq!(templates.len(), 2);

        // Get by name
        let daily = repo.get_prompt_template_by_name("daily_reflection").unwrap();
        assert!(daily.is_default);

        let crisis = repo.get_prompt_template_by_name("crisis_support").unwrap();
        assert!(!crisis.is_default);

        // Get default
        let default = repo.get_default_prompt_template().unwrap();
        assert_eq!(default.name, "daily_reflection");
    }
}
