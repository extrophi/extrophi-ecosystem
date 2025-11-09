# IPC Error Serialization Test

**Status:** Ready to Test
**Date Verified:** 2025-11-09

## Test Purpose
Verify that `BrainDumpError` serializes correctly through the Tauri IPC boundary and can be properly deserialized on the frontend.

## Test Command
A test command exists specifically for this: `test_error_serialization`

**Location:** `/Users/kjd/01-projects/IAC-031-clear-voice-app/src-tauri/src/commands.rs` (lines 277-281)

```rust
#[tauri::command]
pub async fn test_error_serialization() -> Result<String, BrainDumpError> {
    Err(BrainDumpError::Audio(AudioError::PermissionDenied))
}
```

**Registration:** Confirmed in `/Users/kjd/01-projects/IAC-031-clear-voice-app/src-tauri/src/main.rs` (line 282)

## How to Test

### 1. Launch the App
```bash
npm run tauri:dev
```

### 2. Open Browser DevTools
- Press `Cmd + Option + I` (macOS) or `F12` (Windows/Linux)
- Navigate to **Console** tab

### 3. Run the Test Command
Paste this command in the DevTools console:

```javascript
// Test the IPC serialization
try {
    const result = await invoke('test_error_serialization');
    console.log('Unexpected success:', result);
} catch (error) {
    console.log('Caught error object:', error);
    console.log('Error type:', typeof error);
    console.log('Error constructor:', error.constructor.name);
    console.log('Error properties:', Object.keys(error));
    console.log('Full error:', JSON.stringify(error, null, 2));
}
```

### 4. Expected Output
The error should be serialized as a JSON object with the structure:
```json
{
  "type": "Audio",
  "data": "PermissionDenied"
}
```

The console should show:
```
Caught error object: Object
Error type: object
Error constructor: Object
Error properties: ["type", "data"]
Full error: {
  "type": "Audio",
  "data": "PermissionDenied"
}
```

## Verification Checklist
- [ ] App launches without compilation errors
- [ ] Browser console is accessible
- [ ] Command invokes without throwing unhandled exceptions
- [ ] Error object contains `type` and `data` fields
- [ ] Error structure matches expected JSON format
- [ ] Error can be accessed in frontend error handling code

## Compilation Status
**Cargo Check Result:** PASS (0 errors, 0 warnings)
Command: `cargo check` completed successfully in 0.63s

## Notes for PM
- The test command will intentionally throw an error - this is expected behavior
- The browser DevTools console will catch and display the serialized error
- This test does NOT require actual recording or transcription
- All steps must complete without crashes for IPC serialization to be verified as working
