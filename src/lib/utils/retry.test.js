import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  sleep,
  retry,
  isRetryableError,
  withTimeout,
  CircuitBreaker,
} from './retry.js';

describe('retry utilities', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('sleep', () => {
    it('should resolve after specified milliseconds', async () => {
      const promise = sleep(1000);
      vi.advanceTimersByTime(1000);
      await expect(promise).resolves.toBeUndefined();
    });
  });

  describe('retry', () => {
    it('should return result on first success', async () => {
      const operation = vi.fn().mockResolvedValue('success');
      const result = await retry(operation, 3, 100);
      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(1);
    });

    it('should retry on failure', async () => {
      const operation = vi
        .fn()
        .mockRejectedValueOnce(new Error('fail'))
        .mockResolvedValue('success');

      const promise = retry(operation, 3, 100);
      await vi.advanceTimersByTimeAsync(100);
      const result = await promise;

      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(2);
    });

    it('should throw after max retries', async () => {
      // Use real timers for this test to avoid unhandled rejection issues
      vi.useRealTimers();

      const error = new Error('persistent error');
      const operation = vi.fn().mockRejectedValue(error);

      // Use very short delay for fast test execution
      await expect(retry(operation, 2, 1)).rejects.toThrow('persistent error');
      expect(operation).toHaveBeenCalledTimes(3); // initial + 2 retries

      // Restore fake timers for subsequent tests
      vi.useFakeTimers();
    });
  });

  describe('isRetryableError', () => {
    it('should return true for network errors', () => {
      expect(isRetryableError(new Error('Network error'))).toBe(true);
      expect(isRetryableError('ECONNREFUSED')).toBe(true);
    });

    it('should return true for timeout errors', () => {
      expect(isRetryableError(new Error('Request timeout'))).toBe(true);
    });

    it('should return true for rate limit errors', () => {
      expect(isRetryableError(new Error('rate limit exceeded'))).toBe(true);
      expect(isRetryableError('429')).toBe(true);
    });

    it('should return false for auth errors', () => {
      expect(isRetryableError(new Error('API key invalid'))).toBe(false);
      expect(isRetryableError('401')).toBe(false);
      expect(isRetryableError('403')).toBe(false);
    });

    it('should return false for unknown errors', () => {
      expect(isRetryableError(new Error('Unknown error'))).toBe(false);
    });
  });

  describe('withTimeout', () => {
    it('should return result if operation completes in time', async () => {
      const operation = vi.fn().mockResolvedValue('result');
      const result = await withTimeout(operation, 1000);
      expect(result).toBe('result');
    });

    it('should throw timeout error if operation exceeds timeout', async () => {
      const operation = () => new Promise(resolve => setTimeout(resolve, 2000));
      const promise = withTimeout(operation, 1000);

      vi.advanceTimersByTime(1000);

      await expect(promise).rejects.toThrow('Operation timed out after 1000ms');
    });
  });

  describe('CircuitBreaker', () => {
    it('should execute operation when circuit is closed', async () => {
      const breaker = new CircuitBreaker();
      const operation = vi.fn().mockResolvedValue('result');

      const result = await breaker.execute(operation);

      expect(result).toBe('result');
      expect(breaker.state).toBe('CLOSED');
    });

    it('should open circuit after threshold failures', async () => {
      const breaker = new CircuitBreaker({ failureThreshold: 2 });
      const operation = vi.fn().mockRejectedValue(new Error('fail'));

      try { await breaker.execute(operation); } catch {}
      expect(breaker.state).toBe('CLOSED');

      try { await breaker.execute(operation); } catch {}
      expect(breaker.state).toBe('OPEN');
    });

    it('should reject immediately when circuit is open', async () => {
      const breaker = new CircuitBreaker({ failureThreshold: 1, resetTimeout: 60000 });
      const operation = vi.fn().mockRejectedValue(new Error('fail'));

      try { await breaker.execute(operation); } catch {}

      await expect(breaker.execute(operation)).rejects.toThrow('Circuit breaker is OPEN');
      expect(operation).toHaveBeenCalledTimes(1); // Not called again
    });

    it('should reset state on success', async () => {
      const breaker = new CircuitBreaker();
      breaker.failures = 3;

      const operation = vi.fn().mockResolvedValue('success');
      await breaker.execute(operation);

      expect(breaker.failures).toBe(0);
      expect(breaker.state).toBe('CLOSED');
    });
  });
});
