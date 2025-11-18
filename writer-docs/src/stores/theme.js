import { writable } from 'svelte/store';

// Theme store for dark mode toggle
export const theme = writable('light');

// Initialize theme from localStorage (in browser)
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('theme');
  if (stored) {
    theme.set(stored);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme.set('dark');
  }
}

// Subscribe to theme changes and update localStorage
if (typeof window !== 'undefined') {
  theme.subscribe(value => {
    localStorage.setItem('theme', value);
    document.documentElement.classList.toggle('dark', value === 'dark');
  });
}
