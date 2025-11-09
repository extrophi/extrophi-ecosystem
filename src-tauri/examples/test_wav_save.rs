//! Test WAV file saving to BrainDumpSessions directory

use braindump::WavWriter;
use chrono::Local;

fn main() {
    // Generate test audio: 1 second of 440Hz sine wave at 16kHz
    let sample_rate = 16000u32;
    let duration = 1.0; // seconds
    let frequency = 440.0; // A4 note
    
    let num_samples = (sample_rate as f32 * duration) as usize;
    let mut samples = Vec::with_capacity(num_samples);
    
    for i in 0..num_samples {
        let t = i as f32 / sample_rate as f32;
        let sample = (2.0 * std::f32::consts::PI * frequency * t).sin() * 0.3; // 30% volume
        samples.push(sample);
    }
    
    // Generate filename with timestamp
    let filename = format!(
        "{}_recording.wav",
        Local::now().format("%Y-%m-%d_%H-%M-%S")
    );
    
    let filepath = format!(
        "/Users/kjd/09-personal/BrainDumpSessions/audio/{}",
        filename
    );
    
    println!("Saving test audio to: {}", filepath);
    
    // Save WAV file
    match WavWriter::write_with_rate(&filepath, &samples, sample_rate) {
        Ok(_) => {
            println!("SUCCESS! WAV file saved successfully.");
            println!("File path: {}", filepath);
            println!("Format: 16-bit PCM, mono, {}Hz", sample_rate);
            println!("Duration: {} seconds ({} samples)", duration, num_samples);
        }
        Err(e) => {
            eprintln!("ERROR: Failed to save WAV file: {}", e);
            std::process::exit(1);
        }
    }
}
