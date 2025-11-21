//! Tauri IPC command handlers

use braindump::services::claude_api::Message as ClaudeMessage;
use braindump::{
    AppState, AudioCommand, AudioData, AudioError, AudioResponse, BrainDumpError, ClaudeClient,
    DatabaseError, Recording, Transcript, TranscriptionError, WavWriter,
};
use rubato::{Resampler, SincFixedIn};
use std::sync::mpsc;
use std::time::Instant;
use tauri::State;

/// Resample audio from source sample rate to 16kHz for Whisper
fn resample_to_16khz(samples: &[f32], source_rate: u32) -> Result<Vec<f32>, BrainDumpError> {
    if source_rate == 16000 {
        return Ok(samples.to_vec());
    }

    braindump::logging::info(
        "Resampling",
        &format!("Resampling from {}Hz to 16kHz", source_rate),
    );

    let params = rubato::SincInterpolationParameters {
        sinc_len: 256,
        f_cutoff: 0.95,
        interpolation: rubato::SincInterpolationType::Linear,
        oversampling_factor: 256,
        window: rubato::WindowFunction::BlackmanHarris2,
    };

    let mut resampler = SincFixedIn::<f32>::new(
        16000 as f64 / source_rate as f64,
        2.0,
        params,
        samples.len(),
        1,
    )
    .map_err(|_e| BrainDumpError::Transcription(TranscriptionError::InvalidAudioData))?;

    let waves_in = vec![samples.to_vec()];
    let mut waves_out = resampler
        .process(&waves_in, None)
        .map_err(|_e| BrainDumpError::Transcription(TranscriptionError::InvalidAudioData))?;

    braindump::logging::info(
        "Resampling",
        &format!(
            "Resampled {} samples to {} samples",
            samples.len(),
            waves_out[0].len()
        ),
    );

    Ok(waves_out.remove(0))
}

