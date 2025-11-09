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
    fn test_list_recordings() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create multiple recordings
        for i in 1..=5 {
            let recording = Recording {
                id: None,
                filepath: format!("test{}.wav", i),
                duration_ms: i * 1000,
                sample_rate: 16000,
                channels: 1,
                file_size_bytes: Some(i * 16000),
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            repo.create_recording(&recording).unwrap();
        }

        // List with limit
        let recordings = repo.list_recordings(3).unwrap();
        assert_eq!(recordings.len(), 3);

        // Should be ordered by created_at DESC (newest first)
        assert_eq!(recordings[0].filepath, "test5.wav");
    }

    #[test]
    fn test_search() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create recording with transcript
        let recording = Recording {
            id: None,
            filepath: "searchable.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(160000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let rec_id = repo.create_recording(&recording).unwrap();

        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "This is a unique searchable phrase".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1500),
            created_at: Utc::now(),
        };

        repo.create_transcript(&transcript).unwrap();

        // Search should find it
        let results = repo.search_recordings("searchable").unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].filepath, "searchable.wav");

        // Search for non-existent phrase
        let results = repo.search_recordings("nonexistent").unwrap();
        assert_eq!(results.len(), 0);
    }

    #[test]
    fn test_segments() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create recording and transcript
        let recording = Recording {
            id: None,
            filepath: "segment_test.wav".to_string(),
            duration_ms: 10000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(320000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let rec_id = repo.create_recording(&recording).unwrap();

        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "Full transcript text".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1500),
            created_at: Utc::now(),
        };

        let trans_id = repo.create_transcript(&transcript).unwrap();

        // Create segments
        let segment1 = Segment {
            id: None,
            transcript_id: trans_id,
            start_ms: 0,
            end_ms: 5000,
            text: "First half".to_string(),
            confidence: 0.96,
        };

        let segment2 = Segment {
            id: None,
            transcript_id: trans_id,
            start_ms: 5000,
            end_ms: 10000,
            text: "Second half".to_string(),
            confidence: 0.94,
        };

        repo.create_segment(&segment1).unwrap();
        repo.create_segment(&segment2).unwrap();

        // Retrieve segments
        let segments = repo.list_segments_by_transcript(trans_id).unwrap();
        assert_eq!(segments.len(), 2);
        assert_eq!(segments[0].text, "First half");
        assert_eq!(segments[1].text, "Second half");
    }

    #[test]
    fn test_foreign_key_cascade() {
        let conn = initialize_db(":memory:".into()).unwrap();
        let repo = Repository::new(conn);

        // Create recording with transcript and segments
        let recording = Recording {
            id: None,
            filepath: "cascade_test.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(160000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let rec_id = repo.create_recording(&recording).unwrap();

        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "Test cascade".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1500),
            created_at: Utc::now(),
        };

        let trans_id = repo.create_transcript(&transcript).unwrap();

        let segment = Segment {
            id: None,
            transcript_id: trans_id,
            start_ms: 0,
            end_ms: 5000,
            text: "Full text".to_string(),
            confidence: 0.95,
        };

        repo.create_segment(&segment).unwrap();

        // Delete recording - should cascade delete transcript and segments
        repo.delete_recording(rec_id).unwrap();

        // Verify cascade deletion
        assert!(repo.get_transcript_by_recording(rec_id).is_err());
        assert_eq!(repo.list_segments_by_transcript(trans_id).unwrap().len(), 0);
    }
}
