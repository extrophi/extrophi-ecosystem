# Problems to Fix - 2025-11-15

**Branch:** `consolidation/cleanup-2025-11-15`
**Status:** Merged everything, does not compile
**Approach:** Fix problems properly with research, not workarounds

---

## Problem 1: Type Mismatch in `claude_api.rs`

**Location:** `src-tauri/src/services/claude_api.rs:156-165`

**Symptom:**
```
error[E0308]: mismatched types
pub fn get_api_key() -> Result<String> {
    // Returns Result<String, ClaudeApiError>
    // But signature expects Result<String, BrainDumpError>
```

**Root Cause:**
- `Result<T>` is a type alias for `Result<T, BrainDumpError>`
- Function returns `ClaudeApiError`
- Type mismatch

**Current Code:**
```rust
use crate::error::{ClaudeApiError, Result};

pub fn get_api_key() -> Result<String> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
        .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

    entry
        .get_password()
        .map_err(|e| match e {
            keyring::Error::NoEntry => ClaudeApiError::ApiKeyNotFound,
            _ => ClaudeApiError::KeyringError(e.to_string()),
        })
}
```

**Wrong Fix (workaround):**
Change to `std::result::Result<String, ClaudeApiError>`

**Right Fix (to research):**
1. Check how other Tauri apps handle nested error types
2. Check if `ClaudeApiError` should implement `From<BrainDumpError>`
3. Check if we should use `.map_err()` to convert error types
4. Look at Tauri error handling best practices doc
5. Find recommended pattern for service-layer errors

**Questions:**
- Should service errors convert to domain errors?
- Should we use `thiserror` crate better?
- Is there a `From` implementation we're missing?

---

## Problem 2: Wrong Keyring Method Name

**Location:** `src-tauri/src/services/claude_api.rs:168-177`

**Symptom:**
```
error[E0599]: no method named `delete_credential` found for struct `keyring::Entry`
```

**Root Cause:**
- Using wrong method name from keyring crate
- Correct method is `delete_password()`

**Current Code:**
```rust
pub fn delete_api_key() -> Result<()> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
        .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

    entry
        .delete_credential()  // WRONG METHOD
        .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

    Ok(())
}
```

**Right Fix:**
```rust
entry.delete_password()
```

**Questions:**
- Is this the current `keyring` crate version?
- Should we check crate docs for other API changes?
- Are there other keyring methods we're using incorrectly?

---

## Problem 3: CI Whisper.cpp Optional Feature Flag (WORKAROUND)

**Location:** `src-tauri/Cargo.toml`, `build.rs`, `main.rs`

**What was done:**
Made whisper.cpp compilation optional via feature flag to "fix" CI

**Why it's wrong:**
- Workaround, not a fix
- Conditionally compiled features are complex
- Doesn't solve the real problem: CI should have whisper.cpp

**Root Cause:**
- CI runners don't have whisper.cpp installed
- Build script hardcodes paths

**Right Fix (to research):**
1. Check how other Rust projects handle C++ dependencies in CI
2. Look at Tauri CI best practices
3. Find whisper.cpp installation method for GitHub Actions
4. Check if there's a cargo-based approach
5. Look at cmake-based dependency management

**Questions:**
- Should we vendor whisper.cpp?
- Should we use system package managers in CI?
- Is there a cross-platform build approach?
- Can we use a pre-built whisper library?

---

## Problem 4: Svelte 5 Reactive Syntax ($: vs $derived)

**Location:** `src/App.svelte:39-41`

**What was done:**
Converted `$:` to `$derived()` runes

**Is this right?**
Need to verify with Svelte 5 docs we just scraped

**Check:**
- Read `docs/dev/svelte/docs-svelte-$derived.md`
- Verify pattern matches official examples
- Check if there are other legacy patterns in the codebase
- Ensure we're using runes correctly everywhere

**Questions:**
- Are there other Svelte 4 → 5 migrations needed?
- Should we audit all `.svelte` files?
- Are we using `$state` correctly?
- Do we need `$effect` anywhere?

---

## Problem 5: Architecture - No Proper Error Handling

**Location:** Throughout codebase

**Symptoms:**
- `.unwrap()` calls in production code
- No user-facing error messages
- No logging strategy
- Errors fail silently

**Philosophy Violation:**
We have `docs/pm/error-handling-philosophy.md` that says:
- "Fail loudly, never silently"
- "No `.unwrap()` in production code"
- "Three-layer error strategy: logs, UI, events"

**Current State:**
- Not following our own standards
- Band-aid fixes instead of proper error handling
- No structured logging
- No error boundaries

**Right Fix (to research):**
1. Read our own `error-handling-philosophy.md`
2. Check Tauri error handling patterns in docs
3. Look at logging crates (tracing, log, etc.)
4. Find error boundary patterns for Tauri apps
5. Research user-facing error dialog approaches

**Questions:**
- Should we use `tracing` or `log` crate?
- How do we show errors in Tauri UI?
- What's the pattern for async error propagation?
- Should errors emit Tauri events?

---

## Next Steps

1. **Research Phase** (You + Claude Desktop + Docs)
   - Read scraped docs for each problem
   - Find official examples
   - Document the right pattern

2. **Solution Design** (Team decision)
   - Write clean solution with examples
   - Get approval before coding
   - Ensure it follows best practices

3. **Implementation** (Clean, tested, production-grade)
   - Write the fix
   - Add tests
   - Add error handling
   - Document why

4. **Review** (Before merge)
   - Does it solve the problem?
   - Does it follow framework patterns?
   - Is it production-ready?
   - Are there tests?

---

## Rules

1. **No more workarounds**
2. **Research first, code second**
3. **Use official docs we just scraped**
4. **Follow our error-handling-philosophy.md**
5. **Production-grade or don't merge**

---

**Next:** Pick Problem 1, research it properly, document the right fix.
