-- V1: Initial schema for BrainDump V3.0 Stage B

-- Recordings table
CREATE TABLE IF NOT EXISTS recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT NOT NULL UNIQUE,
    duration_ms INTEGER NOT NULL,
    sample_rate INTEGER DEFAULT 16000,
    channels INTEGER DEFAULT 1,
    file_size_bytes INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recordings_created ON recordings(created_at DESC);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    confidence REAL DEFAULT 1.0,
    plugin_name TEXT NOT NULL, -- 'whisper-cpp' or 'candle'
    transcription_duration_ms INTEGER, -- How long transcription took
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transcripts_recording ON transcripts(recording_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_plugin ON transcripts(plugin_name);

-- Transcript segments table (for future timestamp support)
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    text TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_segments_transcript ON segments(transcript_id);
CREATE INDEX IF NOT EXISTS idx_segments_time ON segments(start_ms, end_ms);

-- V2: C2 Integration - Chat Sessions & AI Processing

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_created ON chat_sessions(created_at DESC);

-- Messages table (user recordings + AI responses)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    recording_id INTEGER, -- NULL for AI responses
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL, -- Transcript text or AI response
    privacy_tags TEXT, -- JSON array of detected privacy issues
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC);

-- Prompt templates table (RAG templates)
CREATE TABLE IF NOT EXISTS prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    system_prompt TEXT NOT NULL,
    description TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_name ON prompt_templates(name);

-- Metadata table (for app settings, migrations, etc.)
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- V3: User-Created Prompts Management (Issue #3)

-- Prompts table for user-created AI prompts
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_system INTEGER NOT NULL DEFAULT 0, -- 1 for built-in, 0 for user-created
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(name);
CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at DESC);

-- V7: Multi-language Support (Issue #12)

-- User preferences table (singleton - only one row allowed)
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    language TEXT NOT NULL DEFAULT 'en' CHECK(language IN ('en', 'es', 'fr', 'de', 'ja')),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default preferences
INSERT OR IGNORE INTO user_preferences (id, language) VALUES (1, 'en');

-- Store schema version
INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '7');

-- Insert default RAG prompt templates
INSERT OR IGNORE INTO prompt_templates (name, system_prompt, description, is_default) VALUES
('daily_reflection', 'You are a supportive journaling companion using Rogerian therapy principles. Help the user reflect on their thoughts and feelings with empathy and unconditional positive regard. Ask open-ended questions to deepen their self-understanding. Never judge or diagnose.', 'Daily journaling with supportive reflection', 1),
('crisis_support', 'You are an empathetic crisis support companion. The user may be experiencing distress. Provide a safe, non-judgmental space for them to express their thoughts. Use active listening and validation. Gently encourage healthy coping strategies. If they mention self-harm or suicide, provide crisis hotline information immediately: 988 Suicide & Crisis Lifeline.', 'Crisis support with safety resources', 0);

-- Seed built-in prompts from markdown files
INSERT OR IGNORE INTO prompts (name, title, content, is_system, created_at, updated_at) VALUES
('brain_dump', 'Brain Dump Session', '# Brain Dump Session Prompt

You are a Rogerian therapist assistant helping with brain dump sessions.

**Your Role:**
- Listen without judgment to the user''s stream of consciousness
- Reflect back what you hear to help the user process their thoughts
- Collect baseline psychological data (SUDS, sleep quality, energy levels)
- Help the user identify patterns and themes in their thoughts
- Provide a safe, empathetic space for emotional processing', 1, datetime('now'), datetime('now')),
('end_of_day', 'End of Day Reflection', '# End of Day Reflection Prompt

You are a reflective journaling assistant helping the user process their day.

**Your Role:**
- Guide the user through a structured end-of-day reflection
- Help identify wins, challenges, and lessons learned
- Facilitate gratitude and perspective-taking
- Support planning and intention-setting for tomorrow', 1, datetime('now'), datetime('now')),
('end_of_month', 'End of Month Review', '# End of Month Review Prompt

You are a strategic life coach helping the user conduct a comprehensive monthly review.

**Your Role:**
- Facilitate a big-picture reflection on the past month
- Help identify patterns, trends, and themes
- Guide goal assessment and recalibration
- Support intentional planning for the month ahead', 1, datetime('now'), datetime('now'));

-- V4: Usage Statistics (Issue #10)

-- Usage events table for tracking application usage patterns
CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL CHECK(event_type IN ('message_sent', 'recording_created', 'session_created', 'prompt_used')),
    provider TEXT CHECK(provider IN ('openai', 'claude', NULL)),
    prompt_name TEXT,
    token_count INTEGER,
    recording_duration_ms INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_events_type ON usage_events(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_events_provider ON usage_events(provider);
CREATE INDEX IF NOT EXISTS idx_usage_events_created ON usage_events(created_at DESC);

-- V5: Auto-Backup Functionality (Issue #14)

-- Backup settings table (singleton - only one row allowed)
CREATE TABLE IF NOT EXISTS backup_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 1,
    frequency TEXT NOT NULL DEFAULT 'daily' CHECK(frequency IN ('daily', 'weekly', 'manual')),
    backup_path TEXT NOT NULL,
    retention_count INTEGER NOT NULL DEFAULT 7,
    last_backup_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Backup history table for tracking all backups
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_automatic INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'success' CHECK(status IN ('success', 'failed')),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_backup_history_created ON backup_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backup_history_status ON backup_history(status);

-- V6: Session Tagging System (Issue #13)

-- Tags table for organizing sessions
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#3B82F6',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Session tags junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS session_tags (
    session_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, tag_id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_tags_session ON session_tags(session_id);
CREATE INDEX IF NOT EXISTS idx_session_tags_tag ON session_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Insert predefined tags with Tailwind colors
INSERT OR IGNORE INTO tags (name, color) VALUES
    ('work', '#3B82F6'),      -- blue-500
    ('personal', '#10B981'),   -- green-500
    ('research', '#8B5CF6'),   -- purple-500
    ('meeting', '#F59E0B'),    -- amber-500
    ('idea', '#EC4899'),       -- pink-500
    ('todo', '#EF4444');       -- red-500
