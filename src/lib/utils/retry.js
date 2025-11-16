/**
 * Retry utility functions with exponential backoff
 */

/**
 * Retries an async operation with exponential backoff
 * @param {Function} operation - The async function to retry
 * @param {Object} [options] - Retry options
 * @param {number} [options.maxRetries=3] - Maximum number of retry attempts
 * @param {number} [options.baseDelay=1000] - Base delay in milliseconds
 * @param {number} [options.maxDelay=10000] - Maximum delay in milliseconds
 * @param {Function} [options.onRetry] - Callback function called before each retry
 * @param {Function} [options.shouldRetry] - Function to determine if error is retryable (default: always retry)
 * @returns {Promise} - Result of the operation
 */
export async function retryWithBackoff(operation, options = {}) {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    onRetry = null,
    shouldRetry = () => true
  } = options;

  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      // If this was the last attempt, throw the error
      if (attempt === maxRetries) {
        throw error;
      }

      // Check if the error is retryable
      if (!shouldRetry(error, attempt)) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const exponentialDelay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);

      // Add jitter to prevent thundering herd
      const jitter = Math.random() * 0.3 * exponentialDelay;
      const delay = exponentialDelay + jitter;

      // Call onRetry callback if provided
      if (onRetry) {
        onRetry(attempt + 1, delay, error);
      }

      console.log(`Retry attempt ${attempt + 1}/${maxRetries} after ${Math.round(delay)}ms`);

      // Wait before retrying
      await sleep(delay);
    }
  }

  throw lastError;
}

/**
 * Simple retry without backoff
 * @param {Function} operation - The async function to retry
 * @param {number} retries - Number of retry attempts
 * @param {number} delay - Delay between retries in milliseconds
 * @returns {Promise} - Result of the operation
 */
export async function retry(operation, retries = 3, delay = 1000) {
  for (let i = 0; i <= retries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === retries) {
        throw error;
      }
      await sleep(delay);
    }
  }
}

/**
 * Helper function to sleep for a given duration
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} - Promise that resolves after the delay
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Determines if an error is retryable
 * @param {Error|string} error - The error to check
 * @returns {boolean} - True if the error is retryable
 */
export function isRetryableError(error) {
  const errorStr = typeof error === 'string' ? error : error?.message || JSON.stringify(error);

  // Network errors are retryable
  if (errorStr.includes('Network') || errorStr.includes('ECONNREFUSED') || errorStr.includes('fetch')) {
    return true;
  }

  // Timeout errors are retryable
  if (errorStr.includes('timeout') || errorStr.includes('Timeout')) {
    return true;
  }

  // Rate limit errors are retryable
  if (errorStr.includes('rate limit') || errorStr.includes('429')) {
    return true;
  }

  // Service unavailable errors are retryable
  if (errorStr.includes('503') || errorStr.includes('Service Unavailable')) {
    return true;
  }

  // API key errors are NOT retryable
  if (errorStr.includes('API key') || errorStr.includes('401') || errorStr.includes('403')) {
    return false;
  }

  // Database locked errors might be retryable
  if (errorStr.includes('Locked') || errorStr.includes('locked')) {
    return true;
  }

  // Default to not retryable for unknown errors
  return false;
}

/**
 * Creates a retryable version of a function
 * @param {Function} fn - The function to make retryable
 * @param {Object} options - Retry options
 * @returns {Function} - Retryable version of the function
 */
export function makeRetryable(fn, options = {}) {
  return async function(...args) {
    return retryWithBackoff(() => fn(...args), {
      ...options,
      shouldRetry: options.shouldRetry || isRetryableError
    });
  };
}

/**
 * Wraps an async operation with a timeout
 * @param {Function} operation - The async function to wrap
 * @param {number} timeoutMs - Timeout in milliseconds
 * @returns {Promise} - Result of the operation or timeout error
 */
export async function withTimeout(operation, timeoutMs) {
  return Promise.race([
    operation(),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs)
    )
  ]);
}

/**
 * Circuit breaker pattern to prevent cascading failures
 */
export class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000; // 1 minute
    this.failures = 0;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = Date.now();
  }

  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failures++;
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.resetTimeout;
    }
  }

  reset() {
    this.failures = 0;
    this.state = 'CLOSED';
    this.nextAttempt = Date.now();
  }
}
