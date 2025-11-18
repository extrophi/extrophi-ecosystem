import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  integrations: [
    svelte(),
    tailwind()
  ],
  // Enable Svelte 5 runes mode
  vite: {
    optimizeDeps: {
      exclude: ['svelte']
    }
  }
});
