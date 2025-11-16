//! Repository pattern for database access

use super::models::*;
use chrono::Utc;
use rusqlite::{Connection, Result as SqliteResult, params, OptionalExtension};

// Import usage statistics models
use super::models::{UsageEvent, UsageStats, ProviderUsage, PromptUsage};

// Import tagging models
use super::models::Tag;

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

    // ===== App Settings (Metadata) =====

    pub fn get_app_setting(&self, key: &str) -> SqliteResult<Option<String>> {
        let result = self.conn.query_row(
            "SELECT value FROM metadata WHERE key = ?1",
            params![key],
            |row| row.get(0),
        ).optional()?;

        Ok(result)
    }

    pub fn set_app_setting(&self, key: &str, value: &str) -> SqliteResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?1, ?2, ?3)",
            params![key, value, Utc::now().to_rfc3339()],
        )?;
        Ok(())
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

    // ===== User-Created Prompts (Issue #3) =====

    pub fn list_user_prompts(&self) -> SqliteResult<Vec<Prompt>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, title, content, is_system, created_at, updated_at
             FROM prompts ORDER BY is_system DESC, created_at DESC"
        )?;

        let prompts = stmt.query_map([], |row| {
            Ok(Prompt {
                id: Some(row.get(0)?),
                name: row.get(1)?,
                title: row.get(2)?,
                content: row.get(3)?,
                is_system: row.get::<_, i64>(4)? == 1,
                created_at: row.get::<_, String>(5)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        prompts.collect()
    }

    pub fn get_user_prompt(&self, id: i64) -> SqliteResult<Prompt> {
        self.conn.query_row(
            "SELECT id, name, title, content, is_system, created_at, updated_at
             FROM prompts WHERE id = ?1",
            params![id],
            |row| {
                Ok(Prompt {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    title: row.get(2)?,
                    content: row.get(3)?,
                    is_system: row.get::<_, i64>(4)? == 1,
                    created_at: row.get::<_, String>(5)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    pub fn get_user_prompt_by_name(&self, name: &str) -> SqliteResult<Prompt> {
        self.conn.query_row(
            "SELECT id, name, title, content, is_system, created_at, updated_at
             FROM prompts WHERE name = ?1",
            params![name],
            |row| {
                Ok(Prompt {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    title: row.get(2)?,
                    content: row.get(3)?,
                    is_system: row.get::<_, i64>(4)? == 1,
                    created_at: row.get::<_, String>(5)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    pub fn create_user_prompt(&self, name: &str, title: &str, content: &str) -> SqliteResult<i64> {
        let now = Utc::now();

        self.conn.execute(
            "INSERT INTO prompts (name, title, content, is_system, created_at, updated_at)
             VALUES (?1, ?2, ?3, 0, ?4, ?5)",
            params![name, title, content, now.to_rfc3339(), now.to_rfc3339()]
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    pub fn update_user_prompt(&self, id: i64, title: &str, content: &str) -> SqliteResult<usize> {
        let now = Utc::now();

        // Check if prompt is a system prompt
        let is_system: i64 = self.conn.query_row(
            "SELECT is_system FROM prompts WHERE id = ?1",
            params![id],
            |row| row.get(0)
        )?;

        if is_system == 1 {
            return Err(rusqlite::Error::InvalidParameterName("Cannot modify system prompts".to_string()));
        }

        self.conn.execute(
            "UPDATE prompts SET title = ?1, content = ?2, updated_at = ?3 WHERE id = ?4",
            params![title, content, now.to_rfc3339(), id]
        )
    }

    pub fn delete_user_prompt(&self, id: i64) -> SqliteResult<usize> {
        // Check if prompt is a system prompt
        let is_system: i64 = self.conn.query_row(
            "SELECT is_system FROM prompts WHERE id = ?1",
            params![id],
            |row| row.get(0)
        )?;

        if is_system == 1 {
            return Err(rusqlite::Error::InvalidParameterName("Cannot delete system prompts".to_string()));
        }

        self.conn.execute("DELETE FROM prompts WHERE id = ?1", params![id])
    }

    // ===== Usage Statistics (Issue #10) =====

    /// Track a usage event
    pub fn track_usage_event(&self, event: &UsageEvent) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO usage_events (event_type, provider, prompt_name, token_count, recording_duration_ms, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                event.event_type,
                event.provider,
                event.prompt_name,
                event.token_count,
                event.recording_duration_ms,
                event.created_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    // ===== Tag Management (Issue #13) =====

    /// Get all tags
    pub fn list_tags(&self) -> SqliteResult<Vec<Tag>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, color, created_at
             FROM tags ORDER BY name ASC"
        )?;

        let tags = stmt.query_map([], |row| {
            Ok(Tag {
                id: Some(row.get(0)?),
                name: row.get(1)?,
                color: row.get(2)?,
                created_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        tags.collect()
    }

    /// Get a tag by ID
    pub fn get_tag(&self, tag_id: i64) -> SqliteResult<Tag> {
        self.conn.query_row(
            "SELECT id, name, color, created_at
             FROM tags WHERE id = ?1",
            params![tag_id],
            |row| {
                Ok(Tag {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    color: row.get(2)?,
                    created_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    /// Create a new tag
    pub fn create_tag(&self, name: &str, color: &str) -> SqliteResult<i64> {
        let now = Utc::now();

        self.conn.execute(
            "INSERT INTO tags (name, color, created_at) VALUES (?1, ?2, ?3)",
            params![name, color, now.to_rfc3339()]
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    /// Rename a tag
    pub fn rename_tag(&self, tag_id: i64, new_name: &str) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE tags SET name = ?1 WHERE id = ?2",
            params![new_name, tag_id]
        )
    }

    /// Update tag color
    pub fn update_tag_color(&self, tag_id: i64, color: &str) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE tags SET color = ?1 WHERE id = ?2",
            params![color, tag_id]
        )
    }

    /// Delete a tag (will cascade to session_tags)
    pub fn delete_tag(&self, tag_id: i64) -> SqliteResult<usize> {
        self.conn.execute("DELETE FROM tags WHERE id = ?1", params![tag_id])
    }

    /// Add a tag to a session
    pub fn add_tag_to_session(&self, session_id: i64, tag_id: i64) -> SqliteResult<usize> {
        let now = Utc::now();

        self.conn.execute(
            "INSERT OR IGNORE INTO session_tags (session_id, tag_id, created_at)
             VALUES (?1, ?2, ?3)",
            params![session_id, tag_id, now.to_rfc3339()]
        )
    }

    /// Remove a tag from a session
    pub fn remove_tag_from_session(&self, session_id: i64, tag_id: i64) -> SqliteResult<usize> {
        self.conn.execute(
            "DELETE FROM session_tags WHERE session_id = ?1 AND tag_id = ?2",
            params![session_id, tag_id]
        )
    }

    /// Get all tags for a specific session
    pub fn get_session_tags(&self, session_id: i64) -> SqliteResult<Vec<Tag>> {
        let mut stmt = self.conn.prepare(
            "SELECT t.id, t.name, t.color, t.created_at
             FROM tags t
             INNER JOIN session_tags st ON t.id = st.tag_id
             WHERE st.session_id = ?1
             ORDER BY t.name ASC"
        )?;

        let tags = stmt.query_map(params![session_id], |row| {
            Ok(Tag {
                id: Some(row.get(0)?),
                name: row.get(1)?,
                color: row.get(2)?,
                created_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        tags.collect()
    }

    /// Get sessions filtered by tags
    /// mode: "any" (has any of these tags) or "all" (has all of these tags)
    pub fn get_sessions_by_tags(&self, tag_ids: &[i64], mode: &str, limit: usize) -> SqliteResult<Vec<ChatSession>> {
        if tag_ids.is_empty() {
            return self.list_chat_sessions(limit);
        }

        let query = if mode == "all" {
            // Session must have ALL specified tags
            format!(
                "SELECT DISTINCT cs.id, cs.title, cs.created_at, cs.updated_at
                 FROM chat_sessions cs
                 WHERE (
                     SELECT COUNT(DISTINCT st.tag_id)
                     FROM session_tags st
                     WHERE st.session_id = cs.id
                     AND st.tag_id IN ({})
                 ) = ?1
                 ORDER BY cs.updated_at DESC
                 LIMIT ?2",
                tag_ids.iter().map(|_| "?").collect::<Vec<_>>().join(",")
            )
        } else {
            // Session must have ANY of the specified tags
            format!(
                "SELECT DISTINCT cs.id, cs.title, cs.created_at, cs.updated_at
                 FROM chat_sessions cs
                 INNER JOIN session_tags st ON cs.id = st.session_id
                 WHERE st.tag_id IN ({})
                 ORDER BY cs.updated_at DESC
                 LIMIT ?{}",
                tag_ids.iter().map(|_| "?").collect::<Vec<_>>().join(","),
                tag_ids.len() + 1
            )
        };

        let mut stmt = self.conn.prepare(&query)?;

        // Build parameters based on mode
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = vec![];
        if mode == "all" {
            params_vec.push(Box::new(tag_ids.len() as i64));
        }
        for tag_id in tag_ids {
            params_vec.push(Box::new(*tag_id));
        }
        params_vec.push(Box::new(limit as i64));

        let params_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();

        // Single query_map call to avoid closure type mismatch
        let sessions = stmt.query_map(&*params_refs, |row| {
            Ok(ChatSession {
                id: Some(row.get(0)?),
                title: row.get(1)?,
                created_at: row.get::<_, String>(2)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        sessions.collect()
    }

    /// Get tag usage count (number of sessions using each tag)
    pub fn get_tag_usage_counts(&self) -> SqliteResult<Vec<(Tag, i64)>> {
        let mut stmt = self.conn.prepare(
            "SELECT t.id, t.name, t.color, t.created_at, COUNT(st.session_id) as usage_count
             FROM tags t
             LEFT JOIN session_tags st ON t.id = st.tag_id
             GROUP BY t.id, t.name, t.color, t.created_at
             ORDER BY usage_count DESC, t.name ASC"
        )?;

        let results = stmt.query_map([], |row| {
            Ok((
                Tag {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    color: row.get(2)?,
                    created_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
                },
                row.get(4)?
            ))
        })?;

        results.collect()
    }

    /// Merge two tags (move all sessions from source_tag to target_tag, then delete source)
    pub fn merge_tags(&self, source_tag_id: i64, target_tag_id: i64) -> SqliteResult<()> {
        // Move all session_tags from source to target (ignoring duplicates)
        self.conn.execute(
            "INSERT OR IGNORE INTO session_tags (session_id, tag_id, created_at)
             SELECT session_id, ?1, created_at
             FROM session_tags
             WHERE tag_id = ?2",
            params![target_tag_id, source_tag_id]
        )?;

        // Delete the source tag (will cascade delete old session_tags)
        self.delete_tag(source_tag_id)?;

        Ok(())
    }

    /// Get usage statistics
    pub fn get_usage_stats(&self) -> SqliteResult<UsageStats> {
        // Get total sessions
        let total_sessions: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM chat_sessions",
            [],
            |row| row.get(0)
        )?;

        // Get total messages (user messages only)
        let total_messages: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM messages WHERE role = 'user'",
            [],
            |row| row.get(0)
        )?;

        // Get total recordings
        let total_recordings: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM recordings",
            [],
            |row| row.get(0)
        )?;

        // Get total recording time
        let total_recording_time_ms: i64 = self.conn.query_row(
            "SELECT COALESCE(SUM(duration_ms), 0) FROM recordings",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        // Get provider usage
        let openai_count: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM usage_events WHERE provider = 'openai' AND event_type = 'message_sent'",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        let claude_count: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM usage_events WHERE provider = 'claude' AND event_type = 'message_sent'",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        let total_provider_calls = openai_count + claude_count;
        let provider_usage = ProviderUsage {
            openai_count,
            claude_count,
            openai_percent: if total_provider_calls > 0 {
                (openai_count as f64 / total_provider_calls as f64) * 100.0
            } else { 0.0 },
            claude_percent: if total_provider_calls > 0 {
                (claude_count as f64 / total_provider_calls as f64) * 100.0
            } else { 0.0 },
        };

        // Estimate API costs
        // Rough estimate: 500 tokens per message average
        // OpenAI: $0.15 per 1M tokens = $0.00000015 per token
        // Claude: $3.00 per 1M tokens = $0.000003 per token
        let avg_tokens_per_message = 500.0;
        let openai_cost = (openai_count as f64) * avg_tokens_per_message * 0.00000015;
        let claude_cost = (claude_count as f64) * avg_tokens_per_message * 0.000003;
        let estimated_cost = openai_cost + claude_cost;

        // Get top prompts
        let mut stmt = self.conn.prepare(
            "SELECT prompt_name, COUNT(*) as usage_count
             FROM usage_events
             WHERE event_type = 'prompt_used' AND prompt_name IS NOT NULL
             GROUP BY prompt_name
             ORDER BY usage_count DESC
             LIMIT 5"
        )?;

        let top_prompts = stmt.query_map([], |row| {
            Ok(PromptUsage {
                name: row.get(0)?,
                count: row.get(1)?,
            })
        })?.collect::<SqliteResult<Vec<_>>>().unwrap_or_default();

        // Get sessions this week
        let sessions_this_week: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM chat_sessions
             WHERE created_at >= datetime('now', '-7 days')",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        // Get sessions this month
        let sessions_this_month: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM chat_sessions
             WHERE created_at >= datetime('now', 'start of month')",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        Ok(UsageStats {
            total_sessions,
            total_messages,
            total_recordings,
            total_recording_time_ms,
            estimated_cost,
            provider_usage,
            top_prompts,
            sessions_this_week,
            sessions_this_month,
        })
    }

    // ===== Backup System (Issue #14) =====

    /// Get backup settings (returns default if not initialized)
    pub fn get_backup_settings(&self) -> SqliteResult<BackupSettings> {
        match self.conn.query_row(
            "SELECT id, enabled, frequency, backup_path, retention_count, last_backup_at, updated_at
             FROM backup_settings WHERE id = 1",
            [],
            |row| {
                Ok(BackupSettings {
                    id: Some(row.get(0)?),
                    enabled: row.get::<_, i64>(1)? != 0,
                    frequency: row.get(2)?,
                    backup_path: row.get(3)?,
                    retention_count: row.get(4)?,
                    last_backup_at: row.get::<_, Option<String>>(5)?.and_then(|s| s.parse().ok()),
                    updated_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                })
            },
        ) {
            Ok(settings) => Ok(settings),
            Err(_) => {
                // Return default settings if not initialized
                Ok(BackupSettings {
                    id: Some(1),
                    enabled: true,
                    frequency: "daily".to_string(),
                    backup_path: crate::backup::BackupManager::get_default_backup_dir()
                        .to_string_lossy()
                        .to_string(),
                    retention_count: 7,
                    last_backup_at: None,
                    updated_at: Utc::now(),
                })
            }
        }
    }

    /// Initialize backup settings with defaults
    pub fn initialize_backup_settings(&self, backup_path: &str) -> SqliteResult<()> {
        self.conn.execute(
            "INSERT OR IGNORE INTO backup_settings (id, enabled, frequency, backup_path, retention_count, updated_at)
             VALUES (1, 1, 'daily', ?1, 7, ?2)",
            params![backup_path, Utc::now().to_rfc3339()],
        )?;
        Ok(())
    }

    /// Update backup settings
    pub fn update_backup_settings(&self, settings: &BackupSettings) -> SqliteResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO backup_settings (id, enabled, frequency, backup_path, retention_count, last_backup_at, updated_at)
             VALUES (1, ?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                settings.enabled as i64,
                settings.frequency,
                settings.backup_path,
                settings.retention_count,
                settings.last_backup_at.as_ref().map(|d| d.to_rfc3339()),
                Utc::now().to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    /// Update last backup time
    pub fn update_last_backup_time(&self) -> SqliteResult<()> {
        self.conn.execute(
            "UPDATE backup_settings SET last_backup_at = ?1, updated_at = ?2 WHERE id = 1",
            params![Utc::now().to_rfc3339(), Utc::now().to_rfc3339()],
        )?;
        Ok(())
    }

    /// Create a backup history entry
    pub fn create_backup_history(&self, backup: &BackupHistory) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO backup_history (file_path, file_size_bytes, created_at, is_automatic, status, error_message)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                backup.file_path,
                backup.file_size_bytes,
                backup.created_at.to_rfc3339(),
                backup.is_automatic as i64,
                backup.status,
                backup.error_message,
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    /// List backup history (most recent first)
    pub fn list_backup_history(&self, limit: usize) -> SqliteResult<Vec<BackupHistory>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, file_path, file_size_bytes, created_at, is_automatic, status, error_message
             FROM backup_history ORDER BY created_at DESC LIMIT ?1"
        )?;

        let backups = stmt.query_map(params![limit], |row| {
            Ok(BackupHistory {
                id: Some(row.get(0)?),
                file_path: row.get(1)?,
                file_size_bytes: row.get(2)?,
                created_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
                is_automatic: row.get::<_, i64>(4)? != 0,
                status: row.get(5)?,
                error_message: row.get(6)?,
            })
        })?;

        backups.collect()
    }

    /// Get backup status information
    pub fn get_backup_status(&self) -> SqliteResult<BackupStatus> {
        let settings = self.get_backup_settings()?;

        // Count total backups
        let total_backups: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM backup_history WHERE status = 'success'",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        // Calculate total backup size
        let total_backup_size_bytes: i64 = self.conn.query_row(
            "SELECT COALESCE(SUM(file_size_bytes), 0) FROM backup_history WHERE status = 'success'",
            [],
            |row| row.get(0)
        ).unwrap_or(0);

        // Calculate if backup is overdue based on frequency
        let is_overdue = if let Some(last_backup) = settings.last_backup_at {
            let hours_since_last = (Utc::now() - last_backup).num_hours();
            match settings.frequency.as_str() {
                "daily" => hours_since_last > 26, // 24h + 2h grace period
                "weekly" => hours_since_last > (7 * 24 + 2),
                _ => false,
            }
        } else {
            settings.enabled // Overdue if enabled but never backed up
        };

        // Calculate next backup due time
        let next_backup_due = if settings.enabled {
            settings.last_backup_at.map(|last| {
                match settings.frequency.as_str() {
                    "daily" => last + chrono::Duration::days(1),
                    "weekly" => last + chrono::Duration::weeks(1),
                    _ => last,
                }
            })
        } else {
            None
        };

        Ok(BackupStatus {
            enabled: settings.enabled,
            last_backup_at: settings.last_backup_at,
            next_backup_due,
            total_backups,
            total_backup_size_bytes,
            is_overdue,
        })
    }

    /// Delete old backup history entries (keeps records even if files are deleted)
    pub fn cleanup_backup_history(&self, retention_count: i64) -> SqliteResult<usize> {
        self.conn.execute(
            "DELETE FROM backup_history WHERE id IN (
                SELECT id FROM backup_history
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?1
            )",
            params![retention_count],
        )
    }

    // ===== User Preferences (Language) (Issue #12) =====

    /// Get the user's language preference
    pub fn get_language_preference(&self) -> SqliteResult<String> {
        self.conn.query_row(
            "SELECT language FROM user_preferences WHERE id = 1",
            [],
            |row| row.get(0),
        )
    }

    /// Set the user's language preference
    pub fn set_language_preference(&self, language: &str) -> SqliteResult<()> {
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE user_preferences SET language = ?1, updated_at = ?2 WHERE id = 1",
            params![language, now],
        )?;
        Ok(())
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