#[tauri::command]
pub async fn start_recording(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    let (response_tx, response_rx) = mpsc::channel();

    state
        .audio_tx
        .send((AudioCommand::StartRecording, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    match response_rx
        .recv()
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?
    {
        AudioResponse::RecordingStarted => Ok("Recording started".to_string()),
        AudioResponse::Error(e) => Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => Err(BrainDumpError::Other("Unexpected response".to_string())),
    }
}

#[tauri::command]
pub async fn stop_recording(
    state: State<'_, AppState>,
) -> Result<serde_json::Value, BrainDumpError> {
    // Stop recording via audio thread
    let (response_tx, response_rx) = mpsc::channel();

    state
        .audio_tx
        .send((AudioCommand::StopRecording, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    let (samples, sample_rate) = match response_rx
        .recv()
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?
    {
        AudioResponse::RecordingStopped {
            samples,
            sample_rate,
        } => (samples, sample_rate),
        AudioResponse::Error(e) => {
            return Err(BrainDumpError::Audio(AudioError::RecordingFailed(e)))
        }
        _ => return Err(BrainDumpError::Other("Unexpected response".to_string())),
    };

    eprintln!(
        "✓ Step 1: Recording stopped ({} samples at {}Hz)",
        samples.len(),
        sample_rate
    );

    // Save WAV to test directory
    let timestamp = chrono::Utc::now().format("%Y-%m-%d_%H-%M-%S");
    let filepath = format!(
        "/Users/kjd/01-projects/IAC-031-clear-voice-app/test-recordings/{}.wav",
        timestamp
    );

    eprintln!("✓ Step 2: Saving WAV to {}", filepath);
    WavWriter::write_with_rate(&filepath, &samples, sample_rate).map_err(|e| {
        eprintln!("❌ ERROR: Failed to save WAV: {}", e);
        BrainDumpError::Io(e.to_string())
    })?;

    eprintln!("✓ Step 3: Calling Whisper FFI transcription via plugin manager");
    braindump::logging::info(
        "Transcription",
        &format!("Audio data: {} samples at {}Hz", samples.len(), sample_rate),
    );

    // Check sample rate
    if sample_rate != 16000 {
        braindump::logging::warn(
            "Transcription",
            &format!(
                "Sample rate {}Hz != 16kHz (Whisper requirement). Resampling needed!",
                sample_rate
            ),
        );
        eprintln!(
            "⚠️  WARNING: Audio is {}Hz, Whisper expects 16kHz. Resampling...",
            sample_rate
        );
    }

    // Resample to 16kHz if needed
    let resampled_samples = if sample_rate != 16000 {
        resample_to_16khz(&samples, sample_rate)?
    } else {
        samples.clone()
    };

    braindump::logging::info(
        "Transcription",
        &format!(
            "Prepared {} samples at 16kHz for Whisper",
            resampled_samples.len()
        ),
    );

    // Transcribe
    let start_time = Instant::now();
    let manager = state.plugin_manager.lock();

    let audio_data = AudioData {
        samples: resampled_samples,
        sample_rate: 16000, // Always 16kHz after resampling
        channels: 1,
    };

    braindump::logging::info("Transcription", "Calling plugin manager transcribe()");

    let transcript = match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        manager.transcribe(&audio_data)
    })) {
        Ok(result) => result.map_err(|e| {
            braindump::logging::error("Transcription", &format!("Failed: {}", e));
            eprintln!("❌ ERROR: Transcription failed: {}", e);
            BrainDumpError::Transcription(TranscriptionError::TranscriptionFailed(e.to_string()))
        })?,
        Err(_) => {
            braindump::logging::error("Transcription", "Whisper panicked - audio is safe");
            eprintln!("❌ CRITICAL: Whisper crashed but your audio was saved successfully");
            return Err(BrainDumpError::Transcription(TranscriptionError::TranscriptionFailed(
                "Transcription crashed but your audio was saved successfully. The recording is safe in test-recordings/".to_string()
            )));
        }
    };

    braindump::logging::info(
        "Transcription",
        &format!("Result: {} characters", transcript.text.len()),
    );
    eprintln!("✓ Transcription text: {} characters", transcript.text.len());

    let transcription_duration = start_time.elapsed().as_millis() as i64;
    eprintln!(
        "✓ Step 4: Transcription completed in {}ms",
        transcription_duration
    );
    drop(manager);

    // Save transcript to markdown file
    let transcript_path = format!(
        "/Users/kjd/01-projects/IAC-031-clear-voice-app/test-transcripts/{}.md",
        timestamp
    );

    let markdown_content = format!(
        "# Brain Dump Transcript\n\n**Date:** {}\n**Audio File:** {}.wav\n**Duration:** {}ms\n**Transcription Time:** {}ms\n\n---\n\n{}",
        chrono::Utc::now().format("%Y-%m-%d %H:%M:%S"),
        timestamp,
        (audio_data.samples.len() as i64 * 1000) / audio_data.sample_rate as i64,
        transcription_duration,
        transcript.text
    );

    eprintln!("✓ Step 5: Saving transcript to {}", transcript_path);
    std::fs::write(&transcript_path, markdown_content).map_err(|e| {
        eprintln!("❌ ERROR: Failed to save transcript: {}", e);
        BrainDumpError::Io(e.to_string())
    })?;

    eprintln!("✓ Step 6: Saving to database");

    // Save to database
    let db = state.db.lock();

    // Create recording entry
    let recording = Recording {
        id: None,
        filepath: filepath.clone(),
        duration_ms: (audio_data.samples.len() as i64 * 1000) / audio_data.sample_rate as i64,
        sample_rate: audio_data.sample_rate as i32,
        channels: audio_data.channels as i16,
        file_size_bytes: std::fs::metadata(&filepath).ok().map(|m| m.len() as i64),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    };

    let recording_id = db.create_recording(&recording).map_err(|e| {
        eprintln!("❌ ERROR: Failed to save recording to database: {}", e);
        BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string()))
    })?;

    eprintln!(
        "✓ Step 7: Recording saved to database with ID: {}",
        recording_id
    );

    // Create transcript entry
    let transcript_entry = Transcript {
        id: None,
        recording_id,
        text: transcript.text.clone(),
        language: Some("en".to_string()),
        confidence: 1.0,
        plugin_name: "whisper-cpp".to_string(),
        transcription_duration_ms: Some(transcription_duration),
        created_at: chrono::Utc::now(),
    };

    db.create_transcript(&transcript_entry).map_err(|e| {
        eprintln!("❌ ERROR: Failed to save transcript to database: {}", e);
        BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string()))
    })?;

    eprintln!("✓ Step 8: Transcript saved to database");

    // [NEW] Auto-create chat session with transcript as first message
    eprintln!("✓ Step 9: Auto-creating chat session");
    let session_id = {
        let now = chrono::Utc::now();

        // Create session with timestamp title
        let session = ChatSession {
            id: None,
            title: Some(format!("Brain Dump {}", now.format("%Y-%m-%d %H:%M"))),
            created_at: now,
            updated_at: now,
        };

        let session_id = db.create_chat_session(&session).map_err(|e| {
            eprintln!("❌ ERROR: Failed to create chat session: {}", e);
            BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string()))
        })?;

        eprintln!("✓ Step 10: Chat session created with ID: {}", session_id);

        // Save transcript as first message (role: user)
        let message = Message {
            id: None,
            session_id,
            recording_id: Some(recording_id),
            role: MessageRole::User,
            content: transcript.text.clone(),
            privacy_tags: None,
            created_at: now,
        };

        db.create_message(&message).map_err(|e| {
            eprintln!("❌ ERROR: Failed to save message: {}", e);
            BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string()))
        })?;

        eprintln!("✓ Step 11: Transcript saved as user message");

        session_id
    };

    drop(db);

    eprintln!("✓ Step 12: All steps completed successfully");

    // Return both transcript and session_id
    Ok(serde_json::json!({
        "transcript": transcript.text,
        "session_id": session_id,
        "recording_id": recording_id,
        "message": "Recording completed and chat session created"
    }))
}

use serde::Serialize;

#[derive(Serialize)]
pub struct TranscriptHistoryItem {
    pub id: i64,
    pub filepath: String,
    pub text: String,
    pub created_at: String,
    pub duration_ms: i64,
}

#[tauri::command]
pub async fn get_transcripts(
    state: State<'_, AppState>,
    limit: usize,
) -> Result<Vec<TranscriptHistoryItem>, BrainDumpError> {
    let db = state.db.lock();
    let recordings = db
        .list_recordings(limit)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    let mut results = Vec::new();
    for rec in recordings {
        if let Some(rec_id) = rec.id {
            if let Ok(trans) = db.get_transcript_by_recording(rec_id) {
                results.push(TranscriptHistoryItem {
                    id: rec_id,
                    filepath: rec.filepath,
                    text: trans.text,
                    created_at: rec.created_at.to_rfc3339(),
                    duration_ms: rec.duration_ms,
                });
            }
        }
    }

    Ok(results)
}

