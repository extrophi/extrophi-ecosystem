# Writer (BrainDump v3.0) - Demo Script
## Duration: 3 minutes
## Format: Teleprompter-style with timestamps

---

## [0:00-0:15] OPENING

Welcome to Writer - the privacy-first voice journaling app built for people who need to externalize their thoughts without surrendering their privacy.

Let me show you how it works.

---

## [0:15-0:45] LAUNCHING THE APP

Here's the Writer desktop app - you'll notice it launches in under a second. That's the benefit of using Tauri instead of Electron - we get native performance with a tiny footprint.

The interface is intentionally minimal. Three main areas: your session list on the left, the chat panel in the center, and settings on the right.

No clutter. No distractions. Just you and your thoughts.

---

## [0:45-1:15] VOICE RECORDING & TRANSCRIPTION

Let's start a new session. I'll click the "New Session" button and give it a name - "Project Planning".

Now watch what happens when I click the microphone button and start talking.

[DEMONSTRATE: Click record, speak for 5-10 seconds]

"I'm working on the Extrophi documentation and need to organize my thoughts about the video script structure. The product overview should come first, followed by specific demos for each component."

[DEMONSTRATE: Stop recording]

Notice how the transcription appears almost instantly. That's because everything is happening locally on this machine using whisper.cpp with Metal GPU acceleration.

Your voice never leaves your computer. There's no cloud processing. No one is listening.

---

## [1:15-1:45] AI CHAT INTERFACE

Now here's where it gets useful. I can chat with AI about my transcription.

I'll select my AI provider - let's use Claude Sonnet 4.5 for this example.

[DEMONSTRATE: Type a message]

"Can you help me structure these thoughts into a clear outline?"

[DEMONSTRATE: Show AI response]

The AI responds with a structured outline based on my voice notes.

But notice - even though I'm using Claude's API, the conversation is happening directly from my machine. Writer isn't storing your conversations on a remote server. It's not training AI models on your private thoughts.

You control the API keys. You control the data.

---

## [1:45-2:15] SESSION MANAGEMENT & TEMPLATES

Let me show you session management.

I can create multiple sessions for different topics - work projects, personal journaling, research notes.

Each session maintains its own conversation history and transcriptions.

[DEMONSTRATE: Switch between sessions]

I can rename sessions, delete them when I'm done, or export them to markdown for my documentation workflow.

And here's a powerful feature - prompt templates.

[DEMONSTRATE: Open templates panel]

I've set up templates for common use cases: daily journaling prompts, project planning frameworks, writing analysis requests.

Instead of typing the same instructions every time, I can select a template and it populates the chat with my preset prompt.

You can create, edit, and delete templates to match your workflow.

---

## [2:15-2:35] PRIVACY FEATURES

Let's talk about privacy - because this is where Writer really shines.

All API keys are stored in your system's secure keychain - on Mac, that's Keychain Access. They're never stored in plain text.

Transcriptions are saved to a local SQLite database - again, on your machine, not in the cloud.

There's no analytics, no telemetry, no "improving our services" data collection.

This app serves one person: you.

---

## [2:35-2:50] EXPORT & PUBLISHING

When you're ready to publish or share your work, Writer can export your sessions to markdown.

[DEMONSTRATE: Export functionality]

This markdown file includes your transcriptions, your AI conversations, and any notes you've added.

You can drop it directly into your blogging workflow, your note-taking system, or your documentation repository.

And if you're using the Extrophi Backend API, you can publish directly and track attribution rewards - but that's completely optional.

---

## [2:50-3:00] CLOSING

Writer - privacy-first voice journaling for people under stress.

No cloud. No subscriptions. No data collection.

Just your voice, your words, your control.

---

## PRODUCTION NOTES

**Screen Recording Sections:**
- 0:15-0:45: Show full app launch and interface tour
- 0:45-1:15: Record actual voice input and show transcription appearing
- 1:15-1:45: Demonstrate AI chat with real response
- 1:45-2:15: Navigate between sessions, show template selector
- 2:15-2:35: Show keychain settings (blur API keys), database location
- 2:35-2:50: Export a session to markdown, show the file

**Visual Overlays:**
- Highlight UI elements as they're mentioned
- Show "LOCAL PROCESSING" badge during transcription
- Display API key security icon during privacy section
- Show file path when discussing local storage

**Demo Preparation:**
- Pre-create 2-3 sample sessions
- Set up 2-3 template examples
- Have API keys configured (blur in recording)
- Prepare a sample export file to show

**Tone:** Calm, confident, reassuring. Emphasize control and privacy without being paranoid.

**Pacing:** Allow the app to breathe - don't rush through interactions. Let users see how fast/smooth it is.

**Key Messages:**
1. Fast, native performance
2. Everything is local - your privacy is guaranteed
3. Simple, distraction-free interface
4. Powerful AI integration without cloud lock-in
5. Flexible export for any workflow
