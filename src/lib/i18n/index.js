/**
 * i18n Configuration for BrainDump v3.0
 *
 * Supports 5 languages: English, Spanish, French, German, Japanese
 * Uses svelte-i18n library for lightweight, Svelte-native internationalization
 *
 * RTL support prepared for future Arabic/Hebrew support
 */

import { register, init, getLocaleFromNavigator, locale } from 'svelte-i18n';

// Register all available locales
register('en', () => import('./locales/en.json'));
register('es', () => import('./locales/es.json'));
register('fr', () => import('./locales/fr.json'));
register('de', () => import('./locales/de.json'));
register('ja', () => import('./locales/ja.json'));

// Supported languages configuration
export const languages = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' }
];

/**
 * Initialize i18n with fallback to browser language or English
 * @param {string} initialLocale - Optional initial locale to use
 */
export function setupI18n(initialLocale = null) {
  init({
    fallbackLocale: 'en',
    initialLocale: initialLocale || getLocaleFromNavigator(),
    loadingDelay: 200,
  });
}

/**
 * Change the current locale
 * @param {string} newLocale - The locale code to switch to
 */
export function setLocale(newLocale) {
  locale.set(newLocale);
}

/**
 * Get the current locale
 * @returns {string} Current locale code
 */
export function getCurrentLocale() {
  let currentLocale;
  locale.subscribe(value => currentLocale = value)();
  return currentLocale;
}

/**
 * Check if a locale is RTL (Right-to-Left)
 * Prepared for future Arabic/Hebrew support
 * @param {string} localeCode - The locale code to check
 * @returns {boolean} True if RTL
 */
export function isRTL(localeCode) {
  const rtlLocales = ['ar', 'he', 'fa', 'ur'];
  return rtlLocales.includes(localeCode);
}
