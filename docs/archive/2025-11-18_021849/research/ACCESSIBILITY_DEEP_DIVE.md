# Accessibility Deep Dive: Voice-First Applications
## WCAG 2.1 Level AA Compliance for BrainDump v3.0

**Document Version**: 1.0
**Date**: 2025-11-16
**Agent**: Sigma2 (Accessibility Researcher)
**Target Compliance**: WCAG 2.1 Level AA
**Application**: BrainDump - Privacy-First Voice Journaling Desktop App (Tauri 2.0 + Svelte 5)

---

## Executive Summary

This document provides comprehensive accessibility requirements and implementation guidelines for voice-first applications, with specific focus on BrainDump v3.0. Voice journaling applications present unique accessibility challenges because they:

1. **Require keyboard alternatives** to voice input for motor accessibility
2. **Must provide visual transcripts** for hearing accessibility
3. **Need high contrast and readable UI** for vision accessibility
4. **Demand focus management** for cognitive accessibility
5. **Support multiple input modalities** for motor accessibility

### Key Statistics
- **Color contrast violations**: #1 accessibility issue (83.6% of websites)
- **Keyboard accessibility issues**: 15% of all digital accessibility problems
- **Screen reader usage**: NVDA (65.6%), JAWS (60%), VoiceOver (44%)
- **Auto-detection capability**: axe-core finds ~57% of WCAG issues (43% requires manual testing)
- **Voice app users**: Include users with vision, hearing, motor, and cognitive disabilities

### Compliance Levels
- **Level A**: Minimum compliance (lowest barrier)
- **Level AA**: Recommended standard (target for BrainDump)
- **Level AAA**: Enhanced compliance (optional, nice-to-have)

---

## Part 1: WCAG 2.1 Level AA Compliance Framework

### Core Principles (POUR)

WCAG 2.1 is built on four foundational principles:

#### 1. **Perceivable**
Content must be perceivable to at least one sensory modality.

**Key Requirements**:
- Text alternatives for non-text content (alt text, captions)
- Captions and transcripts for all audio content
- Adaptable content (can be presented in multiple ways)
- Color contrast: **4.5:1 for normal text (AA)**, **3:1 for large text** (18pt+ or 14pt+ bold)
- No reliance on color alone to convey meaning

**For Voice Apps**:
- Transcripts of recorded audio (✓ BrainDump provides this via Whisper)
- Visual indicators for audio recording status
- Captions for any video tutorials
- High contrast UI for readability

#### 2. **Operable**
Interfaces must be operable with multiple input methods.

**Key Requirements**:
- Full keyboard accessibility (Tab, Enter, Arrow keys, Escape)
- No keyboard traps (can always exit)
- Focus visible and logical
- No seizure triggers (flashing less than 3x/second)
- Multiple ways to find content

