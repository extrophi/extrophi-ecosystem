# Platform Support - BrainDump v3.1

**Last Updated**: 2025-11-16

---

## Current Status

### macOS - PRIMARY TARGET
- **Status**: ✅ Active Development
- **CI**: Running
- **Build**: Supported
- **Testing**: Full coverage

### Linux (Ubuntu) - DEFERRED
- **Status**: ❌ Not Currently Supported
- **CI**: Removed from matrix
- **Reason**: Focus on macOS MVP first
- **Future**: Re-enable after macOS is stable

### Windows - DEFERRED
- **Status**: ❌ Not Currently Supported
- **Reason**: Focus on macOS MVP first
- **Future**: Consider after Linux support

---

## Why macOS Only?

1. **Faster CI**: Ubuntu jobs were slow and failing
2. **Core dependency**: whisper.cpp + Metal GPU acceleration
3. **MVP Focus**: Get one platform rock solid before expanding
4. **Developer environment**: Primary dev is on macOS
5. **Resource constraints**: Limited time/credits to burn

---

## Re-enabling Linux Support (Future)

When ready to add Linux back:

1. **CI Matrix** (`.github/workflows/ci.yml`):
```yaml
matrix:
  os: [macos-latest, ubuntu-latest]  # Re-add ubuntu
```

2. **Dependencies** (already configured):
```bash
sudo apt-get install -y \
  build-essential pkg-config \
  libglib2.0-dev libgtk-3-dev \
  libwebkit2gtk-4.1-dev libsoup-3.0-dev \
  libjavascriptcoregtk-4.1-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev libasound2-dev
```

3. **Feature flags**:
```bash
# Linux uses --no-default-features (no whisper.cpp FFI)
cargo check --no-default-features
cargo test --no-default-features
```

4. **Dev dependencies**:
```toml
[dev-dependencies]
tempfile = "3.10"  # Required for tests
```

---

## Commits Related to This Decision

- `f31bf5a` - ci: Remove Ubuntu from CI matrix - macOS only for now
- `39f10a8` - fix: Update test expectations for schema v7 and default prompt length
- `882c698` - docs: Add CCW task for Whisper model manager + VAD + quantization
- `2012344` - fix: Add tempfile dev-dependency for tests
- `f1e779f` - fix: Add libasound2-dev for ALSA support on Linux CI

---

## Notes for Future Self

- Ubuntu was burning CI credits with repeated failures
- ALSA, tempfile, schema version, prompt tests all fixed but...
- macOS had same test failures (schema version, prompt length)
- Better to fix one platform well than chase two
- Linux support is NOT removed from code, just CI
- Can add back anytime by changing CI matrix

---

## CCW Agent Instructions

**DO NOT** add Linux CI back without explicit PM approval.

**DO** ensure all Rust code compiles with `--no-default-features` for future Linux compatibility.

**DO** document any macOS-specific code paths clearly.
