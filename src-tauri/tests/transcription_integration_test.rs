//! Integration test for transcription functionality
//! Tests the full workflow with actual audio files

#![cfg(feature = "whisper")]

use braindump::plugin::{whisper_cpp::WhisperCppPlugin, TranscriptionPlugin, AudioData};
use hound::WavReader;
use std::path::Path;
use std::time::Instant;

#[test]
fn test_transcription_with_real_audio() {
    // Skip if model not available
    let model_path = "models/ggml-base.bin";
    if !Path::new(model_path).exists() {
        println!("Skipping test - Whisper model not found at {}", model_path);
        println!("This is expected in CI without whisper-cpp installed");
        return;
    }

    // Skip if test audio not available
    let test_file = "../test-qa-final.wav";
    if !Path::new(test_file).exists() {
        println!("Skipping test - test-qa-final.wav not found at {}", test_file);
        println!("Current dir: {:?}", std::env::current_dir().unwrap());
        return;
    }

    println!("=== Transcription Integration Test ===");
    println!("");

    // Load audio
    println!("Loading audio file: {}", test_file);
    let mut reader = WavReader::open(test_file)
        .expect("Failed to open test audio file");

    let spec = reader.spec();
    println!("  Sample rate: {} Hz", spec.sample_rate);
    println!("  Channels: {}", spec.channels);
    println!("  Bits per sample: {}", spec.bits_per_sample);

    // Convert to f32 samples
    let samples: Vec<f32> = reader.samples::<i16>()
        .map(|s| s.unwrap() as f32 / i16::MAX as f32)
        .collect();

    let duration_sec = samples.len() as f32 / spec.sample_rate as f32;
    println!("  Duration: {:.2}s", duration_sec);
    println!("  Total samples: {}", samples.len());
    println!("");

    let audio = AudioData {
        samples,
        sample_rate: spec.sample_rate,
        channels: spec.channels,
    };

    // Initialize plugin
    println!("Initializing Whisper model...");
    let model_path = "models/ggml-base.bin";
    let mut plugin = WhisperCppPlugin::new(model_path.to_string());

    let init_start = Instant::now();
    plugin.initialize()
        .expect("Failed to initialize Whisper plugin");
    let init_duration = init_start.elapsed();
    println!("  Model initialized in {:.3}s", init_duration.as_secs_f32());
    println!("");

    // Transcribe
    println!("Transcribing audio...");
    let transcribe_start = Instant::now();
    let transcript = plugin.transcribe(&audio)
        .expect("Transcription failed - this should not happen if libraries are linked correctly!");
    let transcribe_duration = transcribe_start.elapsed();

    println!("");
    println!("=== RESULTS ===");
    println!("Transcription time: {:.3}s", transcribe_duration.as_secs_f32());
    println!("Speed factor: {:.1}x faster than real-time",
        duration_sec / transcribe_duration.as_secs_f32());
    println!("");
    println!("Transcribed text:");
    println!("---");
    println!("{}", transcript.text);
    println!("---");

    if let Some(lang) = &transcript.language {
        println!("Detected language: {}", lang);
    }

    // Assertions
    assert!(!transcript.text.is_empty(), "Transcript should not be empty");
    assert!(transcript.segments.len() > 0, "Should have at least one segment");

    println!("");
    println!("✓ TEST PASSED: Transcription completed successfully");
    println!("✓ No error code 43959840");
    println!("✓ Libraries linked correctly");
}

#[test]
fn test_plugin_initialization() {
    println!("Testing plugin initialization...");

    let model_path = "models/ggml-base.bin";

    // Skip if model not available
    if !Path::new(model_path).exists() {
        println!("Skipping test - Whisper model not found at {}", model_path);
        println!("This is expected in CI without whisper-cpp installed");
        return;
    }

    let mut plugin = WhisperCppPlugin::new(model_path.to_string());

    assert_eq!(plugin.name(), "whisper-cpp");
    assert_eq!(plugin.version(), "1.8.2");
    assert!(!plugin.is_initialized());

    plugin.initialize()
        .expect("Plugin initialization failed");

    assert!(plugin.is_initialized());

    println!("✓ Plugin initialized successfully");
}
