# Mobile Voice Transcription Performance Optimization Research

**Research Date**: November 2025
**Author**: Agent Phi
**Project**: BrainDump Mobile Strategy

---

## Executive Summary

This report analyzes mobile voice transcription performance optimization strategies, focusing on whisper.cpp deployment on iOS and Android platforms. Key findings indicate that mobile deployment is feasible with careful model selection, thermal management, and platform-specific optimizations. The tiny/base models with INT8 quantization offer the best tradeoffs for mobile, while Tauri 2.0's mobile support provides a viable path forward with some performance considerations.

---

## 1. Whisper.cpp on Mobile Platforms

### 1.1 iOS Performance

**Hardware Acceleration**:
- Apple Silicon optimized via ARM NEON, Accelerate framework, Metal GPU, and Core ML
- Neural Engine (ANE) provides 3x+ speedup compared to CPU-only execution
- iPhone 13 ANE: 3.47 ms latency at 0.454 W (highly efficient)
- Peak throughput: 15.8 TFLOPS (A15) to 38 TOPS (M4)

**Real-World Benchmarks** (iPhone 13 Mini):
- Base model: ~1 second for 30-second audio chunk (encoder only)
- Small model: ~3 seconds for 30-second audio chunk
- Metal GPU inference runs fully on-device

**CoreML Integration**:
```bash
# Build with CoreML support
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```

**Deployment Notes**:
- First-run compiles CoreML model to ANE format (~15 minutes on M1)
- Subsequent runs significantly faster
- XCFramework simplifies iOS/macOS integration
- macOS Sonoma 14+ recommended to avoid hallucination issues

### 1.2 Android Performance

**Recommended Audio APIs** (2025):
- **Oboe** or **AAudio** (OpenSL ES deprecated from Android 11)
- AAudio provides lowest latency with `AAUDIO_INPUT_PRESET_VOICE_RECOGNITION`
- Buffer optimization critical: Use burst size multiples

**NDK Integration**:
- Qualcomm Hexagon DSP and ARM NEON intrinsics available
- TensorFlow Lite and ONNX Runtime for hardware acceleration
- JNI boundary calls can account for 60%+ of performance bottlenecks
- Target `-Wl,--gc-sections` for minimal binary size

**Optimization Targets**:
- Reduce native code by 200KB = ~18% faster initial load (mid-tier devices)
- Minimize JNI boundary crossings
- Use appropriate Proguard rules

### 1.3 Model Size vs Performance Tradeoffs

| Model | Parameters | Disk Size | Memory | English WER | Inference Speed | Mobile Recommendation |
|-------|------------|-----------|--------|-------------|-----------------|----------------------|
| **tiny** | 39M | 75 MB | ~150 MB | ~8% | ~2000 FPS | **Best for resource-constrained** |
| **tiny.en** | 39M | 75 MB | ~150 MB | ~6% | ~2000 FPS | **Optimal for English-only** |
| **base** | 74M | 142 MB | ~250 MB | ~5% | ~1500 FPS | **Balanced choice** |
| **base.en** | 74M | 142 MB | ~250 MB | ~4% | ~1500 FPS | **Recommended for English** |
| **small** | 244M | 466 MB | ~500 MB | ~3.5% | ~1000 FPS | High memory, good accuracy |
| **small.en** | 244M | 466 MB | ~500 MB | ~3% | ~1000 FPS | Professional apps only |
| **distil-small.en** | 166M | 332 MB | ~350 MB | ~4% WER of large-v3 | 6x faster | **Excellent for mobile** |

**Key Recommendations**:
- **Devices < 4GB RAM**: tiny or tiny.en only with graceful degradation
- **Standard mobile**: base.en offers best accuracy/resource balance
- **Professional apps**: small.en with 500MB+ memory budget
- **Quantized models** (q5_1): 26 MB with good accuracy/size tradeoff

### 1.4 Quantization Benefits

| Quantization | Size Reduction | Speed Improvement | Accuracy Impact |
|--------------|----------------|-------------------|-----------------|
| **INT8 (dynamic)** | 57% smaller | 20-30% faster | < 1% WER increase |
| **INT4** | ~75% smaller | Variable | 2-5% WER increase |
| **FP16** | 50% smaller | Metal GPU optimal | Negligible |

