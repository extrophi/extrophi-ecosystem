/**
 * Vim-style keyboard shortcuts for Writer
 * Single-key navigation without modifiers
 */

import { writable, get } from 'svelte/store';

export type ShortcutMode = 'normal' | 'insert';

export interface KeyboardShortcut {
  key: string;
  description: string;
  handler: () => void;
}

/**
 * Current keyboard mode (normal or insert)
 */
export const keyboardMode = writable<ShortcutMode>('normal');

/**
 * Currently selected card index
 */
export const selectedCardIndex = writable<number>(0);

/**
 * Total number of cards
 */
export const totalCards = writable<number>(0);

/**
 * Show/hide keyboard shortcuts help overlay
 */
export const showShortcutsHelp = writable<boolean>(false);

/**
 * Callbacks for shortcut actions
 */
interface ShortcutCallbacks {
  onNavigateUp?: () => void;
  onNavigateDown?: () => void;
  onFocusSearch?: () => void;
  onNewCard?: () => void;
  onEditCard?: () => void;
  onDeleteCard?: () => void;
  onShowHelp?: () => void;
  onEscape?: () => void;
}

let callbacks: ShortcutCallbacks = {};

/**
 * Register callbacks for shortcut actions
 */
export function registerShortcutCallbacks(cbs: ShortcutCallbacks) {
  callbacks = { ...callbacks, ...cbs };
}

/**
 * Handle vim-style keyboard shortcuts
 */
export function handleVimShortcut(event: KeyboardEvent): boolean {
  const mode = get(keyboardMode);

  // Check if we're in an input field
  const target = event.target as HTMLElement;
  const isInputField = target.tagName === 'INPUT' ||
                       target.tagName === 'TEXTAREA' ||
                       target.contentEditable === 'true';

  // In insert mode, only Escape works
  if (mode === 'insert') {
    if (event.key === 'Escape') {
      keyboardMode.set('normal');
      callbacks.onEscape?.();
      return true;
    }
    return false;
  }

  // In normal mode, ignore shortcuts if typing in input fields
  // except for / and ? which can be triggered from anywhere
  if (isInputField && event.key !== '/' && event.key !== '?') {
    return false;
  }

  // Handle vim-style shortcuts in normal mode
  switch (event.key) {
    case 'j':
      // Navigate down
      event.preventDefault();
      callbacks.onNavigateDown?.();
      return true;

    case 'k':
      // Navigate up
      event.preventDefault();
      callbacks.onNavigateUp?.();
      return true;

    case '/':
      // Focus search
      event.preventDefault();
      keyboardMode.set('insert');
      callbacks.onFocusSearch?.();
      return true;

    case 'n':
      // New card
      event.preventDefault();
      callbacks.onNewCard?.();
      return true;

    case 'e':
      // Edit current card
      event.preventDefault();
      keyboardMode.set('insert');
      callbacks.onEditCard?.();
      return true;

    case 'd':
      // Delete current card
      event.preventDefault();
      callbacks.onDeleteCard?.();
      return true;

    case '?':
      // Show help overlay
      event.preventDefault();
      showShortcutsHelp.update(val => !val);
      callbacks.onShowHelp?.();
      return true;

    case 'Escape':
      // Exit mode / deselect
      event.preventDefault();
      keyboardMode.set('normal');
      callbacks.onEscape?.();
      return true;

    default:
      return false;
  }
}

/**
 * Initialize vim-style keyboard shortcuts
 */
export function initVimShortcuts() {
  const handleKeydown = (event: KeyboardEvent) => {
    handleVimShortcut(event);
  };

  window.addEventListener('keydown', handleKeydown);

  return () => {
    window.removeEventListener('keydown', handleKeydown);
  };
}

/**
 * Get all available shortcuts with descriptions
 */
export function getShortcuts(): KeyboardShortcut[] {
  return [
    { key: 'j', description: 'Navigate to next card', handler: () => callbacks.onNavigateDown?.() },
    { key: 'k', description: 'Navigate to previous card', handler: () => callbacks.onNavigateUp?.() },
    { key: '/', description: 'Focus search', handler: () => callbacks.onFocusSearch?.() },
    { key: 'n', description: 'Create new card', handler: () => callbacks.onNewCard?.() },
    { key: 'e', description: 'Edit current card', handler: () => callbacks.onEditCard?.() },
    { key: 'd', description: 'Delete current card', handler: () => callbacks.onDeleteCard?.() },
    { key: '?', description: 'Show this help', handler: () => showShortcutsHelp.update(v => !v) },
    { key: 'Esc', description: 'Exit mode / deselect', handler: () => callbacks.onEscape?.() },
  ];
}

/**
 * Navigate to the next card
 */
export function navigateDown() {
  const current = get(selectedCardIndex);
  const total = get(totalCards);

  if (current < total - 1) {
    selectedCardIndex.set(current + 1);
  }
}

/**
 * Navigate to the previous card
 */
export function navigateUp() {
  const current = get(selectedCardIndex);

  if (current > 0) {
    selectedCardIndex.set(current - 1);
  }
}
