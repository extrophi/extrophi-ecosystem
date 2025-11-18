//! Performance benchmarks for Candle plugin
//!
//! Compares pure Rust Candle implementation against C++ FFI plugin

use braindump::plugin::{candle::CandlePlugin, AudioData, TranscriptionPlugin};
use std::path::PathBuf;
use std::time::Instant;

/// Generate test audio (silence - just for performance testing)
fn generate_test_audio(duration_secs: usize) -> AudioData {
    let sample_rate = 16000;
    let samples = vec![0.0_f32; sample_rate * duration_secs];

    AudioData {
        samples,
        sample_rate: sample_rate as u32,
        channels: 1,
    }
}

/// Benchmark Candle plugin transcription
fn benchmark_candle_transcription() {
    println!("\n=== Candle Plugin Performance Benchmark ===\n");

    let model_path = PathBuf::from("models/candle/model.safetensors");

    if !model_path.exists() {
        eprintln!("❌ Model file not found: {}", model_path.display());
        eprintln!("   Run: scripts/download_candle_models.sh");
        return;
    }

    let mut plugin = CandlePlugin::new(model_path);

    // Measure initialization time
    println!("1. Initialization");
    let start = Instant::now();
    match plugin.initialize() {
        Ok(_) => {
            let init_time = start.elapsed();
            println!(
                "   ✅ Initialized in {:.2}ms",
                init_time.as_secs_f64() * 1000.0
            );
        }
        Err(e) => {
            eprintln!("   ❌ Initialization failed: {}", e);
            return;
        }
    }

    // Test different audio durations
    let test_durations = vec![5, 10, 30, 60];

    println!("\n2. Transcription Performance");
    for duration in test_durations {
        let audio = generate_test_audio(duration);
        let audio_size_mb = (audio.samples.len() * 4) as f64 / (1024.0 * 1024.0);

        print!(
            "   Testing {}s audio ({:.1}MB)... ",
            duration, audio_size_mb
        );

        let start = Instant::now();
        match plugin.transcribe(&audio) {
            Ok(transcript) => {
                let elapsed = start.elapsed();
                let elapsed_secs = elapsed.as_secs_f64();
                let realtime_factor = elapsed_secs / duration as f64;

                println!("✅ {:.2}s ({:.2}× realtime)", elapsed_secs, realtime_factor);
                println!("      Transcript length: {} chars", transcript.text.len());
            }
            Err(e) => {
                println!("❌ Failed: {}", e);
            }
        }
    }

    // Shutdown
    println!("\n3. Shutdown");
    let start = Instant::now();
    plugin.shutdown().unwrap();
    let shutdown_time = start.elapsed();
    println!(
        "   ✅ Shutdown in {:.2}ms",
        shutdown_time.as_secs_f64() * 1000.0
    );

    println!("\n=== Benchmark Complete ===\n");
}

/// Compare performance expectations
fn print_performance_targets() {
    println!("\n=== Performance Targets (from PRD) ===\n");
    println!("Candle Plugin:");
    println!("  • Target: <4s per 1min audio");
    println!("  • Acceptable: Within 2× of C++ plugin");
    println!("  • GPU: Metal acceleration on M-series Macs");
    println!("  • Accuracy: >95% (±1% WER vs C++)");
    println!("\nC++ Plugin (Reference):");
    println!("  • Target: <2s per 1min audio");
    println!("  • 25× faster than realtime");
    println!();
}

fn main() {
    print_performance_targets();
    benchmark_candle_transcription();
}
