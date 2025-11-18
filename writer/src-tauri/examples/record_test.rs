//! Integration test: Record 5 seconds of audio and save to WAV
//!
//! Usage: cargo run --example record_test
//!
//! This will:
//! 1. Record 5 seconds of audio from default microphone
//! 2. Save to output.wav in project root
//! 3. Print statistics and instructions to play back

use braindump::{Recorder, WavWriter};
use std::io::{self, Write};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("BrainDump Rust Audio Recorder - Integration Test");
    println!("================================================\n");

    // Create recorder
    println!("Initializing recorder (16kHz mono)...");
    let mut recorder = Recorder::new()?;
    println!("Sample rate: {} Hz", recorder.sample_rate());
    println!();

    // Start recording
    println!("Starting recording...");
    recorder.start()?;
    println!("Recording started! Speak into your microphone.");
    println!();

    // Record for 5 seconds with progress indicator
    for i in 1..=5 {
        print!(
            "\rRecording: {} seconds... (peak: {:.4})",
            i,
            recorder.get_peak_level()
        );
        io::stdout().flush()?;
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
    println!("\n");

    // Stop recording
    println!("Stopping recorder...");
    let samples = recorder.stop()?;
    println!("Recording stopped!");
    println!();

    // Statistics
    let duration_secs = samples.len() as f32 / recorder.sample_rate() as f32;
    let peak = samples.iter().map(|s| s.abs()).fold(0.0, f32::max);

    println!("Recording Statistics:");
    println!("  Samples: {}", samples.len());
    println!("  Duration: {:.2} seconds", duration_secs);
    println!("  Peak level: {:.4}", peak);
    println!("  Memory used: ~{} KB", samples.len() * 4 / 1024);
    println!();

    // Save to WAV
    let output_path = "output.wav";
    println!("Saving to {}...", output_path);
    WavWriter::write_with_rate(output_path, &samples, recorder.sample_rate())?;

    // Get file size
    let metadata = std::fs::metadata(output_path)?;
    println!(
        "File saved! Size: {} bytes (~{} KB)",
        metadata.len(),
        metadata.len() / 1024
    );
    println!();

    // Playback instructions
    println!("To play back:");
    println!("  afplay {}", output_path);
    println!();

    println!("Test completed successfully!");

    Ok(())
}
