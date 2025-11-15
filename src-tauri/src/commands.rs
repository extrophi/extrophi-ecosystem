//! Tauri IPC command handlers

use braindump::{
    AppState, WavWriter, AudioData, Recording, Transcript, AudioCommand, AudioResponse,
    BrainDumpError, AudioError, DatabaseError, TranscriptionError,
};
use tauri::State;
use std::time::Instant;
use std::sync::mpsc;
use rubato::{SincFixedIn, Resampler};

/// Resample audio from source sample rate to 16kHz for Whisper
fn resample_to_16khz(samples: &[f32], source_rate: u32) -> Result<Vec<f32>, BrainDumpError> {
    if source_rate == 16000 {
        return Ok(samples.to_vec());
    }

    braindump::logging::info("Resampling", &format!("Resampling from {}Hz to 16kHz", source_rate));

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
    ).map_err(|_e| BrainDumpError::Transcription(TranscriptionError::InvalidAudioData))?;

    let waves_in = vec![samples.to_vec()];
    let mut waves_out = resampler.process(&waves_in, None)
        .map_err(|_e| BrainDumpError::Transcription(TranscriptionError::InvalidAudioData))?;

    braindump::logging::info("Resampling", &format!("Resampled {} samples to {} samples", samples.len(), waves_out[0].len()));

    Ok(waves_out.remove(0))
}

#[tauri::command]
pub async fn start_recording(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    let (response_tx, response_rx) = mpsc::channel();

    state.audio_tx.send((AudioCommand::StartRecording, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    match response_rx.recv().map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))? {
        AudioResponse::RecordingStarted => Ok("Recording started".to_string()),
        AudioResponse::Error(e) => Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => Err(BrainDumpError::Other("Unexpected response".to_string())),
    }
}

#[tauri::command]
pub async fn stop_recording(state: State<'_, AppState>) -> Result<String, BrainDumpError> {
    // Stop recording via audio thread
    let (response_tx, response_rx) = mpsc::channel();

    state.audio_tx.send((AudioCommand::StopRecording, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    let (samples, sample_rate) = match response_rx.recv().map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))? {
        AudioResponse::RecordingStopped { samples, sample_rate } => (samples, sample_rate),
        AudioResponse::Error(e) => return Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => return Err(BrainDumpError::Other("Unexpected response".to_string())),
    };

    eprintln!("✓ Step 1: Recording stopped ({} samples at {}Hz)", samples.len(), sample_rate);

    // Save WAV to test directory
    let timestamp = chrono::Utc::now().format("%Y-%m-%d_%H-%M-%S");
    let filepath = format!(
        "/Users/kjd/01-projects/IAC-031-clear-voice-app/test-recordings/{}.wav",
        timestamp
    );

    eprintln!("✓ Step 2: Saving WAV to {}", filepath);
    WavWriter::write_with_rate(&filepath, &samples, sample_rate)
        .map_err(|e| {
            eprintln!("❌ ERROR: Failed to save WAV: {}", e);
            BrainDumpError::Io(e.to_string())
        })?;

    eprintln!("✓ Step 3: Calling Whisper FFI transcription via plugin manager");
    braindump::logging::info("Transcription", &format!("Audio data: {} samples at {}Hz", samples.len(), sample_rate));

    // Check sample rate
    if sample_rate != 16000 {
        braindump::logging::warn("Transcription", &format!("Sample rate {}Hz != 16kHz (Whisper requirement). Resampling needed!", sample_rate));
        eprintln!("⚠️  WARNING: Audio is {}Hz, Whisper expects 16kHz. Resampling...", sample_rate);
    }

    // Resample to 16kHz if needed
    let resampled_samples = if sample_rate != 16000 {
        resample_to_16khz(&samples, sample_rate)?
    } else {
        samples.clone()
    };

    braindump::logging::info("Transcription", &format!("Prepared {} samples at 16kHz for Whisper", resampled_samples.len()));

    // Transcribe
    let start_time = Instant::now();
    let manager = state.plugin_manager.lock();

    let audio_data = AudioData {
        samples: resampled_samples,
        sample_rate: 16000,  // Always 16kHz after resampling
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

    braindump::logging::info("Transcription", &format!("Result: {} characters", transcript.text.len()));
    eprintln!("✓ Transcription text: {} characters", transcript.text.len());

    let transcription_duration = start_time.elapsed().as_millis() as i64;
    eprintln!("✓ Step 4: Transcription completed in {}ms", transcription_duration);
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
    std::fs::write(&transcript_path, markdown_content)
        .map_err(|e| {
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

    let recording_id = db.create_recording(&recording)
        .map_err(|e| {
            eprintln!("❌ ERROR: Failed to save recording to database: {}", e);
            BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string()))
        })?;

    eprintln!("✓ Step 7: Recording saved to database with ID: {}", recording_id);

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

    db.create_transcript(&transcript_entry)
        .map_err(|e| {
            eprintln!("❌ ERROR: Failed to save transcript to database: {}", e);
            BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string()))
        })?;

    eprintln!("✓ Step 8: Transcript saved to database");
    drop(db);

    eprintln!("✓ Step 9: All steps completed successfully");
    Ok(transcript.text)
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
    let recordings = db.list_recordings(limit)
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

    state.audio_tx.send((AudioCommand::GetPeakLevel, response_tx))
        .map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))?;

    match response_rx.recv().map_err(|e| BrainDumpError::Audio(AudioError::DeviceInitFailed(e.to_string())))? {
        AudioResponse::PeakLevel(level) => Ok(level),
        AudioResponse::Error(e) => Err(BrainDumpError::Audio(AudioError::RecordingFailed(e))),
        _ => Err(BrainDumpError::Other("Unexpected response".to_string())),
    }
}

#[tauri::command]
pub async fn is_model_loaded(state: State<'_, AppState>) -> Result<bool, BrainDumpError> {
    let manager = state.plugin_manager.lock();

    // Check if any plugin is registered and initialized
    Ok(manager.get_active()
        .map(|_| true)
        .unwrap_or(false))
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

    let session_id = db.create_chat_session(&session)
        .map_err(|e| BrainDumpError::Database(DatabaseError::WriteFailed(e.to_string())))?;

    // Fetch the created session to return with ID
    let created_session = db.get_chat_session(session_id)
        .map_err(|e| BrainDumpError::Database(DatabaseError::ReadFailed(e.to_string())))?;

    Ok(created_session)
}

#[tauri::command]
pub async fn list_chat_sessions(
    state: State<'_, AppState>,
    limit: usize,
) -> Result<Vec<ChatSession>, BrainDumpError> {
    let db = state.db.lock();

    let sessions = db.list_chat_sessions(limit)
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

    let message_role = MessageRole::from_str(&role)
        .map_err(|e| BrainDumpError::Other(e))?;

    let message = Message {
        id: None,
        session_id,
        recording_id,
        role: message_role,
        content,
        privacy_tags: None,
        created_at: chrono::Utc::now(),
    };

    let message_id = db.create_message(&message)
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

    let messages = db.list_messages_by_session(session_id)
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