**Best Practice**: INT8 quantization is the "safe minimum" for production, providing the optimal balance of size, speed, and accuracy.

---

## 2. Performance Patterns and Optimization Strategies

### 2.1 Chunked Transcription Architecture

**Challenge**: Whisper processes audio in 30-second segments, not ideal for real-time mobile use.

**Chunking Strategy**:
```
Audio Stream → VAD Detection → Smart Chunking → Transcription Queue → Result Merging
```

**Implementation Approaches**:

1. **Fixed Chunking** (Simple):
   - 5-10 second chunks
   - Average latency: 0.5 seconds for 5-second chunks
   - Risk: Word boundary splits cause errors

2. **VAD-Based Chunking** (Recommended):
   - Silero VAD for speech probability detection
   - Split on natural pauses
   - Better accuracy, slightly higher complexity

3. **Whisper-Streaming** (Advanced):
   - Local agreement policy with self-adaptive latency
   - MinChunkSize parameter controls quality/latency tradeoff
   - 3.3s average latency for English with 1s MinChunkSize

**Mobile Optimization**:
```swift
// iOS: Process chunks with VAD
let chunkSize: TimeInterval = 5.0 // seconds
let audioChunk = captureBuffer(duration: chunkSize)
if vadDetectsSpeech(audioChunk) {
    queueForTranscription(audioChunk)
}
```

### 2.2 Background Processing

**iOS Constraints**:
- Background tasks killed aggressively after few minutes
- BGTaskScheduler has strict time limits
- Audio session must be configured with proper category

**Recommended Architecture**:
```swift
// iOS: Separate engines for recording vs processing
class AudioManager {
    let recordingEngine: AVAudioEngine // 4096-byte buffer for offline
    let playbackEngine: AVAudioEngine  // 1024-byte buffer for real-time
}
```

**Android Advantages**:
- WorkManager for deferred processing
- Foreground Service for extended background work
- More flexible than iOS constraints

### 2.3 Power Management

**Battery Conservation Strategies**:

1. **Adaptive Model Selection**:
   ```swift
   switch batteryLevel {
   case ..<20: use(.tiny)      // Minimal processing
   case 20..<50: use(.base)    // Balanced
   default: use(.small)        // Full quality
   }
   ```

2. **Processing Throttling**:
   - Queue transcriptions during charging
   - Batch process when on WiFi
   - Defer non-urgent transcriptions

3. **Neural Engine Utilization** (iOS):
   - ANE uses 10x less energy than CPU
   - 49 mW for light tasks vs 2W for heavy inference
   - Always prefer CoreML → ANE path

### 2.4 Memory Constraints

**Peak Memory Usage**:
- tiny model: ~150 MB runtime
- base model: ~250 MB runtime (recommended max for older devices)
- small model: ~500 MB runtime (OOM risk on extended use)

**Memory Optimization**:
- Unload model between transcriptions if memory pressure detected
- Use memory-mapped model files where possible
- Monitor `os_proc_available_memory()` on iOS

---

## 3. Thermal Management

### 3.1 iOS Thermal State Monitoring

```swift
import Foundation

class ThermalManager {
    static let shared = ThermalManager()

    init() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(thermalStateChanged),
            name: ProcessInfo.thermalStateDidChangeNotification,
            object: nil
        )
    }

    @objc func thermalStateChanged() {
        switch ProcessInfo.processInfo.thermalState {
        case .nominal:
            enableFullTranscription()
        case .fair:
            reduceBackgroundWork()
        case .serious:
            downgradeModelSize()  // base → tiny
        case .critical:
            pauseTranscription()
            notifyUser()
        @unknown default:
            break
        }
    }
}
```

**Thermal States**:
- **nominal**: Full processing capability
- **fair**: Delay non-essential work
- **serious**: Scale back CPU/GPU/IO workload
- **critical**: System unable to keep up, UI stuttering likely

### 3.2 Android Thermal API

