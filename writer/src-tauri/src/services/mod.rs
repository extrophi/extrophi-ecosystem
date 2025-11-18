//! Services module
//! Contains external service integrations

pub mod claude_api;
pub mod model_manager;
pub mod openai_api;
pub mod vad;

pub use claude_api::ClaudeClient;
pub use model_manager::{
    delete_model, download_model, get_available_models, get_installed_models, WhisperModel,
};
pub use openai_api::OpenAiClient;
pub use vad::{detect_speech_segments, preprocess_audio_with_vad, VADConfig};
