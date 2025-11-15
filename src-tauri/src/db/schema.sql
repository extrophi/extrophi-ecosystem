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

-- Store schema version
INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '2');

-- Insert default RAG prompt templates
INSERT OR IGNORE INTO prompt_templates (name, system_prompt, description, is_default) VALUES
('daily_reflection', 'You are a supportive journaling companion using Rogerian therapy principles. Help the user reflect on their thoughts and feelings with empathy and unconditional positive regard. Ask open-ended questions to deepen their self-understanding. Never judge or diagnose.', 'Daily journaling with supportive reflection', 1),
('crisis_support', 'You are an empathetic crisis support companion. The user may be experiencing distress. Provide a safe, non-judgmental space for them to express their thoughts. Use active listening and validation. Gently encourage healthy coping strategies. If they mention self-harm or suicide, provide crisis hotline information immediately: 988 Suicide & Crisis Lifeline.', 'Crisis support with safety resources', 0);
