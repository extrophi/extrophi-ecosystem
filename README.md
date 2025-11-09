# Clear Voice App

**Privacy-first voice journaling for people under stress.**

---

## What This Is

A tool for people who need to externalize thoughts during difficult moments. No cloud. No subscriptions. No data collection. Just your voice, your words, your control.

**Built for:**
- People managing executive function challenges
- Those under stress with no one to talk to
- Anyone who needs to organize chaotic thoughts
- Privacy-conscious individuals

**Not built for:**
- Competition with existing products
- Maximum features or complexity
- Cloud-based convenience
- Monetization

---

## The Journey

This project started as an Electron experiment (IAC-30), pivoted through Python implementations, and landed on a C++ core with Rust UI. Each pivot taught us something. Each failure made the next attempt better.

**The breadcrumb trail matters as much as the destination.**

---

## Current State: Stage A

**Status:** ✅ Proven, working C++ Whisper core

**What works:**
- Voice recording via CLI
- Whisper C++ transcription (Metal GPU acceleration)
- 16kHz audio processing
- Markdown output

**Architecture:**
```
Audio Input → C++ Core → Whisper.cpp → Transcript
```

**Why C++:** 
- Direct Metal GPU access
- No Python subprocess complexity
- Small binary size
- Proven reliability

---

## Coming Next: Stage B

**Status:** 🚧 In development

**Adding:**
- Rust/Tauri desktop UI
- Visual feedback during recording
- Clean, minimal interface
- One-click operation

**Why Rust + Tauri:**
- Small bundle size (vs Electron bloat)
- Native performance
- Cross-platform foundation
- Privacy-first by design

---

## Philosophy

### Privacy First

100% local processing. Your voice never leaves your machine. No analytics, no telemetry, no "improving our services."

### User Control

You own your data. You control what gets processed. You decide what stays private.

### Simple By Design

One purpose: externalize thoughts quickly during difficult moments. Everything else is distraction.

### Open & Honest

Open source. Documented decisions. Clear reasoning. Breadcrumbs for others to follow.

---

## Technical Foundation (Stage A)

### Requirements

- macOS (Apple Silicon recommended)
- Homebrew
- Whisper C++ with Metal support
- PortAudio

### Installation

```bash
# Install dependencies
brew install whisper-cpp portaudio

# Clone repository
git clone https://github.com/Iamcodio/IAC-031-clear-voice-app.git
cd IAC-031-clear-voice-app

# Download Whisper model (141MB)
mkdir -p models
curl -L -o models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

### Usage (CLI)

```bash
# Record and transcribe
./braindump-cli run

# Test installation
./braindump-cli test
```

---

## Project Structure

```
├── README.md                    # You are here
├── DESIGN-PROPOSAL-V3.0-STAGE-A.md  # Detailed architecture
├── PRD-v3.0-STAGE-A.md         # Product requirements
├── CHANGELOG.md                # Version history
└── models/                     # Whisper models (not in git)
    └── ggml-base.bin          # Download separately
```

---

## Performance

| Metric | Value |
|--------|-------|
| Transcription Speed | <1s per 10s audio |
| Startup Time | <500ms |
| Memory Usage | <50MB |
| GPU Acceleration | Metal (M-series) |
| Cost | €0 forever |

---

## The Pivot Story

### Why Not Electron?

- Bundle size: 140MB (vs Tauri's 10MB)
- Complex setup: Python subprocesses, node modules
- Maintenance burden: Three languages, multiple runtimes

### Why Not Python-Only?

- Subprocess complexity
- Distribution challenges
- Performance overhead
- GUI framework limitations

### Why C++ + Rust?

- **C++ Core:** Direct Whisper integration, Metal GPU access
- **Rust UI:** Small binaries, memory safety, Tauri framework
- **Clean separation:** Core engine (C++) + Interface (Rust)
- **Proven path:** Stage A works, Stage B builds on solid foundation

---

## Mission

This tool exists because sometimes people need to get thoughts out of their head and onto paper (or screen). No judgment. No features. No bullshit.

**For people who:**
- Can't organize thoughts under stress
- Have no one safe to talk to
- Need privacy above everything else
- Don't trust cloud services with their voice

**Built by someone who:** Was homeless. Got help. Paying it forward.

---

## Non-Goals

❌ Competing with existing products  
❌ Venture funding or growth metrics  
❌ Feature bloat or complexity  
❌ Cloud sync or team features  
❌ Recognition or credit  

**Just:** A working tool for people who need it.

---

## Development Principles

**Document as you build:** Future maintainers (including yourself) need context, not just code.

**Test each stage:** Stage A proven before Stage B starts. No building on shaky foundations.

**Embrace pivots:** Wrong paths teach more than right ones. Document both.

**Privacy is non-negotiable:** If it requires cloud, it doesn't ship.

---

## Credits

**Built by:** Codio  
**AI Pair Programmer:** Claude Sonnet 4.5 (Anthropic)  
**Location:** Tipperary, Ireland  
**Motivation:** Debt of gratitude to people who help others in crisis  

---

## License

MIT License - Use freely, modify freely, share freely.

No restrictions. No attribution required. Just build good things.

---

## Support

Questions? Open an issue.  
Want to contribute? PRs welcome.  
Need help? Reach out.

**We're all struggling with something. Tools should help, not hinder.**

---

## Next Steps

1. ✅ Stage A: C++ core complete
2. 🚧 Stage B: Rust UI in progress
3. 📋 Stage C: Privacy-aware editing (planned)

Follow the breadcrumbs. The journey continues.

---

*"The best products solve your own problems. The best documentation teaches while you build."*

Built with care. Shipped with purpose. Documented for the future.