```kotlin
// Android 10+ Thermal API
class ThermalMonitor(context: Context) {
    private val powerManager = context.getSystemService(PowerManager::class.java)

    init {
        powerManager.addThermalStatusListener { status ->
            when (status) {
                PowerManager.THERMAL_STATUS_NONE -> enableFullProcessing()
                PowerManager.THERMAL_STATUS_LIGHT -> monitorClosely()
                PowerManager.THERMAL_STATUS_MODERATE -> reduceWorkload()
                PowerManager.THERMAL_STATUS_SEVERE -> minimizeProcessing()
                PowerManager.THERMAL_STATUS_CRITICAL -> pauseAll()
                PowerManager.THERMAL_STATUS_EMERGENCY -> emergencyShutdown()
            }
        }
    }

    // Thermal Headroom API - predict future throttling
    fun predictThrottling(): Float {
        return powerManager.getThermalHeadroom(10) // 10 seconds ahead
        // Returns 0.0f (no throttling) to 1.0f (severe throttling)
    }
}
```

### 3.3 Preventing Thermal Throttling

**Research Findings**:
- BERT models cause 80°C CPU temp in <32 seconds
- Thermal throttling triggered in ~6 minutes of continuous inference
- CPU frequency drops 217% after ~150 seconds of sustained ML workload

**Mitigation Strategies**:

1. **Dynamic Model Shifting**:
   ```
   Monitor thermal → High temp detected → Shift to smaller model → Continue processing
   ```
   - Dynamically switch between large/small models based on thermal profile
   - Maintains performance while preventing throttling

2. **Workload Batching**:
   - Process in bursts with cooling periods
   - Example: 30s processing, 60s rest
   - Prevents sustained high temperature

3. **Adaptive Quality**:
   ```swift
   if thermalHeadroom < 0.3 {
       reduceTranscriptionQuality()
       increaseChunkInterval()
       disablePostProcessing()
   }
   ```

4. **User Feedback**:
   - Display temperature indicator
   - Warn before thermal throttling occurs
   - Suggest waiting for device to cool

---

## 4. Tauri 2.0 Mobile Support

### 4.1 Current Capabilities

**Platform Support** (Tauri 2.0 Stable):
- iOS and Android from single codebase
- Native language bindings (Swift/Kotlin)
- Core mobile features: notifications, dialogs, NFC, biometrics, clipboard

**Plugin Architecture**:
```swift
// iOS Plugin (Swift)
class WhisperPlugin: Plugin {
    @Command
    func transcribe(audioPath: String) -> TranscriptionResult {
        // Native Swift implementation
        // Direct access to CoreML/ANE
    }
}
```

```kotlin
// Android Plugin (Kotlin)
@TauriPlugin
class WhisperPlugin : Plugin() {
    @Command
    fun transcribe(audioPath: String): TranscriptionResult {
        // Native Kotlin implementation
        // Access to NDK optimizations
    }
}
```

### 4.2 Performance Limitations

**Critical Issues**:

1. **Main Thread Blocking** (Android):
   - Native commands scheduled on main thread by default
   - Long-running operations cause ANR errors
   - Must explicitly move to background thread

2. **FFI Overhead**:
   - Swift → Rust via swift-rs
   - Java/Kotlin → Rust via JNI (jni-rs)
   - JNI boundary calls can be significant bottleneck

3. **Developer Experience**:
   - Mobile DX still maturing
   - Not all official plugins support mobile
   - Tooling not yet on par with desktop

### 4.3 Recommended Architecture for BrainDump Mobile

```
┌─────────────────────────────────────────┐
│           Tauri Mobile App              │
├─────────────────────────────────────────┤
│  Svelte 5 UI (Shared with Desktop)     │
├─────────────────────────────────────────┤
│  Rust Core (Shared Logic)              │
│  ├─ Session management                  │
│  ├─ Database operations                 │
│  └─ Privacy scanning                    │
├─────────────────────────────────────────┤
│  Native Plugins                         │
│  ├─ iOS: Swift + CoreML/ANE            │
│  │   └─ whisper.cpp Metal acceleration  │
│  └─ Android: Kotlin + NDK              │
│      └─ whisper.cpp NEON optimization   │
└─────────────────────────────────────────┘
```

**Key Benefits**:
- Shared UI codebase (70%+ code reuse)
- Native performance for ML inference
- Platform-specific optimizations where needed
- Rust safety for core logic

### 4.4 Deployment Considerations

