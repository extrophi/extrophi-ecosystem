# Floating UI and Desktop Integration Patterns

**Research Report for BrainDump v3.0**
**Date**: 2025-11-16
**Focus**: Super Whisper-style floating UI implementation strategies

---

## Executive Summary

This report researches floating window and system integration patterns for implementing a Super Whisper-style dictation experience in BrainDump. The findings cover:

1. **Open source implementations** to study (OpenSuperWhisper, WhisperWriter, OpenWhispr)
2. **Tauri 2.0 APIs** for windows, shortcuts, clipboard, and system tray
3. **Platform-specific requirements** for macOS, Windows, and Linux
4. **Recommended architecture** for cross-platform floating UI

Key insight: Tauri 2.0 provides excellent native APIs for all required features, with some platform-specific considerations.

---

## Table of Contents

1. [Open Source Implementations](#1-open-source-implementations-to-study)
2. [Tauri Window Management](#2-tauri-window-management)
3. [Global Keyboard Shortcuts](#3-global-keyboard-shortcuts)
4. [System Tray Integration](#4-system-tray-integration)
5. [Clipboard and Auto-Paste](#5-clipboard-and-auto-paste)
6. [macOS Accessibility Permissions](#6-macos-accessibility-permissions)
7. [Cross-Platform Considerations](#7-cross-platform-considerations)
8. [Recommended Architecture](#8-recommended-architecture)
9. [Code Examples](#9-code-examples)
10. [GitHub Repos to Study](#10-github-repos-to-study)

---

## 1. Open Source Implementations to Study

### 1.1 OpenSuperWhisper (PyQt6)
**GitHub**: https://github.com/TakanariShimbo/open-super-whisper

**Key Features**:
- System tray/menu bar residency
- Global hotkey (default: Ctrl+Shift+R)
- Auto-copy to clipboard
- OpenAI Whisper-1 and GPT-4o transcription

**Architecture**:
```
├─ Recording Layer (microphone capture)
├─ Transcription Service (OpenAI API)
├─ Configuration Management
└─ UI Framework (PyQt6)
```

**Lessons**:
- Clipboard-based delivery (not cursor injection)
- Platform-specific background residency
- Settings allow hotkey customization

### 1.2 WhisperWriter (Python/PyQt5)
**GitHub**: https://github.com/savbell/whisper-writer

**Key Features**:
- Activation key: `ctrl+shift+space` (configurable)
- **Auto-type to active window** (not just clipboard)
- Multiple recording modes (continuous, VAD, press-to-toggle, hold-to-record)
- Cross-platform (Windows, macOS, Linux)

**Architecture**:
- Audio: `sounddevice` library
- Transcription: Local `faster-whisper` OR OpenAI API
- Keyboard simulation: `pynput` library
- Settings GUI: PyQt5 window

**Lessons**:
- Configurable delays between key presses (0.005s default)
- Post-processing options (trailing spaces, period removal)
- Background service waiting for activation

### 1.3 OpenWhispr (Electron/React)
**GitHub**: https://github.com/HeroTools/open-whispr

**Key Features**:
- Customizable global hotkey (default: backtick `)
- **Minimal draggable overlay panel**
- Local Whisper models (39MB to 1.5GB)
- Cross-platform (macOS 10.15+, Windows 10+, Linux)

**Tech Stack**:
```
Frontend: React 19, TypeScript, Tailwind CSS v4
Desktop: Electron 36 with context isolation
Database: better-sqlite3
Speech: OpenAI Whisper (local + API)
Build: Vite
UI: shadcn/ui + Radix primitives
```

**Lessons**:
- Draggable floating panel for dictation controls
- Multiple Linux package formats (AppImage, deb, rpm, tar.gz, Flatpak)
- Fn/Globe key listener option on macOS

---

## 2. Tauri Window Management

### 2.1 Always-On-Top Windows

**JavaScript API**:
```javascript
import { getCurrentWindow } from '@tauri-apps/api/window';

// Set window to always float on top
await getCurrentWindow().setAlwaysOnTop(true);

// Note: Stays on top even when other apps are focused
```

**Rust API**:
```rust
// In setup or command handler
main_window.set_always_on_top(true).unwrap();
```

**Important Behavior**:
- Window stays in front of ALL applications (not just current app)
- No app-wide z-order mechanism - each window is independent
- Must track always_on_top status manually (no getter API)

### 2.2 Frameless & Transparent Windows

**Configuration** (`tauri.conf.json`):
```json
{
  "windows": [
    {
      "label": "main",
      "decorations": false,
      "transparent": true,
      "width": 300,
      "height": 200,
      "alwaysOnTop": true,
      "skipTaskbar": true
    }
  ]
}
```

**CSS Setup**:
```css
body {
  background-color: rgba(0, 0, 0, 0.8);
  border-radius: 12px;
  overflow: hidden;
}
```

**Custom Drag Region** (HTML):
```html
<div data-tauri-drag-region class="titlebar">
  <button onclick="appWindow.minimize()">-</button>
  <button onclick="appWindow.close()">x</button>
</div>
```

**Known Issues**:
- Windows: Transparent windows may only work after resize (workaround: toggle decorations)
- Losing decorations loses native features (moving, aligning on macOS)
- Need to implement custom window controls

### 2.3 Creating Windows Programmatically

**JavaScript**:
```javascript
import { WebviewWindow } from '@tauri-apps/api/webviewWindow';

const floatingPanel = new WebviewWindow('dictation', {
  url: 'dictation.html',
  width: 300,
  height: 80,
  x: 100,
  y: 100,
  decorations: false,
  transparent: true,
  alwaysOnTop: true,
  skipTaskbar: true,
  resizable: false,
  focus: false  // Don't steal focus from current window
});
```

**Rust**:
```rust
use tauri::WebviewWindowBuilder;

let floating = WebviewWindowBuilder::new(
    app,
    "dictation",
    tauri::WebviewUrl::App("dictation.html".into())
)
.title("Dictation")
.inner_size(300.0, 80.0)
.decorations(false)
.transparent(true)
.always_on_top(true)
.skip_taskbar(true)
.resizable(false)
.focused(false)
.build()?;
```

### 2.4 Window Vibrancy Effects (macOS)

For native blur/transparency effects:

```rust
// In Cargo.toml
// window-vibrancy = "0.4"

use window_vibrancy::apply_vibrancy;

let window = app.get_webview_window("main").unwrap();
apply_vibrancy(&window, NSVisualEffectMaterial::HudWindow, None, None).unwrap();
```

---

## 3. Global Keyboard Shortcuts

### 3.1 Installation

**Add Plugin**:
```bash
npm run tauri add global-shortcut
# OR manually:
cargo add tauri-plugin-global-shortcut --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
npm install @tauri-apps/plugin-global-shortcut
```

**Initialize** (`src-tauri/src/lib.rs`):
```rust
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        // ... rest of setup
        .run(tauri::generate_context!())
        .expect("error running app");
}
```

### 3.2 Permission Configuration

**`src-tauri/capabilities/default.json`**:
```json
{
  "permissions": [
    "global-shortcut:allow-is-registered",
    "global-shortcut:allow-register",
    "global-shortcut:allow-unregister",
    "global-shortcut:allow-register-all",
    "global-shortcut:allow-unregister-all"
  ]
}
```

### 3.3 JavaScript Usage

```javascript
import {
  register,
  unregister,
  isRegistered
} from '@tauri-apps/plugin-global-shortcut';

// Register global hotkey
await register('CommandOrControl+Shift+Space', (event) => {
  if (event.state === 'Pressed') {
    console.log('Recording hotkey pressed');
    startRecording();
  } else if (event.state === 'Released') {
    console.log('Recording hotkey released');
    // For hold-to-record mode
  }
});

// Check if registered
const registered = await isRegistered('CommandOrControl+Shift+Space');

// Unregister when done
await unregister('CommandOrControl+Shift+Space');
```

### 3.4 Rust Usage (Preferred for Background Operation)

```rust
use tauri_plugin_global_shortcut::{
    Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState
};

// Define shortcuts
let record_shortcut = Shortcut::new(
    Some(Modifiers::CONTROL | Modifiers::SHIFT),
    Code::Space
);

// Register in setup
app.global_shortcut().on_shortcut(record_shortcut, |app, shortcut, event| {
    match event.state {
        ShortcutState::Pressed => {
            app.emit("shortcut-pressed", "record").unwrap();
        }
        ShortcutState::Released => {
            app.emit("shortcut-released", "record").unwrap();
        }
    }
})?;

// Register the shortcut
app.global_shortcut().register(record_shortcut)?;
```

### 3.5 Key Combinations

**Supported Modifiers**:
- `CommandOrControl` - Cmd on macOS, Ctrl on Windows/Linux
- `Shift`
- `Alt` (Option on macOS)
- `Super` (Win key on Windows, Cmd on macOS)

**Common Patterns**:
- `CommandOrControl+Shift+Space` - Record toggle
- `CommandOrControl+Shift+R` - Alternative record toggle
- `Alt+Space` - Quick dictation
- Backtick (\`) - Minimal activation (OpenWhispr style)

**Important**: If shortcut is taken by another app, handler won't trigger.

---

## 4. System Tray Integration

### 4.1 Enable Feature

**`src-tauri/Cargo.toml`**:
```toml
[dependencies]
tauri = { version = "2.0.0", features = ["tray-icon"] }
```

### 4.2 Rust Implementation

```rust
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, TrayIconBuilder, TrayIconEvent},
    Manager,
};

fn setup_tray(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    // Create menu items
    let show = MenuItem::with_id(app, "show", "Show Window", true, None::<&str>)?;
    let record = MenuItem::with_id(app, "record", "Start Recording", true, None::<&str>)?;
    let separator = tauri::menu::PredefinedMenuItem::separator(app)?;
    let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;

    // Build menu
    let menu = Menu::with_items(app, &[&show, &record, &separator, &quit])?;

    // Create tray icon
    let tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .menu_on_left_click(false)  // Left click shows window, right click shows menu
        .tooltip("BrainDump - Voice Journaling")
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "show" => {
                    if let Some(window) = app.get_webview_window("main") {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                }
                "record" => {
                    app.emit("tray-record", ()).unwrap();
                }
                "quit" => {
                    app.exit(0);
                }
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            match event {
                TrayIconEvent::Click { button: MouseButton::Left, .. } => {
                    let app = tray.app_handle();
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                TrayIconEvent::DoubleClick { .. } => {
                    // Double-click action
                }
                _ => {}
            }
        })
        .build(app)?;

    Ok(())
}
```

### 4.3 JavaScript Implementation

```javascript
import { TrayIcon } from '@tauri-apps/api/tray';
import { Menu } from '@tauri-apps/api/menu';
import { defaultWindowIcon } from '@tauri-apps/api/app';

async function setupTray() {
  const menu = await Menu.new({
    items: [
      {
        id: 'show',
        text: 'Show Window',
        action: () => showMainWindow()
      },
      {
        id: 'record',
        text: 'Start Recording',
        action: () => toggleRecording()
      },
      { item: 'Separator' },
      {
        id: 'quit',
        text: 'Quit',
        action: () => quit()
      }
    ]
  });

  const tray = await TrayIcon.new({
    icon: await defaultWindowIcon(),
    menu,
    menuOnLeftClick: false,
    tooltip: 'BrainDump',
    action: (event) => {
      if (event.type === 'Click' && event.button === 'Left') {
        showMainWindow();
      }
    }
  });
}
```

### 4.4 Tray-Only App Pattern

For apps that primarily run in system tray:

```rust
// In main.rs or lib.rs
.on_window_event(|window, event| {
    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
        // Hide instead of quit
        window.hide().unwrap();
        api.prevent_close();
    }
})
.build(tauri::generate_context!())
.expect("error running app")
.run(|app_handle, event| {
    if let tauri::RunEvent::ExitRequested { api, .. } = event {
        // Prevent auto-exit when all windows closed
        api.prevent_exit();
    }
});
```

### 4.5 Platform Notes

- **Linux**: May need to set an empty menu for icon to be visible
- **macOS**: Shows in menu bar (top-right)
- **Windows**: Shows in system tray (bottom-right)

---

## 5. Clipboard and Auto-Paste

### 5.1 Clipboard Plugin Setup

```bash
npm run tauri add clipboard-manager
# OR manually:
cargo add tauri-plugin-clipboard-manager
npm install @tauri-apps/plugin-clipboard-manager
```

**Initialize**:
```rust
.plugin(tauri_plugin_clipboard_manager::init())
```

**Permissions** (`capabilities/default.json`):
```json
{
  "permissions": [
    "clipboard-manager:allow-read-text",
    "clipboard-manager:allow-write-text",
    "clipboard-manager:allow-write-html"
  ]
}
```

### 5.2 Basic Clipboard Usage

**JavaScript**:
```javascript
import {
  writeText,
  readText,
  writeHtml
} from '@tauri-apps/plugin-clipboard-manager';

// Write transcription to clipboard
await writeText(transcribedText);

// Read current clipboard
const currentClip = await readText();

// Write with HTML formatting
await writeHtml(
  '<p><strong>Transcription:</strong> ' + text + '</p>',
  text  // Fallback plain text
);
```

**Rust**:
```rust
use tauri_plugin_clipboard_manager::ClipboardExt;

// Write to clipboard
app.clipboard().write_text(transcribed_text)?;

// Read from clipboard
let content = app.clipboard().read_text()?;
```

### 5.3 Auto-Paste Implementation Strategies

**Strategy 1: Clipboard + User Paste** (Simplest)
```javascript
// After transcription completes
await writeText(transcribedText);
showNotification('Transcription copied! Press Cmd+V to paste');
```

**Strategy 2: Clipboard + Simulated Keyboard Paste** (Complex)

This requires simulating Cmd+V/Ctrl+V keypresses. Options:

**A. Using `enigo` crate (Recommended)**:
```rust
// In Cargo.toml
// enigo = "0.2"

use enigo::{Enigo, Key, KeyboardControllable};

#[tauri::command]
async fn auto_paste(text: String, state: tauri::State<'_, AppState>) -> Result<(), String> {
    // Write to clipboard first
    app.clipboard().write_text(&text).map_err(|e| e.to_string())?;

    // Small delay for clipboard to settle
    std::thread::sleep(std::time::Duration::from_millis(50));

    // Simulate paste keystroke
    let mut enigo = Enigo::new();

    #[cfg(target_os = "macos")]
    {
        enigo.key_down(Key::Meta);
        enigo.key_click(Key::Layout('v'));
        enigo.key_up(Key::Meta);
    }

    #[cfg(target_os = "windows")]
    {
        enigo.key_down(Key::Control);
        enigo.key_click(Key::Layout('v'));
        enigo.key_up(Key::Control);
    }

    #[cfg(target_os = "linux")]
    {
        enigo.key_down(Key::Control);
        enigo.key_click(Key::Layout('v'));
        enigo.key_up(Key::Control);
    }

    Ok(())
}
```

**B. Using `rdev` crate**:
```rust
// In Cargo.toml
// rdev = "0.5" (or fork for macOS compatibility)

use rdev::{simulate, EventType, Key};

fn simulate_paste() -> Result<(), Box<dyn std::error::Error>> {
    #[cfg(target_os = "macos")]
    {
        simulate(&EventType::KeyPress(Key::MetaLeft))?;
        simulate(&EventType::KeyPress(Key::KeyV))?;
        simulate(&EventType::KeyRelease(Key::KeyV))?;
        simulate(&EventType::KeyRelease(Key::MetaLeft))?;
    }
    Ok(())
}
```

**C. Platform-Specific Commands** (Using subprocess):

```rust
#[cfg(target_os = "macos")]
fn simulate_paste_macos() -> Result<(), String> {
    std::process::Command::new("osascript")
        .arg("-e")
        .arg("tell application \"System Events\" to keystroke \"v\" using command down")
        .output()
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

**Strategy 3: Direct Text Insertion** (Most Complex)

This types out text character by character:

```rust
use enigo::{Enigo, KeyboardControllable};

fn type_text(text: &str) {
    let mut enigo = Enigo::new();

    // Add delay between characters for reliability
    for c in text.chars() {
        enigo.key_sequence(&c.to_string());
        std::thread::sleep(std::time::Duration::from_millis(5));
    }
}
```

### 5.4 Auto-Paste Workflow

```javascript
// Frontend flow after transcription
async function handleTranscriptionComplete(transcript) {
  const settings = await getSettings();

  if (settings.autoCopy) {
    await writeText(transcript);

    if (settings.autoPaste) {
      // Hide floating panel first
      await getCurrentWindow().hide();

      // Small delay for focus to return to original app
      await sleep(100);

      // Trigger paste
      await invoke('simulate_paste');
    } else {
      showNotification('Copied to clipboard!');
    }
  }
}
```

### 5.5 Platform Permissions

- **macOS**: Requires Accessibility permissions for keyboard simulation
- **Linux**: May need special permissions for uinput
- **Windows**: Generally works without special permissions

---

## 6. macOS Accessibility Permissions

### 6.1 Why Required

macOS requires explicit user permission for:
- **Global keyboard monitoring** (NSEvent.addGlobalMonitorForEvents)
- **Simulating keyboard input** (CGEvent posting)
- **Input monitoring** (CGEventTap)

### 6.2 Permission Types

1. **Accessibility** (`AXIsProcessTrusted`):
   - Required for: Global event monitoring, posting keyboard events
   - Settings location: System Preferences > Security & Privacy > Privacy > Accessibility

2. **Input Monitoring** (`IOHIDCheckAccess`):
   - Required for: CGEventTap monitoring
   - Settings location: System Preferences > Security & Privacy > Privacy > Input Monitoring

### 6.3 Checking Permissions in Rust

```rust
#[cfg(target_os = "macos")]
mod accessibility {
    use std::ptr;

    #[link(name = "ApplicationServices", kind = "framework")]
    extern "C" {
        fn AXIsProcessTrustedWithOptions(options: *const std::ffi::c_void) -> bool;
    }

    pub fn check_accessibility_permission(prompt: bool) -> bool {
        unsafe {
            let options = if prompt {
                // Create dictionary with prompt option
                core_foundation::dictionary::CFDictionary::from_pairs(&[
                    (
                        core_foundation::string::CFString::new("AXTrustedCheckOptionPrompt"),
                        core_foundation::boolean::CFBoolean::true_value()
                    )
                ]).as_concrete_TypeRef() as *const _
            } else {
                ptr::null()
            };

            AXIsProcessTrustedWithOptions(options)
        }
    }
}

#[tauri::command]
fn check_accessibility() -> Result<bool, String> {
    #[cfg(target_os = "macos")]
    {
        Ok(accessibility::check_accessibility_permission(false))
    }
    #[cfg(not(target_os = "macos"))]
    {
        Ok(true)
    }
}

#[tauri::command]
fn request_accessibility_permission() -> Result<bool, String> {
    #[cfg(target_os = "macos")]
    {
        Ok(accessibility::check_accessibility_permission(true))
    }
    #[cfg(not(target_os = "macos"))]
    {
        Ok(true)
    }
}
```

### 6.4 Info.plist Configuration

Add to `src-tauri/Info.plist`:
```xml
<key>NSAccessibilityUsageDescription</key>
<string>BrainDump needs accessibility access to use global keyboard shortcuts and auto-paste transcriptions.</string>
```

### 6.5 User-Friendly Permission Flow

```javascript
// In frontend startup
async function checkPermissions() {
  const isMacOS = await platform() === 'darwin';

  if (isMacOS) {
    const hasAccess = await invoke('check_accessibility');

    if (!hasAccess) {
      const shouldRequest = await dialog.confirm(
        'BrainDump needs Accessibility permission for global shortcuts and auto-paste. ' +
        'Would you like to grant access now?',
        { title: 'Permission Required', type: 'info' }
      );

      if (shouldRequest) {
        await invoke('request_accessibility_permission');

        await dialog.message(
          'Please enable BrainDump in System Preferences > Security & Privacy > Privacy > Accessibility, then restart the app.',
          { title: 'Enable Accessibility', type: 'info' }
        );
      }
    }
  }
}
```

---

## 7. Cross-Platform Considerations

### 7.1 Windows

**Floating Windows**:
- Native support via Win32 `HWND_TOPMOST`
- Tauri handles via `set_always_on_top(true)`
- Works reliably across all Windows versions

**Global Shortcuts**:
- No special permissions required
- RegisterHotKey Win32 API under the hood
- Tauri plugin handles cross-platform

**Clipboard**:
- Native Win32 clipboard API
- No special permissions
- Full support in Tauri

**System Tray**:
- Shows in notification area (bottom-right)
- Full feature support

**Known Issues**:
- Transparent windows may require resize workaround
- May need event loop for keyboard simulation

### 7.2 Linux

**Floating Windows**:
- **X11**: Uses `_NET_WM_STATE_ABOVE` atom
  - Well supported across desktop environments
  - Standard EWMH protocol

- **Wayland**: Limited/no standard support
  - No official "always on top" protocol
  - Compositor-specific solutions only
  - May need layer-shell protocol (non-standard)
  - KDE Plasma has built-in support

**Global Shortcuts**:
- X11: XGrabKey mechanism
- Wayland: Varies by compositor
- May conflict with desktop environment shortcuts
- Tauri plugin provides abstraction

**Clipboard**:
- X11: Uses X11 selections (CLIPBOARD)
- Wayland: Uses wl_clipboard
- Tauri plugin handles both

**System Tray**:
- Uses StatusNotifierItem (SNI) protocol
- May need to set empty menu for visibility
- Some events (Leave) unsupported

**Keyboard Simulation**:
- X11: XTest extension or uinput
- Wayland: Limited to compositor-specific methods
- May require root permissions for uinput
- `enigo` crate has experimental Wayland support

### 7.3 macOS

**Floating Windows**:
- NSWindow.Level system
- `.floating` level floats above app windows
- True always-on-top requires NSWindow.Level adjustment on app deactivation
- Use `.screenSaver` level for highest priority

**Global Shortcuts**:
- Requires Accessibility permission
- Carbon Event Manager API
- System-wide hotkey registration
- Well supported by Tauri

**Clipboard**:
- NSPasteboard API
- No special permissions
- Full support

**System Tray**:
- Shows in menu bar (top-right)
- Full macOS integration
- Native appearance

**Keyboard Simulation**:
- Requires Accessibility permission
- CGEvent API or NSEvent injection
- Very reliable once permission granted

**Special macOS Features**:
- Window vibrancy effects
- Native titlebar customization
- Menu bar apps

### 7.4 Platform Detection in Tauri

```javascript
import { platform } from '@tauri-apps/plugin-os';

const os = await platform();
// Returns: 'darwin', 'windows', or 'linux'

if (os === 'darwin') {
  // macOS-specific code
} else if (os === 'windows') {
  // Windows-specific code
} else {
  // Linux-specific code
}
```

---

## 8. Recommended Architecture

### 8.1 Overall Design

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM TRAY                          │
│  ├─ Show/Hide Main Window                               │
│  ├─ Start/Stop Recording                                │
│  └─ Quit Application                                    │
├─────────────────────────────────────────────────────────┤
│                GLOBAL SHORTCUT HANDLER                  │
│  ├─ Cmd/Ctrl+Shift+Space: Toggle Recording             │
│  ├─ Escape: Cancel Recording                           │
│  └─ Custom hotkeys from settings                        │
├─────────────────────────────────────────────────────────┤
│              FLOATING DICTATION PANEL                   │
│  ┌─────────────────────────────────┐                    │
│  │ [🎤 Recording...   ] [Stop] [X] │  ← Minimal UI     │
│  │ [Audio Level: ████░░░░░░░░░░░░] │  ← Visual feedback│
│  └─────────────────────────────────┘                    │
│  ├─ Always on top                                       │
│  ├─ Frameless, transparent, draggable                   │
│  ├─ Doesn't steal focus from active window              │
│  └─ Shows transcription progress                        │
├─────────────────────────────────────────────────────────┤
│               TRANSCRIPTION ENGINE                      │
│  ├─ Whisper.cpp FFI (existing)                          │
│  ├─ Real-time audio processing                          │
│  └─ Privacy-first local processing                      │
├─────────────────────────────────────────────────────────┤
│              AUTO-PASTE HANDLER                         │
│  ├─ Copy to clipboard (default)                         │
│  ├─ Simulate Cmd/Ctrl+V paste                           │
│  └─ Direct text insertion (optional)                    │
└─────────────────────────────────────────────────────────┘
```

### 8.2 File Structure Additions

```
src-tauri/
├─ src/
│   ├─ commands/
│   │   └─ floating.rs          # Floating window commands
│   ├─ plugins/
│   │   └─ auto_paste.rs        # Keyboard simulation
│   └─ lib.rs                   # Plugin registration
└─ capabilities/
    └─ default.json             # Permissions

src/
├─ windows/
│   └─ dictation.html           # Floating panel HTML
├─ components/
│   ├─ DictationPanel.svelte    # Floating panel UI
│   └─ PermissionDialog.svelte  # Permission request UI
└─ lib/
    └─ shortcuts.js             # Shortcut management
```

### 8.3 Implementation Phases

**Phase 1: Foundation** (4-6 hours)
- [ ] Add Tauri plugins (global-shortcut, clipboard-manager)
- [ ] Configure permissions in capabilities
- [ ] Create basic floating window configuration
- [ ] Test always-on-top behavior

**Phase 2: System Tray** (2-3 hours)
- [ ] Enable tray-icon feature
- [ ] Create tray menu with basic actions
- [ ] Implement hide-on-close behavior
- [ ] Add tray icon click handling

**Phase 3: Global Shortcuts** (3-4 hours)
- [ ] Register default recording shortcut
- [ ] Handle shortcut events in Rust
- [ ] Emit events to frontend
- [ ] Add shortcut customization UI

**Phase 4: Floating Panel** (4-6 hours)
- [ ] Create separate window for dictation
- [ ] Design minimal, frameless UI
- [ ] Implement draggable regions
- [ ] Add recording status visualization

**Phase 5: Auto-Paste** (4-6 hours)
- [ ] Implement clipboard write
- [ ] Add keyboard simulation (enigo)
- [ ] Handle macOS permissions
- [ ] Test cross-platform

**Phase 6: Polish** (3-4 hours)
- [ ] Add user preferences for shortcuts
- [ ] Implement permission checking
- [ ] Add notifications
- [ ] Cross-platform testing

**Total Estimated Time**: 20-30 hours

### 8.4 User Experience Flow

1. **App Launch**:
   - App starts minimized to system tray
   - Global shortcut registered
   - Permission check (macOS)

2. **Recording Activation**:
   - User presses Cmd+Shift+Space
   - Floating panel appears (doesn't steal focus)
   - Recording starts automatically

3. **During Recording**:
   - Visual feedback in floating panel
   - User speaks naturally
   - Panel can be dragged if needed

4. **Recording Complete**:
   - User presses shortcut again (or says stop word)
   - Panel shows "Transcribing..."
   - Whisper.cpp processes audio

5. **Transcription Delivery**:
   - Text copied to clipboard
   - Floating panel hides
   - (Optional) Auto-paste with Cmd+V simulation
   - Focus returns to original application

6. **Advanced Usage**:
   - Click system tray for menu
   - Open main app for full features
   - Customize shortcuts in settings

---

## 9. Code Examples

### 9.1 Complete Floating Window Setup

**`src-tauri/tauri.conf.json`** (partial):
```json
{
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "BrainDump",
        "width": 1024,
        "height": 768
      },
      {
        "label": "dictation",
        "title": "Dictation",
        "url": "dictation.html",
        "width": 320,
        "height": 100,
        "decorations": false,
        "transparent": true,
        "alwaysOnTop": true,
        "skipTaskbar": true,
        "resizable": false,
        "visible": false,
        "center": true
      }
    ]
  },
  "plugins": {
    "global-shortcut": {
      "shortcuts": []
    }
  }
}
```

### 9.2 Complete Plugin Registration

**`src-tauri/src/lib.rs`**:
```rust
use tauri::Manager;

mod commands;

pub fn run() {
    tauri::Builder::default()
        // Clipboard plugin
        .plugin(tauri_plugin_clipboard_manager::init())
        // Global shortcuts plugin
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, shortcut, event| {
                    if shortcut.matches(
                        tauri_plugin_global_shortcut::Modifiers::CONTROL
                        | tauri_plugin_global_shortcut::Modifiers::SHIFT,
                        tauri_plugin_global_shortcut::Code::Space
                    ) {
                        match event.state {
                            tauri_plugin_global_shortcut::ShortcutState::Pressed => {
                                let _ = app.emit("recording-toggle", ());
                            }
                            _ => {}
                        }
                    }
                })
                .build(),
        )
        .setup(|app| {
            // Setup system tray
            setup_tray(app)?;

            // Register default shortcut
            let shortcut = tauri_plugin_global_shortcut::Shortcut::new(
                Some(
                    tauri_plugin_global_shortcut::Modifiers::CONTROL
                    | tauri_plugin_global_shortcut::Modifiers::SHIFT
                ),
                tauri_plugin_global_shortcut::Code::Space,
            );
            app.global_shortcut().register(shortcut)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" {
                    window.hide().unwrap();
                    api.prevent_close();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::show_dictation_panel,
            commands::hide_dictation_panel,
            commands::simulate_paste,
            commands::check_accessibility,
        ])
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
```

### 9.3 Floating Panel HTML

**`src/dictation.html`**:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dictation</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: rgba(30, 30, 30, 0.95);
      color: white;
      border-radius: 12px;
      overflow: hidden;
      -webkit-user-select: none;
      user-select: none;
    }

    .panel {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .drag-region {
      -webkit-app-region: drag;
      flex: 1;
      font-weight: 600;
      font-size: 14px;
    }

    .controls {
      display: flex;
      gap: 8px;
      -webkit-app-region: no-drag;
    }

    button {
      background: #4a9eff;
      border: none;
      color: white;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
    }

    button:hover {
      background: #3d8ce6;
    }

    button.stop {
      background: #ff4a4a;
    }

    button.stop:hover {
      background: #e63d3d;
    }

    button.close {
      background: transparent;
      padding: 4px 8px;
    }

    .audio-level {
      height: 8px;
      background: #333;
      border-radius: 4px;
      overflow: hidden;
    }

    .audio-level-fill {
      height: 100%;
      background: linear-gradient(90deg, #4a9eff, #00ff88);
      width: 0%;
      transition: width 100ms ease;
    }

    .status {
      font-size: 12px;
      color: #888;
      text-align: center;
    }

    .status.recording {
      color: #ff4a4a;
    }

    .status.transcribing {
      color: #ffaa00;
    }
  </style>
</head>
<body>
  <div class="panel">
    <div class="header">
      <div class="drag-region" data-tauri-drag-region>
        BrainDump Dictation
      </div>
      <div class="controls">
        <button class="stop" id="stopBtn">Stop</button>
        <button class="close" id="closeBtn">✕</button>
      </div>
    </div>

    <div class="audio-level">
      <div class="audio-level-fill" id="audioLevel"></div>
    </div>

    <div class="status recording" id="status">
      Recording...
    </div>
  </div>

  <script type="module">
    import { listen } from '@tauri-apps/api/event';
    import { getCurrentWindow } from '@tauri-apps/api/window';
    import { invoke } from '@tauri-apps/api/core';

    const window = getCurrentWindow();
    const stopBtn = document.getElementById('stopBtn');
    const closeBtn = document.getElementById('closeBtn');
    const audioLevel = document.getElementById('audioLevel');
    const status = document.getElementById('status');

    // Handle stop button
    stopBtn.addEventListener('click', async () => {
      await invoke('stop_dictation');
    });

    // Handle close button
    closeBtn.addEventListener('click', async () => {
      await window.hide();
    });

    // Listen for audio level updates
    await listen('audio-level', (event) => {
      const level = event.payload;
      audioLevel.style.width = `${level * 100}%`;
    });

    // Listen for status changes
    await listen('dictation-status', (event) => {
      const state = event.payload;
      status.textContent = state;
      status.className = `status ${state.toLowerCase().replace(' ', '-')}`;

      if (state === 'Transcribing') {
        stopBtn.disabled = true;
      }
    });

    // Listen for transcription complete
    await listen('dictation-complete', async () => {
      await window.hide();
    });
  </script>
</body>
</html>
```

### 9.4 Auto-Paste Command

**`src-tauri/src/commands/floating.rs`**:
```rust
use enigo::{Enigo, Key, KeyboardControllable, Settings};
use std::time::Duration;
use tauri_plugin_clipboard_manager::ClipboardExt;

#[tauri::command]
pub async fn show_dictation_panel(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("dictation") {
        window.show().map_err(|e| e.to_string())?;
        window.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn hide_dictation_panel(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("dictation") {
        window.hide().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn simulate_paste(
    text: String,
    app: tauri::AppHandle,
) -> Result<(), String> {
    // Write to clipboard
    app.clipboard()
        .write_text(&text)
        .map_err(|e| e.to_string())?;

    // Small delay for clipboard to settle
    std::thread::sleep(Duration::from_millis(50));

    // Simulate paste keystroke
    let mut enigo = Enigo::new(&Settings::default())
        .map_err(|e| e.to_string())?;

    #[cfg(target_os = "macos")]
    {
        enigo.key_down(Key::Meta).map_err(|e| e.to_string())?;
        enigo.key_click(Key::Layout('v')).map_err(|e| e.to_string())?;
        enigo.key_up(Key::Meta).map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "windows")]
    {
        enigo.key_down(Key::Control).map_err(|e| e.to_string())?;
        enigo.key_click(Key::Layout('v')).map_err(|e| e.to_string())?;
        enigo.key_up(Key::Control).map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "linux")]
    {
        enigo.key_down(Key::Control).map_err(|e| e.to_string())?;
        enigo.key_click(Key::Layout('v')).map_err(|e| e.to_string())?;
        enigo.key_up(Key::Control).map_err(|e| e.to_string())?;
    }

    Ok(())
}

#[cfg(target_os = "macos")]
#[tauri::command]
pub fn check_accessibility() -> Result<bool, String> {
    use core_foundation::base::TCFType;
    use core_foundation::boolean::CFBoolean;
    use core_foundation::dictionary::CFDictionary;
    use core_foundation::string::CFString;
    use std::ptr;

    extern "C" {
        fn AXIsProcessTrustedWithOptions(options: *const std::ffi::c_void) -> bool;
    }

    unsafe {
        let key = CFString::new("AXTrustedCheckOptionPrompt");
        let value = CFBoolean::false_value();
        let options = CFDictionary::from_pairs(&[(key, value)]);
        let result = AXIsProcessTrustedWithOptions(options.as_concrete_TypeRef() as *const _);
        Ok(result)
    }
}

#[cfg(not(target_os = "macos"))]
#[tauri::command]
pub fn check_accessibility() -> Result<bool, String> {
    Ok(true)
}
```

### 9.5 Frontend Shortcut Handler

**`src/lib/shortcuts.js`**:
```javascript
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import { writeText } from '@tauri-apps/plugin-clipboard-manager';

let isRecording = false;

export async function initializeShortcuts() {
  // Listen for recording toggle from global shortcut
  await listen('recording-toggle', async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  });
}

async function startRecording() {
  isRecording = true;

  // Show floating panel
  await invoke('show_dictation_panel');

  // Start actual recording
  await invoke('start_recording');
}

async function stopRecording() {
  isRecording = false;

  // Stop recording and get transcription
  const result = await invoke('stop_recording');

  // Update status
  await invoke('emit_event', {
    event: 'dictation-status',
    payload: 'Transcribing'
  });

  // Transcribe
  const transcript = await invoke('transcribe_audio', {
    samples: result.samples,
    sampleRate: result.sample_rate
  });

  // Handle result based on settings
  const settings = await invoke('get_settings');

  if (settings.auto_paste) {
    // Auto-paste to active window
    await invoke('hide_dictation_panel');
    await new Promise(resolve => setTimeout(resolve, 100));
    await invoke('simulate_paste', { text: transcript });
  } else {
    // Just copy to clipboard
    await writeText(transcript);
    await invoke('hide_dictation_panel');

    // Show notification
    await invoke('show_notification', {
      title: 'Transcription Complete',
      body: 'Text copied to clipboard!'
    });
  }

  await invoke('emit_event', {
    event: 'dictation-complete',
    payload: null
  });
}
```

---

## 10. GitHub Repos to Study

### Primary References

1. **OpenSuperWhisper** (PyQt6)
   - URL: https://github.com/TakanariShimbo/open-super-whisper
   - Study: System tray integration, global hotkeys, settings management

2. **WhisperWriter** (Python/PyQt5)
   - URL: https://github.com/savbell/whisper-writer
   - Study: Auto-type to active window, multiple recording modes, cross-platform

3. **OpenWhispr** (Electron/React)
   - URL: https://github.com/HeroTools/open-whispr
   - Study: Draggable overlay panel, Fn key listener, modern UI

4. **Tauri Global Hotkey**
   - URL: https://github.com/tauri-apps/global-hotkey
   - Study: Cross-platform shortcut implementation in Rust

5. **Tauri Plugin Decorum**
   - URL: https://github.com/clearlysid/tauri-plugin-decorum
   - Study: Opinionated window decorations, transparency

### Supporting Libraries

6. **Enigo** (Rust input simulation)
   - URL: https://github.com/enigo-rs/enigo
   - Study: Cross-platform keyboard/mouse simulation

7. **rdev** (Rust input events)
   - URL: https://github.com/Narsil/rdev
   - Study: Global keyboard monitoring, input simulation

8. **simulate_key.rs**
   - URL: https://github.com/vtempest/simulate_key.rs
   - Study: Simplified keyboard simulation wrapper

### Transcription Tools

9. **Awesome Whisper**
   - URL: https://github.com/sindresorhus/awesome-whisper
   - Study: Comprehensive list of Whisper tools and implementations

10. **faster-whisper**
    - URL: https://github.com/SYSTRAN/faster-whisper
    - Study: Optimized local transcription (Python-based)

---

## Conclusion

Implementing a Super Whisper-style floating UI in BrainDump using Tauri 2.0 is highly feasible. The key components are:

1. **Tauri provides excellent APIs** for all core features (windows, shortcuts, clipboard, tray)
2. **Platform considerations** are manageable with conditional compilation
3. **macOS requires** Accessibility permissions for full functionality
4. **Linux Wayland** has limitations but X11 works well
5. **Open source references** provide proven implementation patterns

**Recommended next steps**:
1. Start with Phase 1 (plugin foundation) to validate architecture
2. Prioritize macOS implementation (primary user base)
3. Add Windows support (easier permissions model)
4. Handle Linux as best-effort (X11 > Wayland)

The estimated 20-30 hours of implementation time would add significant value to BrainDump, transforming it from a window-based app to a system-integrated dictation tool that rivals commercial offerings like Super Whisper.

---

**Report Compiled By**: Agent Psi
**Date**: 2025-11-16
**Research Sources**: GitHub repositories, official Tauri documentation, Stack Overflow, Apple Developer Forums
