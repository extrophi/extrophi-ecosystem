/**
 * Editor utility functions and actions
 */

import { invoke } from '@tauri-apps/api/core';

export interface SaveMessageParams {
  sessionId: number;
  role: 'user' | 'assistant';
  content: string;
  recordingId?: number | null;
}

export interface SaveMessageResult {
  id: number;
  session_id: number;
  role: string;
  content: string;
  privacy_tags: string[] | null;
  created_at: string;
}

/**
 * Save a message to the database via Tauri backend
 */
export async function saveMessage(params: SaveMessageParams): Promise<SaveMessageResult> {
  try {
    const result = await invoke<SaveMessageResult>('save_message', {
      sessionId: params.sessionId,
      role: params.role,
      content: params.content,
      recordingId: params.recordingId || null,
    });
    return result;
  } catch (error) {
    console.error('Failed to save message:', error);
    throw error;
  }
}

/**
 * Get keyboard shortcut key for current platform
 * Returns 'Cmd' on Mac, 'Ctrl' on other platforms
 */
export function getModifierKey(): string {
  const platform = navigator.platform.toLowerCase();
  return platform.includes('mac') ? 'Cmd' : 'Ctrl';
}

/**
 * Format keyboard shortcut text for display
 */
export function formatShortcut(key: string): string {
  const modifier = getModifierKey();
  return `${modifier}+${key}`;
}

/**
 * Detect if user is on Mac
 */
export function isMac(): boolean {
  return navigator.platform.toLowerCase().includes('mac');
}

/**
 * Format date/time for save status display
 */
export function formatSaveTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Less than 1 minute
  if (diff < 60000) {
    return 'Just now';
  }

  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000);
    return `${minutes} min${minutes !== 1 ? 's' : ''} ago`;
  }

  // Show time
  return date.toLocaleTimeString();
}

/**
 * Validate session ID
 */
export function isValidSessionId(sessionId: string | number): boolean {
  const id = typeof sessionId === 'string' ? parseInt(sessionId) : sessionId;
  return !isNaN(id) && id > 0;
}

/**
 * Extract text from CodeMirror EditorView
 */
export function getEditorText(editorView: any): string {
  if (!editorView || !editorView.state) {
    return '';
  }
  return editorView.state.doc.toString();
}

/**
 * Set text in CodeMirror EditorView
 */
export function setEditorText(editorView: any, text: string): void {
  if (!editorView || !editorView.state) {
    return;
  }

  const transaction = editorView.state.update({
    changes: {
      from: 0,
      to: editorView.state.doc.length,
      insert: text,
    },
  });

  editorView.dispatch(transaction);
}
