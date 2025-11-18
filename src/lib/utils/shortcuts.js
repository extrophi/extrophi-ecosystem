/**
 * Keyboard Shortcuts Manager
 * Defines global and context-specific keyboard shortcuts for the app
 */

/**
 * Global keyboard shortcuts configuration
 * Each shortcut has a key, modifiers array, and description
 */
export const shortcuts = {
  // Global actions
  record: {
    key: 'r',
    modifiers: ['cmd', 'ctrl'],
    description: 'Start/stop recording',
    action: 'toggle_recording'
  },
  settings: {
    key: ',',
    modifiers: ['cmd', 'ctrl'],
    description: 'Open settings',
    action: 'open_settings'
  },
  search: {
    key: 'f',
    modifiers: ['cmd', 'ctrl'],
    description: 'Focus search box',
    action: 'focus_search'
  },
  export: {
    key: 'e',
    modifiers: ['cmd', 'ctrl'],
    description: 'Export current session',
    action: 'export_session'
  },
  newSession: {
    key: 'n',
    modifiers: ['cmd', 'ctrl'],
    description: 'Create new chat session',
    action: 'new_session'
  },
  help: {
    key: '?',
    modifiers: ['cmd', 'ctrl'],
    description: 'Show keyboard shortcuts',
    action: 'show_help'
  },

  // View switching
  chatView: {
    key: '1',
    modifiers: ['cmd', 'ctrl'],
    description: 'Switch to Chat view',
    action: 'switch_chat'
  },
  transcriptView: {
    key: '2',
    modifiers: ['cmd', 'ctrl'],
    description: 'Switch to Transcript view',
    action: 'switch_transcript'
  },
  promptsView: {
    key: '3',
    modifiers: ['cmd', 'ctrl'],
    description: 'Switch to Prompts view',
    action: 'switch_prompts'
  },
  privacyView: {
    key: '4',
    modifiers: ['cmd', 'ctrl'],
    description: 'Toggle Privacy panel',
    action: 'toggle_privacy'
  }
};

/**
 * Context-specific shortcuts (not requiring modifiers)
 * These are documented for the help modal but handled in specific components
 */
export const contextShortcuts = {
  chat: [
    { key: 'Enter', description: 'Send message' },
    { key: 'Shift+Enter', description: 'New line in message' },
    { key: 'Escape', description: 'Clear message input' }
  ],
  sessions: [
    { key: '↑/↓', description: 'Navigate sessions list' },
    { key: 'Enter', description: 'Select session' }
  ],
  general: [
    { key: 'Tab', description: 'Navigate between elements' },
    { key: 'Escape', description: 'Close modals/panels' }
  ]
};

/**
 * Checks if a keyboard event matches a shortcut definition
 * @param {KeyboardEvent} event - The keyboard event to check
 * @param {Object} shortcut - The shortcut definition to match against
 * @returns {boolean} - True if the event matches the shortcut
 */
export function matchesShortcut(event, shortcut) {
  // Check if the key matches (case-insensitive)
  const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
  if (!keyMatches) return false;

  // Check if at least one of the required modifiers is pressed
  const hasModifier = shortcut.modifiers.some(mod => {
    switch (mod) {
      case 'cmd':
        return event.metaKey; // Command key on Mac
      case 'ctrl':
        return event.ctrlKey; // Control key on Windows/Linux
      case 'shift':
        return event.shiftKey;
      case 'alt':
        return event.altKey;
      default:
        return false;
    }
  });

  return hasModifier;
}

/**
 * Returns the display name for a modifier key based on the platform
 * @param {string} modifier - The modifier name (cmd, ctrl, shift, alt)
 * @returns {string} - Platform-appropriate display name
 */
export function getModifierDisplay(modifier) {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  switch (modifier) {
    case 'cmd':
      return isMac ? '⌘' : 'Ctrl';
    case 'ctrl':
      return isMac ? '⌘' : 'Ctrl';
    case 'shift':
      return '⇧';
    case 'alt':
      return isMac ? '⌥' : 'Alt';
    default:
      return modifier;
  }
}

/**
 * Formats a shortcut for display
 * @param {Object} shortcut - The shortcut definition
 * @returns {string} - Formatted shortcut string (e.g., "⌘+R" or "Ctrl+R")
 */
export function formatShortcut(shortcut) {
  const modifier = getModifierDisplay(shortcut.modifiers[0]);
  const key = shortcut.key.toUpperCase();
  return `${modifier}+${key}`;
}

/**
 * Formats a simple key combination for display
 * @param {string} keys - The key combination (e.g., "Shift+Enter")
 * @returns {string} - Formatted key combination
 */
export function formatKeys(keys) {
  return keys.split('+').map(k => {
    if (k.toLowerCase() === 'shift') return '⇧';
    if (k.toLowerCase() === 'enter') return '↵';
    if (k.toLowerCase() === 'escape') return 'Esc';
    if (k.toLowerCase() === 'tab') return '⇥';
    return k;
  }).join('+');
}