#[tauri::command]
pub async fn get_peak_level(state: State<'_, AppState>) -> Result<f32, BrainDumpError> {
    let (response_tx, response_rx) = mpsc::channel();

    state
        .audio_tx
        .send((AudioCommand::GetPeakLevel, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    match response_rx
        .recv()
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?
    {
        AudioResponse::PeakLevel(level) => Ok(level),
        AudioResponse::Error(e) => Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => Err(BrainDumpError::Other("Unexpected response".to_string())),
    }
}

#[tauri::command]
pub async fn pause_recording(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    let (response_tx, response_rx) = mpsc::channel();

    state
        .audio_tx
        .send((AudioCommand::PauseRecording, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    match response_rx
        .recv()
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?
    {
        AudioResponse::RecordingPaused => Ok("Recording paused".to_string()),
        AudioResponse::Error(e) => Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => Err(BrainDumpError::Other("Unexpected response".to_string())),
    }
}

#[tauri::command]
pub async fn resume_recording(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    let (response_tx, response_rx) = mpsc::channel();

    state
        .audio_tx
        .send((AudioCommand::ResumeRecording, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    match response_rx
        .recv()
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?
    {
        AudioResponse::RecordingResumed => Ok("Recording resumed".to_string()),
        AudioResponse::Error(e) => Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => Err(BrainDumpError::Other("Unexpected response".to_string())),
    }
}

#[tauri::command]
pub async fn is_model_loaded(state: State<'_, AppState>) -> Result<bool, BrainDumpError> {
    let manager = state.plugin_manager.lock();

    // Check if any plugin is registered and initialized
    Ok(manager.get_active().map(|_| true).unwrap_or(false))
}

/// Test command to verify IPC error serialization
/// This ensures BrainDumpError can be properly serialized across the IPC boundary
#[tauri::command]
pub async fn test_error_serialization() -> Result<String, BrainDumpError> {
    Err(BrainDumpError::Audio(AudioError::PermissionDenied))
}

// ===== C2 Integration Commands =====

use braindump::db::models::{ChatSession, Message, MessageRole};

#[tauri::command]
pub async fn create_chat_session(
    state: State<'_, AppState>,
    title: String,
) -> Result<ChatSession, BrainDumpError> {
    let db = state.db.lock();

    let session = ChatSession {
        id: None,
        title: Some(title),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    };

    let session_id = db
        .create_chat_session(&session)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    // Fetch the created session to return with ID
    let created_session = db
        .get_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    Ok(created_session)
}

#[tauri::command]
pub async fn list_chat_sessions(
    state: State<'_, AppState>,
    limit: usize,
) -> Result<Vec<ChatSession>, BrainDumpError> {
    let db = state.db.lock();

    let sessions = db
        .list_chat_sessions(limit)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    Ok(sessions)
}

#[tauri::command]
pub async fn save_message(
    state: State<'_, AppState>,
    session_id: i64,
    role: String,
    content: String,
    recording_id: Option<i64>,
) -> Result<Message, BrainDumpError> {
    let db = state.db.lock();

    let message_role = MessageRole::from_str(&role).map_err(|e| BrainDumpError::Other(e))?;

    let message = Message {
        id: None,
        session_id,
        recording_id,
        role: message_role,
        content,
        privacy_tags: None,
        created_at: chrono::Utc::now(),
    };

    let message_id = db
        .create_message(&message)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    // Return the message with ID
    Ok(Message {
        id: Some(message_id),
        ..message
    })
}

#[tauri::command]
pub async fn get_messages(
    state: State<'_, AppState>,
    session_id: i64,
) -> Result<Vec<Message>, BrainDumpError> {
    let db = state.db.lock();

    let messages = db
        .list_messages_by_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    Ok(messages)
}

use braindump::db::models::PromptTemplate;

#[tauri::command]
pub async fn list_prompt_templates(
    state: State<'_, AppState>,
) -> Result<Vec<PromptTemplate>, BrainDumpError> {
    let db = state.db.lock();

    db.list_prompt_templates()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

#[tauri::command]
pub async fn get_prompt_template(
    state: State<'_, AppState>,
    name: String,
) -> Result<PromptTemplate, BrainDumpError> {
    let db = state.db.lock();

    db.get_prompt_template_by_name(&name)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}
// ============================================================================
// Claude API Commands
// ============================================================================

/// Send message to Claude API (testing)
#[tauri::command]
pub async fn send_message_to_claude(
    state: State<'_, AppState>,
    message: String,
) -> Result<String, BrainDumpError> {
    let user_message = ClaudeMessage::user(message);
    let claude_client = state.claude_client.lock().clone();
    let response = claude_client.send_message(vec![user_message]).await?;
    Ok(response)
}

/// Store API key
#[tauri::command]
pub async fn store_api_key(key: String) -> Result<(), BrainDumpError> {
    ClaudeClient::store_api_key(&key)?;
    Ok(())
}

/// Check if API key exists
#[tauri::command]
pub async fn has_api_key() -> Result<bool, BrainDumpError> {
    Ok(ClaudeClient::has_api_key())
}

/// Test API key validity
#[tauri::command]
pub async fn test_api_key(state: State<'_, AppState>) -> Result<bool, BrainDumpError> {
    let claude_client = state.claude_client.lock().clone();
    let result = claude_client.test_api_key().await?;
    Ok(result)
}

/// Delete stored API key
#[tauri::command]
pub async fn delete_api_key() -> Result<(), BrainDumpError> {
    ClaudeClient::delete_api_key()?;
    Ok(())
}

/// Open browser to Anthropic console for authentication
#[tauri::command]
pub async fn open_auth_browser() -> Result<(), BrainDumpError> {
    let url = "https://console.anthropic.com/settings/keys";

    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(url)
            .spawn()
            .map_err(|e| BrainDumpError::Other(format!("Failed to open browser: {}", e)))?;
    }

    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(&["/C", "start", url])
            .spawn()
            .map_err(|e| BrainDumpError::Other(format!("Failed to open browser: {}", e)))?;
    }

    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(url)
            .spawn()
            .map_err(|e| BrainDumpError::Other(format!("Failed to open browser: {}", e)))?;
    }

    Ok(())
}

// ============================================================================
// OpenAI API Commands
// ============================================================================

use braindump::services::openai_api::ChatMessage as OpenAiChatMessage;
use braindump::OpenAiClient;

/// Send message to OpenAI API
#[tauri::command]
pub async fn send_openai_message(
    state: State<'_, AppState>,
    messages: Vec<(String, String)>, // (role, content) pairs
    system_prompt: Option<String>,
) -> Result<String, BrainDumpError> {
    let openai_client = &state.openai_client;

    // Convert tuples to ChatMessage format
    let chat_messages: Vec<OpenAiChatMessage> = messages
        .into_iter()
        .map(|(role, content)| OpenAiChatMessage { role, content })
        .collect();

    let response = openai_client
        .send_message(chat_messages, system_prompt)
        .await?;
    Ok(response)
}

/// Store OpenAI API key
#[tauri::command]
pub async fn store_openai_key(key: String) -> Result<(), BrainDumpError> {
    OpenAiClient::store_api_key(&key)?;
    Ok(())
}

/// Check if OpenAI API key exists
#[tauri::command]
pub async fn has_openai_key() -> Result<bool, BrainDumpError> {
    Ok(OpenAiClient::has_api_key())
}

/// Test OpenAI API key validity
#[tauri::command]
pub async fn test_openai_connection(state: State<'_, AppState>) -> Result<bool, BrainDumpError> {
    let result = state.openai_client.test_connection().await?;
    Ok(result)
}

/// Delete stored OpenAI API key
#[tauri::command]
pub async fn delete_openai_key() -> Result<(), BrainDumpError> {
    OpenAiClient::delete_api_key()?;
    Ok(())
}

/// Open browser to OpenAI console for API key
#[tauri::command]
pub async fn open_openai_auth_browser() -> Result<(), BrainDumpError> {
    let url = "https://platform.openai.com/api-keys";

    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(url)
            .spawn()
            .map_err(|e| BrainDumpError::Other(format!("Failed to open browser: {}", e)))?;
    }

    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(&["/C", "start", url])
            .spawn()
            .map_err(|e| BrainDumpError::Other(format!("Failed to open browser: {}", e)))?;
    }

    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(url)
            .spawn()
            .map_err(|e| BrainDumpError::Other(format!("Failed to open browser: {}", e)))?;
    }

    Ok(())
}

// ============================================================================
// Export Commands
// ============================================================================

/// Export chat session to markdown
#[tauri::command]
pub async fn export_session(
    session_id: i64,
    state: State<'_, AppState>,
) -> Result<String, BrainDumpError> {
    let db = state.db.lock();

    // Get session and messages
    let session = db
        .get_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    let messages = db
        .list_messages_by_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    drop(db);

    if messages.is_empty() {
        return Err(BrainDumpError::Other(
            "Cannot export empty session".to_string(),
        ));
    }

    // Export to markdown
    let file_path = braindump::export::markdown::export_session_to_markdown(&session, &messages)?;

    Ok(file_path.to_string_lossy().to_string())
}

/// Export chat session to PDF
#[tauri::command]
pub async fn export_session_pdf(
    session_id: i64,
    output_path: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    use braindump::export::{pdf::PDFExporter, Exporter, ExportOptions, ExportFormat};

    let db = state.db.lock();
    let session = db.get_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
    let messages = db.list_messages_by_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
    drop(db);

    let exporter = PDFExporter::new();
    let options = ExportOptions {
        format: ExportFormat::PDF,
        ..Default::default()
    };

    exporter.export(&session, &messages, std::path::PathBuf::from(output_path), &options)
        .map_err(|e| BrainDumpError::Other(e))
}

/// Export chat session to DOCX
#[tauri::command]
pub async fn export_session_docx(
    session_id: i64,
    output_path: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    use braindump::export::{docx::DocxExporter, Exporter, ExportOptions, ExportFormat};

    let db = state.db.lock();
    let session = db.get_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
    let messages = db.list_messages_by_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
    drop(db);

    let exporter = DocxExporter::new();
    let options = ExportOptions {
        format: ExportFormat::DOCX,
        ..Default::default()
    };

    exporter.export(&session, &messages, std::path::PathBuf::from(output_path), &options)
        .map_err(|e| BrainDumpError::Other(e))
}

/// Export chat session to HTML
#[tauri::command]
pub async fn export_session_html(
    session_id: i64,
    output_path: String,
    template: Option<String>,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    use braindump::export::{html::HTMLExporter, Exporter, ExportOptions, ExportFormat};

    let db = state.db.lock();
    let session = db.get_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
    let messages = db.list_messages_by_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
    drop(db);

    let exporter = HTMLExporter::new();
    let options = ExportOptions {
        format: ExportFormat::HTML,
        template,
        ..Default::default()
    };

    exporter.export(&session, &messages, std::path::PathBuf::from(output_path), &options)
        .map_err(|e| BrainDumpError::Other(e))
}

/// Export multiple sessions to a ZIP file
#[tauri::command]
pub async fn export_batch(
    session_ids: Vec<i64>,
    output_zip: String,
    format: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    use braindump::export::{batch::BatchExporter, ExportFormat, ExportOptions};

    // Parse format
    let export_format = match format.to_lowercase().as_str() {
        "pdf" => ExportFormat::PDF,
        "docx" => ExportFormat::DOCX,
        "html" => ExportFormat::HTML,
        "markdown" => ExportFormat::Markdown,
        _ => return Err(BrainDumpError::Other(format!("Invalid export format: {}", format))),
    };

    // Collect sessions and their messages
    let db = state.db.lock();
    let mut sessions_with_messages = Vec::new();

    for session_id in session_ids {
        let session = db.get_chat_session(session_id)
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;
        let messages = db.list_messages_by_session(session_id)
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

        sessions_with_messages.push((session, messages));
    }
    drop(db);

    // Create batch exporter
    let exporter = BatchExporter::new();
    let options = ExportOptions {
        format: export_format,
        ..Default::default()
    };

    exporter.export_multiple(sessions_with_messages, std::path::PathBuf::from(output_zip), &options)
        .map_err(|e| BrainDumpError::Other(e))
}

// ============================================================================
// File-based Prompt Template Commands
// ============================================================================

/// Load a prompt template from markdown file by name
#[tauri::command]
pub async fn load_prompt(name: String) -> Result<String, BrainDumpError> {
    braindump::prompts::load_prompt_template(&name)
}

/// List all available prompt templates from prompts directory
#[tauri::command]
pub async fn list_prompts() -> Result<Vec<String>, BrainDumpError> {
    braindump::prompts::list_prompt_templates()
}

// ============================================================================
// Session Management Commands
// ============================================================================

/// Rename a chat session
#[tauri::command]
pub async fn rename_session(
    session_id: i64,
    new_title: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    if new_title.trim().is_empty() {
        return Err(BrainDumpError::Other("Title cannot be empty".to_string()));
    }

    let db = state.db.lock();
    db.update_chat_session_title(session_id, &new_title)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    Ok(())
}

/// Delete a chat session and all its messages
#[tauri::command]
pub async fn delete_session(
    session_id: i64,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    let db = state.db.lock();

    // Delete session (messages will be cascade deleted due to foreign key constraint)
    db.delete_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    Ok(())
}

// ============================================================================
// App Settings Commands
// ============================================================================

/// Get selected AI provider (openai or claude)
#[tauri::command]
pub async fn get_selected_provider(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    let db = state.db.lock();
    let provider = db
        .get_app_setting("selected_provider")
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?
        .unwrap_or_else(|| "openai".to_string());
    Ok(provider)
}

/// Set selected AI provider (openai or claude)
#[tauri::command]
pub async fn set_selected_provider(
    provider: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    // Validate provider value
    if provider != "openai" && provider != "claude" {
        return Err(BrainDumpError::Other(
            "Invalid provider. Must be 'openai' or 'claude'".to_string(),
        ));
    }

    let db = state.db.lock();
    db.set_app_setting("selected_provider", &provider)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    eprintln!("✓ Provider set to: {}", provider);
    Ok(())
}

// ============================================================================
// Unified AI Message Command (with Provider Routing)
// ============================================================================

/// Send message to AI with automatic provider routing based on user selection
#[tauri::command]
pub async fn send_ai_message(
    state: State<'_, AppState>,
    messages: Vec<(String, String)>, // (role, content) pairs
    system_prompt: Option<String>,
) -> Result<String, BrainDumpError> {
    // Get selected provider from database
    let selected_provider = {
        let db = state.db.lock();
        db.get_app_setting("selected_provider")
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?
            .unwrap_or_else(|| "openai".to_string())
    };

    eprintln!("🔀 Routing message to provider: {}", selected_provider);

    // Route to appropriate client based on selected provider
    let response = match selected_provider.as_str() {
        "openai" => {
            eprintln!("  → Using OpenAI GPT-4");
            let client = &state.openai_client;

            // Convert tuples to OpenAI ChatMessage format
            let openai_messages: Vec<OpenAiChatMessage> = messages
                .into_iter()
                .map(|(role, content)| OpenAiChatMessage { role, content })
                .collect();

            client.send_message(openai_messages, system_prompt).await?
        }
        "claude" => {
            eprintln!("  → Using Claude (Anthropic)");
            let claude_client = state.claude_client.lock().clone();

            // For Claude, we'll send the most recent message
            // Claude client currently expects simple message format
            if let Some((_role, content)) = messages.last() {
                let claude_message = ClaudeMessage::user(content.clone());
                claude_client.send_message(vec![claude_message]).await?
            } else {
                return Err(BrainDumpError::Other("No messages to send".to_string()));
            }
        }
        _ => {
            return Err(BrainDumpError::Other(format!(
                "Unknown provider: {}",
                selected_provider
            )));
        }
    };

    eprintln!("✓ Response received from {}", selected_provider);
    Ok(response)
}

// ============================================================================
// User-Created Prompts Management Commands (Issue #3)
// ============================================================================

use braindump::db::models::Prompt;

/// List all user prompts (both system and user-created)
#[tauri::command]
pub async fn list_user_prompts(state: State<'_, AppState>) -> Result<Vec<Prompt>, BrainDumpError> {
    let db = state.db.lock();
    db.list_user_prompts()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Get a single prompt by ID
#[tauri::command]
pub async fn get_user_prompt(
    id: i64,
    state: State<'_, AppState>,
) -> Result<Prompt, BrainDumpError> {
    let db = state.db.lock();
    db.get_user_prompt(id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Create a new user prompt
#[tauri::command]
pub async fn create_user_prompt(
    name: String,
    title: String,
    content: String,
    state: State<'_, AppState>,
) -> Result<i64, BrainDumpError> {
    let db = state.db.lock();
    db.create_user_prompt(&name, &title, &content)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))
}

/// Update an existing user prompt
#[tauri::command]
pub async fn update_user_prompt(
    id: i64,
    title: String,
    content: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    let db = state.db.lock();
    db.update_user_prompt(id, &title, &content)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Delete a user prompt
#[tauri::command]
pub async fn delete_user_prompt(id: i64, state: State<'_, AppState>) -> Result<(), BrainDumpError> {
    let db = state.db.lock();
    db.delete_user_prompt(id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

// ============================================================================
// Usage Statistics Commands (Issue #10)
// ============================================================================

use braindump::db::models::{UsageEvent, UsageStats};

/// Get usage statistics for the dashboard
#[tauri::command]
pub async fn get_usage_stats(state: State<'_, AppState>) -> Result<UsageStats, BrainDumpError> {
    let db = state.db.lock();

    let stats = db
        .get_usage_stats()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    Ok(stats)
}

/// Track a usage event (for analytics)
#[tauri::command]
pub async fn track_usage(
    event_type: String,
    provider: Option<String>,
    prompt_name: Option<String>,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    let db = state.db.lock();

    let event = UsageEvent {
        id: None,
        event_type,
        provider,
        prompt_name,
        token_count: None,
        recording_duration_ms: None,
        created_at: chrono::Utc::now(),
    };

    db.track_usage_event(&event)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    Ok(())
}

// ============================================================================
// Session Tagging System Commands (Issue #13)
// ============================================================================

use braindump::db::models::Tag;

/// Get all tags
#[tauri::command]
pub async fn get_all_tags(state: State<'_, AppState>) -> Result<Vec<Tag>, BrainDumpError> {
    let db = state.db.lock();
    db.list_tags()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Create a new tag
#[tauri::command]
pub async fn create_tag(
    name: String,
    color: String,
    state: State<'_, AppState>,
) -> Result<Tag, BrainDumpError> {
    // Validate color format (should be hex color)
    if !color.starts_with('#') || color.len() != 7 {
        return Err(BrainDumpError::Other(
            "Invalid color format. Use hex color like #3B82F6".to_string(),
        ));
    }

    let db = state.db.lock();
    let tag_id = db
        .create_tag(&name, &color)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    db.get_tag(tag_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Add tag to session
#[tauri::command]
pub async fn add_tag_to_session(
    session_id: i64,
    tag_id: i64,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    let db = state.db.lock();
    db.add_tag_to_session(session_id, tag_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Remove tag from session
#[tauri::command]
pub async fn remove_tag_from_session(
    session_id: i64,
    tag_id: i64,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    let db = state.db.lock();
    db.remove_tag_from_session(session_id, tag_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Get tags for a specific session
#[tauri::command]
pub async fn get_session_tags(
    session_id: i64,
    state: State<'_, AppState>,
) -> Result<Vec<Tag>, BrainDumpError> {
    let db = state.db.lock();
    db.get_session_tags(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Delete a tag
#[tauri::command]
pub async fn delete_tag(tag_id: i64, state: State<'_, AppState>) -> Result<(), BrainDumpError> {
    let db = state.db.lock();
    db.delete_tag(tag_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Rename a tag
#[tauri::command]
pub async fn rename_tag(
    tag_id: i64,
    new_name: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    let db = state.db.lock();
    db.rename_tag(tag_id, &new_name)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Update tag color
#[tauri::command]
pub async fn update_tag_color(
    tag_id: i64,
    color: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    // Validate color format
    if !color.starts_with('#') || color.len() != 7 {
        return Err(BrainDumpError::Other(
            "Invalid color format. Use hex color like #3B82F6".to_string(),
        ));
    }

    let db = state.db.lock();
    db.update_tag_color(tag_id, &color)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Get tag usage counts (for tag manager)
#[tauri::command]
pub async fn get_tag_usage_counts(
    state: State<'_, AppState>,
) -> Result<Vec<serde_json::Value>, BrainDumpError> {
    let db = state.db.lock();
    let tag_counts = db
        .get_tag_usage_counts()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    // Convert to JSON with tag and count
    let results: Vec<serde_json::Value> = tag_counts
        .into_iter()
        .map(|(tag, count)| {
            serde_json::json!({
                "tag": tag,
                "usage_count": count
            })
        })
        .collect();

    Ok(results)
}

/// Merge two tags
#[tauri::command]
pub async fn merge_tags(
    source_tag_id: i64,
    target_tag_id: i64,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    if source_tag_id == target_tag_id {
        return Err(BrainDumpError::Other(
            "Cannot merge a tag with itself".to_string(),
        ));
    }

    let db = state.db.lock();
    db.merge_tags(source_tag_id, target_tag_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;
    Ok(())
}

/// Get sessions filtered by tags
#[tauri::command]
pub async fn get_sessions_by_tags(
    tag_ids: Vec<i64>,
    mode: String, // "any" or "all"
    limit: usize,
    state: State<'_, AppState>,
) -> Result<Vec<ChatSession>, BrainDumpError> {
    // Validate mode
    if mode != "any" && mode != "all" {
        return Err(BrainDumpError::Other(
            "Invalid mode. Use 'any' or 'all'".to_string(),
        ));
    }

    let db = state.db.lock();
    db.get_sessions_by_tags(&tag_ids, &mode, limit)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

// ============================================================================
// Backup System Commands (Issue #14)
// ============================================================================

use braindump::db::models::{BackupHistory, BackupSettings, BackupStatus};
use std::path::PathBuf;

/// Create a manual database backup
#[tauri::command]
pub async fn create_backup(
    state: State<'_, AppState>,
) -> Result<serde_json::Value, BrainDumpError> {
    braindump::logging::info("Backup", "Manual backup requested");

    // Get backup settings
    let settings = {
        let db = state.db.lock();
        db.get_backup_settings()
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?
    };

    // Get database path (from AppState or environment)
    let db_path = dirs::home_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join(".braindump/data/braindump.db");

    let backup_dir = PathBuf::from(&settings.backup_path);

    // Create backup manager
    let manager = braindump::backup::BackupManager::new(db_path, backup_dir)?;

    // Create backup
    let backup_info = manager.create_backup(false)?; // false = manual backup

    // Save backup history to database
    {
        let db = state.db.lock();

        let history = BackupHistory {
            id: None,
            file_path: backup_info.file_path.clone(),
            file_size_bytes: backup_info.file_size_bytes,
            created_at: backup_info.created_at,
            is_automatic: false,
            status: "success".to_string(),
            error_message: None,
        };

        db.create_backup_history(&history)
            .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

        // Update last backup time
        db.update_last_backup_time()
            .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

        // Clean up old backups based on retention setting
        manager.cleanup_old_backups(settings.retention_count as usize)?;
    }

    braindump::logging::info(
        "Backup",
        &format!("Backup created: {}", backup_info.file_name),
    );

    Ok(serde_json::json!({
        "file_path": backup_info.file_path,
        "file_name": backup_info.file_name,
        "file_size_bytes": backup_info.file_size_bytes,
        "created_at": backup_info.created_at.to_rfc3339(),
    }))
}

/// List all available backups
#[tauri::command]
pub async fn list_backups(
    state: State<'_, AppState>,
) -> Result<Vec<serde_json::Value>, BrainDumpError> {
    let settings = {
        let db = state.db.lock();
        db.get_backup_settings()
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?
    };

    let backup_dir = PathBuf::from(&settings.backup_path);
    let db_path = dirs::home_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join(".braindump/data/braindump.db");

    let manager = braindump::backup::BackupManager::new(db_path, backup_dir)?;
    let backups = manager.list_backups()?;

    // Convert to JSON
    let result = backups
        .iter()
        .map(|b| {
            serde_json::json!({
                "file_path": b.file_path,
                "file_name": b.file_name,
                "file_size_bytes": b.file_size_bytes,
                "created_at": b.created_at.to_rfc3339(),
                "is_automatic": b.is_automatic,
            })
        })
        .collect();

    Ok(result)
}

/// Restore database from a backup file
#[tauri::command]
pub async fn restore_backup(
    backup_path: String,
    state: State<'_, AppState>,
) -> Result<String, BrainDumpError> {
    braindump::logging::info(
        "Backup",
        &format!("Restore requested from: {}", backup_path),
    );

    let db_path = dirs::home_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join(".braindump/data/braindump.db");

    let settings = {
        let db = state.db.lock();
        db.get_backup_settings()
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?
    };

    let backup_dir = PathBuf::from(&settings.backup_path);
    let manager = braindump::backup::BackupManager::new(db_path, backup_dir)?;

    // Restore the backup
    let backup_file = PathBuf::from(&backup_path);
    manager.restore_backup(&backup_file)?;

    braindump::logging::info("Backup", "Restore completed successfully");

    Ok("Database restored successfully. Please restart the application.".to_string())
}

/// Delete a specific backup file
#[tauri::command]
pub async fn delete_backup(
    backup_path: String,
    state: State<'_, AppState>,
) -> Result<String, BrainDumpError> {
    let db_path = dirs::home_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join(".braindump/data/braindump.db");

    let settings = {
        let db = state.db.lock();
        db.get_backup_settings()
            .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?
    };

    let backup_dir = PathBuf::from(&settings.backup_path);
    let manager = braindump::backup::BackupManager::new(db_path, backup_dir)?;

    let backup_file = PathBuf::from(&backup_path);
    manager.delete_backup(&backup_file)?;

    braindump::logging::info("Backup", &format!("Backup deleted: {}", backup_path));

    Ok("Backup deleted successfully".to_string())
}

/// Get backup settings
#[tauri::command]
pub async fn get_backup_settings(
    state: State<'_, AppState>,
) -> Result<BackupSettings, BrainDumpError> {
    let db = state.db.lock();
    db.get_backup_settings()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Update backup settings
#[tauri::command]
pub async fn update_backup_settings(
    settings: BackupSettings,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    braindump::logging::info("Backup", "Updating backup settings");

    let db = state.db.lock();
    db.update_backup_settings(&settings)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    Ok(())
}

/// Get backup status information
#[tauri::command]
pub async fn get_backup_status(state: State<'_, AppState>) -> Result<BackupStatus, BrainDumpError> {
    let db = state.db.lock();
    db.get_backup_status()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// List backup history from database
#[tauri::command]
pub async fn list_backup_history(
    limit: usize,
    state: State<'_, AppState>,
) -> Result<Vec<BackupHistory>, BrainDumpError> {
    let db = state.db.lock();
    db.list_backup_history(limit)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

// ========== Language Preference Commands (Issue #12) ==========

/// Get the user's language preference
#[tauri::command]
pub async fn get_language_preference(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    braindump::logging::info("Language", "Getting language preference");

    let db = state.db.lock();
    db.get_language_preference()
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))
}

/// Set the user's language preference
#[tauri::command]
pub async fn set_language_preference(
    language: String,
    state: State<'_, AppState>,
) -> Result<(), BrainDumpError> {
    braindump::logging::info(
        "Language",
        &format!("Setting language preference to: {}", language),
    );

    // Validate language code
    let valid_languages = vec!["en", "es", "fr", "de", "ja"];
    if !valid_languages.contains(&language.as_str()) {
        return Err(BrainDumpError::Other(format!(
            "Invalid language code: {}. Supported languages: en, es, fr, de, ja",
            language
        )));
    }

    let db = state.db.lock();
    db.set_language_preference(&language)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    Ok(())
}

// ========== Git Publish Commands (Wave 2 - ZETA) ==========

use braindump::{GitPublisher, PublishResult, PublishStatus};
use std::path::PathBuf;

/// Initialize Git repository for publishing
#[tauri::command]
pub async fn git_init_repository(repo_path: String) -> Result<(), BrainDumpError> {
    braindump::logging::info("Git", &format!("Initializing repository at: {}", repo_path));

    let publisher = GitPublisher::new(repo_path);
    publisher.initialize_repository()?;

    braindump::logging::info("Git", "Repository initialized successfully");
    Ok(())
}

/// Get publish status (publishable card count, last publish time, etc.)
#[tauri::command]
pub async fn git_get_publish_status(
    repo_path: String,
    state: State<'_, AppState>,
) -> Result<PublishStatus, BrainDumpError> {
    braindump::logging::info("Git", "Getting publish status");

    let publisher = GitPublisher::new(repo_path);
    let db = state.db.lock();
    let status = publisher.get_status(&db)?;

    Ok(status)
}

/// Publish cards to Git repository
#[tauri::command]
pub async fn git_publish_cards(
    repo_path: String,
    commit_message: String,
    should_push: bool,
    remote_name: String,
    branch: String,
    state: State<'_, AppState>,
) -> Result<PublishResult, BrainDumpError> {
    braindump::logging::info(
        "Git",
        &format!("Publishing cards (push: {})", should_push),
    );

    // Get all cards from database
    let db = state.db.lock();
    let cards = db
        .get_publishable_cards(10000)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    drop(db); // Release lock before git operations

    braindump::logging::info("Git", &format!("Found {} publishable cards", cards.len()));

    // Publish cards
    let publisher = GitPublisher::new(repo_path);
    let result = publisher.publish_cards(
        &cards,
        &commit_message,
        should_push,
        &remote_name,
        &branch,
    )?;

    // Update published status in database
    let db = state.db.lock();
    for card in cards {
        if let Some(card_id) = card.id {
            let _ = db.publish_card(card_id, &result.commit_sha);
        }
    }

    braindump::logging::info(
        "Git",
        &format!(
            "Published {} cards, commit: {}",
            result.cards_published, result.commit_sha
        ),
    );

    Ok(result)
}

/// Get count of publishable cards (BUSINESS + IDEAS only)
#[tauri::command]
pub async fn git_get_publishable_count(state: State<'_, AppState>) -> Result<usize, BrainDumpError> {
    braindump::logging::info("Git", "Getting publishable card count");

    let db = state.db.lock();
    let cards = db
        .get_publishable_cards(10000)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    Ok(cards.len())
}

// ============================================================================
// Research API Integration Commands (Writer-Research Integration #126)
// ============================================================================

use braindump::services::research_client::{EnrichmentRequest, ResearchClient};

/// Enrich content via Research API
#[tauri::command]
pub async fn enrich_content(
    content: String,
    enrichment_type: String,
) -> Result<String, BrainDumpError> {
    braindump::logging::info(
        "Research",
        &format!("Enriching content (type: {})", enrichment_type),
    );

    // Validate enrichment type
    if !["expand", "summarize", "analyze"].contains(&enrichment_type.as_str()) {
        return Err(BrainDumpError::Other(
            "Invalid enrichment type. Must be 'expand', 'summarize', or 'analyze'".to_string(),
        ));
    }

    // Get Research API URL from environment or default
    let api_url = ResearchClient::get_base_url();
    let client = ResearchClient::new(api_url);

    // Create enrichment request
    let request = EnrichmentRequest {
        content,
        enrichment_type,
    };

    // Enrich with retry logic (3 retries with exponential backoff)
    match client.enrich_content_with_retry(request, 3).await {
        Ok(response) => {
            braindump::logging::info(
                "Research",
                &format!("Enrichment successful (job: {})", response.job_id),
            );
            Ok(response.enriched_content)
        }
        Err(e) => {
            braindump::logging::error("Research", &format!("Enrichment failed: {}", e));
            Err(e)
        }
    }
}

/// Check enrichment job status
#[tauri::command]
pub async fn check_enrichment_status(job_id: String) -> Result<String, BrainDumpError> {
    braindump::logging::info("Research", &format!("Checking job status: {}", job_id));

    let api_url = ResearchClient::get_base_url();
    let client = ResearchClient::new(api_url);

    match client.check_status(&job_id).await {
        Ok(status) => {
            braindump::logging::info("Research", &format!("Job status: {}", status));
            Ok(status)
        }
        Err(e) => {
            braindump::logging::error("Research", &format!("Status check failed: {}", e));
            Err(e)
        }
    }
}

/// Test connection to Research API
#[tauri::command]
pub async fn test_research_connection() -> Result<bool, BrainDumpError> {
    braindump::logging::info("Research", "Testing Research API connection");

    let api_url = ResearchClient::get_base_url();
    let client = ResearchClient::new(api_url);

    match client.test_connection().await {
        Ok(connected) => {
            if connected {
                braindump::logging::info("Research", "Connection successful");
            } else {
                braindump::logging::warn("Research", "Connection failed");
            }
            Ok(connected)
        }
        Err(e) => {
            braindump::logging::error("Research", &format!("Connection test error: {}", e));
            Err(e)
        }
    }
}

// ============================================================================
// Search Commands (OMICRON-2 Issue #75)
// ============================================================================

use braindump::db::models::{SearchFilters, SearchResult};

/// Search across sessions, transcripts, and messages
#[tauri::command]
pub async fn search_all(
    query: String,
    tags: Option<Vec<i64>>,
    start_date: Option<String>,
    end_date: Option<String>,
    state: State<'_, AppState>,
) -> Result<Vec<SearchResult>, BrainDumpError> {
    braindump::logging::info("Search", &format!("Searching for: {}", query));

    if query.len() < 2 {
        return Ok(Vec::new());
    }

    let filters = SearchFilters {
        tags,
        start_date,
        end_date,
    };

    let db = state.db.lock();
    let results = db
        .search_all(&query, filters)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    braindump::logging::info("Search", &format!("Found {} results", results.len()));

    Ok(results)
}
