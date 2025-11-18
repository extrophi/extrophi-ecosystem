// Vitest setup file for Svelte 5 component testing
import '@testing-library/svelte/vitest';

// Global test utilities
import { vi, afterEach } from 'vitest';

// Mock Tauri API for tests
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

// Clean up after each test
afterEach(() => {
  vi.clearAllMocks();
});
