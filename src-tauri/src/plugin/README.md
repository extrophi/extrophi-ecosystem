# BrainDump Plugin System

**Module 5: Plugin System Core** - Trait-based architecture for swappable transcription engines

## Overview

The BrainDump plugin system provides a modular, type-safe interface for implementing transcription engines. This architecture enables:

- **Swappable Engines**: Switch between C++ FFI (fast) and Rust Candle (safe) implementations
- **Future-Proofing**: Easy to add new engines (Anthropic, Groq, etc.) without changing core code
- **Type Safety**: Strong Rust type system prevents runtime errors
- **Thread Safety**: All plugins are `Send + Sync` for multi-threaded use

## Architecture

```
┌─────────────────────────────────────┐
│       TranscriptionPlugin           │
│           (Trait)                   │
│  - transcribe(audio) -> Transcript  │
│  - initialize() / shutdown()        │
└─────────────────────────────────────┘
           ▲                ▲
           │                │
    ┌──────┴───┐      ┌────┴──────┐
    │  C++ FFI │      │  Candle   │
    │  Plugin  │      │  Plugin   │
    │ (Module 6)      │ (Module 7)│
    └──────────┘      └───────────┘
```

## Core Types

### AudioData

Input to all transcription plugins:

```rust
pub struct AudioData {
    pub samples: Vec<f32>,      // Raw PCM samples (-1.0 to 1.0)
    pub sample_rate: u32,       // Hz (typically 16000)
    pub channels: u16,          // 1 = mono, 2 = stereo
}
```

### Transcript

Output from transcription:

```rust
pub struct Transcript {
    pub text: String,                       // Full transcribed text
    pub language: Option<String>,           // ISO 639-1 code (e.g., "en")
    pub segments: Vec<TranscriptSegment>,   // Timestamped segments
}

pub struct TranscriptSegment {
    pub start_ms: u64,      // Start time in milliseconds
    pub end_ms: u64,        // End time in milliseconds
    pub text: String,       // Segment text
    pub confidence: f32,    // Confidence score (0.0 - 1.0)
}
```

### PluginError

All plugin operations return `Result<T, PluginError>`:

```rust
pub enum PluginError {
    NotFound(String),               // Plugin not registered
    NotInitialized(String),         // Called before initialize()
    TranscriptionFailed(String),    // Transcription error
    InitializationFailed(String),   // Setup error
    Io(std::io::Error),             // File I/O error
    // ... other variants
}
```

## Implementing a Plugin

### 1. Implement the TranscriptionPlugin trait

```rust
use braindump::plugin::{TranscriptionPlugin, PluginError, AudioData, Transcript};

pub struct MyCustomPlugin {
    model: Option<MyModel>,
    initialized: bool,
}

impl TranscriptionPlugin for MyCustomPlugin {
    fn name(&self) -> &str {
        "my-custom-engine"
    }

    fn version(&self) -> &str {
        "1.0.0"
    }

    fn initialize(&mut self) -> Result<(), PluginError> {
        // Load models, allocate resources
        self.model = Some(MyModel::load()?);
        self.initialized = true;
        Ok(())
    }

    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError> {
        if !self.initialized {
            return Err(PluginError::NotInitialized(self.name().to_string()));
        }

        // Convert audio to model-specific format
        let processed_audio = preprocess_audio(audio);

        // Run inference
        let result = self.model
            .as_ref()
            .unwrap()
            .transcribe(&processed_audio)?;

        // Convert to Transcript
        Ok(Transcript {
            text: result.text,
            language: Some("en".to_string()),
            segments: result.segments.into_iter().map(|s| {
                TranscriptSegment {
                    start_ms: s.start,
                    end_ms: s.end,
                    text: s.text,
                    confidence: s.confidence,
                }
            }).collect(),
        })
    }

    fn shutdown(&mut self) -> Result<(), PluginError> {
        self.model = None;
        self.initialized = false;
        Ok(())
    }

    fn is_initialized(&self) -> bool {
        self.initialized
    }
}
```

### 2. Register with PluginManager

```rust
use braindump::plugin::PluginManager;

let mut manager = PluginManager::new();

// Register your plugin
manager.register(Box::new(MyCustomPlugin::new()))?;

// Or register multiple plugins
manager.register(Box::new(WhisperCppPlugin::new(model_path)))?;
manager.register(Box::new(CandlePlugin::new(model_path)))?;
```

### 3. Use the Plugin

```rust
// Transcribe with active plugin
let audio = AudioData {
    samples: vec![0.0; 16000],  // 1 second of silence
    sample_rate: 16000,
    channels: 1,
};

let transcript = manager.transcribe(&audio)?;
println!("Transcribed: {}", transcript.text);

// Switch plugins
manager.switch_plugin("my-custom-engine")?;
let transcript2 = manager.transcribe(&audio)?;

// List all plugins
for plugin in manager.list_plugins() {
    println!("{} v{} ({})",
        plugin.name,
        plugin.version,
        if plugin.is_active { "active" } else { "inactive" }
    );
}
```

## Helper Functions

The `types` module provides utility functions:

### Audio Processing

```rust
use braindump::plugin::types::{stereo_to_mono, resample_audio, normalize_audio};

// Convert stereo to mono
let mono = stereo_to_mono(&stereo_samples);

// Resample audio
let resampled = resample_audio(&samples, 44100, 16000);

// Normalize to [-1.0, 1.0]
let normalized = normalize_audio(&samples);
```

