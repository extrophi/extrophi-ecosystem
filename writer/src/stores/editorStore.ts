/**
 * Editor state management
 * Manages editor preferences and shared state
 */

import { writable, derived, type Writable, type Readable } from 'svelte/store';

export interface EditorPreferences {
  vimModeEnabled: boolean;
  autoSaveEnabled: boolean;
  autoSaveDelay: number; // milliseconds
  showPrivacyWarnings: boolean;
  fontSize: number;
  fontFamily: string;
  theme: 'light' | 'dark';
}

export interface EditorSession {
  sessionId: string;
  content: string;
  lastModified: Date;
  isSaving: boolean;
  lastSaved: Date | null;
}

// Default preferences
const DEFAULT_PREFERENCES: EditorPreferences = {
  vimModeEnabled: true,
  autoSaveEnabled: true,
  autoSaveDelay: 500,
  showPrivacyWarnings: true,
  fontSize: 14,
  fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", "Consolas", monospace',
  theme: 'light',
};

// Editor preferences store
export const editorPreferences: Writable<EditorPreferences> = writable(DEFAULT_PREFERENCES);

// Active editor sessions
export const editorSessions: Writable<Map<string, EditorSession>> = writable(new Map());

/**
 * Load preferences from localStorage
 */
export function loadPreferences(): void {
  if (typeof window === 'undefined') return;

  try {
    const stored = localStorage.getItem('editor-preferences');
    if (stored) {
      const parsed = JSON.parse(stored);
      editorPreferences.set({ ...DEFAULT_PREFERENCES, ...parsed });
    }
  } catch (error) {
    console.error('Failed to load editor preferences:', error);
  }
}

/**
 * Save preferences to localStorage
 */
export function savePreferences(prefs: EditorPreferences): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem('editor-preferences', JSON.stringify(prefs));
    editorPreferences.set(prefs);
  } catch (error) {
    console.error('Failed to save editor preferences:', error);
  }
}

/**
 * Toggle vim mode
 */
export function toggleVimMode(): void {
  editorPreferences.update(prefs => ({
    ...prefs,
    vimModeEnabled: !prefs.vimModeEnabled,
  }));
}

/**
 * Update font size
 */
export function setFontSize(size: number): void {
  editorPreferences.update(prefs => ({
    ...prefs,
    fontSize: Math.max(10, Math.min(24, size)),
  }));
}

/**
 * Update auto-save delay
 */
export function setAutoSaveDelay(delay: number): void {
  editorPreferences.update(prefs => ({
    ...prefs,
    autoSaveDelay: Math.max(100, Math.min(5000, delay)),
  }));
}

/**
 * Get or create editor session
 */
export function getOrCreateSession(sessionId: string, initialContent: string = ''): EditorSession {
  let session: EditorSession | undefined;

  editorSessions.update(sessions => {
    session = sessions.get(sessionId);

    if (!session) {
      session = {
        sessionId,
        content: initialContent,
        lastModified: new Date(),
        isSaving: false,
        lastSaved: null,
      };
      sessions.set(sessionId, session);
    }

    return sessions;
  });

  return session!;
}

/**
 * Update session content
 */
export function updateSessionContent(sessionId: string, content: string): void {
  editorSessions.update(sessions => {
    const session = sessions.get(sessionId);
    if (session) {
      session.content = content;
      session.lastModified = new Date();
    }
    return sessions;
  });
}

/**
 * Mark session as saving
 */
export function markSessionSaving(sessionId: string, isSaving: boolean): void {
  editorSessions.update(sessions => {
    const session = sessions.get(sessionId);
    if (session) {
      session.isSaving = isSaving;
      if (!isSaving) {
        session.lastSaved = new Date();
      }
    }
    return sessions;
  });
}

/**
 * Remove session
 */
export function removeSession(sessionId: string): void {
  editorSessions.update(sessions => {
    sessions.delete(sessionId);
    return sessions;
  });
}

/**
 * Clear all sessions
 */
export function clearAllSessions(): void {
  editorSessions.set(new Map());
}

// Derived store: is vim mode enabled
export const isVimModeEnabled: Readable<boolean> = derived(
  editorPreferences,
  $prefs => $prefs.vimModeEnabled
);

// Derived store: auto-save delay
export const autoSaveDelay: Readable<number> = derived(
  editorPreferences,
  $prefs => $prefs.autoSaveDelay
);

// Initialize preferences on module load
if (typeof window !== 'undefined') {
  loadPreferences();

  // Save preferences when they change
  editorPreferences.subscribe(prefs => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('editor-preferences', JSON.stringify(prefs));
    }
  });
}