**iOS**:
- XCFramework for whisper.cpp distribution
- CoreML model conversion (20-minute build step)
- App Store binary size limits (150MB without on-demand resources)
- Model downloaded on first launch recommended

**Android**:
- NDK integration for whisper.cpp
- APK size optimization via App Bundles
- Play Store requires 64-bit support
- Consider model streaming for large models

---

## 5. Open Source Mobile ML Frameworks

### 5.1 Framework Comparison (2025)

| Framework | Best For | Model Support | Performance | Mobile Focus |
|-----------|----------|---------------|-------------|--------------|
| **TensorFlow Lite** | Android native | TensorFlow models | Excellent | High |
| **CoreML** | iOS exclusive | Multi-framework | Best on iOS | High |
| **ONNX Runtime Mobile** | Cross-platform | Universal ONNX | Very Good | Medium |
| **PyTorch Mobile** | Research/Prototyping | PyTorch models | Good | Medium |
| **whisper.cpp** | Whisper specifically | Whisper only | Optimal | High |

### 5.2 TensorFlow Lite

**Advantages**:
- First-class Android support
- GPU delegate for Metal (iOS) and OpenGL/Vulkan (Android)
- Extensive quantization tools
- Model Maker for speech recognition

**Whisper Alternative**:
- Train custom speech model with TF Lite Model Maker
- 70-140 MB model size typical
- Good for keyword/command recognition
- Less accurate than Whisper for general transcription

### 5.3 CoreML (iOS)

**Optimization Features**:
- Automatic CPU/GPU/ANE dispatch
- Model compression and quantization built-in
- Low memory footprint
- Best battery efficiency on iOS

**Whisper Integration**:
```bash
# Convert Whisper to CoreML
python convert-whisper-to-coreml.py --model base.en --output ./models/
```

### 5.4 ONNX Runtime Mobile

**Cross-Platform Benefits**:
- Train in PyTorch/TensorFlow, deploy to ONNX
- Execution providers for different hardware
- Consistent API across platforms
- 60 MB INT8 Whisper checkpoint achievable

**Performance**:
- RTF = 0.20 on MacBook Pro M1 (5x real-time)
- 43% lower latency than FP16 baseline
- Good for on-device deployment

### 5.5 Model Quantization Deep Dive

**Quantization Types**:

1. **Post-Training Quantization (PTQ)**:
   - Quick, no retraining needed
   - 20-30% speedup typical
   - Best for deployment

2. **Quantization-Aware Training (QAT)**:
   - Better accuracy preservation
   - Requires training pipeline
   - Worth it for production

3. **Dynamic Quantization**:
   - 57% size reduction for Whisper
   - Best accuracy/size tradeoff
   - Recommended for whisper.cpp

**Whisper-Specific Recommendations**:
- Per-channel quantization for accuracy (Quanto INT8)
- Dynamic quantization for flexibility
- Avoid <8-bit unless acoustic variability is low

---

## 6. Implementation Recommendations

### 6.1 Phase 1: MVP Mobile (3-4 months)

**Target**: iOS + Android with basic transcription

**Model Selection**:
- Primary: base.en (142 MB, ~4% WER)
- Fallback: tiny.en (75 MB, ~6% WER)
- Consider: distil-small.en (166M params, excellent balance)

**Architecture**:
```
Recording → Local Processing → Sync to Cloud (optional)
```

**Key Features**:
- Offline transcription with base.en
- Thermal monitoring with automatic downgrade
- Battery-aware processing queues
- Simple chunking (5-10 second fixed)

**Tauri Mobile Strategy**:
- Shared UI with desktop app
- Native plugins for whisper.cpp integration
- Platform-specific thermal/battery APIs
- Model bundled separately (on-demand download)

### 6.2 Phase 2: Optimized Experience (2-3 months)

**Enhancements**:
- VAD-based smart chunking
- Adaptive model selection based on context
- Background processing with proper lifecycle management
- Streaming results UI

**Technical Improvements**:
- CoreML/ANE optimization for iOS
- NDK NEON intrinsics for Android
- INT8 quantized models
- Memory-mapped model loading

### 6.3 Phase 3: Advanced Features (3-4 months)

**Premium Features**:
- Real-time streaming transcription
- Multi-language support
- Speaker diarization
- Noise reduction preprocessing

