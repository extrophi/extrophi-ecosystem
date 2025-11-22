/**
 * Retry utility with exponential backoff
 * Provides resilient error handling for API calls and async operations
 */

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if an error is retryable
 * @param {Error|string|object} error - Error to check
 * @returns {boolean}
 */
export function isRetryableError(error) {
  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  // Timeout errors
  if (error.message && error.message.toLowerCase().includes('timeout')) {
    return true;
  }

  // Rate limit errors
  if (error.message && error.message.toLowerCase().includes('rate limit')) {
    return true;
  }

  // Server errors (5xx)
  if (error.status && error.status >= 500 && error.status < 600) {
    return true;
  }

  // Connection errors
  if (error.message && (
    error.message.includes('ECONNREFUSED') ||
    error.message.includes('ENOTFOUND') ||
    error.message.includes('ETIMEDOUT')
  )) {
    return true;
  }

  // Tauri-specific retryable errors
  if (typeof error === 'object' && error.type) {
    const retryableTypes = ['Network', 'Timeout', 'ConnectionFailed'];
    return retryableTypes.includes(error.type);
  }

  return false;
}

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Async function to retry
 * @param {Object} options - Retry options
 * @param {number} options.maxRetries - Maximum number of retry attempts (default: 3)
 * @param {number} options.initialDelay - Initial delay in ms (default: 1000)
 * @param {number} options.maxDelay - Maximum delay in ms (default: 10000)
 * @param {number} options.backoffFactor - Exponential backoff multiplier (default: 2)
 * @param {Function} options.shouldRetry - Custom function to determine if error is retryable
 * @param {Function} options.onRetry - Callback called before each retry
 * @returns {Promise<any>} - Result of the function
 * @throws {Error} - Last error if all retries fail
 */
export async function retryWithBackoff(fn, options = {}) {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
    shouldRetry = isRetryableError,
    onRetry = null
  } = options;

  let lastError;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if this is the last attempt
      if (attempt === maxRetries) {
        break;
      }

      // Check if error is retryable
      if (!shouldRetry(error)) {
        throw error;
      }

      // Call onRetry callback if provided
      if (onRetry) {
        onRetry(attempt + 1, error);
      }

      console.warn(`Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms. Error:`, error);

      // Wait before retrying
      await sleep(delay);

      // Exponential backoff with max delay cap
      delay = Math.min(delay * backoffFactor, maxDelay);
    }
  }

  // All retries failed
  throw lastError;
}

/**
 * Create a retryable version of an async function
 * @param {Function} fn - Async function to make retryable
 * @param {Object} options - Retry options (same as retryWithBackoff)
 * @returns {Function} - Wrapped function with retry logic
 */
export function withRetry(fn, options = {}) {
  return async (...args) => {
    return retryWithBackoff(() => fn(...args), options);
  };
}

/**
 * Retry with jittered exponential backoff
 * Adds randomness to prevent thundering herd problem
 * @param {Function} fn - Async function to retry
 * @param {Object} options - Retry options (same as retryWithBackoff)
 * @returns {Promise<any>}
 */
export async function retryWithJitter(fn, options = {}) {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
    shouldRetry = isRetryableError,
    onRetry = null
  } = options;

  let lastError;
  let baseDelay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt === maxRetries || !shouldRetry(error)) {
        break;
      }

      if (onRetry) {
        onRetry(attempt + 1, error);
      }

      // Add jitter: random delay between 0 and baseDelay
      const jitteredDelay = Math.min(
        Math.random() * baseDelay,
        maxDelay
      );

      console.warn(`Retry attempt ${attempt + 1}/${maxRetries} after ${jitteredDelay.toFixed(0)}ms (jittered). Error:`, error);

      await sleep(jitteredDelay);

      baseDelay = Math.min(baseDelay * backoffFactor, maxDelay);
    }
  }

  throw lastError;
}

/**
 * Circuit breaker pattern
 * Prevents repeated calls to a failing service
 */
export class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000; // 1 minute
    this.state = 'closed'; // closed, open, half-open
    this.failures = 0;
    this.lastFailureTime = null;
  }

  async execute(fn) {
    if (this.state === 'open') {
      // Check if we should try half-open
      if (Date.now() - this.lastFailureTime >= this.resetTimeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();

      // Success - reset circuit breaker
      if (this.state === 'half-open') {
        this.state = 'closed';
        this.failures = 0;
      }

      return result;
    } catch (error) {
      this.failures++;
      this.lastFailureTime = Date.now();

      if (this.failures >= this.failureThreshold) {
        this.state = 'open';
        console.error(`Circuit breaker opened after ${this.failures} failures`);
      }

      throw error;
    }
  }

  reset() {
    this.state = 'closed';
    this.failures = 0;
    this.lastFailureTime = null;
  }
}
