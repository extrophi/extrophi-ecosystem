//! Memory-safe audio recorder using cpal

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Stream, StreamConfig};
use std::sync::{Arc, Mutex};

#[derive(Debug, thiserror::Error)]
pub enum RecorderError {
    #[error("Audio device error: {0}")]
    DeviceError(String),
    
    #[error("Stream error: {0}")]
    StreamError(String),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Recorder not started")]
    NotStarted,
}

pub type RecorderResult<T> = Result<T, RecorderError>;

/// Recorder state shared across threads
struct RecorderState {
    is_recording: bool,
    samples: Vec<f32>,
    peak_level: f32, // For real-time visualization
}

/// Audio recorder
pub struct Recorder {
    device: Device,
    config: StreamConfig,
    stream: Option<Stream>,
    state: Arc<Mutex<RecorderState>>,
}

impl Recorder {
    /// Create new recorder (device native sample rate, mono)
    pub fn new() -> RecorderResult<Self> {
        let host = cpal::default_host();

        let device = host.default_input_device()
            .ok_or_else(|| RecorderError::DeviceError("No input device found".to_string()))?;

        // Get the device's default config
        let default_config = device.default_input_config()
            .map_err(|e| RecorderError::DeviceError(format!("Failed to get default config: {}", e)))?;

        // Use device's native sample rate (typically 48kHz on Mac)
        // We'll resample to 16kHz when saving
        let sample_rate = default_config.sample_rate();
        let buffer_size = match default_config.buffer_size() {
            cpal::SupportedBufferSize::Range { min, max: _ } => cpal::BufferSize::Fixed(*min.max(&512)),
            cpal::SupportedBufferSize::Unknown => cpal::BufferSize::Default,
        };

        let config = StreamConfig {
            channels: 1, // Force mono for Whisper.cpp
            sample_rate,
            buffer_size,
        };

        let state = Arc::new(Mutex::new(RecorderState {
            is_recording: false,
            samples: Vec::new(),
            peak_level: 0.0,
        }));

        Ok(Self {
            device,
            config,
            stream: None,
            state,
        })
    }
    
    /// Start recording
    pub fn start(&mut self) -> RecorderResult<()> {
        if self.is_recording() {
            return Ok(()); // Already recording
        }
        
        // Clear previous samples
        {
            let mut state = match self.state.lock() {
                Ok(guard) => guard,
                Err(poisoned) => {
                    eprintln!("Recorder mutex poisoned during start, recovering");
                    poisoned.into_inner()
                }
            };
            state.samples.clear();
            state.is_recording = true;
            state.peak_level = 0.0;
        }
        
        // Create audio stream
        let state_clone = Arc::clone(&self.state);
        
        let stream = self.device.build_input_stream(
            &self.config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                let mut state = match state_clone.lock() {
                    Ok(guard) => guard,
                    Err(poisoned) => {
                        eprintln!("Audio callback mutex poisoned, recovering");
                        poisoned.into_inner()
                    }
                };

                if state.is_recording {
                    // Append samples
                    state.samples.extend_from_slice(data);

                    // Update peak level for visualization
                    let peak = data.iter().map(|s| s.abs()).fold(0.0, f32::max);
                    state.peak_level = state.peak_level.max(peak);
                }
            },
            |err| eprintln!("Audio stream error: {}", err),
            None,
        ).map_err(|e| RecorderError::StreamError(e.to_string()))?;
        
        stream.play().map_err(|e| RecorderError::StreamError(e.to_string()))?;
        
        self.stream = Some(stream);
        Ok(())
    }
    
    /// Stop recording and return samples
    pub fn stop(&mut self) -> RecorderResult<Vec<f32>> {
        if !self.is_recording() {
            return Err(RecorderError::NotStarted);
        }
        
        // Stop stream
        if let Some(stream) = self.stream.take() {
            drop(stream); // Stops automatically on drop
        }
        
        // Extract samples
        let mut state = match self.state.lock() {
            Ok(guard) => guard,
            Err(poisoned) => {
                eprintln!("Recorder mutex poisoned during stop, recovering");
                poisoned.into_inner()
            }
        };
        state.is_recording = false;

        Ok(std::mem::take(&mut state.samples))
    }
    
    /// Check if currently recording
    pub fn is_recording(&self) -> bool {
        self.state.lock().map(|s| s.is_recording).unwrap_or(false)
    }
    
    /// Get current peak level (for waveform visualization)
    pub fn get_peak_level(&self) -> f32 {
        self.state.lock().map(|s| s.peak_level).unwrap_or(0.0)
    }
    
    /// Get sample rate
    pub fn sample_rate(&self) -> u32 {
        self.config.sample_rate.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_recorder_create() {
        let recorder = Recorder::new();
        assert!(recorder.is_ok());
    }
    
    #[test]
    fn test_start_stop() {
        let mut recorder = Recorder::new().expect("Test: failed to create recorder");

        assert!(!recorder.is_recording());

        recorder.start().expect("Test: failed to start recording");
        assert!(recorder.is_recording());

        std::thread::sleep(std::time::Duration::from_millis(100));

        let samples = recorder.stop().expect("Test: failed to stop recording");
        assert!(!recorder.is_recording());
        assert!(!samples.is_empty());
    }
}
