// Prevents additional console window on Windows in release builds
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use braindump::{AppState, audio, db, plugin, AudioCommand, AudioResponse, ClaudeClient, OpenAiClient};
use std::sync::{Arc, mpsc};
use std::thread;
use parking_lot::Mutex;
use tauri::Emitter;

mod commands;

fn main() {
    eprintln!("=== MAIN STARTED ===");
    eprintln!("Current dir: {:?}", std::env::current_dir());
    eprintln!("Executable: {:?}", std::env::current_exe());
    eprintln!("About to initialize logger...");
    
    // Initialize logger FIRST - so we can capture all errors
    if let Err(e) = braindump::logging::Logger::init() {
        eprintln!("Failed to initialize logger: {}", e);
        // Continue anyway - logging failure shouldn't block startup
    }
    
    eprintln!("=== LOGGER INITIALIZED ===");
    
    braindump::logging::info("Startup", "BrainDump v3.0.0 initializing");
    braindump::logging::info("Startup", &format!("Current directory: {:?}", std::env::current_dir()));
    braindump::logging::info("Startup", &format!("Executable path: {:?}", std::env::current_exe()));
    
    let db_path = dirs::home_dir()
        .unwrap_or_else(|| {
            eprintln!("No home directory found, using current directory");
            std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."))
        })
        .join(".braindump")
        .join("data")
        .join("braindump.db");

    // Ensure directory exists
    if let Some(parent) = db_path.parent() {
        if let Err(e) = std::fs::create_dir_all(parent) {
            eprintln!("Failed to create data directory: {}", e);
            // Continue - might work later
        }
    }
    braindump::logging::info("Database", &format!("Opening database at: {}", db_path.display()));

    let conn = match db::initialize_db(db_path.clone()) {
        Ok(c) => {
            braindump::logging::info("Database", "Database initialized successfully");
            c
        }
        Err(e) => {
            braindump::logging::critical("Database", &format!("Failed to initialize: {}", e));
            panic!("Database initialization failed: {}", e);
        }
    };

    let repository = Arc::new(Mutex::new(db::Repository::new(conn)));
    
    // Initialize plugin manager
    braindump::logging::info("Plugin", "Initializing plugin manager");
    let plugin_manager = plugin::manager::PluginManager::new();
    
    // Determine model path (absolute path for Tauri)
    let model_path = if cfg!(debug_assertions) {
        // Development mode: use project root
        std::env::current_dir()
            .unwrap_or_else(|_| {
                eprintln!("Could not determine current directory, using default");
                std::path::PathBuf::from(".")
            })
            .join("models/ggml-base.bin")
    } else {
        // Production mode: bundled in app resources
        // In macOS .app bundle, resources are in Contents/Resources/
        std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|p| p.to_path_buf()))
            .and_then(|p| p.parent().map(|p| p.to_path_buf()))
            .map(|p| p.join("Resources/models/ggml-base.bin"))
            .unwrap_or_else(|| {
                eprintln!("Could not determine model path, using default");
                std::path::PathBuf::from("models/ggml-base.bin")
            })
    };

    braindump::logging::info("Model", &format!("Model path: {}", model_path.display()));
    braindump::logging::info("Model", &format!("Model exists: {}", model_path.exists()));
    
    if !model_path.exists() {
        braindump::logging::error("Model", &format!("Model file NOT FOUND at: {}", model_path.display()));
    } else {
        if let Ok(metadata) = std::fs::metadata(&model_path) {
            braindump::logging::info("Model", &format!("Model file size: {} MB", metadata.len() / 1_048_576));
        }
    }

    println!("Whisper model will be loaded in background from: {}", model_path.display());

    let plugin_manager = Arc::new(Mutex::new(plugin_manager));

    // Create audio thread
    braindump::logging::info("Audio", "Creating audio recording thread");
    let (audio_tx, audio_rx) = mpsc::channel::<(AudioCommand, mpsc::Sender<AudioResponse>)>();

    thread::spawn(move || {
        braindump::logging::info("Audio", "Audio thread started");
        let mut recorder: Option<audio::Recorder> = None;

        while let Ok((cmd, response_tx)) = audio_rx.recv() {
            match cmd {
                AudioCommand::StartRecording => {
                    braindump::logging::info("Audio", "StartRecording command received");
                    
                    if recorder.is_some() {
                        braindump::logging::warn("Audio", "Recording already in progress");
                        let _ = response_tx.send(AudioResponse::Error("Already recording".to_string()));
                        continue;
                    }

                    match audio::Recorder::new() {
                        Ok(mut rec) => {
                            braindump::logging::info("Audio", "Recorder created, starting capture");
                            if let Err(e) = rec.start() {
                                braindump::logging::error("Audio", &format!("Failed to start recording: {}", e));
                                let _ = response_tx.send(AudioResponse::Error(e.to_string()));
                            } else {
                                braindump::logging::info("Audio", "Recording started successfully");
                                recorder = Some(rec);
                                let _ = response_tx.send(AudioResponse::RecordingStarted);
                            }
                        }
                        Err(e) => {
                            braindump::logging::error("Audio", &format!("Failed to create recorder: {}", e));
                            let _ = response_tx.send(AudioResponse::Error(e.to_string()));
                        }
                    }
                }
                AudioCommand::StopRecording => {
                    braindump::logging::info("Audio", "StopRecording command received");
                    
                    if let Some(mut rec) = recorder.take() {
                        match rec.stop() {
                            Ok(samples) => {
                                let sample_rate = rec.sample_rate();
                                braindump::logging::info("Audio", &format!("Recording stopped: {} samples at {}Hz", samples.len(), sample_rate));
                                let _ = response_tx.send(AudioResponse::RecordingStopped {
                                    samples,
                                    sample_rate
                                });
                            }
                            Err(e) => {
                                braindump::logging::error("Audio", &format!("Failed to stop recording: {}", e));
                                let _ = response_tx.send(AudioResponse::Error(e.to_string()));
                            }
                        }
                    } else {
                        braindump::logging::warn("Audio", "No active recording to stop");
                        let _ = response_tx.send(AudioResponse::Error("Not recording".to_string()));
                    }
                }
                AudioCommand::GetPeakLevel => {
                    if let Some(rec) = &recorder {
                        let level = rec.get_peak_level();
                        let _ = response_tx.send(AudioResponse::PeakLevel(level));
                    } else {
                        let _ = response_tx.send(AudioResponse::PeakLevel(0.0));
                    }
                }
                AudioCommand::Shutdown => {
                    braindump::logging::info("Audio", "Audio thread shutting down");
                    break;
                }
            }
        }
    });

    // Clone for background initialization
    let plugin_manager_for_init = plugin_manager.clone();
    let model_path_for_init = model_path.clone();

    // Initialize Claude API client
    braindump::logging::info("Claude", "Initializing Claude API client");
    let claude_client = Arc::new(Mutex::new(ClaudeClient::new()));

    // Initialize OpenAI API client
    braindump::logging::info("OpenAI", "Initializing OpenAI API client");
    let openai_client = Arc::new(OpenAiClient::new());

    let app_state = AppState {
        plugin_manager,
        db: repository,
        audio_tx,
        claude_client,
        openai_client,
    };

    braindump::logging::info("Tauri", "Building Tauri application");

    tauri::Builder::default()
        .manage(app_state)
        .setup(move |app| {
            braindump::logging::info("Tauri", "Tauri setup() called");
            
            let app_handle = app.handle().clone();
            let plugin_manager_clone = plugin_manager_for_init;
            let model_path_clone = model_path_for_init;

            // Spawn background task for plugin initialization
            tauri::async_runtime::spawn(async move {
                braindump::logging::info("Plugin", "Starting background model loading");
                
                // Emit loading status
                let _ = app_handle.emit(
                    "model-loading",
                    serde_json::json!({
                        "status": "loading",
                        "message": "Initializing Whisper model..."
                    })
                );

                // Register and initialize plugin in background
                let result: Result<(), String> = (|| {
                    #[cfg(feature = "whisper")]
                    {
                        let mut manager = plugin_manager_clone.lock();

                        braindump::logging::info("Plugin", "Registering WhisperCpp plugin");

                        // Register C++ FFI plugin
                        let cpp_plugin = Box::new(plugin::whisper_cpp::WhisperCppPlugin::new(
                            model_path_clone.to_string_lossy().to_string()
                        ));

                        if let Err(e) = manager.register(cpp_plugin) {
                            let err_msg = format!("Failed to register plugin: {}", e);
                            braindump::logging::error("Plugin", &err_msg);
                            return Err(err_msg);
                        }

                        braindump::logging::info("Plugin", "Initializing plugins");

                        // Initialize all plugins
                        let init_results = manager.initialize_all();
                        for (name, result) in init_results {
                            if let Err(e) = result {
                                let err_msg = format!("Failed to initialize plugin {}: {}", name, e);
                                braindump::logging::error("Plugin", &err_msg);
                                return Err(err_msg);
                            } else {
                                braindump::logging::info("Plugin", &format!("Plugin '{}' initialized successfully", name));
                            }
                        }
                    }

                    #[cfg(not(feature = "whisper"))]
                    {
                        braindump::logging::info("Plugin", "Whisper support disabled (feature not enabled)");
                    }

                    Ok(())
                })();

                // Emit result
                match result {
                    Ok(_) => {
                        braindump::logging::info("Plugin", "Whisper model loaded successfully!");
                        println!("Whisper model loaded successfully!");
                        let _ = app_handle.emit(
                            "model-loading",
                            serde_json::json!({
                                "status": "ready",
                                "message": "Model loaded successfully"
                            })
                        );
                    }
                    Err(e) => {
                        braindump::logging::critical("Plugin", &format!("Failed to load model: {}", e));
                        eprintln!("Failed to load model: {}", e);
                        let _ = app_handle.emit(
                            "model-loading",
                            serde_json::json!({
                                "status": "error",
                                "message": e
                            })
                        );
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::start_recording,
            commands::stop_recording,
            commands::get_transcripts,
            commands::get_peak_level,
            commands::is_model_loaded,
            commands::test_error_serialization,
            // C2 Integration Commands
            commands::create_chat_session,
            commands::list_chat_sessions,
            commands::save_message,
            commands::get_messages,
            commands::list_prompt_templates,
            commands::get_prompt_template,
            // Claude API Commands
            commands::send_message_to_claude,
            commands::store_api_key,
            commands::has_api_key,
            commands::test_api_key,
            commands::delete_api_key,
            commands::open_auth_browser,
            // OpenAI API Commands
            commands::send_openai_message,
            commands::store_openai_key,
            commands::has_openai_key,
            commands::test_openai_connection,
            commands::delete_openai_key,
            commands::open_openai_auth_browser,
            // Export Commands
            commands::export_session,
            // File-based Prompt Template Commands
            commands::load_prompt,
            commands::list_prompts,
        ])
        .run(tauri::generate_context!())
        .unwrap_or_else(|e| {
            braindump::logging::critical("Tauri", &format!("Failed to run application: {}", e));
            eprintln!("Error while running Tauri application: {}", e);
        });
    
    braindump::logging::info("Shutdown", "Application exiting");
}