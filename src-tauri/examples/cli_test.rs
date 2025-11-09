//! Command-line test for recording logic
//! Run with: cargo run --example cli_test

use braindump::{AudioCommand, AudioResponse, Recorder};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    println!("=== BrainDump Recording Test ===\n");

    // Create audio thread
    let (audio_tx, audio_rx) = mpsc::channel::<(AudioCommand, mpsc::Sender<AudioResponse>)>();

    let audio_handle = thread::spawn(move || {
        let mut recorder: Option<Recorder> = None;

        while let Ok((cmd, response_tx)) = audio_rx.recv() {
            match cmd {
                AudioCommand::StartRecording => {
                    if recorder.is_some() {
                        let _ = response_tx.send(AudioResponse::Error("Already recording".to_string()));
                        continue;
                    }

                    match Recorder::new() {
                        Ok(mut rec) => {
                            if let Err(e) = rec.start() {
                                let _ = response_tx.send(AudioResponse::Error(e.to_string()));
                            } else {
                                recorder = Some(rec);
                                let _ = response_tx.send(AudioResponse::RecordingStarted);
                            }
                        }
                        Err(e) => {
                            let _ = response_tx.send(AudioResponse::Error(e.to_string()));
                        }
                    }
                }
                AudioCommand::StopRecording => {
                    if let Some(mut rec) = recorder.take() {
                        match rec.stop() {
                            Ok(samples) => {
                                let sample_rate = rec.sample_rate();
                                let _ = response_tx.send(AudioResponse::RecordingStopped {
                                    samples,
                                    sample_rate
                                });
                            }
                            Err(e) => {
                                let _ = response_tx.send(AudioResponse::Error(e.to_string()));
                            }
                        }
                    } else {
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
                    break;
                }
            }
        }
    });

    // Start recording
    println!("1. Starting recording...");
    let (response_tx, response_rx) = mpsc::channel();
    audio_tx.send((AudioCommand::StartRecording, response_tx)).unwrap();

    match response_rx.recv_timeout(Duration::from_secs(2)).unwrap() {
        AudioResponse::RecordingStarted => println!("   ✓ Recording started"),
        AudioResponse::Error(e) => {
            eprintln!("   ✗ Error: {}", e);
            return;
        }
        _ => {
            eprintln!("   ✗ Unexpected response");
            return;
        }
    }

    // Monitor peak level
    println!("\n2. Recording for 5 seconds... (speak into microphone)");
    for i in 1..=5 {
        thread::sleep(Duration::from_secs(1));

        let (response_tx, response_rx) = mpsc::channel();
        audio_tx.send((AudioCommand::GetPeakLevel, response_tx)).unwrap();

        if let AudioResponse::PeakLevel(level) = response_rx.recv().unwrap() {
            let bars = "█".repeat((level * 50.0) as usize);
            println!("   [{}s] {:<50} {:.1}%", i, bars, level * 100.0);
        }
    }

    // Stop recording
    println!("\n3. Stopping recording...");
    let (response_tx, response_rx) = mpsc::channel();
    audio_tx.send((AudioCommand::StopRecording, response_tx)).unwrap();

    match response_rx.recv_timeout(Duration::from_secs(2)).unwrap() {
        AudioResponse::RecordingStopped { samples, sample_rate } => {
            println!("   ✓ Recording stopped");
            println!("   - Samples: {}", samples.len());
            println!("   - Sample rate: {} Hz", sample_rate);
            println!("   - Duration: {:.2} seconds", samples.len() as f32 / sample_rate as f32);
            println!("   - Peak amplitude: {:.1}%", samples.iter().map(|s| s.abs()).fold(0.0, f32::max) * 100.0);
        }
        AudioResponse::Error(e) => {
            eprintln!("   ✗ Error: {}", e);
            return;
        }
        _ => {
            eprintln!("   ✗ Unexpected response");
            return;
        }
    }

    // Cleanup
    let (response_tx, _) = mpsc::channel();
    audio_tx.send((AudioCommand::Shutdown, response_tx)).unwrap();
    audio_handle.join().unwrap();

    println!("\n=== Test Complete ===");
}
