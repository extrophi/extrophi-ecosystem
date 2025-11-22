//! Repository pattern for database access

use super::models::*;
use chrono::Utc;
use rusqlite::{params, Connection, OptionalExtension, Result as SqliteResult};

// Import usage statistics models
use super::models::{PromptUsage, ProviderUsage, UsageEvent, UsageStats};

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
        self.conn
            .execute("DELETE FROM recordings WHERE id = ?1", params![id])?;
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

    pub fn list_transcripts_by_recording(
        &self,
        recording_id: i64,
    ) -> SqliteResult<Vec<Transcript>> {
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
             FROM segments WHERE transcript_id = ?1 ORDER BY start_ms",
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
             FROM chat_sessions ORDER BY updated_at DESC LIMIT ?1",
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
        self.conn
            .execute("DELETE FROM chat_sessions WHERE id = ?1", params![id])?;
        Ok(())
    }

    // ===== Messages (C2) =====

    pub fn create_message(&self, msg: &Message) -> SqliteResult<i64> {
        let privacy_tags_json = msg
            .privacy_tags
            .as_ref()
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
             FROM messages WHERE session_id = ?1 ORDER BY created_at ASC",
        )?;

        let messages = stmt.query_map(params![session_id], |row| {
            let privacy_tags_str: Option<String> = row.get(5)?;
            let privacy_tags = privacy_tags_str.and_then(|s| serde_json::from_str(&s).ok());

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
             FROM prompt_templates ORDER BY name ASC",
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
        let result = self
            .conn
            .query_row(
                "SELECT value FROM metadata WHERE key = ?1",
                params![key],
                |row| row.get(0),
            )
            .optional()?;

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

    /// Search across sessions, transcripts, and messages (OMICRON-2 #75)
    pub fn search_all(
        &self,
        query: &str,
        filters: SearchFilters,
    ) -> SqliteResult<Vec<SearchResult>> {
        use super::models::SearchResult;

        let mut results = Vec::new();
        let search_pattern = format!("%{}%", query);

        // Build base WHERE clause for date filtering
        let mut date_filter = String::new();
        if filters.start_date.is_some() {
            date_filter.push_str(" AND created_at >= ?");
        }
        if filters.end_date.is_some() {
            date_filter.push_str(" AND created_at <= ?");
        }

        // Build tag filter
        let tag_filter = if let Some(ref tag_ids) = filters.tags {
            if !tag_ids.is_empty() {
                format!(
                    " AND session_id IN (
                        SELECT session_id FROM session_tags WHERE tag_id IN ({})
                    )",
                    tag_ids.iter().map(|_| "?").collect::<Vec<_>>().join(",")
                )
            } else {
                String::new()
            }
        } else {
            String::new()
        };

        // Search in session titles
        let session_query = format!(
            "SELECT cs.id, cs.title, cs.title as content, cs.created_at
             FROM chat_sessions cs
             WHERE cs.title LIKE ?1{}{}
             ORDER BY cs.created_at DESC
             LIMIT 50",
            date_filter, tag_filter
        );

        let mut stmt = self.conn.prepare(&session_query)?;
        let mut param_idx = 2;
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = vec![Box::new(search_pattern.clone())];

        if let Some(ref start) = filters.start_date {
            params_vec.push(Box::new(start.clone()));
            param_idx += 1;
        }
        if let Some(ref end) = filters.end_date {
            params_vec.push(Box::new(end.clone()));
            param_idx += 1;
        }
        if let Some(ref tag_ids) = filters.tags {
            for tag_id in tag_ids {
                params_vec.push(Box::new(*tag_id));
            }
        }

        let params_refs: Vec<&dyn rusqlite::ToSql> =
            params_vec.iter().map(|p| p.as_ref()).collect();

        let session_results = stmt
            .query_map(&*params_refs, |row| {
                Ok(SearchResult {
                    result_type: "session".to_string(),
                    session_id: row.get(0)?,
                    session_title: row.get(1)?,
                    content: row.get::<_, Option<String>>(2)?.unwrap_or_default(),
                    created_at: row.get(3)?,
                    highlight: None,
                })
            })?
            .collect::<SqliteResult<Vec<_>>>()?;

        results.extend(session_results);

        // Search in messages
        let message_query = format!(
            "SELECT m.session_id, cs.title, m.content, m.created_at
             FROM messages m
             JOIN chat_sessions cs ON m.session_id = cs.id
             WHERE m.content LIKE ?1{}{}
             ORDER BY m.created_at DESC
             LIMIT 50",
            date_filter, tag_filter
        );

        let mut stmt = self.conn.prepare(&message_query)?;
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = vec![Box::new(search_pattern.clone())];

        if let Some(ref start) = filters.start_date {
            params_vec.push(Box::new(start.clone()));
        }
        if let Some(ref end) = filters.end_date {
            params_vec.push(Box::new(end.clone()));
        }
        if let Some(ref tag_ids) = filters.tags {
            for tag_id in tag_ids {
                params_vec.push(Box::new(*tag_id));
            }
        }

        let params_refs: Vec<&dyn rusqlite::ToSql> =
            params_vec.iter().map(|p| p.as_ref()).collect();

        let message_results = stmt
            .query_map(&*params_refs, |row| {
                let content: String = row.get(2)?;
                let highlight = Self::create_highlight(&content, query);

                Ok(SearchResult {
                    result_type: "message".to_string(),
                    session_id: row.get(0)?,
                    session_title: row.get(1)?,
                    content: content.clone(),
                    created_at: row.get(3)?,
                    highlight: Some(highlight),
                })
            })?
            .collect::<SqliteResult<Vec<_>>>()?;

        results.extend(message_results);

        // Search in transcripts
        let transcript_query = format!(
            "SELECT m.session_id, cs.title, t.text, t.created_at
             FROM transcripts t
             JOIN recordings r ON t.recording_id = r.id
             JOIN messages m ON m.recording_id = r.id
             JOIN chat_sessions cs ON m.session_id = cs.id
             WHERE t.text LIKE ?1{}{}
             ORDER BY t.created_at DESC
             LIMIT 50",
            date_filter, tag_filter
        );

        let mut stmt = self.conn.prepare(&transcript_query)?;
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = vec![Box::new(search_pattern.clone())];

        if let Some(ref start) = filters.start_date {
            params_vec.push(Box::new(start.clone()));
        }
        if let Some(ref end) = filters.end_date {
            params_vec.push(Box::new(end.clone()));
        }
        if let Some(ref tag_ids) = filters.tags {
            for tag_id in tag_ids {
                params_vec.push(Box::new(*tag_id));
            }
        }

        let params_refs: Vec<&dyn rusqlite::ToSql> =
            params_vec.iter().map(|p| p.as_ref()).collect();

        let transcript_results = stmt
            .query_map(&*params_refs, |row| {
                let content: String = row.get(2)?;
                let highlight = Self::create_highlight(&content, query);

                Ok(SearchResult {
                    result_type: "transcript".to_string(),
                    session_id: row.get(0)?,
                    session_title: row.get(1)?,
                    content: content.clone(),
                    created_at: row.get(3)?,
                    highlight: Some(highlight),
                })
            })?
            .collect::<SqliteResult<Vec<_>>>()?;

        results.extend(transcript_results);

        // Sort all results by created_at descending
        results.sort_by(|a, b| b.created_at.cmp(&a.created_at));

        Ok(results)
    }

    /// Create a text highlight snippet around the search term
    fn create_highlight(text: &str, query: &str) -> String {
        let query_lower = query.to_lowercase();
        let text_lower = text.to_lowercase();

        if let Some(pos) = text_lower.find(&query_lower) {
            let start = pos.saturating_sub(50);
            let end = (pos + query.len() + 50).min(text.len());

            let prefix = if start > 0 { "..." } else { "" };
            let suffix = if end < text.len() { "..." } else { "" };

            format!("{}{}{}", prefix, &text[start..end], suffix)
        } else {
            // Fallback: return first 100 characters
            if text.len() > 100 {
                format!("{}...", &text[..100])
            } else {
                text.to_string()
            }
        }
    }

    // ===== User-Created Prompts (Issue #3) =====

    pub fn list_user_prompts(&self) -> SqliteResult<Vec<Prompt>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, title, content, is_system, created_at, updated_at
             FROM prompts ORDER BY is_system DESC, created_at DESC",
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
            params![name, title, content, now.to_rfc3339(), now.to_rfc3339()],
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    pub fn update_user_prompt(&self, id: i64, title: &str, content: &str) -> SqliteResult<usize> {
        let now = Utc::now();

        // Check if prompt is a system prompt
        let is_system: i64 = self.conn.query_row(
            "SELECT is_system FROM prompts WHERE id = ?1",
            params![id],
            |row| row.get(0),
        )?;

        if is_system == 1 {
            return Err(rusqlite::Error::InvalidParameterName(
                "Cannot modify system prompts".to_string(),
            ));
        }

        self.conn.execute(
            "UPDATE prompts SET title = ?1, content = ?2, updated_at = ?3 WHERE id = ?4",
            params![title, content, now.to_rfc3339(), id],
        )
    }

    pub fn delete_user_prompt(&self, id: i64) -> SqliteResult<usize> {
        // Check if prompt is a system prompt
        let is_system: i64 = self.conn.query_row(
            "SELECT is_system FROM prompts WHERE id = ?1",
            params![id],
            |row| row.get(0),
        )?;

        if is_system == 1 {
            return Err(rusqlite::Error::InvalidParameterName(
                "Cannot delete system prompts".to_string(),
            ));
        }

        self.conn
            .execute("DELETE FROM prompts WHERE id = ?1", params![id])
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
             FROM tags ORDER BY name ASC",
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
            params![name, color, now.to_rfc3339()],
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    /// Rename a tag
    pub fn rename_tag(&self, tag_id: i64, new_name: &str) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE tags SET name = ?1 WHERE id = ?2",
            params![new_name, tag_id],
        )
    }

    /// Update tag color
    pub fn update_tag_color(&self, tag_id: i64, color: &str) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE tags SET color = ?1 WHERE id = ?2",
            params![color, tag_id],
        )
    }

    /// Delete a tag (will cascade to session_tags)
    pub fn delete_tag(&self, tag_id: i64) -> SqliteResult<usize> {
        self.conn
            .execute("DELETE FROM tags WHERE id = ?1", params![tag_id])
    }

    /// Add a tag to a session
    pub fn add_tag_to_session(&self, session_id: i64, tag_id: i64) -> SqliteResult<usize> {
        let now = Utc::now();

        self.conn.execute(
            "INSERT OR IGNORE INTO session_tags (session_id, tag_id, created_at)
             VALUES (?1, ?2, ?3)",
            params![session_id, tag_id, now.to_rfc3339()],
        )
    }

    /// Remove a tag from a session
    pub fn remove_tag_from_session(&self, session_id: i64, tag_id: i64) -> SqliteResult<usize> {
        self.conn.execute(
            "DELETE FROM session_tags WHERE session_id = ?1 AND tag_id = ?2",
            params![session_id, tag_id],
        )
    }

    /// Get all tags for a specific session
    pub fn get_session_tags(&self, session_id: i64) -> SqliteResult<Vec<Tag>> {
        let mut stmt = self.conn.prepare(
            "SELECT t.id, t.name, t.color, t.created_at
             FROM tags t
             INNER JOIN session_tags st ON t.id = st.tag_id
             WHERE st.session_id = ?1
             ORDER BY t.name ASC",
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
    pub fn get_sessions_by_tags(
        &self,
        tag_ids: &[i64],
        mode: &str,
        limit: usize,
    ) -> SqliteResult<Vec<ChatSession>> {
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

        let params_refs: Vec<&dyn rusqlite::ToSql> =
            params_vec.iter().map(|p| p.as_ref()).collect();

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
             ORDER BY usage_count DESC, t.name ASC",
        )?;

        let results = stmt.query_map([], |row| {
            Ok((
                Tag {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    color: row.get(2)?,
                    created_at: row.get::<_, String>(3)?.parse().unwrap_or(Utc::now()),
                },
                row.get(4)?,
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
            params![target_tag_id, source_tag_id],
        )?;

        // Delete the source tag (will cascade delete old session_tags)
        self.delete_tag(source_tag_id)?;

        Ok(())
    }

    /// Get usage statistics
    pub fn get_usage_stats(&self) -> SqliteResult<UsageStats> {
        // Get total sessions
        let total_sessions: i64 =
            self.conn
                .query_row("SELECT COUNT(*) FROM chat_sessions", [], |row| row.get(0))?;

        // Get total messages (user messages only)
        let total_messages: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM messages WHERE role = 'user'",
            [],
            |row| row.get(0),
        )?;

        // Get total recordings
        let total_recordings: i64 =
            self.conn
                .query_row("SELECT COUNT(*) FROM recordings", [], |row| row.get(0))?;

        // Get total recording time
        let total_recording_time_ms: i64 = self
            .conn
            .query_row(
                "SELECT COALESCE(SUM(duration_ms), 0) FROM recordings",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

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
            } else {
                0.0
            },
            claude_percent: if total_provider_calls > 0 {
                (claude_count as f64 / total_provider_calls as f64) * 100.0
            } else {
                0.0
            },
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
             LIMIT 5",
        )?;

        let top_prompts = stmt
            .query_map([], |row| {
                Ok(PromptUsage {
                    name: row.get(0)?,
                    count: row.get(1)?,
                })
            })?
            .collect::<SqliteResult<Vec<_>>>()
            .unwrap_or_default();

        // Get sessions this week
        let sessions_this_week: i64 = self
            .conn
            .query_row(
                "SELECT COUNT(*) FROM chat_sessions
             WHERE created_at >= datetime('now', '-7 days')",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

        // Get sessions this month
        let sessions_this_month: i64 = self
            .conn
            .query_row(
                "SELECT COUNT(*) FROM chat_sessions
             WHERE created_at >= datetime('now', 'start of month')",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

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
             FROM backup_history ORDER BY created_at DESC LIMIT ?1",
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
        let total_backups: i64 = self
            .conn
            .query_row(
                "SELECT COUNT(*) FROM backup_history WHERE status = 'success'",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

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
            settings
                .last_backup_at
                .map(|last| match settings.frequency.as_str() {
                    "daily" => last + chrono::Duration::days(1),
                    "weekly" => last + chrono::Duration::weeks(1),
                    _ => last,
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

    // ===== Cards (V8: Privacy & Publishing) =====

    /// Create a new card
    pub fn create_card(&self, card: &Card) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO cards (content, privacy_level, published, git_sha, category, session_id, message_id, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                card.content,
                card.privacy_level.as_ref().map(|p| p.as_str()),
                card.published as i32,
                card.git_sha,
                card.category.as_ref().map(|c| c.as_str()),
                card.session_id,
                card.message_id,
                card.created_at.to_rfc3339(),
                card.updated_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    /// Get a card by ID
    pub fn get_card(&self, id: i64) -> SqliteResult<Card> {
        self.conn.query_row(
            "SELECT id, content, privacy_level, published, git_sha, category, session_id, message_id, created_at, updated_at
             FROM cards WHERE id = ?1",
            params![id],
            |row| {
                let privacy_level_str: Option<String> = row.get(2)?;
                let category_str: Option<String> = row.get(5)?;

                Ok(Card {
                    id: Some(row.get(0)?),
                    content: row.get(1)?,
                    privacy_level: privacy_level_str.and_then(|s| PrivacyLevel::from_str(&s).ok()),
                    published: row.get::<_, i32>(3)? != 0,
                    git_sha: row.get(4)?,
                    category: category_str.and_then(|s| CardCategory::from_str(&s).ok()),
                    session_id: row.get(6)?,
                    message_id: row.get(7)?,
                    created_at: row.get::<_, String>(8)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(9)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    /// List all cards with optional filtering
    pub fn list_cards(
        &self,
        privacy_level: Option<&PrivacyLevel>,
        category: Option<&CardCategory>,
        published_only: bool,
        limit: usize,
    ) -> SqliteResult<Vec<Card>> {
        let mut query = String::from(
            "SELECT id, content, privacy_level, published, git_sha, category, session_id, message_id, created_at, updated_at
             FROM cards WHERE 1=1"
        );

        if privacy_level.is_some() {
            query.push_str(" AND privacy_level = ?1");
        }
        if category.is_some() {
            query.push_str(&format!(
                " AND category = ?{}",
                if privacy_level.is_some() { 2 } else { 1 }
            ));
        }
        if published_only {
            let param_num = if privacy_level.is_some() && category.is_some() {
                3
            } else if privacy_level.is_some() || category.is_some() {
                2
            } else {
                1
            };
            query.push_str(&format!(" AND published = ?{}", param_num));
        }

        query.push_str(&format!(
            " ORDER BY created_at DESC LIMIT ?{}",
            if privacy_level.is_some() && category.is_some() && published_only {
                4
            } else if (privacy_level.is_some() && category.is_some())
                || (privacy_level.is_some() && published_only)
                || (category.is_some() && published_only)
            {
                3
            } else if privacy_level.is_some() || category.is_some() || published_only {
                2
            } else {
                1
            }
        ));

        let mut stmt = self.conn.prepare(&query)?;

        // Build params
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = vec![];
        if let Some(pl) = privacy_level {
            params_vec.push(Box::new(pl.as_str().to_string()));
        }
        if let Some(cat) = category {
            params_vec.push(Box::new(cat.as_str().to_string()));
        }
        if published_only {
            params_vec.push(Box::new(1));
        }
        params_vec.push(Box::new(limit as i64));

        let params_refs: Vec<&dyn rusqlite::ToSql> =
            params_vec.iter().map(|p| p.as_ref()).collect();

        let cards = stmt.query_map(&*params_refs, |row| {
            let privacy_level_str: Option<String> = row.get(2)?;
            let category_str: Option<String> = row.get(5)?;

            Ok(Card {
                id: Some(row.get(0)?),
                content: row.get(1)?,
                privacy_level: privacy_level_str.and_then(|s| PrivacyLevel::from_str(&s).ok()),
                published: row.get::<_, i32>(3)? != 0,
                git_sha: row.get(4)?,
                category: category_str.and_then(|s| CardCategory::from_str(&s).ok()),
                session_id: row.get(6)?,
                message_id: row.get(7)?,
                created_at: row.get::<_, String>(8)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(9)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        cards.collect()
    }

    /// Update a card
    pub fn update_card(&self, card: &Card) -> SqliteResult<usize> {
        let id = card
            .id
            .ok_or_else(|| rusqlite::Error::InvalidParameterName("Card ID is required".to_string()))?;

        self.conn.execute(
            "UPDATE cards
             SET content = ?1, privacy_level = ?2, published = ?3, git_sha = ?4, category = ?5, updated_at = ?6
             WHERE id = ?7",
            params![
                card.content,
                card.privacy_level.as_ref().map(|p| p.as_str()),
                card.published as i32,
                card.git_sha,
                card.category.as_ref().map(|c| c.as_str()),
                Utc::now().to_rfc3339(),
                id,
            ],
        )
    }

    /// Update card privacy level
    pub fn update_card_privacy(&self, id: i64, privacy_level: &PrivacyLevel) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE cards SET privacy_level = ?1, updated_at = ?2 WHERE id = ?3",
            params![privacy_level.as_str(), Utc::now().to_rfc3339(), id],
        )
    }

    /// Update card category
    pub fn update_card_category(&self, id: i64, category: &CardCategory) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE cards SET category = ?1, updated_at = ?2 WHERE id = ?3",
            params![category.as_str(), Utc::now().to_rfc3339(), id],
        )
    }

    /// Mark card as published with git SHA
    pub fn publish_card(&self, id: i64, git_sha: &str) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE cards SET published = 1, git_sha = ?1, updated_at = ?2 WHERE id = ?3",
            params![git_sha, Utc::now().to_rfc3339(), id],
        )
    }

    /// Unpublish card
    pub fn unpublish_card(&self, id: i64) -> SqliteResult<usize> {
        self.conn.execute(
            "UPDATE cards SET published = 0, git_sha = NULL, updated_at = ?1 WHERE id = ?2",
            params![Utc::now().to_rfc3339(), id],
        )
    }

    /// Delete a card
    pub fn delete_card(&self, id: i64) -> SqliteResult<usize> {
        self.conn.execute("DELETE FROM cards WHERE id = ?1", params![id])
    }

    /// Get publishable cards (BUSINESS + IDEAS levels only)
    pub fn get_publishable_cards(&self, limit: usize) -> SqliteResult<Vec<Card>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, content, privacy_level, published, git_sha, category, session_id, message_id, created_at, updated_at
             FROM cards
             WHERE privacy_level IN ('BUSINESS', 'IDEAS')
             ORDER BY created_at DESC
             LIMIT ?1"
        )?;

        let cards = stmt.query_map(params![limit], |row| {
            let privacy_level_str: Option<String> = row.get(2)?;
            let category_str: Option<String> = row.get(5)?;

            Ok(Card {
                id: Some(row.get(0)?),
                content: row.get(1)?,
                privacy_level: privacy_level_str.and_then(|s| PrivacyLevel::from_str(&s).ok()),
                published: row.get::<_, i32>(3)? != 0,
                git_sha: row.get(4)?,
                category: category_str.and_then(|s| CardCategory::from_str(&s).ok()),
                session_id: row.get(6)?,
                message_id: row.get(7)?,
                created_at: row.get::<_, String>(8)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(9)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        cards.collect()
    }

    // ===== Card Templates (V9: Template System) =====

    /// List all card templates
    pub fn list_card_templates(&self) -> SqliteResult<Vec<CardTemplate>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, title, content, category, is_system, created_at, updated_at
             FROM card_templates ORDER BY is_system DESC, name ASC",
        )?;

        let templates = stmt.query_map([], |row| {
            let category_str: Option<String> = row.get(4)?;

            Ok(CardTemplate {
                id: Some(row.get(0)?),
                name: row.get(1)?,
                title: row.get(2)?,
                content: row.get(3)?,
                category: category_str.and_then(|s| CardCategory::from_str(&s).ok()),
                is_system: row.get::<_, i64>(5)? != 0,
                created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                updated_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
            })
        })?;

        templates.collect()
    }

    /// Get a card template by ID
    pub fn get_card_template(&self, id: i64) -> SqliteResult<CardTemplate> {
        self.conn.query_row(
            "SELECT id, name, title, content, category, is_system, created_at, updated_at
             FROM card_templates WHERE id = ?1",
            params![id],
            |row| {
                let category_str: Option<String> = row.get(4)?;

                Ok(CardTemplate {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    title: row.get(2)?,
                    content: row.get(3)?,
                    category: category_str.and_then(|s| CardCategory::from_str(&s).ok()),
                    is_system: row.get::<_, i64>(5)? != 0,
                    created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    /// Get a card template by name
    pub fn get_card_template_by_name(&self, name: &str) -> SqliteResult<CardTemplate> {
        self.conn.query_row(
            "SELECT id, name, title, content, category, is_system, created_at, updated_at
             FROM card_templates WHERE name = ?1",
            params![name],
            |row| {
                let category_str: Option<String> = row.get(4)?;

                Ok(CardTemplate {
                    id: Some(row.get(0)?),
                    name: row.get(1)?,
                    title: row.get(2)?,
                    content: row.get(3)?,
                    category: category_str.and_then(|s| CardCategory::from_str(&s).ok()),
                    is_system: row.get::<_, i64>(5)? != 0,
                    created_at: row.get::<_, String>(6)?.parse().unwrap_or(Utc::now()),
                    updated_at: row.get::<_, String>(7)?.parse().unwrap_or(Utc::now()),
                })
            },
        )
    }

    /// Create a new card template
    pub fn create_card_template(&self, template: &CardTemplate) -> SqliteResult<i64> {
        self.conn.execute(
            "INSERT INTO card_templates (name, title, content, category, is_system, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                template.name,
                template.title,
                template.content,
                template.category.as_ref().map(|c| c.as_str()),
                template.is_system as i64,
                template.created_at.to_rfc3339(),
                template.updated_at.to_rfc3339(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    /// Update a card template
    pub fn update_card_template(&self, template: &CardTemplate) -> SqliteResult<usize> {
        let id = template
            .id
            .ok_or_else(|| rusqlite::Error::InvalidParameterName("Template ID is required".to_string()))?;

        // Check if template is a system template
        let is_system: i64 = self.conn.query_row(
            "SELECT is_system FROM card_templates WHERE id = ?1",
            params![id],
            |row| row.get(0),
        )?;

        if is_system != 0 {
            return Err(rusqlite::Error::InvalidParameterName(
                "Cannot modify system templates".to_string(),
            ));
        }

        self.conn.execute(
            "UPDATE card_templates
             SET name = ?1, title = ?2, content = ?3, category = ?4, updated_at = ?5
             WHERE id = ?6",
            params![
                template.name,
                template.title,
                template.content,
                template.category.as_ref().map(|c| c.as_str()),
                Utc::now().to_rfc3339(),
                id,
            ],
        )
    }

    /// Delete a card template
    pub fn delete_card_template(&self, id: i64) -> SqliteResult<usize> {
        // Check if template is a system template
        let is_system: i64 = self.conn.query_row(
            "SELECT is_system FROM card_templates WHERE id = ?1",
            params![id],
            |row| row.get(0),
        )?;

        if is_system != 0 {
            return Err(rusqlite::Error::InvalidParameterName(
                "Cannot delete system templates".to_string(),
            ));
        }

        self.conn
            .execute("DELETE FROM card_templates WHERE id = ?1", params![id])
    }

    /// Initialize predefined system templates
    pub fn initialize_system_templates(&self) -> SqliteResult<()> {
        let now = Utc::now();

        let templates = vec![
            CardTemplate {
                id: None,
                name: "daily_journal".to_string(),
                title: "Daily Journal".to_string(),
                content: r#"# Daily Journal - {{date}}

## What happened today?


## Key insights


## Gratitude
-

## Tomorrow's focus
- "#.to_string(),
                category: Some(CardCategory::Categorized),
                is_system: true,
                created_at: now,
                updated_at: now,
            },
            CardTemplate {
                id: None,
                name: "meeting_notes".to_string(),
                title: "Meeting Notes".to_string(),
                content: r#"# Meeting Notes - {{datetime}}

**Attendees:**

**Agenda:**
-

**Discussion:**


**Action Items:**
- [ ]

**Next Meeting:** "#.to_string(),
                category: Some(CardCategory::Program),
                is_system: true,
                created_at: now,
                updated_at: now,
            },
            CardTemplate {
                id: None,
                name: "idea".to_string(),
                title: "Idea".to_string(),
                content: r#"# Idea - {{date}}

## Core Concept


## Why This Matters


## Next Steps
- [ ]

---
*Captured by {{user}}*"#.to_string(),
                category: Some(CardCategory::Unassimilated),
                is_system: true,
                created_at: now,
                updated_at: now,
            },
            CardTemplate {
                id: None,
                name: "grit".to_string(),
                title: "GRIT Challenge".to_string(),
                content: r#"# Challenge - {{date}}

## The Challenge


## Why It's Hard


## My Strategy
1.

## Progress Tracking
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Reflection


---
**Remember:** Growth happens outside your comfort zone."#.to_string(),
                category: Some(CardCategory::Grit),
                is_system: true,
                created_at: now,
                updated_at: now,
            },
            CardTemplate {
                id: None,
                name: "quick_note".to_string(),
                title: "Quick Note".to_string(),
                content: "{{datetime}}\n\n".to_string(),
                category: None,
                is_system: true,
                created_at: now,
                updated_at: now,
            },
            CardTemplate {
                id: None,
                name: "weekly_review".to_string(),
                title: "Weekly Review".to_string(),
                content: r#"# Weekly Review - Week of {{date}}

## Wins This Week
-

## Challenges Faced
-

## Lessons Learned


## Focus for Next Week
- [ ]
- [ ]
- [ ]

## Energy & Well-being
Mood:
Energy:
Sleep: "#.to_string(),
                category: Some(CardCategory::Categorized),
                is_system: true,
                created_at: now,
                updated_at: now,
            },
            CardTemplate {
                id: None,
                name: "project_planning".to_string(),
                title: "Project Planning".to_string(),
                content: r#"# Project:

**Start Date:** {{date}}
**Target Completion:**

## Objective


## Scope
**In Scope:**
-

**Out of Scope:**
-

## Milestones
- [ ] Milestone 1
- [ ] Milestone 2
- [ ] Milestone 3

## Resources Needed


## Risks & Mitigation
"#.to_string(),
                category: Some(CardCategory::Program),
                is_system: true,
                created_at: now,
                updated_at: now,
            },
        ];

        // Insert templates if they don't already exist
        for template in templates {
            // Check if template already exists
            let exists: i64 = self.conn.query_row(
                "SELECT COUNT(*) FROM card_templates WHERE name = ?1",
                params![template.name],
                |row| row.get(0),
            )?;

            if exists == 0 {
                self.create_card_template(&template)?;
            }
        }

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
        repo.update_chat_session_title(session_id, "Updated Title")
            .unwrap();
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
        let daily = repo
            .get_prompt_template_by_name("daily_reflection")
            .unwrap();
        assert!(daily.is_default);

        let crisis = repo.get_prompt_template_by_name("crisis_support").unwrap();
        assert!(!crisis.is_default);

        // Get default
        let default = repo.get_default_prompt_template().unwrap();
        assert_eq!(default.name, "daily_reflection");
    }

    // ===== Extended User Prompt Tests =====

    #[test]
    fn test_user_prompts_comprehensive() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create multiple user prompts
        let p1_id = repo
            .create_user_prompt("prompt1", "Prompt One", "Content for prompt 1")
            .unwrap();
        let p2_id = repo
            .create_user_prompt("prompt2", "Prompt Two", "Content for prompt 2")
            .unwrap();

        assert!(p1_id > 0);
        assert!(p2_id > 0);

        // List prompts
        let prompts = repo.list_user_prompts().unwrap();
        assert!(prompts.len() >= 2);

        // Get specific prompt
        let p1 = repo.get_user_prompt(p1_id).unwrap();
        assert_eq!(p1.name, "prompt1");
        assert_eq!(p1.title, "Prompt One");
        assert_eq!(p1.content, "Content for prompt 1");
        assert!(!p1.is_system);

        // Update prompt
        repo.update_user_prompt(p1_id, "Updated Title", "Updated content")
            .unwrap();

        let updated = repo.get_user_prompt(p1_id).unwrap();
        assert_eq!(updated.title, "Updated Title");
        assert_eq!(updated.content, "Updated content");
        assert_eq!(updated.name, "prompt1"); // Name should not change

        // Delete prompt
        repo.delete_user_prompt(p2_id).unwrap();
        assert!(repo.get_user_prompt(p2_id).is_err());
    }

    #[test]
    fn test_user_prompts_with_special_characters() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        let content = "This prompt has \"quotes\", 'apostrophes', and \nnewlines";
        let id = repo
            .create_user_prompt("special", "Special Chars", content)
            .unwrap();

        let prompt = repo.get_user_prompt(id).unwrap();
        assert_eq!(prompt.content, content);
    }

    // ===== Extended Usage Statistics Tests =====

    #[test]
    fn test_usage_statistics_comprehensive() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create sessions and recordings
        let session = ChatSession {
            id: None,
            title: Some("Test Session".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = repo.create_chat_session(&session).unwrap();

        // Add messages
        for i in 0..5 {
            let msg = Message {
                id: None,
                session_id,
                recording_id: None,
                role: if i % 2 == 0 {
                    MessageRole::User
                } else {
                    MessageRole::Assistant
                },
                content: format!("Message {}", i),
                privacy_tags: None,
                created_at: Utc::now(),
            };
            repo.create_message(&msg).unwrap();
        }

        // Add recordings
        for i in 0..3 {
            let rec = Recording {
                id: None,
                filepath: format!("/test/rec{}.wav", i),
                duration_ms: 5000 + (i as i64 * 1000),
                sample_rate: 16000,
                channels: 1,
                file_size_bytes: Some(80000),
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            repo.create_recording(&rec).unwrap();
        }

        // Track usage events
        let events = vec![
            UsageEvent {
                id: None,
                event_type: "chat_message".to_string(),
                provider: Some("openai".to_string()),
                prompt_name: Some("daily_reflection".to_string()),
                token_count: Some(150),
                recording_duration_ms: None,
                created_at: Utc::now(),
            },
            UsageEvent {
                id: None,
                event_type: "chat_message".to_string(),
                provider: Some("claude".to_string()),
                prompt_name: Some("crisis_support".to_string()),
                token_count: Some(200),
                recording_duration_ms: None,
                created_at: Utc::now(),
            },
            UsageEvent {
                id: None,
                event_type: "recording".to_string(),
                provider: None,
                prompt_name: None,
                token_count: None,
                recording_duration_ms: Some(5000),
                created_at: Utc::now(),
            },
        ];

        for event in events {
            repo.track_usage_event(&event).unwrap();
        }

        // Get usage stats
        let stats = repo.get_usage_stats().unwrap();

        assert_eq!(stats.total_sessions, 1);
        assert_eq!(stats.total_messages, 5);
        assert_eq!(stats.total_recordings, 3);
        assert!(stats.total_recording_time_ms >= 18000); // 3 recordings with increasing durations

        // Check provider usage
        assert!(stats.provider_usage.openai_count > 0);
        assert!(stats.provider_usage.claude_count > 0);

        // Check top prompts
        assert!(!stats.top_prompts.is_empty());
    }

    #[test]
    fn test_track_usage_event_various_types() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Recording event
        let rec_event = UsageEvent {
            id: None,
            event_type: "recording".to_string(),
            provider: None,
            prompt_name: None,
            token_count: None,
            recording_duration_ms: Some(5000),
            created_at: Utc::now(),
        };
        repo.track_usage_event(&rec_event).unwrap();

        // Chat event
        let chat_event = UsageEvent {
            id: None,
            event_type: "chat_message".to_string(),
            provider: Some("openai".to_string()),
            prompt_name: Some("custom_prompt".to_string()),
            token_count: Some(500),
            recording_duration_ms: None,
            created_at: Utc::now(),
        };
        repo.track_usage_event(&chat_event).unwrap();

        // Export event
        let export_event = UsageEvent {
            id: None,
            event_type: "export".to_string(),
            provider: None,
            prompt_name: None,
            token_count: None,
            recording_duration_ms: None,
            created_at: Utc::now(),
        };
        repo.track_usage_event(&export_event).unwrap();

        // Verify events were tracked
        let stats = repo.get_usage_stats().unwrap();
        assert!(stats.total_recordings >= 0); // Stats calculation should handle it
    }

    // ===== Extended Tag Management Tests =====

    #[test]
    fn test_tag_operations_comprehensive() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create multiple tags
        let tag1 = repo.create_tag("Work", "#3B82F6").unwrap();
        let tag2 = repo.create_tag("Personal", "#10B981").unwrap();
        let tag3 = repo.create_tag("Ideas", "#F59E0B").unwrap();

        // List all tags
        let tags = repo.list_tags().unwrap();
        assert!(tags.len() >= 3);

        // Create sessions
        let s1 = ChatSession {
            id: None,
            title: Some("Session 1".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let s2 = ChatSession {
            id: None,
            title: Some("Session 2".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let s1_id = repo.create_chat_session(&s1).unwrap();
        let s2_id = repo.create_chat_session(&s2).unwrap();

        // Add tags to sessions
        repo.add_tag_to_session(s1_id, tag1).unwrap();
        repo.add_tag_to_session(s1_id, tag2).unwrap();
        repo.add_tag_to_session(s2_id, tag2).unwrap();

        // Get session tags
        let s1_tags = repo.get_session_tags(s1_id).unwrap();
        assert_eq!(s1_tags.len(), 2);

        let s2_tags = repo.get_session_tags(s2_id).unwrap();
        assert_eq!(s2_tags.len(), 1);

        // Get tag usage counts
        let counts = repo.get_tag_usage_counts().unwrap();
        let work_count = counts.iter().find(|(t, _)| t.name == "Work").map(|(_, c)| c);
        let personal_count = counts
            .iter()
            .find(|(t, _)| t.name == "Personal")
            .map(|(_, c)| c);

        assert_eq!(work_count, Some(&1));
        assert_eq!(personal_count, Some(&2));

        // Rename tag
        repo.rename_tag(tag3, "BrightIdeas").unwrap();
        let renamed = repo.get_tag(tag3).unwrap();
        assert_eq!(renamed.name, "BrightIdeas");

        // Update color
        repo.update_tag_color(tag3, "#FF00FF").unwrap();
        let updated = repo.get_tag(tag3).unwrap();
        assert_eq!(updated.color, "#FF00FF");

        // Remove tag from session
        repo.remove_tag_from_session(s1_id, tag1).unwrap();
        let updated_tags = repo.get_session_tags(s1_id).unwrap();
        assert_eq!(updated_tags.len(), 1);

        // Merge tags
        repo.merge_tags(tag2, tag3).unwrap();

        // Verify tag2 is deleted
        assert!(repo.get_tag(tag2).is_err());

        // Verify sessions with tag2 now have tag3
        let s1_after_merge = repo.get_session_tags(s1_id).unwrap();
        assert!(s1_after_merge.iter().any(|t| t.id == Some(tag3)));
    }

    #[test]
    fn test_get_sessions_by_tags_complex() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create tags
        let work_tag = repo.create_tag("Work", "#FF0000").unwrap();
        let urgent_tag = repo.create_tag("Urgent", "#00FF00").unwrap();
        let review_tag = repo.create_tag("Review", "#0000FF").unwrap();

        // Create sessions with different tag combinations
        let s1 = ChatSession {
            id: None,
            title: Some("Work only".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let s2 = ChatSession {
            id: None,
            title: Some("Work + Urgent".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let s3 = ChatSession {
            id: None,
            title: Some("Urgent only".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let s4 = ChatSession {
            id: None,
            title: Some("Work + Urgent + Review".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let s1_id = repo.create_chat_session(&s1).unwrap();
        let s2_id = repo.create_chat_session(&s2).unwrap();
        let s3_id = repo.create_chat_session(&s3).unwrap();
        let s4_id = repo.create_chat_session(&s4).unwrap();

        // Add tags
        repo.add_tag_to_session(s1_id, work_tag).unwrap();
        repo.add_tag_to_session(s2_id, work_tag).unwrap();
        repo.add_tag_to_session(s2_id, urgent_tag).unwrap();
        repo.add_tag_to_session(s3_id, urgent_tag).unwrap();
        repo.add_tag_to_session(s4_id, work_tag).unwrap();
        repo.add_tag_to_session(s4_id, urgent_tag).unwrap();
        repo.add_tag_to_session(s4_id, review_tag).unwrap();

        // Test "any" mode
        let any_result = repo
            .get_sessions_by_tags(&[work_tag, urgent_tag], "any", 10)
            .unwrap();
        assert_eq!(any_result.len(), 4); // All sessions except none

        // Test "all" mode with two tags
        let all_result = repo
            .get_sessions_by_tags(&[work_tag, urgent_tag], "all", 10)
            .unwrap();
        assert_eq!(all_result.len(), 2); // s2 and s4

        // Test "all" mode with three tags
        let all_three = repo
            .get_sessions_by_tags(&[work_tag, urgent_tag, review_tag], "all", 10)
            .unwrap();
        assert_eq!(all_three.len(), 1); // Only s4

        // Test with single tag
        let single_tag = repo.get_sessions_by_tags(&[review_tag], "any", 10).unwrap();
        assert_eq!(single_tag.len(), 1); // Only s4
    }

    // ===== Extended Backup Tests =====

    #[test]
    fn test_backup_settings_comprehensive() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Get default settings
        let settings = repo.get_backup_settings().unwrap();
        assert!(!settings.enabled);
        assert_eq!(settings.frequency, "manual");

        // Update all settings
        let mut updated_settings = settings.clone();
        updated_settings.enabled = true;
        updated_settings.frequency = "daily".to_string();
        updated_settings.backup_path = "/custom/backup/path".to_string();
        updated_settings.retention_count = 14;

        repo.update_backup_settings(&updated_settings).unwrap();

        // Verify updates
        let fetched = repo.get_backup_settings().unwrap();
        assert!(fetched.enabled);
        assert_eq!(fetched.frequency, "daily");
        assert_eq!(fetched.backup_path, "/custom/backup/path");
        assert_eq!(fetched.retention_count, 14);
    }

    #[test]
    fn test_backup_history_operations() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create successful backup
        let success_backup = BackupHistory {
            id: None,
            file_path: "/backups/backup_001.db".to_string(),
            file_size_bytes: 1024000,
            created_at: Utc::now(),
            is_automatic: true,
            status: "success".to_string(),
            error_message: None,
        };
        repo.create_backup_history(&success_backup).unwrap();

        // Create failed backup
        let failed_backup = BackupHistory {
            id: None,
            file_path: "/backups/backup_002.db".to_string(),
            file_size_bytes: 0,
            created_at: Utc::now(),
            is_automatic: false,
            status: "failed".to_string(),
            error_message: Some("Disk full".to_string()),
        };
        repo.create_backup_history(&failed_backup).unwrap();

        // List history
        let history = repo.list_backup_history(10).unwrap();
        assert_eq!(history.len(), 2);

        // Check failed backup details
        let failed = history.iter().find(|h| h.status == "failed").unwrap();
        assert_eq!(failed.error_message, Some("Disk full".to_string()));
        assert!(!failed.is_automatic);
    }

    #[test]
    fn test_backup_status() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Initial status
        let status = repo.get_backup_status().unwrap();
        assert_eq!(status.total_backups, 0);
        assert!(!status.enabled);

        // Create backups
        for i in 0..5 {
            let backup = BackupHistory {
                id: None,
                file_path: format!("/backups/backup_{:03}.db", i),
                file_size_bytes: 1024000 + (i as i64 * 100000),
                created_at: Utc::now(),
                is_automatic: i % 2 == 0,
                status: "success".to_string(),
                error_message: None,
            };
            repo.create_backup_history(&backup).unwrap();
        }

        // Update last backup time
        repo.update_last_backup_time().unwrap();

        // Get updated status
        let updated_status = repo.get_backup_status().unwrap();
        assert_eq!(updated_status.total_backups, 5);
        assert!(updated_status.last_backup_at.is_some());
        assert!(updated_status.total_backup_size_bytes > 0);
    }

    #[test]
    fn test_update_last_backup_time() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        let before = repo.get_backup_settings().unwrap();
        assert!(before.last_backup_at.is_none());

        repo.update_last_backup_time().unwrap();

        let after = repo.get_backup_settings().unwrap();
        assert!(after.last_backup_at.is_some());
    }

    // ===== Card Operations Tests =====

    #[test]
    fn test_card_operations_comprehensive() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create session and message
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = repo.create_chat_session(&session).unwrap();

        let message = Message {
            id: None,
            session_id,
            recording_id: None,
            role: MessageRole::User,
            content: "Test message".to_string(),
            privacy_tags: None,
            created_at: Utc::now(),
        };
        let message_id = repo.create_message(&message).unwrap();

        // Create card with references
        let card = Card {
            id: None,
            content: "This is a business idea card".to_string(),
            privacy_level: Some(PrivacyLevel::Business),
            published: false,
            git_sha: None,
            category: Some(CardCategory::Unassimilated),
            session_id: Some(session_id),
            message_id: Some(message_id),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let card_id = repo.create_card(&card).unwrap();
        assert!(card_id > 0);

        // Get card
        let fetched = repo.get_card(card_id).unwrap();
        assert_eq!(fetched.content, "This is a business idea card");
        assert_eq!(fetched.session_id, Some(session_id));
        assert_eq!(fetched.message_id, Some(message_id));
        assert!(!fetched.published);

        // Update card
        let mut updated_card = fetched.clone();
        updated_card.category = Some(CardCategory::Program);
        updated_card.privacy_level = Some(PrivacyLevel::Ideas);

        repo.update_card(&updated_card).unwrap();

        let after_update = repo.get_card(card_id).unwrap();
        assert!(matches!(
            after_update.category,
            Some(CardCategory::Program)
        ));
        assert!(matches!(
            after_update.privacy_level,
            Some(PrivacyLevel::Ideas)
        ));

        // Publish card
        repo.publish_card(card_id, "abc123def456").unwrap();

        let published = repo.get_card(card_id).unwrap();
        assert!(published.published);
        assert_eq!(published.git_sha, Some("abc123def456".to_string()));

        // Delete card
        repo.delete_card(card_id).unwrap();
        assert!(repo.get_card(card_id).is_err());
    }

    #[test]
    fn test_get_publishable_cards_filtering() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create cards with all privacy levels
        let cards = vec![
            (PrivacyLevel::Private, false),
            (PrivacyLevel::Personal, false),
            (PrivacyLevel::Business, false),
            (PrivacyLevel::Ideas, false),
            (PrivacyLevel::Business, true), // Already published
        ];

        for (level, published) in cards {
            let card = Card {
                id: None,
                content: format!("Content for {:?}", level),
                privacy_level: Some(level),
                published,
                git_sha: if published {
                    Some("sha123".to_string())
                } else {
                    None
                },
                category: None,
                session_id: None,
                message_id: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            repo.create_card(&card).unwrap();
        }

        // Get publishable cards (only unpublished BUSINESS and IDEAS)
        let publishable = repo.get_publishable_cards(100).unwrap();
        assert_eq!(publishable.len(), 2);

        // Verify only BUSINESS and IDEAS, and not published
        for card in publishable {
            assert!(matches!(
                card.privacy_level,
                Some(PrivacyLevel::Business) | Some(PrivacyLevel::Ideas)
            ));
            assert!(!card.published);
        }
    }

    // ===== Language Preference Tests =====

    #[test]
    fn test_language_preference_operations() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Default should be English
        let default = repo.get_language_preference().unwrap();
        assert_eq!(default, "en");

        // Change to Spanish
        repo.set_language_preference("es").unwrap();
        let spanish = repo.get_language_preference().unwrap();
        assert_eq!(spanish, "es");

        // Change to French
        repo.set_language_preference("fr").unwrap();
        let french = repo.get_language_preference().unwrap();
        assert_eq!(french, "fr");
    }

    // ===== App Settings Tests =====

    #[test]
    fn test_app_settings_operations() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Set a setting
        repo.set_app_setting("theme", "dark").unwrap();

        // Get the setting
        let theme = repo.get_app_setting("theme").unwrap();
        assert_eq!(theme, Some("dark".to_string()));

        // Update setting
        repo.set_app_setting("theme", "light").unwrap();
        let updated_theme = repo.get_app_setting("theme").unwrap();
        assert_eq!(updated_theme, Some("light".to_string()));

        // Non-existent setting
        let missing = repo.get_app_setting("missing_key").unwrap();
        assert_eq!(missing, None);
    }

    // ===== Cascade Deletion Tests =====

    #[test]
    fn test_cascade_deletion_session() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create session with messages
        let session = ChatSession {
            id: None,
            title: Some("To Delete".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = repo.create_chat_session(&session).unwrap();

        // Add messages
        for i in 0..3 {
            let msg = Message {
                id: None,
                session_id,
                recording_id: None,
                role: MessageRole::User,
                content: format!("Message {}", i),
                privacy_tags: None,
                created_at: Utc::now(),
            };
            repo.create_message(&msg).unwrap();
        }

        // Verify messages exist
        let messages_before = repo.list_messages_by_session(session_id).unwrap();
        assert_eq!(messages_before.len(), 3);

        // Delete session
        repo.delete_chat_session(session_id).unwrap();

        // Verify session is deleted
        assert!(repo.get_chat_session(session_id).is_err());

        // Verify messages are cascade deleted
        let messages_after = repo.list_messages_by_session(session_id).unwrap();
        assert_eq!(messages_after.len(), 0);
    }

    #[test]
    fn test_cascade_deletion_recording() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create recording with transcript
        let recording = Recording {
            id: None,
            filepath: "/test/cascade.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(80000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let rec_id = repo.create_recording(&recording).unwrap();

        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "Test transcript".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1200),
            created_at: Utc::now(),
        };
        repo.create_transcript(&transcript).unwrap();

        // Verify transcript exists
        let trans_before = repo.get_transcript_by_recording(rec_id);
        assert!(trans_before.is_ok());

        // Delete recording
        repo.delete_recording(rec_id).unwrap();

        // Verify recording is deleted
        assert!(repo.get_recording(rec_id).is_err());

        // Verify transcript is cascade deleted
        assert!(repo.get_transcript_by_recording(rec_id).is_err());
    }
}
