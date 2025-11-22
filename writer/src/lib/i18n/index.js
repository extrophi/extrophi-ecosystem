/**
 * Internationalization (i18n) setup
 * Simple stub for BrainDump - defaults to English
 */

import { init, register, locale } from 'svelte-i18n';

// Register default locale
register('en', () => import('./locales/en.json'));

/**
 * Setup i18n with the specified language
 * @param {string} language - Language code (e.g., 'en', 'es', 'fr')
 */
export function setupI18n(language = 'en') {
  init({
    fallbackLocale: 'en',
    initialLocale: language,
  });

  locale.set(language);
}

/**
 * Set the current language
 * @param {string} language - Language code
 */
export function setLanguage(language) {
  locale.set(language);
}

/**
 * Available languages
 */
export const languages = [
  {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸'
  },
  {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸'
  },
  {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷'
  },
  {
    code: 'de',
    name: 'German',
    nativeName: 'Deutsch',
    flag: '🇩🇪'
  },
  {
    code: 'it',
    name: 'Italian',
    nativeName: 'Italiano',
    flag: '🇮🇹'
  },
  {
    code: 'pt',
    name: 'Portuguese',
    nativeName: 'Português',
    flag: '🇵🇹'
  },
  {
    code: 'ja',
    name: 'Japanese',
    nativeName: '日本語',
    flag: '🇯🇵'
  },
  {
    code: 'zh',
    name: 'Chinese',
    nativeName: '中文',
    flag: '🇨🇳'
  },
  {
    code: 'ko',
    name: 'Korean',
    nativeName: '한국어',
    flag: '🇰🇷'
  },
  {
    code: 'ru',
    name: 'Russian',
    nativeName: 'Русский',
    flag: '🇷🇺'
  }
];