**Performance Targets**:
- < 3 second latency for 10-second audio
- < 5% WER for clean speech
- 4+ hours continuous recording on single charge
- No thermal throttling under normal use

### 6.4 Model Distribution Strategy

**Approach A: Bundled (Recommended for MVP)**
- Include base.en model in app bundle
- Pros: Immediate offline use
- Cons: 150+ MB download

**Approach B: On-Demand Download**
- Download model on first use
- Pros: Smaller initial install
- Cons: First-run UX friction

**Approach C: Tiered Models**
- tiny.en bundled (75 MB)
- base.en on-demand (142 MB)
- small.en premium (466 MB)
- Pros: User choice
- Cons: Complexity

### 6.5 Battery Optimization Checklist

- [ ] Use Neural Engine (iOS) / NPU (Android) when available
- [ ] Implement thermal state monitoring
- [ ] Batch non-urgent transcriptions
- [ ] Disable processing below 20% battery
- [ ] Use efficient audio codecs (Opus)
- [ ] Minimize background wake-ups
- [ ] Profile with Instruments/Android Profiler
- [ ] Target < 10% battery per hour of active use

### 6.6 Testing Strategy

**Device Matrix**:
- iOS: iPhone 11+ (A13 Bionic minimum for ANE)
- Android: Snapdragon 855+ / Dimensity 1000+ equivalent
- Minimum RAM: 4GB
- Storage: 500MB+ free

**Performance Benchmarks**:
- Transcription RTF (Real-Time Factor) < 0.5
- Memory peak < 300MB
- Battery consumption < 15% per hour
- Thermal headroom maintained > 0.3

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Model too large for bundle | High | On-demand download, model compression |
| Thermal throttling on prolonged use | High | Dynamic model switching, cooling periods |
| Battery drain complaints | High | Aggressive power management, user controls |
| Transcription accuracy issues | Medium | Model fine-tuning, noise reduction |
| Tauri mobile limitations | Medium | Native plugin development, fallback approaches |
| iOS background restrictions | Medium | Foreground service notifications, user education |
| Android fragmentation | Medium | Extensive device testing, graceful degradation |

---

## 8. Conclusions

### Key Takeaways

1. **Mobile whisper.cpp is production-ready** with careful model selection and optimization
2. **base.en model** offers the best balance for mobile: 142MB, ~4% WER, <250MB RAM
3. **INT8 quantization** provides 57% size reduction with minimal accuracy loss
4. **Thermal management is critical** - continuous inference triggers throttling in ~6 minutes
5. **Tauri 2.0 mobile support is viable** but requires native plugin development for optimal performance
6. **CoreML/ANE on iOS** provides 3x speedup with 10x better power efficiency
7. **Chunked processing with VAD** enables real-time-like experience on mobile

### Final Recommendation

Proceed with Tauri 2.0 mobile development using:
- **Model**: base.en with INT8 quantization (or distil-small.en if available)
- **Architecture**: Native Swift/Kotlin plugins for ML, shared Svelte UI
- **Optimization**: CoreML/ANE (iOS), NDK/NEON (Android), thermal monitoring
- **Strategy**: On-demand model download with tiny.en fallback
- **Timeline**: 8-11 months for full-featured mobile release (3 phases)

The mobile market opportunity is significant, and the technical foundation is solid. Success depends on rigorous thermal/battery management and thoughtful UX for processing delays.

---

## References

1. whisper.cpp GitHub Repository - ggml-org/whisper.cpp
2. Tauri 2.0 Documentation - v2.tauri.app
3. Apple Neural Engine Research - machinelearning.apple.com
4. Android Thermal API - developer.android.com
5. Distil-Whisper - huggingface/distil-whisper
6. "Quantizing Whisper-small" - arxiv.org/abs/2511.08093
7. "Play It Cool: Dynamic Shifting Prevents Thermal Throttling" - arxiv.org/abs/2206.10849
8. iOS ProcessInfo Documentation - developer.apple.com
9. ONNX Runtime Mobile - opensource.microsoft.com
10. Mobile AI Frameworks 2025 - booleaninc.com

---

*Report generated by Agent Phi for BrainDump v3.0 mobile strategy planning*
