# Quickstart: 5 Minutes to Your First Card

Get from zero to published card in 5 minutes. This guide walks you through installing the Writer app, creating your first voice note, and publishing it to earn $EXTROPY tokens.

---

## Prerequisites

- **macOS** (Apple Silicon recommended for Metal GPU acceleration)
- **Homebrew** package manager
- **10 minutes of time**

---

## Step 1: System Dependencies (2 minutes)

Install required system packages:

```bash
# Install whisper.cpp with Metal support for voice transcription
brew install whisper-cpp portaudio

# Download the Whisper base model (141MB)
mkdir -p ~/extrophi-models
curl -L -o ~/extrophi-models/ggml-base.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
```

**Why these dependencies?**
- `whisper-cpp`: Local voice-to-text transcription (privacy-first, no cloud)
- `portaudio`: Audio recording interface
- Whisper model: AI model for speech recognition (runs locally on your Mac)

---

## Step 2: Install Writer App (1 minute)

Download and install the BrainDump Writer desktop app:

```bash
# Clone the repository
git clone https://github.com/extrophi/extrophi-ecosystem.git
cd extrophi-ecosystem/writer

# Install dependencies
npm install

# Launch the app in development mode
npm run tauri:dev
```

**What is Writer?**
Writer is a privacy-first voice journaling desktop app. Your voice never leaves your machine—all transcription happens locally using whisper.cpp.

---

## Step 3: Configure API Keys (Optional, 30 seconds)

If you want to use AI chat features (OpenAI GPT-4 or Claude Sonnet):

1. Click **Settings** (⚙️ icon)
2. Enter your API keys:
   - **OpenAI API Key**: For GPT-4 chat (optional)
   - **Claude API Key**: For Claude Sonnet chat (optional)
3. Click **Save**

**Note**: API keys are stored securely in macOS Keychain. They're optional—you can still record and transcribe without them.

---

## Step 4: Record Your First Voice Note (1 minute)

1. Click the **🎤 Record** button
2. Speak for 10-60 seconds about a business idea, insight, or thought
3. Click **Stop** when done
4. Watch as your voice is transcribed in real-time

**Example topics:**
- "Here's my strategy for growing my Twitter following..."
- "I noticed a pattern in successful content creators..."
- "My plan for launching my first digital product..."

---

## Step 5: Categorize and Publish (30 seconds)

To publish your card and earn $EXTROPY tokens:

1. **Set Privacy Level**: Choose `BUSINESS` or `IDEAS`
   - ✅ **BUSINESS**: Publicly publishable (work, business, strategy)
   - ✅ **IDEAS**: Publicly publishable (creative ideas, insights)
   - ❌ **PERSONAL/PRIVATE/JOURNAL**: Not published (stays private)

2. **Add Tags** (optional): `business`, `content`, `strategy`, etc.

3. **Click "Publish"**

Your card will be:
- ✅ Published to `https://extrophi.ai/cards/your-card-slug`
- ✅ Stored in PostgreSQL database
- ✅ Rewarded with **1.00000000 $EXTROPY token**

---

## Step 6: View Your Published Card

After publishing, you'll see:

```
✅ Card published!
📍 URL: https://extrophi.ai/cards/how-to-grow-on-twitter-a1b2c3d4
💰 Earned: 1.00000000 $EXTROPY
```

Visit your card URL to see it live on the web.

---

## What You Just Did

✅ Installed privacy-first voice transcription
✅ Recorded your first voice note
✅ Published it to the web
✅ Earned your first $EXTROPY tokens

---

## Next Steps

### 1. **Create More Cards**
- Record daily insights, business ideas, or creative thoughts
- Earn 1 $EXTROPY token per published card
- Build your public knowledge base

### 2. **Learn About Attributions**
When others cite, remix, or reply to your cards, you earn more $EXTROPY:
- **Citation** (+0.1 $EXTROPY): Someone references your card
- **Remix** (+0.5 $EXTROPY): Someone builds upon your idea
- **Reply** (+0.05 $EXTROPY): Someone comments on your card

### 3. **Use AI Chat** (Optional)
If you added API keys:
- Click on any transcribed note
- Click **"Chat with AI"**
- Ask GPT-4 or Claude to analyze, expand, or refine your ideas

### 4. **Export Your Cards**
- Click **"Export"** to download all cards as markdown
- Use them for blog posts, newsletters, or course content

---

## Troubleshooting

### "Whisper library not found"
```bash
# Reinstall whisper.cpp
brew reinstall whisper-cpp

# Verify installation
pkg-config --libs whisper
```

### "Model not found"
Make sure you downloaded the Whisper model to the correct location:
```bash
ls -lh ~/extrophi-models/ggml-base.bin
```

### "Permission denied" during recording
Go to **System Settings > Privacy & Security > Microphone** and enable access for the Writer app.

### App won't launch
```bash
# Clean build and restart
cd writer
rm -rf node_modules
npm install
npm run tauri:dev
```

---

## Understanding $EXTROPY Tokens

$EXTROPY is the native token of the Extrophi ecosystem:

**Earning**:
- 1 token per published card
- 0.05-0.5 tokens when others attribute your work

**Spending**:
- Attribute others' work (cite, remix, reply)
- Transfer tokens to other users
- Future: Premium features, API access

**Precision**: All balances use 8 decimal places (cryptocurrency-grade precision)

**Immutable Ledger**: Every transaction is recorded permanently in PostgreSQL

---

## API Access (Advanced)

Want to publish programmatically? See the [API Guide](./api-guide.md) for:
- RESTful API endpoints
- Authentication with API keys
- Publishing cards via HTTP
- Querying attributions and token balances

---

## Privacy Philosophy

Extrophi is built privacy-first:

✅ **Voice transcription**: 100% local (whisper.cpp on your Mac)
✅ **API keys**: Stored in macOS Keychain (never sent to Extrophi servers)
✅ **Privacy levels**: You control what gets published
❌ **No tracking**: No analytics, no telemetry
❌ **No cloud**: Your voice never leaves your machine

**You own your data. You control what's public.**

---

## Resources

- **Writer Guide**: [./writer-guide.md](./writer-guide.md) - Full voice journaling tutorial
- **Research Guide**: [./research-guide.md](./research-guide.md) - Scraping and content intelligence
- **API Guide**: [./api-guide.md](./api-guide.md) - Programmatic access
- **GitHub**: [github.com/extrophi/extrophi-ecosystem](https://github.com/extrophi/extrophi-ecosystem)

---

## Support

**Questions?** Open an issue: [GitHub Issues](https://github.com/extrophi/extrophi-ecosystem/issues)

**Found a bug?** We welcome contributions: [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Built with care. Shipped with purpose. Privacy-first by design.**

🎤 → 📝 → 🌍 → 💰

*Voice → Text → Web → Tokens*