**For Voice Apps**:
- Keyboard navigation alongside voice input
- Voice control + mouse/touchpad options
- Skip links for long content
- Clear focus indicators
- Customizable keyboard shortcuts (don't conflict with voice recognition)

#### 3. **Understandable**
Content and interactions must be understandable.

**Key Requirements**:
- Readable text (simple language, clear headings)
- Text at secondary education level (WCAG SC 3.1.5)
- Predictable behavior (consistent navigation, controls)
- Error prevention and recovery
- Definitions for unusual terms

**For Voice Apps**:
- Simple, clear button labels
- Consistent UI patterns
- Helpful error messages with recovery suggestions
- Definitions for voice commands

#### 4. **Robust**
Compatible with current and future assistive technologies.

**Key Requirements**:
- Valid HTML5 markup
- Proper use of ARIA (Accessible Rich Internet Applications)
- Semantic elements (not just divs)
- Support for screen readers
- Support for voice recognition software

**For Voice Apps**:
- Proper ARIA roles and labels
- Semantic HTML buttons/inputs
- Voice recognition compatibility (label in name)
- Screen reader support

---

### WCAG 2.1 Level AA Success Criteria (Key for Voice Apps)

#### **Perception Criteria**

| Criterion | Requirement | BrainDump Status | Notes |
|-----------|-------------|------------------|-------|
| 1.1.1 Non-text Content | Alt text for images | ✓ Low priority (minimal graphics) | Transcripts serve as alt text for voice |
| 1.3.1 Info & Relationships | Semantic structure | ⚠️ Check Svelte component markup | Ensure proper heading hierarchy |
| 1.4.3 Contrast Minimum | 4.5:1 text, 3:1 large text | ❌ TO DO | Critical: Review all UI colors |
| 1.4.4 Resize Text | Text must scale to 200% | ✓ CSS supports scaling | Test with DevTools zoom |
| 1.4.5 Images of Text | Avoid text in images | ✓ All text is real text | SVG icons OK |
| 1.4.11 Non-text Contrast | 3:1 for UI components | ❌ TO DO | Buttons, focus indicators, icons |
| 1.4.13 Content on Hover | Dismissible, hoverable, persistent | ⚠️ Check tooltips | Mouse/focus tooltips must dismiss with Escape |

#### **Operability Criteria**

| Criterion | Requirement | BrainDump Status | Notes |
|-----------|-------------|------------------|-------|
| 2.1.1 Keyboard | All functionality via keyboard | ⚠️ PARTIAL | Record/stop via voice, need keyboard shortcuts |
| 2.1.2 No Keyboard Trap | Can Tab out of all elements | ✓ Unknown | Manual testing required |
| 2.1.4 Character Key Shortcuts | Can disable/remap shortcuts | ⚠️ PARTIAL | Need settings for voice command conflicts |
| 2.4.3 Focus Order | Tab order follows visual flow | ⚠️ Check Svelte | Runes API may need focus management |
| 2.4.7 Focus Visible | Clear focus indicator | ❌ TO DO | Add visible outline/highlight on Tab |
| 2.5.3 Label in Name | Visible text = ARIA name | ⚠️ Check all buttons | Critical for voice recognition users |
| 2.5.4 Motion Actuation | Alternatives to accelerometer/shake | N/A | Desktop app, not relevant |

#### **Understandability Criteria**

| Criterion | Requirement | BrainDump Status | Notes |
|-----------|-------------|------------------|-------|
| 3.1.2 Language of Parts | Mark non-English content | ✓ Minimal foreign content | Transcripts may auto-detect language |
| 3.2.1 On Focus | No unexpected changes on focus | ✓ Check component behavior | No auto-submit on focus |
| 3.2.2 On Input | No unexpected changes on input | ✓ Check dropdowns | Changing provider shouldn't auto-send message |
| 3.3.1 Error Identification | Describe errors clearly | ⚠️ PARTIAL | Need better error messages |
| 3.3.4 Error Prevention | Confirm submissions | ⚠️ PARTIAL | Consider confirmation for delete operations |

#### **Robustness Criteria**

| Criterion | Requirement | BrainDump Status | Notes |
|-----------|-------------|------------------|-------|
| 4.1.1 Parsing | Valid HTML/CSS | ✓ Svelte compiles to valid HTML | Run validator |
| 4.1.2 Name, Role, Value | Proper ARIA implementation | ⚠️ Check | Every button needs aria-label if needed |
| 4.1.3 Status Messages | Use ARIA live regions | ⚠️ TO DO | Announce transcription status |

---

## Part 2: Voice Input Accessibility Guidelines

Voice-first applications have unique accessibility considerations because they serve users with disabilities AND introduce new barriers for users with speech disabilities.

### Critical Voice Input Requirements

#### **1. Keyboard Alternatives (2.1.1)**

**Requirement**: All voice input must have keyboard alternatives.

**Why**: Users without speech disabilities (or with intermittent speech disabilities) need alternatives.

**Implementation for BrainDump**:
```javascript
// Voice input should NOT be the only way to interact
✓ CORRECT:
  - Voice recording (primary)
  - Type message in chat (alternative)
  - Keyboard shortcut to start recording (Alt+R)

✗ WRONG:
  - Voice-only journaling without text input
  - No keyboard shortcut for record button
```

#### **2. Label in Name (2.5.3) - CRITICAL FOR VOICE RECOGNITION**

**Requirement**: Visible button text must match the accessible name so voice users can say the label.

**Example**:
```javascript
// ❌ WRONG - Voice user says "Send" but button coded as "submit"
<button aria-label="submit">Send</button>

// ✓ CORRECT - Visible text matches accessible name
<button aria-label="Send message">Send</button>

// ✓ CORRECT - Using button text only (preferred)
<button>Send</button>  <!-- Screen reader announces "Send" -->
```

**For BrainDump**:
- Record button: visible text = "Record", aria-label = "Record voice journal" ✓
- Stop button: visible text = "Stop", aria-label = "Stop recording" ✓
- Send message: visible text = "Send", aria-label = "Send message to AI" ✓
- Settings: visible text = "Settings", aria-label = "Open settings" ✓

#### **3. Character Key Shortcuts (2.1.4)**

**Requirement**: Custom keyboard shortcuts must not conflict with voice recognition software.

**Why**: Voice recognition software uses keyboard simulation. Custom shortcuts can interfere.

**Common Voice Recognition Hotkeys**:
- Windows Speech Recognition: Uses number commands (1-9)
- Dragon NaturallySpeaking: Uses hotkeys for commands
- macOS Voice Control: Uses spoken commands mapped to keyboard

**Implementation**:
```javascript
// ✓ GOOD: Provide Settings to customize/disable shortcuts
Settings > Keyboard > Shortcuts
- [ ] Enable Record Shortcut (Alt+R)
- [ ] Enable Settings Shortcut (Cmd+,)
- [ ] Enable Search Shortcut (Cmd+F)

// ✗ AVOID: Hard-coding conflicting shortcuts
- Single letter keys (A, B, C) - conflicts with voice
- Number keys (1, 2, 3) - used by screen readers
```

#### **4. Speech Input Compatibility**

**Error Handling for Whisper**:
```rust
// If Whisper returns empty or confidence < threshold
if transcript.is_empty() || confidence < 0.5 {
    // Show UI message: "Could not understand. Please try again."
    // Don't auto-retry without user action
    // Provide option to manually type instead
}
```

**Voice Recognition UX**:
```svelte
<!-- Show confidence/status to user -->
<RecordingStatus>
  Recording... 72% confidence
  <!-- Tell user what they said so far -->
</RecordingStatus>
```

---

## Part 3: Vision Accessibility

Vision disabilities range from low vision (partially sighted) to complete blindness, affecting 43 million people in the US alone.

### Color Contrast (WCAG 1.4.3 & 1.4.11)

**Level AA Requirements**:
- Normal text: **4.5:1** contrast ratio
- Large text (18pt+): **3:1** contrast ratio
- UI components & borders: **3:1** contrast ratio

**Color Blindness Impact**:
- **Protanopia** (red-blind): 1% of males, see world as blue/yellow
- **Deuteranopia** (green-blind): 1% of males, also see blue/yellow
- **Tritanopia** (blue-blind): <0.01% of population, see red/green
- **#1 accessibility violation**: 83.6% of websites fail contrast requirements

**DO NOT**:
```css
/* ✗ WRONG: Relies on color alone */
.error { color: red; }
.success { color: green; }
.warning { color: orange; }

/* ✗ WRONG: Insufficient contrast on light background */
.text { color: #999; background: #fff; } /* 2.9:1 - FAIL */

/* ✗ WRONG: Insufficient contrast on light button */
.button { color: #666; background: #f0f0f0; } /* 2.4:1 - FAIL */
```

**DO**:
```css
/* ✓ CORRECT: Text + icon + color */
.error {
  color: #d32f2f; /* Dark red, 7:1 contrast */
  border-left: 4px solid #d32f2f;
}
.error::before { content: "⚠️ "; }

/* ✓ CORRECT: Sufficient contrast (4.5:1 or better) */
.text { color: #1a1a1a; background: #fff; } /* 19:1 - PASS */

/* ✓ CORRECT: Focus indicator with 3:1 contrast */
button:focus {
  outline: 2px solid #0066cc; /* Dark blue, clear */
  outline-offset: 2px;
}
```

**Testing**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- axe DevTools: Free Chrome extension, checks contrast automatically
- Lighthouse: Built into Chrome DevTools, includes contrast checks

### Font and Text Readability

**WCAG SC 3.1.5: Reading Level**
- Text should be at secondary education level (grade 8)
- For complex topics, provide plain language summaries

**For BrainDump Chat**:
```javascript
// ✗ WRONG: Complex AI responses
"Utilizing temporal analysis of phenomenological introspection..."

// ✓ CORRECT: Simple, clear responses
"Looking at what you said and analyzing your feelings..."
```

**Text Styling**:
```css
/* Font selection for readability */
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  /* Avoid: Thin strokes, unusual features */
  /* Use: Standard sans-serif fonts */

  font-size: 16px;  /* Minimum, 14px with bold OK */
  line-height: 1.5; /* 1.5-2.0 recommended for dyslexia */
  letter-spacing: 0.12em; /* Helps with tracking */
  word-spacing: 0.16em; /* Improves word recognition */
}

/* Avoid text in images - use real text */
h1 { font-size: 28px; }  /* Real text */
/* NOT: <img src="heading.png" alt="Title"> */
```

### High Contrast and User Preferences

**Respect System Preferences**:
```css
/* Use prefers-color-scheme to respect user preference */
@media (prefers-color-scheme: dark) {
  body {
    background: #1a1a1a;
    color: #e0e0e0;
  }
}

/* Support Windows High Contrast Mode */
@media (prefers-contrast: more) {
  body {
    border: 1px solid currentColor;
  }
  button {
    border: 2px solid currentColor;
    font-weight: bold;
  }
}
```

**Dyslexia-Friendly Fonts**:
- Recommended: Open Dyslexic, Lexie Readable, Comic Sans
- BrainDump: Consider adding font selection in Settings
```svelte
<Settings>
  <label>
    Font Style
    <select bind:value={settings.font}>
      <option>System Default</option>
      <option>Dyslexia-Friendly (OpenDyslexic)</option>
      <option>High Contrast</option>
    </select>
  </label>
</Settings>
```

### Screen Magnification Support

**Requirements**:
- App must work at 200% zoom (WCAG 1.4.4)
- No horizontal scrolling at 320px width
- Text must reflow properly

**Testing**:
```bash
# Chrome DevTools: Cmd+Shift+P, search "Rendering"
# Set device pixel ratio to 2.0 (200% zoom)
# Or use browser zoom: Cmd++ to 200%
```

---

## Part 4: Motor Accessibility

Motor disabilities affect fine motor control, tremors, and physical reach. Voice input is PRIMARY advantage, but alternatives are essential.

### Keyboard Navigation (WCAG 2.1.1 & 2.4.3)

**Requirements**:
- Tab: Move to next interactive element
- Shift+Tab: Move to previous interactive element
- Enter/Space: Activate buttons
- Arrow keys: Navigate within components (radios, menus, sliders)
- Escape: Close dialogs/menus
- No keyboard traps

**For BrainDump**:
```javascript
// Tab order should follow visual flow
// Left panel (sessions) → Chat → Right panel (settings)

const tabOrder = [
  sessionList,      // 1. Previous sessions
  recordButton,     // 2. Record button
  messageInput,     // 3. Chat message input
  sendButton,       // 4. Send button
  settingsButton    // 5. Settings
];

// ✓ Each element must be reachable via Tab
// ✓ Each element must indicate focus clearly
```

**Svelte 5 Implementation**:
```svelte
<script>
  let focused = $state(null);

  function handleKeydown(e) {
    if (e.key === 'Escape') {
      // Close any open panels
      closePanel();
    }
    if (e.key === 'Enter' && focused === 'record') {
      startRecording();
    }
  }
</script>

<button
  on:focus={() => focused = 'record'}
  on:blur={() => focused = null}
  aria-label="Record voice journal"
>
  Record
</button>
```

### Focus Indicators (WCAG 2.4.7)

**Requirement**: Every interactive element needs visible focus indicator.

**✗ WRONG - Don't do this**:
```css
button {
  outline: none;  /* NEVER remove focus indicator */
  border: 0;
}
```

**✓ CORRECT - Provide clear focus**:
```css
button:focus-visible {  /* Better: only show on keyboard (not mouse) */
  outline: 3px solid #0066cc;  /* Dark blue, 3:1 contrast */
  outline-offset: 2px;
}

/* Or on dark backgrounds */
button:focus-visible {
  outline: 3px solid #66b3ff;  /* Light blue, 3:1 contrast on dark */
  outline-offset: 2px;
}
```

### Switch Control & Eye Tracking Support

**Advanced Motor Accessibility**:
- macOS Voice Control: Navigate with voice + keyboard
- Eye Tracking: Control cursor with eyes (iPadOS/iOS, coming to macOS)
- Switch Control: Single or dual switch scanning
- Dwell Control: Select by holding gaze/switch

**For Desktop Apps**:
- Voice Control on macOS: Tauri apps get basic support
- Can be enhanced with semantic HTML and ARIA
- No special Tauri code needed (works via accessibility APIs)

**Best Practice**:
```html
<!-- Use semantic HTML for native support -->
<button>Record</button>  <!-- Voice Control recognizes this -->
<a href="#">Link</a>     <!-- Natural element support -->

<!-- AVOID -->
<div role="button">Record</div>  <!-- Needs custom handling -->
```

### Dwell and Dwelltime

For users with very limited motor control:
```javascript
// Could support held-click to activate
<button
  onmousedown={(e) => {
    setTimeout(() => {
      // Activate if still held for 500ms
      activate();
    }, 500);
  }}
  onmouseup={() => {
    // Cancel if released early
  }}
>
  Hold to Record (500ms)
</button>
```

---

## Part 5: Cognitive Accessibility

Cognitive disabilities include ADHD, dyslexia, intellectual disability, autism spectrum, dementia, and mental health conditions. About 4-6% of the population has significant cognitive disabilities.

### Simple Language (WCAG 3.1.5)

**Requirements**:
- Secondary education reading level (grade 8, age 14+)
- Average word length: 5-6 letters
- Average sentence: 15 words
- Clear, simple headings

**Score with Flesch-Kincaid**:
```
Grade Level = (0.39 × words/sentences) + (11.8 × syllables/words) - 15.59

Target: Grade 6-8 for accessibility
Current BrainDump: Estimate Grade 10-12 (too complex)
```

**Examples**:
```javascript
// ✗ COMPLEX (Grade 12)
"Leveraging voice-based phenomenological analysis facilitates introspective
narrative documentation for psychological self-examination."

// ✓ SIMPLE (Grade 8)
"Talk about your day. We'll listen and help you reflect on your feelings."
```

**For BrainDump UI**:
```svelte
<!-- ✗ TOO COMPLEX -->
<label>Multimodal AI Provider Selection</label>
<select>
  <option>OpenAI GPT-4 Turbo (Fast)</option>
  <option>Anthropic Claude 3 (Accurate)</option>
</select>

<!-- ✓ SIMPLE -->
<label>Which AI would you like?</label>
<select>
  <option>OpenAI (Quick answers)</option>
  <option>Claude (More detailed)</option>
</select>
```

### Focus and Attention Management

**For users with ADHD**:
- Minimize distractions
- Clear focus point
- One task per screen
- Remove unnecessary elements

**Implementation**:
```svelte
<!-- ✗ Too much: Settings with 50 options -->
<SettingsPanel>
  <!-- Overwhelming -->
</SettingsPanel>

<!-- ✓ Better: Organize into tabs -->
<Settings>
  <Tabs>
    <Tab label="Basic">
      <BasicSettings />
    </Tab>
    <Tab label="Advanced">
      <AdvancedSettings />
    </Tab>
  </Tabs>
</Settings>
```

**Focus Mode Feature** (Recommended):
```svelte
<ToggleSwitch
  label="Focus Mode"
  description="Hide everything except chat and recording"
  bind:checked={focusMode}
/>

{#if focusMode}
  <!-- Show ONLY record button and chat -->
{:else}
  <!-- Show full UI with all panels -->
{/if}
```

### Memory and Context

**Requirement**: Don't require users to memorize information.

**Don'ts**:
- Complex passwords
- Remembering previous choices
- Context switching
- Multi-step processes without confirmation

**Implementation**:
```javascript
// ✗ WRONG: Requires memorization
// User must remember to save before closing

// ✓ CORRECT: Auto-save with visual confirmation
if (messageChanged) {
  saveDraft();
  showMessage("Draft saved");
}

// ✓ CORRECT: Remember previous preferences
settings.rememberProvider = true;  // Default to last-used AI
settings.rememberFocusMode = true; // Remember focus mode preference
```

### Error Prevention (WCAG 3.3.4)

**Requirement**: Prevent or confirm destructive actions.

**For BrainDump - Deleting a Session**:
```svelte
<!-- ✗ NO CONFIRMATION - User can accidentally delete -->
<button onclick={() => deleteSession()}>Delete</button>

<!-- ✓ CONFIRMATION DIALOG -->
<DeleteConfirmation
  message="Delete this journal entry? This cannot be undone."
  confirmLabel="Delete"
  cancelLabel="Keep it"
  onConfirm={deleteSession}
/>
```

### Definitions and Abbreviations

**Requirement**: Define unusual terms on first use.

```svelte
<!-- ✓ First use includes definition -->
<p>
  Your <abbr title="Automatic Speech Recognition">ASR</abbr> quality affects
  transcription accuracy. <a href="#glossary-asr">Learn more</a>
</p>

<Glossary id="glossary-asr">
  <Term id="asr">
    <Title>ASR (Automatic Speech Recognition)</Title>
    <Definition>
      The technology that converts your voice to text. Better ASR means more
      accurate transcriptions.
    </Definition>
  </Term>
</Glossary>
```

---

## Part 6: Hearing Accessibility

Hearing loss affects 48 million Americans. Voice apps present unique challenges for deaf and hard-of-hearing users.

### Critical Requirement: Always Provide Transcripts

**WCAG 1.2.1 Audio-only Content**:
- Every audio recording must have a transcript
- ✓ BrainDump: Whisper provides transcripts automatically
- Transcripts must be easy to access and read

**Implementation**:
```javascript
// ✓ CORRECT: Transcript visible without clicking
<RecordingPlayback>
  <AudioPlayer src="recording.wav" />

  <!-- ALWAYS show transcript alongside audio -->
  <Transcript>
    {transcript}
  </Transcript>
</RecordingPlayback>
```

### Visual Indicators for Audio Status

**Requirement**: No audio-only information. Always provide visual alternatives.

**Don'ts**:
```javascript
// ✗ WRONG: Beep to indicate recording started
// User can't hear the beep

// ✗ WRONG: Only audio confirmation "Recording started"
```

**Do**:
```svelte
<!-- ✓ CORRECT: Visual feedback for recording status -->
<RecordingStatus>
  {#if isRecording}
    <div class="recording-indicator">
      <div class="pulse-animation"></div>
      <span>Recording... {duration}s</span>
    </div>
  {/if}
</RecordingStatus>

<!-- ✓ CORRECT: Show confidence visually -->
<TranscriptionStatus>
  {#if transcribing}
    <ProgressBar value={confidence} max={100} />
    <span>{confidence}% confidence</span>
  {/if}
</TranscriptionStatus>
```

### Captions and Live Transcription

**For future video tutorials**:
- All videos must have captions (synchronized)
- Captions should include [speaker sounds] and music cues
- Recommend: Use YouTube auto-captions + human review

**For live chat**:
```svelte
<!-- If implementing voice in chat someday -->
<ChatMessage>
  <Audio src="voice-message.wav" />
  <!-- ALWAYS include transcript alongside -->
  <Transcript>{transcriptionText}</Transcript>
</ChatMessage>
```

### Multi-Sensory Feedback

**Design Principle**: Use multiple feedback channels.

```svelte
<!-- ✓ CORRECT: Combined feedback -->
<Button onclick={recordingDone}>
  <!-- Visual -->
  <CompleteIcon />
  <!-- Text -->
  Recording complete
  <!-- Could add haptic on mobile -->
</Button>

<!-- Notification combines visual + text -->
<Notification type="success">
  <CheckIcon /> Your journal entry was saved
</Notification>
```

---

## Part 7: Testing Tools and Strategies

### Automated Testing (57% Detection Rate)

#### **1. axe-core / axe DevTools**

**Coverage**: WCAG 2.0, 2.1, 2.2 (Levels A, AA, AAA) + best practices

**Installation**:
```bash
# Browser Extension (free)
# Chrome: https://chromewebstore.google.com/detail/axe-devtools
# Firefox: Firefox Add-ons
# Edge: Microsoft Edge Add-ons

# NPM (for automated testing)
npm install --save-dev @axe-core/playwright
npm install --save-dev @axe-core/react
```

**Browser Testing**:
1. Open DevTools (F12)
2. Click "axe DevTools" tab
3. Click "Scan ALL of my page"
4. Review violations, review checks, best practices

**Automated Testing Example**:
```javascript
// Playwright + axe-core
import { injectAxe, checkA11y } from 'axe-playwright';

test('Homepage is accessible', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await injectAxe(page);
  await checkA11y(page, null, {
    rules: {
      'color-contrast': { enabled: true },
      'label-title-only': { enabled: false },  // Custom rules
    }
  });
});
```

**Limitations**:
- Only catches 57% of issues
- False positives/negatives possible
- Can't test keyboard navigation
- Can't validate focus management

#### **2. Lighthouse (Chrome DevTools)**

**Built into Chrome** - no installation needed.

**How to Run**:
1. Open your site in Chrome
2. DevTools → Lighthouse tab
3. Select "Accessibility"
4. Click "Analyze page load"

**What it Tests**:
- Color contrast
- ARIA attributes
- Heading hierarchy
- Form labels
- Image alt text

**Coverage**: Similar to axe-core, uses same underlying engine

**Limitations**: Same as axe-core

#### **3. WAVE (WebAIM)**

**Free browser extension** - visual feedback on page.

**Installation**:
- Chrome/Firefox/Edge: Search "WAVE" in extension store
- Website: https://wave.webaim.org

**How to Use**:
1. Install extension
2. Navigate to your site
3. Click WAVE icon
4. Icons appear on page showing issues

**What it Tests**: Same WCAG 2.1 as axe-core, different UX (visual injection into page)

**Pros vs axe**:
- Visual overlay on page (easier to locate issues)
- Useful for editors and designers
- No technical knowledge needed

**Cons**:
- Can't test in complex web apps easily
- Less detailed reporting

---

### Manual Testing (43% Detection Rate)

#### **1. Keyboard Navigation Testing**

**Procedure**:
```bash
# Step 1: Disconnect mouse or close trackpad
# Step 2: Navigate using ONLY keyboard

Tab          # Move to next element (should be obvious where you are)
Shift+Tab    # Move to previous element
Enter/Space  # Activate button
Arrow Keys   # Navigate within components (radio, select, slider)
Escape       # Close dialog/menu
```

**Checklist**:
```
☐ Can Tab to all interactive elements?
☐ Tab order follows visual left-to-right, top-to-bottom?
☐ Focus indicator is clearly visible (not hidden by scrolling)?
☐ No focus traps (can Tab out of everything)?
☐ Escape key closes dialogs and dropdowns?
☐ Arrow keys work in radio groups, select menus?
☐ Skip links present for long content?
```

**For BrainDump**:
```
☐ Can Tab to record button?
☐ Can Tab to previous sessions list?
☐ Can Tab through chat messages?
☐ Can Tab to settings button?
☐ Focus indicator visible on each element?
☐ Record button activates with Enter/Space?
☐ Settings opens/closes with Escape?
☐ Message input accepts Tab key (not jump away)?
```

#### **2. Screen Reader Testing**

**Most Common Screen Readers**:
- **NVDA** (Windows, free): https://www.nvaccess.org
- **JAWS** (Windows, commercial)
- **VoiceOver** (macOS, iOS, built-in)

**Basic VoiceOver Testing (macOS)**:
```bash
# Enable VoiceOver
Cmd+F5

# Basic Commands
VO = Control+Option

VO+Right Arrow      # Move to next element
VO+Left Arrow       # Move to previous element
VO+Space           # Activate button
VO+Shift+Down      # Enter group (like a menu)
VO+Shift+Up        # Exit group

# Disable VoiceOver
Cmd+F5
```

**What to Test**:
1. **Heading Structure**: Are headings announced correctly?
   ```
   VO announces: "Heading level 1: Chat"
   Good: Logical hierarchy (h1 > h2 > h3)
   Bad: Skipping levels (h1 > h3)
   ```

2. **Button Labels**: Is the label clear?
   ```
   VO announces: "Record, button"
   Good: Clear, matches visible text
   Bad: "Button 1" or "Click here"
   ```

3. **Form Fields**: Are fields labeled?
   ```
   VO announces: "Chat message, editable text"
   Bad: VO announces: "Text input" (no label)
   ```

4. **Images**: Do they have descriptions?
   ```
   VO announces: "Icons showing recording status"
   Bad: VO announces: "Image" (no alt text)
   ```

5. **ARIA Live Regions**: Are updates announced?
   ```
   User types in chat
   VO should announce: "Message sent" (via aria-live)
   Bad: VO says nothing
   ```

**Screen Reader Testing Checklist**:
```
☐ All page headings have proper hierarchy?
☐ All buttons have clear labels?
☐ All form fields are labeled?
☐ No images without alt text or purpose?
☐ Live regions (aria-live) announce updates?
☐ Keyboard navigation works smoothly?
☐ Tab stops make logical sense?
☐ Focus is visible when announced?
☐ Form errors are described?
☐ Links have clear purpose?
```

#### **3. Voice Recognition Testing**

**Windows Speech Recognition** (built-in):
```bash
# Enable: Settings > Accessibility > Voice access

# Test with BrainDump:
"Click record"      # Should focus record button
"Start voice typing" # Activate speech recognition
"Send"              # Activate send button
```

**VoiceOver with Voice Control** (macOS):
```
# Enable: System Preferences > Accessibility > Voice Control

# Test
"Show names"        # Display numbers on clickable items
"1 2 3"            # Click item 1, 2, or 3
```

**Testing Checklist**:
```
☐ Button labels are clear and unique?
☐ Label in name test: visible text = aria-label?
☐ No conflicts with voice software hotkeys?
☐ Error messages are clear?
☐ Focus visible after voice commands?
☐ Can navigate to all UI elements by voice?
```

---

### Manual Testing: Vision and Color Contrast

#### **1. Color Contrast Verification**

**Tools**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- axe DevTools: Checks automatically
- Lighthouse: Checks automatically

**How to Test Manually**:
```bash
# Using browser inspector:
1. Right-click element
2. Inspect
3. Look at computed colors
4. Use contrast checker tool

# Or use browser extension:
axe DevTools → Scan → Look for "Color contrast"
```

**Target Ratios**:
- Normal text: 4.5:1
- Large text (18pt+): 3:1
- UI components: 3:1

#### **2. Zoom and Magnification**

**Test at 200% Zoom**:
```bash
# Chrome DevTools
1. F12
2. Cmd+Shift+P
3. Search "rendering"
4. Set device pixel ratio to 2.0

# Or use browser zoom
Cmd++ × 2  # Zoom to 200%
```

**Checklist**:
```
☐ Text remains readable at 200% zoom?
☐ No horizontal scrolling?
☐ Layout doesn't break?
☐ Buttons are still clickable?
☐ Focus visible at zoom level?
```

#### **3. Color Blindness Testing**

**Tool**: Coblis Color Blindness Simulator
- https://www.color-blindness.com/coblis-color-blindness-simulator/
- Upload screenshot, see how color-blind users see it

**Checklist**:
```
☐ Can you understand UI without relying on color alone?
☐ Error states are marked with icons, not just color?
☐ Status indicators use text labels?
☐ All meaningful information is conveyed in multiple ways?
```

---

### Testing in BrainDump Context

#### **Environment Setup**

```bash
# Install testing tools
npm install --save-dev @axe-core/playwright
npm install --save-dev axe-core

# Install screen reader testing utility
npm install --save-dev testing-library/jest-dom
```

#### **Automated Accessibility Tests**

Create `/src-tauri/tests/accessibility.test.ts`:

```typescript
import { injectAxe, checkA11y } from 'axe-playwright';
import { test, expect } from '@playwright/test';

test.describe('BrainDump Accessibility', () => {
  test('main UI passes WCAG 2.1 AA checks', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await injectAxe(page);

    // Check full page
    await checkA11y(page, null, {
      rules: {
        'wcag2aa': { enabled: true },
        'wcag2a': { enabled: true },
      }
    });
  });

  test('chat panel is keyboard navigable', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Record button should be reachable
    await page.keyboard.press('Tab');
    expect(await page.locator(':focus').getAttribute('aria-label'))
      .toContain('Record');

    // Tab to message input
    await page.keyboard.press('Tab');
    expect(await page.locator(':focus').getAttribute('aria-label'))
      .toContain('Chat');
  });

  test('all interactive elements have labels', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const buttons = await page.locator('button').count();
    for (let i = 0; i < buttons; i++) {
      const button = page.locator('button').nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');

      expect(text || ariaLabel).toBeTruthy(
        `Button ${i} has no label`
      );
    }
  });
});
```

#### **Component Testing**

```svelte
<!-- Testing VoiceOver in Svelte components -->
<script>
  import { render } from '@testing-library/svelte';

  test('ChatPanel announces recording status', async () => {
    const { container } = render(ChatPanel);

    // Check ARIA live region
    const status = container.querySelector('[aria-live="polite"]');
    expect(status).toBeInTheDocument();
    expect(status?.textContent).toContain('Ready to record');
  });
</script>
```

---

## Part 8: BrainDump v3.0 Accessibility Compliance Checklist

### Critical Issues (MUST FIX for v1.0)

```
WCAG 2.1 Level AA Compliance Status:

PERCEPTION
☐ 1.4.3 Contrast (Minimum) - Review color scheme
  Status: ❌ NOT TESTED
  Action: Run axe-core, WebAIM contrast checker

☐ 1.4.11 Non-text Contrast - UI components
  Status: ❌ NOT TESTED
  Action: Verify button, focus indicator, icon contrast

☐ 1.3.1 Info & Relationships - Semantic structure
  Status: ⚠️ PARTIAL
  Action: Check heading hierarchy in Svelte components

OPERABILITY
☐ 2.1.1 Keyboard - All functionality via keyboard
  Status: ⚠️ PARTIAL (need keyboard record shortcut)
  Action: Add Alt+R to start recording

☐ 2.4.3 Focus Order - Tab follows visual layout
  Status: ⚠️ UNKNOWN
  Action: Keyboard testing with Tab/Shift+Tab

☐ 2.4.7 Focus Visible - Clear focus indicator
  Status: ❌ TODO
  Action: Add outline:3px to all :focus-visible elements

☐ 2.5.3 Label in Name - Visible text matches ARIA
  Status: ⚠️ PARTIAL
  Action: Audit all buttons for visible/ARIA mismatch

UNDERSTANDABILITY
☐ 3.1.5 Reading Level - Secondary education
  Status: ⚠️ PARTIAL
  Action: Simplify UI copy and error messages

☐ 3.3.1 Error Identification - Clear error messages
  Status: ⚠️ PARTIAL
  Action: Improve transcription/API error descriptions

☐ 3.3.4 Error Prevention - Confirm destructive actions
  Status: ❌ TODO
  Action: Confirmation dialog for delete session

ROBUSTNESS
☐ 4.1.2 Name, Role, Value - ARIA implementation
  Status: ⚠️ PARTIAL
  Action: Verify all custom components have ARIA

☐ 4.1.3 Status Messages - Announce via aria-live
  Status: ❌ TODO
  Action: Add aria-live="polite" for transcription status
```

### Priority Implementation Order

**Phase 1: Foundation (Week 1)**
1. Add focus indicators (2.4.7)
2. Test color contrast (1.4.3)
3. Keyboard navigation (2.1.1, 2.4.3)

**Phase 2: Enhancement (Week 2)**
1. Fix label-in-name issues (2.5.3)
2. Add aria-live regions (4.1.3)
3. Improve error messages (3.3.1)

**Phase 3: Polish (Week 3)**
1. Simplify language (3.1.5)
2. Add confirmation dialogs (3.3.4)
3. Full screen reader testing

---

## Part 9: Implementation Patterns for Svelte 5

### Accessible Button Component

```svelte
<!-- src/components/AccessibleButton.svelte -->
<script>
  let {
    label = $bindable(''),
    ariaLabel = label,
    variant = 'primary',
    disabled = false,
    onclick,
    onkeydown,
    children = $bindable()
  } = $props();

  function handleKeydown(e) {
    // Support activation via Enter or Space
    if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
      onkeydown?.(e);
      onclick?.(e);
    }
  }
</script>

<button
  class={`btn btn-${variant}`}
  aria-label={ariaLabel || label}
  disabled={disabled}
  on:click={onclick}
  on:keydown={handleKeydown}
>
  {label}
  {@html children}
</button>

<style>
  button {
    /* Clear focus indicator (3:1 contrast minimum) */
    outline: 2px solid transparent;
    outline-offset: 2px;
    transition: outline 150ms ease-in-out;
  }

  button:focus-visible {
    outline-color: #0066cc;  /* 7:1 contrast on white */
    outline-width: 3px;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Color + icon for better accessibility */
  .btn-primary {
    background: #0066cc;
    color: white;
    border: none;
    padding: 10px 16px;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-danger {
    background: #d32f2f;
    color: white;
    border-left: 4px solid #d32f2f;
  }

  .btn-danger::before {
    content: '⚠️ ';
  }
</style>
```

### Accessible Form Component

```svelte
<!-- src/components/AccessibleInput.svelte -->
<script>
  let {
    label,
    id = `input-${Math.random()}`,
    type = 'text',
    value = $bindable(''),
    error,
    required = false,
    helperText
  } = $props();
</script>

<div class="form-group">
  <!-- Explicit label connected via id -->
  <label for={id}>
    {label}
    {#if required}
      <span aria-label="required">*</span>
    {/if}
  </label>

  <input
    {id}
    {type}
    bind:value
    aria-invalid={error ? 'true' : 'false'}
    aria-describedby={error ? `${id}-error` : helperText ? `${id}-help` : undefined}
  />

  <!-- Error message announced to screen readers -->
  {#if error}
    <div id={`${id}-error`} class="error-message" role="alert">
      {error}
    </div>
  {/if}

  <!-- Helper text for context -->
  {#if helperText}
    <div id={`${id}-help`} class="helper-text">
      {helperText}
    </div>
  {/if}
</div>

<style>
  .form-group {
    margin-bottom: 20px;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #1a1a1a;
  }

  input {
    width: 100%;
    padding: 8px 12px;
    border: 2px solid #ccc;
    border-radius: 4px;
    font-size: 16px;
  }

  input:focus-visible {
    outline: 3px solid #0066cc;
    outline-offset: 2px;
    border-color: #0066cc;
  }

  input[aria-invalid='true'] {
    border-color: #d32f2f;
    background-color: #fff5f5;
  }

  .error-message {
    color: #d32f2f;
    font-size: 14px;
    margin-top: 6px;
    /* Use red + icon to not rely on color alone */
  }

  .error-message::before {
    content: '⚠️ ';
  }

  .helper-text {
    color: #666;
    font-size: 12px;
    margin-top: 6px;
  }
</style>
```

### Screen Reader Announcements (aria-live)

```svelte
<!-- src/components/TranscriptionStatus.svelte -->
<script>
  let { status = '', confidence = 0 } = $props();
</script>

<!-- Live region: announced when content changes -->
<div
  aria-live="polite"
  aria-atomic="true"
  role="status"
  class="status-announce"
>
  {#if status === 'recording'}
    Recording in progress... {confidence}% confidence
  {:else if status === 'done'}
    Transcription complete. Ready to chat.
  {/if}
</div>

<!-- Visual status for sighted users -->
<div class="status-visual">
  {#if status === 'recording'}
    <div class="pulse" />
    <span>Recording... {confidence}%</span>
  {/if}
</div>

<style>
  .status-announce {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    /* Screen-reader only text (not visible to sighted users) */
  }

  .status-visual {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .pulse {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #d32f2f;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
</style>
```

### Focus Management for Modals

```svelte
<!-- src/components/Modal.svelte -->
<script>
  import { onMount } from 'svelte';

  let {
    title,
    isOpen = $bindable(false),
    children = $bindable(),
    onClose
  } = $props();

  let previousFocus;
  let modalElement;

  onMount(() => {
    // Return focus to button that opened modal
    previousFocus = document.activeElement;
  });

  function handleKeydown(e) {
    if (e.key === 'Escape' && isOpen) {
      closeModal();
    }

    // Trap focus within modal
    if (e.key === 'Tab') {
      const focusableElements = modalElement?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements?.[0];
      const lastElement = focusableElements?.[focusableElements.length - 1];

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    }
  }

  function closeModal() {
    isOpen = false;
    onClose?.();
    // Return focus to button that opened modal
    previousFocus?.focus();
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
  <!-- Backdrop -->
  <div
    class="modal-backdrop"
    on:click={closeModal}
    role="presentation"
  />

  <!-- Modal -->
  <div
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
    bind:this={modalElement}
    class="modal"
  >
    <header>
      <h2 id="modal-title">{title}</h2>
      <button
        aria-label="Close dialog"
        on:click={closeModal}
      >
        ✕
      </button>
    </header>

    <div class="modal-content">
      {@html children}
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
  }

  .modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    z-index: 1001;
    max-width: 600px;
    max-height: 80vh;
    overflow: auto;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #eee;
  }

  h2 {
    margin: 0;
    font-size: 20px;
  }

  button {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
  }

  button:focus-visible {
    outline: 2px solid #0066cc;
    border-radius: 4px;
  }
</style>
```

---

## Part 10: Development Checklist for v1.0 Release

### Pre-Launch Accessibility Audit

#### Week 1: Testing Setup
```
☐ Install axe-core/axe-DevTools in team
☐ Add Lighthouse to CI/CD pipeline
☐ Set up screen reader testing environment (VoiceOver/NVDA)
☐ Create accessibility test files
☐ Document testing procedures in CONTRIBUTING.md
```

#### Week 2: Automated Testing
```
☐ Run axe-core against all pages → Fix violations
☐ Run Lighthouse accessibility checks → Fix failures
☐ Check color contrast (4.5:1 normal, 3:1 large, 3:1 UI)
☐ Verify ARIA labels and roles
☐ Test at 200% zoom
```

#### Week 3: Manual Testing
```
☐ Keyboard navigation (Tab, Shift+Tab, Enter, Escape)
☐ Focus indicators visible?
☐ Focus order logical?
☐ No focus traps?
☐ Screen reader testing (VoiceOver on Mac)
  ☐ Headings announced correctly?
  ☐ Button labels clear?
  ☐ Form fields labeled?
  ☐ Live regions working?
```

#### Week 4: Voice & Special Cases
```
☐ Voice recognition testing (macOS Voice Control)
☐ Label-in-name verification
☐ Error messages clear?
☐ Delete confirmation dialogs present?
☐ High contrast mode support
☐ Dyslexia-friendly fonts available?
```

#### Week 5: Documentation & Sign-Off
```
☐ Accessibility statement on website
☐ Known issues documented
☐ Remediation plan for non-compliant features
☐ Provide user feedback mechanism
☐ VPAT (Voluntary Product Accessibility Template) if needed
```

### Automated Testing Integration

Add to `package.json`:
```json
{
  "scripts": {
    "test:a11y": "axe --require axe.config.js src/",
    "test:a11y:lighthouse": "lighthouse http://localhost:5173 --view",
    "test:a11y:keyboard": "echo 'Manual keyboard testing required'",
    "audit": "npm run test:a11y && npm run build"
  }
}
```

Add `axe.config.js`:
```javascript
module.exports = {
  rules: {
    'color-contrast': { enabled: true },
    'label-title-only': { enabled: false }, // Evaluate case by case
    'valid-aria-label': { enabled: true },
    'button-name': { enabled: true },
  },
  runOnly: {
    type: 'tag',
    values: ['wcag2aa'],
  }
};
```

---

## Part 11: Resources and References

### WCAG 2.1 Standards
- **Official**: https://www.w3.org/WAI/WCAG21/quickref/
- **Understanding WCAG 2.1**: https://www.w3.org/WAI/WCAG21/Understanding/
- **WebAIM**: https://webaim.org/ (great tutorials)

### Testing Tools
- **axe-core**: https://github.com/dequelabs/axe-core
- **Lighthouse**: Built into Chrome DevTools
- **WAVE**: https://wave.webaim.org
- **NVDA**: https://www.nvaccess.org (free screen reader)
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/

### Screen Reader Documentation
- **VoiceOver**: https://www.apple.com/accessibility/voiceover/
- **NVDA**: https://www.nvaccess.org/download/
- **Testing Guides**: https://webaim.org/articles/screenreader_testing/

### Svelte Accessibility
- **Official Docs**: https://svelte.dev/docs/accessibility-warnings
- **SvelteKit Guide**: https://kit.svelte.dev/docs/accessibility
- **Best Practices**: https://blog.datawrapper.de/sveltekit-accessibility-tips/

### Voice UI Design
- **Accessibility.com**: https://www.accessibility.com/blog/voice-user-interfaces
- **Web Speech API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API

### General Accessibility
- **A11y Project**: https://www.a11yproject.com
- **Accessible Colors**: https://accessible-colors.com
- **MDN Accessibility**: https://developer.mozilla.org/en-US/docs/Web/Accessibility

---

## Summary: Accessibility Requirements for BrainDump v3.0

### Must Have (WCAG 2.1 AA)

1. **Color Contrast**: 4.5:1 normal text, 3:1 UI components
2. **Keyboard Navigation**: Full Tab/Shift+Tab/Enter/Escape support
3. **Focus Indicators**: Visible 3px outline on all focusable elements
4. **Label in Name**: Button text matches aria-label for voice recognition
5. **Transcripts**: Always available (✓ via Whisper)
6. **Screen Reader Support**: Semantic HTML, ARIA labels, aria-live
7. **Error Messages**: Clear, actionable, announced to screen readers
8. **Keyboard Shortcuts**: Customizable, don't conflict with voice software

### Should Have (Enhanced Accessibility)

1. **High Contrast Mode**: Respect system preferences
2. **Focus Mode**: Reduce distractions for ADHD users
3. **Font Options**: Dyslexia-friendly fonts available
4. **Simple Language**: Grade 8 reading level
5. **Confirmation Dialogs**: Prevent accidental deletion
6. **Multi-Sensory Feedback**: Visual + text, not audio alone

### Nice to Have (AAA Level)

1. **Text Spacing Control**: 1.5x line height, 1.5x letter spacing
2. **Audio Descriptions**: For any video content
3. **Reduced Motion Option**: Disable animations
4. **Keyboard Shortcut Help**: Display all shortcuts
5. **Multiple Ways to Find Content**: Search, browsing, shortcuts

---

## Next Steps

1. **Week 1**: Run automated testing (axe-core, Lighthouse)
2. **Week 2**: Fix critical contrast and keyboard issues
3. **Week 3**: Manual testing with screen readers
4. **Week 4**: Voice recognition and edge case testing
5. **Week 5**: Documentation and user feedback mechanism

**Target**: WCAG 2.1 Level AA compliance before v1.0 release

**Ongoing**: Regular testing as new features are added

---

**Document Version**: 1.0
**Last Updated**: 2025-11-16
**Status**: Ready for implementation
**Next Review**: After automated testing phase
