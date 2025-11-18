import { writable } from 'svelte/store';

export const toasts = writable([]);

export function showToast(message, type = 'error', duration = 5000) {
  const id = Date.now();
  toasts.update(t => [...t, { id, message, type }]);

  setTimeout(() => {
    toasts.update(t => t.filter(toast => toast.id !== id));
  }, duration);
}

export function showError(message) {
  showToast(message, 'error');
}

export function showSuccess(message) {
  showToast(message, 'success');
}

export function showInfo(message) {
  showToast(message, 'info');
}