### Duration Calculation

```rust
use braindump::plugin::types::calculate_duration_ms;

let duration = calculate_duration_ms(
    samples.len(),
    sample_rate,
    channels
);
println!("Audio duration: {}ms", duration);
```

## Testing Your Plugin

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_plugin_lifecycle() {
        let mut plugin = MyCustomPlugin::new();

        assert!(!plugin.is_initialized());

        plugin.initialize().unwrap();
        assert!(plugin.is_initialized());

        plugin.shutdown().unwrap();
        assert!(!plugin.is_initialized());
    }

    #[test]
    fn test_transcribe() {
        let mut plugin = MyCustomPlugin::new();
        plugin.initialize().unwrap();

        let audio = AudioData {
            samples: vec![0.0; 16000],
            sample_rate: 16000,
            channels: 1,
        };

        let transcript = plugin.transcribe(&audio).unwrap();
        assert!(!transcript.text.is_empty());
    }

    #[test]
    fn test_transcribe_not_initialized() {
        let plugin = MyCustomPlugin::new();

        let audio = AudioData {
            samples: vec![0.0; 16000],
            sample_rate: 16000,
            channels: 1,
        };

        let result = plugin.transcribe(&audio);
        assert!(matches!(result, Err(PluginError::NotInitialized(_))));
    }
}
```

### Integration with PluginManager

```rust
#[test]
fn test_plugin_manager_integration() {
    let mut manager = PluginManager::new();

    manager.register(Box::new(MyCustomPlugin::new())).unwrap();
    assert_eq!(manager.plugin_count(), 1);

    // Initialize plugin
    let plugin = manager.get_active().unwrap();
    plugin.lock().unwrap().initialize().unwrap();

    // Transcribe
    let audio = AudioData {
        samples: vec![0.0; 16000],
        sample_rate: 16000,
        channels: 1,
    };

    let transcript = manager.transcribe(&audio).unwrap();
    assert!(!transcript.text.is_empty());
}
```

## Performance Considerations

### Target Performance

- **C++ FFI Plugin**: <2s per 1min audio
- **Rust Candle Plugin**: <4s per 1min audio
- **Custom Plugins**: Aim for <5s per 1min audio

### Optimization Tips

1. **Lazy Initialization**: Load models only when needed
2. **GPU Acceleration**: Use Metal/CUDA where available
3. **Batch Processing**: Process multiple segments together
4. **Caching**: Cache frequently used models
5. **Memory Pools**: Reuse audio buffers

### Example: GPU-Accelerated Plugin

```rust
impl TranscriptionPlugin for MyGpuPlugin {
    fn initialize(&mut self) -> Result<(), PluginError> {
        // Try GPU first, fall back to CPU
        let device = Device::new_metal(0)
            .or_else(|_| Device::new_cuda(0))
            .unwrap_or(Device::Cpu);

        self.model = Some(Model::load(device)?);
        self.initialized = true;
        Ok(())
    }

    fn transcribe(&self, audio: &AudioData) -> Result<Transcript, PluginError> {
        // Use GPU tensor operations
        let tensor = Tensor::from_slice(
            &audio.samples,
            &self.model.device
        )?;

        let result = self.model.transcribe(&tensor)?;
        Ok(result.into())
    }
}
```

## Thread Safety

All plugins must be `Send + Sync`:

```rust
pub trait TranscriptionPlugin: Send + Sync {
    // ...
}
```

This enables:

- Multi-threaded transcription
- Background processing
- Parallel plugin benchmarking

Example:

```rust
use std::sync::Arc;
use std::thread;

let manager = Arc::new(manager);
let mut handles = vec![];

for i in 0..10 {
    let manager_clone = Arc::clone(&manager);
    let handle = thread::spawn(move || {
        let audio = load_audio(i);
        manager_clone.transcribe(&audio)
    });
    handles.push(handle);
}

for handle in handles {
    let transcript = handle.join().unwrap().unwrap();
    println!("{}", transcript.text);
}
```

## Examples

### Module 6: C++ FFI Plugin

See `src-tauri/src/plugins/whisper_cpp/` for a complete example of:
- FFI bindings to C++ code
- Safe wrapper around unsafe FFI calls
- Memory management across FFI boundary

### Module 7: Candle Plugin

See `src-tauri/src/plugins/candle/` for a complete example of:
- Pure Rust ML implementation
- GPU acceleration with Metal
- Model loading from Hugging Face Hub

## Best Practices

1. **Error Handling**: Always return descriptive errors
2. **Resource Cleanup**: Implement `shutdown()` properly
3. **Initialization Check**: Validate state before transcription
4. **Documentation**: Document thread safety guarantees
5. **Testing**: Aim for 90%+ test coverage

## API Reference

Full documentation: [docs.rs/braindump](https://docs.rs/braindump)

- `TranscriptionPlugin` trait
- `PluginManager` struct
- `AudioData`, `Transcript`, `TranscriptSegment` types
- `PluginError` enum
- Helper functions in `types` module

## Contributing

When adding a new plugin:

1. Implement `TranscriptionPlugin` trait
2. Add comprehensive tests (see above)
3. Document performance characteristics
4. Update this README with examples
5. Submit PR to Stage B branch

## License

MIT License - See LICENSE file

## Support

- Issues: https://github.com/iamcodio/braindump/issues
- Discussions: https://github.com/iamcodio/braindump/discussions
- Email: support@extrophi.com
