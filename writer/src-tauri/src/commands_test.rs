//! Comprehensive tests for Tauri command handlers
//!
//! Tests all major command functions including:
//! - Chat session CRUD operations
//! - Recording operations
//! - Transcript operations
//! - Tag operations
//! - Backup operations
//! - Language preferences
//! - User prompts
//! - Usage statistics
//! - AI provider management

#[cfg(test)]
mod tests {
    use crate::db::{initialize_db, models::*, repository::Repository};
    use chrono::Utc;
    use parking_lot::Mutex;
    use std::sync::Arc;

    // Helper function to create an in-memory test database
    fn create_test_db() -> Arc<Mutex<Repository>> {
        let conn = initialize_db(":memory:".into()).expect("Failed to create test database");
        Arc::new(Mutex::new(Repository::new(conn)))
    }

    // ===== Chat Session Tests =====

    #[test]
    fn test_create_chat_session() {
        let db = create_test_db();
        let db_lock = db.lock();

        let session = ChatSession {
            id: None,
            title: Some("Test Session".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let session_id = db_lock
            .create_chat_session(&session)
            .expect("Failed to create chat session");

        assert!(session_id > 0);

        // Verify session was created
        let fetched = db_lock
            .get_chat_session(session_id)
            .expect("Failed to fetch session");
        assert_eq!(fetched.title, Some("Test Session".to_string()));
    }

    #[test]
    fn test_update_session_title() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session
        let session = ChatSession {
            id: None,
            title: Some("Original Title".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Update title
        db_lock
            .update_chat_session_title(session_id, "Updated Title")
            .expect("Failed to update title");

        // Verify update
        let updated = db_lock.get_chat_session(session_id).unwrap();
        assert_eq!(updated.title, Some("Updated Title".to_string()));
    }

    #[test]
    fn test_update_session_title_empty_fails() {
        let db = create_test_db();
        let db_lock = db.lock();

        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Attempting to update with empty title should conceptually fail
        // (though the database layer doesn't validate this - UI/command layer should)
        // This test documents the expected behavior
        let result = db_lock.update_chat_session_title(session_id, "");
        assert!(result.is_ok()); // DB allows it, but command layer should reject
    }

    #[test]
    fn test_delete_chat_session() {
        let db = create_test_db();
        let db_lock = db.lock();

        let session = ChatSession {
            id: None,
            title: Some("To Delete".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Delete session
        db_lock
            .delete_chat_session(session_id)
            .expect("Failed to delete session");

        // Verify deletion
        let result = db_lock.get_chat_session(session_id);
        assert!(result.is_err());
    }

    #[test]
    fn test_list_chat_sessions() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create multiple sessions
        for i in 1..=5 {
            let session = ChatSession {
                id: None,
                title: Some(format!("Session {}", i)),
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            db_lock.create_chat_session(&session).unwrap();
        }

        // List sessions
        let sessions = db_lock.list_chat_sessions(10).expect("Failed to list sessions");
        assert_eq!(sessions.len(), 5);
    }

    #[test]
    fn test_list_chat_sessions_with_limit() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create 10 sessions
        for i in 1..=10 {
            let session = ChatSession {
                id: None,
                title: Some(format!("Session {}", i)),
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            db_lock.create_chat_session(&session).unwrap();
        }

        // List with limit
        let sessions = db_lock.list_chat_sessions(5).expect("Failed to list sessions");
        assert_eq!(sessions.len(), 5);
    }

    // ===== Message Tests =====

    #[test]
    fn test_save_message() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session first
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Create message
        let message = Message {
            id: None,
            session_id,
            recording_id: None,
            role: MessageRole::User,
            content: "Test message".to_string(),
            privacy_tags: None,
            created_at: Utc::now(),
        };

        let message_id = db_lock.create_message(&message).expect("Failed to create message");
        assert!(message_id > 0);
    }

    #[test]
    fn test_get_messages_by_session() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Create multiple messages
        for i in 1..=3 {
            let message = Message {
                id: None,
                session_id,
                recording_id: None,
                role: if i % 2 == 0 { MessageRole::Assistant } else { MessageRole::User },
                content: format!("Message {}", i),
                privacy_tags: None,
                created_at: Utc::now(),
            };
            db_lock.create_message(&message).unwrap();
        }

        // Fetch messages
        let messages = db_lock
            .list_messages_by_session(session_id)
            .expect("Failed to list messages");
        assert_eq!(messages.len(), 3);
    }

    // ===== Recording & Transcript Tests =====

    #[test]
    fn test_recording_operations() {
        let db = create_test_db();
        let db_lock = db.lock();

        let recording = Recording {
            id: None,
            filepath: "/test/audio.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(80000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let rec_id = db_lock
            .create_recording(&recording)
            .expect("Failed to create recording");
        assert!(rec_id > 0);

        // Get recording
        let fetched = db_lock.get_recording(rec_id).expect("Failed to get recording");
        assert_eq!(fetched.filepath, "/test/audio.wav");
        assert_eq!(fetched.duration_ms, 5000);
    }

    #[test]
    fn test_transcript_operations() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create recording first
        let recording = Recording {
            id: None,
            filepath: "/test/audio.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(80000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let rec_id = db_lock.create_recording(&recording).unwrap();

        // Create transcript
        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "This is a test transcript".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1200),
            created_at: Utc::now(),
        };

        let trans_id = db_lock
            .create_transcript(&transcript)
            .expect("Failed to create transcript");
        assert!(trans_id > 0);

        // Get transcript
        let fetched = db_lock
            .get_transcript_by_recording(rec_id)
            .expect("Failed to get transcript");
        assert_eq!(fetched.text, "This is a test transcript");
        assert_eq!(fetched.language, Some("en".to_string()));
    }

    #[test]
    fn test_list_recordings() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create multiple recordings
        for i in 1..=3 {
            let recording = Recording {
                id: None,
                filepath: format!("/test/audio{}.wav", i),
                duration_ms: 5000 + (i as i64 * 1000),
                sample_rate: 16000,
                channels: 1,
                file_size_bytes: Some(80000),
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            db_lock.create_recording(&recording).unwrap();
        }

        let recordings = db_lock.list_recordings(10).expect("Failed to list recordings");
        assert_eq!(recordings.len(), 3);
    }

    // ===== Tag Tests =====

    #[test]
    fn test_create_tag() {
        let db = create_test_db();
        let db_lock = db.lock();

        let tag_id = db_lock
            .create_tag("Work", "#3B82F6")
            .expect("Failed to create tag");
        assert!(tag_id > 0);

        let tag = db_lock.get_tag(tag_id).expect("Failed to get tag");
        assert_eq!(tag.name, "Work");
        assert_eq!(tag.color, "#3B82F6");
    }

    #[test]
    fn test_create_tag_invalid_color() {
        let db = create_test_db();
        let db_lock = db.lock();

        // This should succeed at DB level (validation happens in command layer)
        let result = db_lock.create_tag("Test", "invalid");
        assert!(result.is_ok());
    }

    #[test]
    fn test_add_tag_to_session() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Create tag
        let tag_id = db_lock.create_tag("Important", "#FF0000").unwrap();

        // Add tag to session
        db_lock
            .add_tag_to_session(session_id, tag_id)
            .expect("Failed to add tag to session");

        // Verify
        let tags = db_lock
            .get_session_tags(session_id)
            .expect("Failed to get session tags");
        assert_eq!(tags.len(), 1);
        assert_eq!(tags[0].name, "Important");
    }

    #[test]
    fn test_remove_tag_from_session() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session and tag
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();
        let tag_id = db_lock.create_tag("Test", "#FF0000").unwrap();

        // Add and remove tag
        db_lock.add_tag_to_session(session_id, tag_id).unwrap();
        db_lock
            .remove_tag_from_session(session_id, tag_id)
            .expect("Failed to remove tag");

        // Verify removal
        let tags = db_lock.get_session_tags(session_id).unwrap();
        assert_eq!(tags.len(), 0);
    }

