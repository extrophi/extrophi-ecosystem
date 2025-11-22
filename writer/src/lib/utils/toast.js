/**
 * Toast notification utility
 * Simple notification system for user feedback
 */

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {object} options - Toast options
 * @param {string} options.type - Toast type: 'success', 'error', 'info', 'warning'
 * @param {number} options.duration - Duration in milliseconds (default: 3000)
 */
export function showToast(message, options = {}) {
  const {
    type = 'info',
    duration = 3000
  } = options;

  // Dispatch custom event for toast notification
  // A ToastContainer component would listen for this event
  const event = new CustomEvent('show-toast', {
    detail: {
      message,
      type,
      duration
    }
  });

  window.dispatchEvent(event);

  // Console log as fallback
  const emoji = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }[type] || 'ℹ️';

  console.log(`${emoji} ${message}`);
}

/**
 * Show success toast
 * @param {string} message - Message to display
 */
export function showSuccess(message) {
  showToast(message, { type: 'success' });
}

/**
 * Show error toast
 * @param {string} message - Message to display
 */
export function showError(message) {
  showToast(message, { type: 'error', duration: 5000 });
}

/**
 * Show warning toast
 * @param {string} message - Message to display
 */
export function showWarning(message) {
  showToast(message, { type: 'warning', duration: 4000 });
}

/**
 * Show info toast
 * @param {string} message - Message to display
 */
export function showInfo(message) {
  showToast(message, { type: 'info' });
}
