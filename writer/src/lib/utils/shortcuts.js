/**
 * Keyboard shortcuts configuration
 */

export const shortcuts = {
  // Global shortcuts
  record: { key: 'r', mod: true }, // Cmd/Ctrl+R
  settings: { key: ',', mod: true }, // Cmd/Ctrl+,
  help: { key: '?', mod: true }, // Cmd/Ctrl+?
  search: { key: 'f', mod: true }, // Cmd/Ctrl+F
  export: { key: 'e', mod: true }, // Cmd/Ctrl+E
  newSession: { key: 'n', mod: true }, // Cmd/Ctrl+N
  terminal: { key: '`', ctrl: true }, // Ctrl+`

  // View shortcuts
  chatView: { key: '1', mod: true }, // Cmd/Ctrl+1
  transcriptView: { key: '2', mod: true }, // Cmd/Ctrl+2
  promptsView: { key: '3', mod: true }, // Cmd/Ctrl+3
  privacyView: { key: 'p', mod: true, shift: true }, // Cmd/Ctrl+Shift+P
};

/**
 * Check if a keyboard event matches a shortcut
 * @param {KeyboardEvent} event
 * @param {Object} shortcut
 * @returns {boolean}
 */
export function matchesShortcut(event, shortcut) {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const modKey = isMac ? event.metaKey : event.ctrlKey;

  // Handle mod key (Cmd on Mac, Ctrl on Windows/Linux)
  if (shortcut.mod && !modKey) return false;

  // Handle explicit Ctrl requirement (for Ctrl+` which should be Ctrl on all platforms)
  if (shortcut.ctrl && !event.ctrlKey) return false;

  // Handle shift key
  if (shortcut.shift && !event.shiftKey) return false;
  if (!shortcut.shift && event.shiftKey && shortcut.key !== '?') return false;

  // Check if key matches
  return event.key.toLowerCase() === shortcut.key.toLowerCase();
}