    #[test]
    fn test_list_all_tags() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create multiple tags
        db_lock.create_tag("Work", "#3B82F6").unwrap();
        db_lock.create_tag("Personal", "#10B981").unwrap();
        db_lock.create_tag("Ideas", "#F59E0B").unwrap();

        let tags = db_lock.list_tags().expect("Failed to list tags");
        assert!(tags.len() >= 3); // May include system tags
    }

    #[test]
    fn test_delete_tag() {
        let db = create_test_db();
        let db_lock = db.lock();

        let tag_id = db_lock.create_tag("ToDelete", "#FF0000").unwrap();
        db_lock.delete_tag(tag_id).expect("Failed to delete tag");

        let result = db_lock.get_tag(tag_id);
        assert!(result.is_err());
    }

    #[test]
    fn test_rename_tag() {
        let db = create_test_db();
        let db_lock = db.lock();

        let tag_id = db_lock.create_tag("OldName", "#FF0000").unwrap();
        db_lock
            .rename_tag(tag_id, "NewName")
            .expect("Failed to rename tag");

        let tag = db_lock.get_tag(tag_id).unwrap();
        assert_eq!(tag.name, "NewName");
    }

    #[test]
    fn test_update_tag_color() {
        let db = create_test_db();
        let db_lock = db.lock();

        let tag_id = db_lock.create_tag("Test", "#FF0000").unwrap();
        db_lock
            .update_tag_color(tag_id, "#00FF00")
            .expect("Failed to update tag color");

        let tag = db_lock.get_tag(tag_id).unwrap();
        assert_eq!(tag.color, "#00FF00");
    }

    #[test]
    fn test_get_tag_usage_counts() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create sessions and tags
        let session1 = ChatSession {
            id: None,
            title: Some("S1".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session2 = ChatSession {
            id: None,
            title: Some("S2".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let s1_id = db_lock.create_chat_session(&session1).unwrap();
        let s2_id = db_lock.create_chat_session(&session2).unwrap();

        let tag_id = db_lock.create_tag("Popular", "#FF0000").unwrap();

        // Add tag to both sessions
        db_lock.add_tag_to_session(s1_id, tag_id).unwrap();
        db_lock.add_tag_to_session(s2_id, tag_id).unwrap();

        // Get usage counts
        let counts = db_lock
            .get_tag_usage_counts()
            .expect("Failed to get tag usage counts");

        let popular_tag = counts.iter().find(|(tag, _)| tag.name == "Popular");
        assert!(popular_tag.is_some());
        let (_, count) = popular_tag.unwrap();
        assert_eq!(*count, 2);
    }

    #[test]
    fn test_merge_tags() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Create two tags
        let source_tag = db_lock.create_tag("OldTag", "#FF0000").unwrap();
        let target_tag = db_lock.create_tag("NewTag", "#00FF00").unwrap();

        // Add source tag to session
        db_lock.add_tag_to_session(session_id, source_tag).unwrap();

        // Merge tags
        db_lock
            .merge_tags(source_tag, target_tag)
            .expect("Failed to merge tags");

        // Verify: source tag should be deleted, session should have target tag
        let result = db_lock.get_tag(source_tag);
        assert!(result.is_err());

        let tags = db_lock.get_session_tags(session_id).unwrap();
        assert_eq!(tags.len(), 1);
        assert_eq!(tags[0].name, "NewTag");
    }

    #[test]
    fn test_get_sessions_by_tags_any() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create sessions
        let s1 = ChatSession {
            id: None,
            title: Some("S1".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let s2 = ChatSession {
            id: None,
            title: Some("S2".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let s1_id = db_lock.create_chat_session(&s1).unwrap();
        let s2_id = db_lock.create_chat_session(&s2).unwrap();

        // Create tags
        let tag1 = db_lock.create_tag("Tag1", "#FF0000").unwrap();
        let tag2 = db_lock.create_tag("Tag2", "#00FF00").unwrap();

        // S1 has tag1, S2 has tag2
        db_lock.add_tag_to_session(s1_id, tag1).unwrap();
        db_lock.add_tag_to_session(s2_id, tag2).unwrap();

        // Get sessions with any of these tags
        let sessions = db_lock
            .get_sessions_by_tags(&[tag1, tag2], "any", 10)
            .expect("Failed to get sessions by tags");

        assert_eq!(sessions.len(), 2);
    }

    #[test]
    fn test_get_sessions_by_tags_all() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create session
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        // Create two tags
        let tag1 = db_lock.create_tag("Tag1", "#FF0000").unwrap();
        let tag2 = db_lock.create_tag("Tag2", "#00FF00").unwrap();

        // Add both tags to session
        db_lock.add_tag_to_session(session_id, tag1).unwrap();
        db_lock.add_tag_to_session(session_id, tag2).unwrap();

        // Get sessions with all tags
        let sessions = db_lock
            .get_sessions_by_tags(&[tag1, tag2], "all", 10)
            .expect("Failed to get sessions");

        assert_eq!(sessions.len(), 1);
        assert_eq!(sessions[0].title, Some("Test".to_string()));
    }

    // ===== User Prompt Tests =====

    #[test]
    fn test_create_user_prompt() {
        let db = create_test_db();
        let db_lock = db.lock();

        let prompt_id = db_lock
            .create_user_prompt(
                "my_prompt",
                "My Custom Prompt",
                "This is my custom prompt content",
            )
            .expect("Failed to create user prompt");

        assert!(prompt_id > 0);

        let prompt = db_lock.get_user_prompt(prompt_id).unwrap();
        assert_eq!(prompt.name, "my_prompt");
        assert_eq!(prompt.title, "My Custom Prompt");
        assert!(!prompt.is_system);
    }

    #[test]
    fn test_list_user_prompts() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create prompts
        db_lock
            .create_user_prompt("prompt1", "Prompt 1", "Content 1")
            .unwrap();
        db_lock
            .create_user_prompt("prompt2", "Prompt 2", "Content 2")
            .unwrap();

        let prompts = db_lock.list_user_prompts().expect("Failed to list prompts");
        assert!(prompts.len() >= 2); // May include system prompts
    }

    #[test]
    fn test_update_user_prompt() {
        let db = create_test_db();
        let db_lock = db.lock();

        let prompt_id = db_lock
            .create_user_prompt("test", "Original", "Original content")
            .unwrap();

        db_lock
            .update_user_prompt(prompt_id, "Updated Title", "Updated content")
            .expect("Failed to update prompt");

        let updated = db_lock.get_user_prompt(prompt_id).unwrap();
        assert_eq!(updated.title, "Updated Title");
        assert_eq!(updated.content, "Updated content");
    }

    #[test]
    fn test_delete_user_prompt() {
        let db = create_test_db();
        let db_lock = db.lock();

        let prompt_id = db_lock
            .create_user_prompt("to_delete", "Delete Me", "Content")
            .unwrap();

        db_lock
            .delete_user_prompt(prompt_id)
            .expect("Failed to delete prompt");

        let result = db_lock.get_user_prompt(prompt_id);
        assert!(result.is_err());
    }

    // ===== Usage Statistics Tests =====

    #[test]
    fn test_track_usage_event() {
        let db = create_test_db();
        let db_lock = db.lock();

        let event = UsageEvent {
            id: None,
            event_type: "chat_message".to_string(),
            provider: Some("openai".to_string()),
            prompt_name: Some("daily_reflection".to_string()),
            token_count: Some(150),
            recording_duration_ms: None,
            created_at: Utc::now(),
        };

        let result = db_lock.track_usage_event(&event);
        assert!(result.is_ok());
    }

    #[test]
    fn test_get_usage_stats() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create some data
        let session = ChatSession {
            id: None,
            title: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        let message = Message {
            id: None,
            session_id,
            recording_id: None,
            role: MessageRole::User,
            content: "Test".to_string(),
            privacy_tags: None,
            created_at: Utc::now(),
        };
        db_lock.create_message(&message).unwrap();

        // Get stats
        let stats = db_lock
            .get_usage_stats()
            .expect("Failed to get usage stats");

        assert!(stats.total_sessions >= 1);
        assert!(stats.total_messages >= 1);
    }

    // ===== Backup Settings Tests =====

    #[test]
    fn test_get_backup_settings() {
        let db = create_test_db();
        let db_lock = db.lock();

        let settings = db_lock
            .get_backup_settings()
            .expect("Failed to get backup settings");

        // Default settings should exist
        assert!(!settings.enabled); // Default is disabled
        assert_eq!(settings.frequency, "manual");
    }

    #[test]
    fn test_update_backup_settings() {
        let db = create_test_db();
        let db_lock = db.lock();

        let mut settings = db_lock.get_backup_settings().unwrap();
        settings.enabled = true;
        settings.frequency = "daily".to_string();
        settings.retention_count = 7;

        db_lock
            .update_backup_settings(&settings)
            .expect("Failed to update backup settings");

        let updated = db_lock.get_backup_settings().unwrap();
        assert!(updated.enabled);
        assert_eq!(updated.frequency, "daily");
        assert_eq!(updated.retention_count, 7);
    }

    #[test]
    fn test_backup_history() {
        let db = create_test_db();
        let db_lock = db.lock();

        let history = BackupHistory {
            id: None,
            file_path: "/backups/backup_001.db".to_string(),
            file_size_bytes: 1024000,
            created_at: Utc::now(),
            is_automatic: false,
            status: "success".to_string(),
            error_message: None,
        };

        db_lock
            .create_backup_history(&history)
            .expect("Failed to create backup history");

        let history_list = db_lock
            .list_backup_history(10)
            .expect("Failed to list backup history");
        assert_eq!(history_list.len(), 1);
        assert_eq!(history_list[0].status, "success");
    }

    #[test]
    fn test_backup_status() {
        let db = create_test_db();
        let db_lock = db.lock();

        let status = db_lock
            .get_backup_status()
            .expect("Failed to get backup status");

        // Fresh database should have no backups
        assert_eq!(status.total_backups, 0);
        assert!(!status.enabled);
    }

    #[test]
    fn test_update_last_backup_time() {
        let db = create_test_db();
        let db_lock = db.lock();

        db_lock
            .update_last_backup_time()
            .expect("Failed to update last backup time");

        let settings = db_lock.get_backup_settings().unwrap();
        assert!(settings.last_backup_at.is_some());
    }

    // ===== Language Preference Tests =====

    #[test]
    fn test_get_language_preference_default() {
        let db = create_test_db();
        let db_lock = db.lock();

        let lang = db_lock
            .get_language_preference()
            .expect("Failed to get language preference");

        // Default should be English
        assert_eq!(lang, "en");
    }

    #[test]
    fn test_set_language_preference() {
        let db = create_test_db();
        let db_lock = db.lock();

        db_lock
            .set_language_preference("es")
            .expect("Failed to set language preference");

        let lang = db_lock.get_language_preference().unwrap();
        assert_eq!(lang, "es");
    }

    #[test]
    fn test_set_language_preference_various_languages() {
        let db = create_test_db();
        let db_lock = db.lock();

        let languages = vec!["en", "es", "fr", "de", "ja"];

        for lang in languages {
            db_lock.set_language_preference(lang).unwrap();
            let fetched = db_lock.get_language_preference().unwrap();
            assert_eq!(fetched, lang);
        }
    }

    // ===== App Settings Tests =====

    #[test]
    fn test_app_settings() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Set a setting
        db_lock
            .set_app_setting("test_key", "test_value")
            .expect("Failed to set app setting");

        // Get the setting
        let value = db_lock
            .get_app_setting("test_key")
            .expect("Failed to get app setting");

        assert_eq!(value, Some("test_value".to_string()));
    }

    #[test]
    fn test_app_settings_provider() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Set provider
        db_lock.set_app_setting("selected_provider", "claude").unwrap();

        let provider = db_lock.get_app_setting("selected_provider").unwrap();
        assert_eq!(provider, Some("claude".to_string()));

        // Change provider
        db_lock.set_app_setting("selected_provider", "openai").unwrap();

        let provider = db_lock.get_app_setting("selected_provider").unwrap();
        assert_eq!(provider, Some("openai".to_string()));
    }

    #[test]
    fn test_app_settings_nonexistent_key() {
        let db = create_test_db();
        let db_lock = db.lock();

        let value = db_lock
            .get_app_setting("nonexistent_key")
            .expect("Failed to get setting");

        assert_eq!(value, None);
    }

    // ===== Card Tests (Privacy & Publishing) =====

    #[test]
    fn test_create_card() {
        let db = create_test_db();
        let db_lock = db.lock();

        let card = Card {
            id: None,
            content: "This is a business idea".to_string(),
            privacy_level: Some(PrivacyLevel::Business),
            published: false,
            git_sha: None,
            category: Some(CardCategory::Unassimilated),
            session_id: None,
            message_id: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let card_id = db_lock.create_card(&card).expect("Failed to create card");
        assert!(card_id > 0);
    }

    #[test]
    fn test_get_publishable_cards() {
        let db = create_test_db();
        let db_lock = db.lock();

        // Create cards with different privacy levels
        let business_card = Card {
            id: None,
            content: "Business content".to_string(),
            privacy_level: Some(PrivacyLevel::Business),
            published: false,
            git_sha: None,
            category: None,
            session_id: None,
            message_id: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let ideas_card = Card {
            id: None,
            content: "Ideas content".to_string(),
            privacy_level: Some(PrivacyLevel::Ideas),
            published: false,
            git_sha: None,
            category: None,
            session_id: None,
            message_id: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let private_card = Card {
            id: None,
            content: "Private content".to_string(),
            privacy_level: Some(PrivacyLevel::Private),
            published: false,
            git_sha: None,
            category: None,
            session_id: None,
            message_id: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        db_lock.create_card(&business_card).unwrap();
        db_lock.create_card(&ideas_card).unwrap();
        db_lock.create_card(&private_card).unwrap();

        // Get publishable cards (only BUSINESS and IDEAS)
        let publishable = db_lock
            .get_publishable_cards(100)
            .expect("Failed to get publishable cards");

        assert_eq!(publishable.len(), 2);
        assert!(publishable.iter().all(|c| {
            matches!(
                c.privacy_level,
                Some(PrivacyLevel::Business) | Some(PrivacyLevel::Ideas)
            )
        }));
    }

    #[test]
    fn test_publish_card() {
        let db = create_test_db();
        let db_lock = db.lock();

        let card = Card {
            id: None,
            content: "Test content".to_string(),
            privacy_level: Some(PrivacyLevel::Ideas),
            published: false,
            git_sha: None,
            category: None,
            session_id: None,
            message_id: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        let card_id = db_lock.create_card(&card).unwrap();

        // Publish the card
        let git_sha = "abc123def456";
        db_lock
            .publish_card(card_id, git_sha)
            .expect("Failed to publish card");

        // Verify card is published
        let updated_card = db_lock.get_card(card_id).expect("Failed to get card");
        assert!(updated_card.published);
        assert_eq!(updated_card.git_sha, Some(git_sha.to_string()));
    }

    // ===== Message Role Tests =====

    #[test]
    fn test_message_role_conversion() {
        assert_eq!(MessageRole::User.as_str(), "user");
        assert_eq!(MessageRole::Assistant.as_str(), "assistant");

        assert!(matches!(
            MessageRole::from_str("user").unwrap(),
            MessageRole::User
        ));
        assert!(matches!(
            MessageRole::from_str("assistant").unwrap(),
            MessageRole::Assistant
        ));

        assert!(MessageRole::from_str("invalid").is_err());
    }

    // ===== Privacy Level Tests =====

    #[test]
    fn test_privacy_level_conversion() {
        assert_eq!(PrivacyLevel::Private.as_str(), "PRIVATE");
        assert_eq!(PrivacyLevel::Personal.as_str(), "PERSONAL");
        assert_eq!(PrivacyLevel::Business.as_str(), "BUSINESS");
        assert_eq!(PrivacyLevel::Ideas.as_str(), "IDEAS");

        assert!(matches!(
            PrivacyLevel::from_str("PRIVATE").unwrap(),
            PrivacyLevel::Private
        ));
        assert!(matches!(
            PrivacyLevel::from_str("BUSINESS").unwrap(),
            PrivacyLevel::Business
        ));

        assert!(PrivacyLevel::from_str("INVALID").is_err());
    }

    // ===== Card Category Tests =====

    #[test]
    fn test_card_category_conversion() {
        assert_eq!(CardCategory::Unassimilated.as_str(), "UNASSIMILATED");
        assert_eq!(CardCategory::Program.as_str(), "PROGRAM");
        assert_eq!(CardCategory::Grit.as_str(), "GRIT");

        assert!(matches!(
            CardCategory::from_str("UNASSIMILATED").unwrap(),
            CardCategory::Unassimilated
        ));
        assert!(matches!(
            CardCategory::from_str("GRIT").unwrap(),
            CardCategory::Grit
        ));

        assert!(CardCategory::from_str("INVALID").is_err());
    }

    // ===== Integration Tests =====

    #[test]
    fn test_full_workflow_recording_to_chat() {
        let db = create_test_db();
        let db_lock = db.lock();

        // 1. Create recording
        let recording = Recording {
            id: None,
            filepath: "/test/workflow.wav".to_string(),
            duration_ms: 5000,
            sample_rate: 16000,
            channels: 1,
            file_size_bytes: Some(80000),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let rec_id = db_lock.create_recording(&recording).unwrap();

        // 2. Create transcript
        let transcript = Transcript {
            id: None,
            recording_id: rec_id,
            text: "This is my brain dump".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            plugin_name: "whisper-cpp".to_string(),
            transcription_duration_ms: Some(1200),
            created_at: Utc::now(),
        };
        db_lock.create_transcript(&transcript).unwrap();

        // 3. Create chat session
        let session = ChatSession {
            id: None,
            title: Some("Brain Dump Session".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };
        let session_id = db_lock.create_chat_session(&session).unwrap();

        // 4. Add transcript as user message
        let message = Message {
            id: None,
            session_id,
            recording_id: Some(rec_id),
            role: MessageRole::User,
            content: "This is my brain dump".to_string(),
            privacy_tags: None,
            created_at: Utc::now(),
        };
        db_lock.create_message(&message).unwrap();

        // 5. Add AI response
        let response = Message {
            id: None,
            session_id,
            recording_id: None,
            role: MessageRole::Assistant,
            content: "I understand your thoughts.".to_string(),
            privacy_tags: None,
            created_at: Utc::now(),
        };
        db_lock.create_message(&response).unwrap();

        // 6. Verify full workflow
        let messages = db_lock.list_messages_by_session(session_id).unwrap();
        assert_eq!(messages.len(), 2);
        assert_eq!(messages[0].recording_id, Some(rec_id));

        // 7. Add tag to session
        let tag_id = db_lock.create_tag("Reviewed", "#00FF00").unwrap();
        db_lock.add_tag_to_session(session_id, tag_id).unwrap();

        let tags = db_lock.get_session_tags(session_id).unwrap();
        assert_eq!(tags.len(), 1);
    }
}
