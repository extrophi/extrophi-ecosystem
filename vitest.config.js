import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte({ hot: !process.env.VITEST })],
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{js,ts}'],
    // Svelte 5 component testing setup
    setupFiles: ['./src/tests/setup.js'],
    // Enable CSS processing for component tests
    css: true,
    // Better output for CI/CD
    reporters: ['verbose'],
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src-tauri/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/tests/**',
      ],
    },
  },
  resolve: {
    conditions: ['browser'],
  },
});
