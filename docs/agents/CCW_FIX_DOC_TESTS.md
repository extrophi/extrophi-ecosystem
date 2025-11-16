# CCW URGENT: Fix Doc Tests

**Priority**: CRITICAL - CI Blocking
**Status**: IMMEDIATE ACTION REQUIRED

---

## Problem

Doc tests in Rust are failing because examples don't have proper imports:

```
error[E0425]: cannot find function `load_prompt_template` in this scope
error[E0425]: cannot find function `list_prompt_templates` in this scope
error[E0422]: cannot find struct `AudioData` in this scope
```

---

## Files to Fix

### 1. `src-tauri/src/prompts.rs` (lines 20-23, 82-84)

**Current (BROKEN):**
```rust
/// # Examples
/// ```
/// let prompt = load_prompt_template("brain_dump")?;
/// let prompt = load_prompt_template("end_of_day")?;
/// ```
```

**Fix to:**
```rust
/// # Examples
/// ```no_run
/// use braindump::prompts::load_prompt_template;
///
/// let prompt = load_prompt_template("brain_dump").unwrap();
/// let prompt = load_prompt_template("end_of_day").unwrap();
/// ```
```

### 2. `src-tauri/src/plugin/manager.rs` (lines 32, 77, 116, 201)

Fix all doc examples to include proper imports:

```rust
/// # Examples
/// ```no_run
/// use braindump::plugin::manager::PluginManager;
/// use braindump::plugin::types::AudioData;
///
/// let manager = PluginManager::new();
/// // rest of example
/// ```
```

---

## Steps

1. **Clone and checkout**:
```bash
git clone https://github.com/Iamcodio/IAC-031-clear-voice-app.git
cd IAC-031-clear-voice-app
git checkout claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
git pull
```

2. **Find all doc tests**:
```bash
cd src-tauri
cargo test --doc 2>&1 | grep "error\[E"
```

3. **Fix each one** - Add proper imports or use `no_run` if example is illustrative only

4. **Verify locally**:
```bash
cargo test --all-features
```

5. **Push fix**:
```bash
git add -A
git commit -m "fix: Add proper imports to all doc test examples"
git push origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
```

---

## Important Notes

- Use `/// ```no_run` for examples that shouldn't actually execute
- Use `/// ```ignore` for pseudo-code examples
- All real examples need `use braindump::...` imports
- Error handling: use `.unwrap()` or `?` with proper fn signature
- Check ALL files in src-tauri/src/ for doc examples

---

## Success Criteria

- [ ] `cargo test --all-features` passes 100%
- [ ] All doc examples compile
- [ ] No skipped tests
- [ ] CI goes green

**DO THIS NOW. THIS IS BLOCKING THE PR.**
