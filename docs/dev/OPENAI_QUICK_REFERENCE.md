# OpenAI Integration - Quick Reference

## All Files Modified/Created

### Created (1 file)
- `/home/user/IAC-031-clear-voice-app/src-tauri/src/services/openai_api.rs` (296 lines)

### Modified (5 files)
1. `/home/user/IAC-031-clear-voice-app/src-tauri/src/services/mod.rs`
2. `/home/user/IAC-031-clear-voice-app/src-tauri/src/error.rs`
3. `/home/user/IAC-031-clear-voice-app/src-tauri/src/lib.rs`
4. `/home/user/IAC-031-clear-voice-app/src-tauri/src/commands.rs`
5. `/home/user/IAC-031-clear-voice-app/src-tauri/src/main.rs`

## Quick Test Commands (Frontend Console)

```javascript
// 1. Store your OpenAI API key
await invoke('store_openai_key', { 
  key: 'sk-proj-YOUR_API_KEY_HERE' 
});

// 2. Verify key was stored
const hasKey = await invoke('has_openai_key');
console.log('Has key:', hasKey); // Should be true

// 3. Test connection (validates key with OpenAI)
const isValid = await invoke('test_openai_connection');
console.log('Key is valid:', isValid); // Should be true if key is correct

// 4. Send a simple message
const response = await invoke('send_openai_message', {
  messages: [
    ['user', 'What is 2+2?']
  ],
  systemPrompt: null
});
console.log('Response:', response); // Should get "4" or similar

// 5. Multi-turn conversation
const conversation = await invoke('send_openai_message', {
  messages: [
    ['user', 'My name is Alice'],
    ['assistant', 'Hello Alice! Nice to meet you.'],
    ['user', 'What is my name?']
  ],
  systemPrompt: 'You are a helpful assistant.'
});
console.log('Response:', conversation); // Should remember "Alice"

// 6. Delete API key (cleanup)
await invoke('delete_openai_key');
```

## Error Handling Example

```javascript
try {
  const response = await invoke('send_openai_message', {
    messages: [['user', 'Hello']],
    systemPrompt: null
  });
  console.log('Success:', response);
} catch (error) {
  // Error format: { type: "OpenAiApi", data: "ErrorVariant" }
  console.error('Error type:', error.type);
  console.error('Error data:', error.data);
  
  if (error.type === 'OpenAiApi') {
    switch (error.data) {
      case 'ApiKeyNotFound':
        console.log('Please configure your API key first');
        break;
      case 'InvalidApiKey':
        console.log('Your API key is invalid');
        break;
      case 'RateLimitExceeded':
        console.log('Rate limit exceeded, please wait');
        break;
      case 'Timeout':
        console.log('Request timed out, please try again');
        break;
      default:
        console.log('Unknown error:', error.data);
    }
  }
}
```

## Available Commands

| Command | Purpose | Parameters |
|---------|---------|------------|
| `send_openai_message` | Send messages to GPT-4 | `messages: [role, content][]`, `systemPrompt?: string` |
| `store_openai_key` | Store API key securely | `key: string` |
| `has_openai_key` | Check if key exists | None |
| `test_openai_connection` | Validate API key | None |
| `delete_openai_key` | Remove stored key | None |
| `open_openai_auth_browser` | Open OpenAI console | None |

## Configuration

- **Model**: `gpt-4-turbo-preview`
- **Max Tokens**: 4096
- **Timeout**: 60 seconds
- **Rate Limit**: 60 requests/minute
- **Keyring Service**: `braindump-openai`
- **API Endpoint**: `https://api.openai.com/v1/chat/completions`

## TypeScript Types (for frontend)

```typescript
// Add these to your Tauri command types

interface OpenAiMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// Commands
declare function send_openai_message(
  messages: [string, string][],
  systemPrompt: string | null
): Promise<string>;

declare function store_openai_key(key: string): Promise<void>;
declare function has_openai_key(): Promise<boolean>;
declare function test_openai_connection(): Promise<boolean>;
declare function delete_openai_key(): Promise<void>;
declare function open_openai_auth_browser(): Promise<void>;

// Error type
interface OpenAiError {
  type: 'OpenAiApi';
  data: 
    | 'ApiKeyNotFound'
    | 'InvalidApiKey'
    | 'RateLimitExceeded'
    | 'Timeout'
    | { ConnectionFailed: string }
    | { RequestFailed: string }
    | { InvalidResponse: string }
    | { KeyringError: string }
    | { Other: string };
}
```

## Getting Your OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)
5. Use `store_openai_key` command to save it

**Or use the helper command:**
```javascript
await invoke('open_openai_auth_browser'); // Opens the API keys page
```

## Troubleshooting

### "ApiKeyNotFound" Error
```javascript
// Fix: Store your API key first
await invoke('store_openai_key', { key: 'sk-proj-...' });
```

### "InvalidApiKey" Error (401)
```javascript
// Fix: Get a new key from OpenAI console
await invoke('delete_openai_key'); // Remove old key
await invoke('open_openai_auth_browser'); // Get new key
await invoke('store_openai_key', { key: 'NEW_KEY' });
```

### "RateLimitExceeded" Error (429)
```javascript
// Fix: Wait 60 seconds between batches of requests
// The client has built-in rate limiting (60 req/min)
```

### "Timeout" Error
```javascript
// Fix: Check internet connection and retry
// Requests timeout after 60 seconds
```

## Complete Example App

```javascript
class OpenAiChat {
  async setup() {
    // Check if key exists
    const hasKey = await invoke('has_openai_key');
    
    if (!hasKey) {
      const apiKey = prompt('Enter your OpenAI API key:');
      await invoke('store_openai_key', { key: apiKey });
    }
    
    // Test connection
    const isValid = await invoke('test_openai_connection');
    if (!isValid) {
      alert('Invalid API key');
      return false;
    }
    
    return true;
  }
  
  async sendMessage(userMessage, history = []) {
    // Convert history to format expected by API
    const messages = history.map(msg => [msg.role, msg.content]);
    messages.push(['user', userMessage]);
    
    try {
      const response = await invoke('send_openai_message', {
        messages,
        systemPrompt: 'You are a helpful journaling assistant.'
      });
      
      return response;
    } catch (error) {
      console.error('OpenAI error:', error);
      throw error;
    }
  }
}

// Usage
const chat = new OpenAiChat();
await chat.setup();
const response = await chat.sendMessage('Hello!');
console.log('AI:', response);
```

## Status

✅ **100% Complete**

All features implemented and ready for frontend integration.

## Next Steps

1. Add TypeScript types to your frontend
2. Build API key settings UI
3. Integrate into chat interface
4. Add error handling in UI
5. Display conversation history

## Documentation

- Full test guide: `OPENAI_INTEGRATION_TEST.md`
- Implementation summary: `OPENAI_IMPLEMENTATION_SUMMARY.md`
- Source code: `src-tauri/src/services/openai_api.rs`
