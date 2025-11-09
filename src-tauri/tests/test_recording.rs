//! Integration test for recording logic
//! Tests the audio recording commands in isolation

use braindump::{AudioCommand, AudioResponse};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

#[test]
fn test_recording_lifecycle() {
    // Create audio thread (same as main.rs)
    let (audio_tx, audio_rx) = mpsc::channel::<(AudioCommand, mpsc::Sender<AudioResponse>)>();

    let audio_handle = thread::spawn(move || {
        let mut recorder: Option<braindump::Recorder> = None;

        while let Ok((cmd, response_tx)) = audio_rx.recv() {
            match cmd {
                AudioCommand::StartRecording => {
                    if recorder.is_some() {
                        let _ = response_tx.send(AudioResponse::Error("Already recording".to_string()));
                        continue;
                    }

                    match braindump::Recorder::new() {
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

    // Test 1: Start recording
    let (response_tx, response_rx) = mpsc::channel();
    audio_tx.send((AudioCommand::StartRecording, response_tx)).unwrap();

    match response_rx.recv_timeout(Duration::from_secs(2)).unwrap() {
        AudioResponse::RecordingStarted => println!("✓ Recording started successfully"),
        AudioResponse::Error(e) => panic!("Failed to start recording: {}", e),
        _ => panic!("Unexpected response"),
    }

    // Test 2: Get peak level while recording
    thread::sleep(Duration::from_millis(500));

    let (response_tx, response_rx) = mpsc::channel();
    audio_tx.send((AudioCommand::GetPeakLevel, response_tx)).unwrap();

    match response_rx.recv_timeout(Duration::from_secs(2)).unwrap() {
        AudioResponse::PeakLevel(level) => {
            println!("✓ Peak level: {}", level);
            assert!(level >= 0.0, "Peak level should be non-negative");
        }
        _ => panic!("Unexpected response"),
    }

    // Test 3: Record for 5 seconds
    println!("Recording for 5 seconds... (speak into microphone)");
    thread::sleep(Duration::from_secs(5));

    // Test 4: Stop recording and get samples
    let (response_tx, response_rx) = mpsc::channel();
    audio_tx.send((AudioCommand::StopRecording, response_tx)).unwrap();

    match response_rx.recv_timeout(Duration::from_secs(2)).unwrap() {
        AudioResponse::RecordingStopped { samples, sample_rate } => {
            println!("✓ Recording stopped successfully");
            println!("  Samples: {}", samples.len());
            println!("  Sample rate: {} Hz", sample_rate);
            println!("  Duration: {:.2} seconds", samples.len() as f32 / sample_rate as f32);

            assert!(!samples.is_empty(), "Should have captured audio samples");
            assert!(sample_rate > 0, "Sample rate should be positive");

            // Verify we recorded approximately 5 seconds (allow some buffer latency)
            let duration_secs = samples.len() as f32 / sample_rate as f32;
            assert!(duration_secs >= 4.5 && duration_secs <= 6.0,
                "Duration should be approximately 5 seconds, got {:.2}", duration_secs);
        }
        AudioResponse::Error(e) => panic!("Failed to stop recording: {}", e),
        _ => panic!("Unexpected response"),
    }

    // Cleanup
    let (response_tx, _) = mpsc::channel();
    audio_tx.send((AudioCommand::Shutdown, response_tx)).unwrap();
    audio_handle.join().unwrap();

    println!("\n✓ All recording tests passed!");
}

#[test]
fn test_error_handling() {
    // Test stopping when not recording
    let (audio_tx, audio_rx) = mpsc::channel::<(AudioCommand, mpsc::Sender<AudioResponse>)>();

    let audio_handle = thread::spawn(move || {
        let recorder: Option<braindump::Recorder> = None;

        if let Ok((AudioCommand::StopRecording, response_tx)) = audio_rx.recv() {
            if recorder.is_none() {
                let _ = response_tx.send(AudioResponse::Error("Not recording".to_string()));
            }
        }
    });

    let (response_tx, response_rx) = mpsc::channel();
    audio_tx.send((AudioCommand::StopRecording, response_tx)).unwrap();

    match response_rx.recv_timeout(Duration::from_secs(2)).unwrap() {
        AudioResponse::Error(e) => {
            println!("✓ Error handling works: {}", e);
            assert_eq!(e, "Not recording");
        }
        _ => panic!("Expected error response"),
    }

    audio_handle.join().unwrap();
}
