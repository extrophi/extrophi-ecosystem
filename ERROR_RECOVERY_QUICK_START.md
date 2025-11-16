# Error Recovery UI - Quick Start Guide

## Overview

The BrainDump app now has comprehensive error recovery UI. This guide shows you how to test and use the new features.

---

## 🎯 Test Scenarios

### 1. Test API Key Error
**Steps**:
1. Open Settings (⌘, or click gear icon)
2. Clear your API keys
3. Try to send a message
4. **Expected**: Error boundary shows "API Key Not Found" with "Open Settings" button
5. Click "Open Settings" → Settings panel opens
6. Add API key back → Error dismisses

### 2. Test Network Error (Simulated)
**Steps**:
1. Disconnect from internet
2. Try to send a message
3. **Expected**: Error shows "Connection Error" with "Retry" button
4. Reconnect to internet
5. Click "Retry" → Message sends successfully

### 3. Test Message Input Preservation
**Steps**:
1. Type a long message
2. (Simulate error by disconnecting internet)
3. Send the message → Error occurs
4. **Expected**: Your typed message is still in the input box
5. Reconnect internet
6. Click "Retry" → Message sends with original text

### 4. Test Global Error Toast
**Steps**:
1. Open browser console
2. Paste: `throw new Error("Test error")`
3. **Expected**: Red toast appears in top-right corner
4. Toast auto-dismisses after 10 seconds
5. Or click [✕] to dismiss immediately

### 5. Test Empty States
**Steps**:
1. Create a new session
2. **Expected**: See "No messages yet" with helpful hint
3. View shows icon, message, and guidance

---

## 🏗️ Components Reference

### ErrorBoundary
**Props**:
- `error`: The error to display (bindable)
- `retry`: Function to call on retry
- `context`: Error context ("message", "session", "general")
- `fullScreen`: Boolean for full-screen mode

**Example**:
```svelte
<ErrorBoundary
  bind:error={myError}
  retry={retryFunction}
  context="message"
/>
```

### LoadingState
**Props**:
- `message`: Primary loading message
- `submessage`: Secondary message (optional)
- `size`: "small" | "medium" | "large"
- `fullScreen`: Boolean for full-screen mode

**Example**:
```svelte
<LoadingState
  message="Loading..."
  submessage="Please wait"
  size="medium"
/>
```

---

## 🔄 Retry Utilities

### Basic Retry
```javascript
import { retryWithBackoff } from '../lib/utils/retry.js';

const result = await retryWithBackoff(
  () => invoke('my_command'),
  { maxRetries: 3 }
);
```

### Advanced Retry
```javascript
const result = await retryWithBackoff(
  () => invoke('my_command'),
  {
    maxRetries: 5,
    baseDelay: 2000,
    onRetry: (attempt, delay) => {
      console.log(`Attempt ${attempt}, waiting ${delay}ms`);
    }
  }
);
```

---

## 📋 Error Types Handled

| Error Type | Icon | Action | Context |
|------------|------|--------|---------|
| API Key Missing | 🔑 | Open Settings | API key validation |
| Network Error | 📡 | Retry | Connection issues |
| Transcription Failed | 🎤 | Try Again | Audio processing |
| Database Error | 💾 | Retry/Reload | Storage issues |
| Session Failed | 💬 | New Session | Session loading |
| Message Failed | ✉️ | Retry | Message sending |

---

## 🎨 UI States

### Loading States
- Session loading: Full-screen spinner
- Message sending: Typing indicator
- Data fetching: Inline spinner

### Error States
- Inline errors: Above input area
- Full-screen errors: Centered with backdrop
- Toast errors: Top-right corner

### Empty States
- No messages: Helpful icon and hint
- No session: Guidance to create one
- Empty search: "No results" message

---

## 🚀 Production Checklist

Before deploying to production, verify:

- [ ] Build passes: `npm run build`
- [ ] API key errors redirect to settings
- [ ] Network errors offer retry
- [ ] Message input preserved on error
- [ ] Global errors show toast
- [ ] Empty states display correctly
- [ ] Loading states show during operations
- [ ] Technical details collapsible
- [ ] All buttons have aria-labels
- [ ] Error messages are non-technical

---

## 📁 Files Changed

### New Files
- `src/lib/components/ErrorBoundary.svelte` (263 lines)
- `src/lib/components/LoadingState.svelte` (55 lines)
- `src/lib/utils/retry.js` (233 lines)

### Modified Files
- `src/lib/components/ChatView.svelte` (added error recovery)
- `src/components/ChatPanel.svelte` (added error recovery)
- `src/App.svelte` (global error handler, 75 lines added)

---

## 🐛 Troubleshooting

### Error boundary not showing
- Check `error` is not null
- Verify `context` prop is valid
- Check console for component errors

### Retry not working
- Verify `retry` function is provided
- Check network connectivity
- Review console for retry attempts

### Global toast not appearing
- Check browser console for errors
- Verify `globalError` state is set
- Check z-index conflicts

---

## 📞 Support

For questions or issues:
1. Check console for error messages
2. Review `ERROR_RECOVERY_UI_REPORT.md` for details
3. Open an issue on GitHub
4. Contact the development team

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
**Status**: Production Ready ✅
