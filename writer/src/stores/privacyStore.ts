/**
 * Privacy Store
 * Svelte 5 runes-based state management for privacy scanner
 *
 * Manages:
 * - Current privacy level classification
 * - Privacy matches found in content
 * - Scan performance metrics
 */

import { writable, derived, type Writable } from 'svelte/store';
import {
  scanText,
  classifyText,
  getMatchCountsByLevel,
  type PrivacyLevel,
  type PrivacyMatch
} from '../lib/privacy-rules';

/**
 * Store state interface
 */
interface PrivacyState {
  content: string;
  matches: PrivacyMatch[];
  level: PrivacyLevel;
  scanTime: number; // milliseconds
  lastScanned: Date | null;
}

/**
 * Create a privacy store instance
 * Uses Svelte 5 compatible store pattern
 *
 * @param initialContent - Initial content to scan
 * @returns Privacy store with helper methods
 */
export function createPrivacyStore(initialContent: string = '') {
  // Base state
  const state: Writable<PrivacyState> = writable({
    content: initialContent,
    matches: [],
    level: 'IDEAS',
    scanTime: 0,
    lastScanned: null
  });

  /**
   * Scan content and update state
   * Measures performance and updates all derived values
   *
   * @param content - Text content to scan
   */
  function scan(content: string): void {
    const startTime = performance.now();

    const matches = scanText(content);
    const level = classifyText(content);

    const endTime = performance.now();
    const scanTime = endTime - startTime;

    state.set({
      content,
      matches,
      level,
      scanTime,
      lastScanned: new Date()
    });
  }

  /**
   * Update content and trigger scan
   * Debounced externally by component
   *
   * @param content - New content
   */
  function setContent(content: string): void {
    scan(content);
  }

  /**
   * Clear all state
   */
  function clear(): void {
    state.set({
      content: '',
      matches: [],
      level: 'IDEAS',
      scanTime: 0,
      lastScanned: null
    });
  }

  /**
   * Get counts by privacy level
   */
  function getCounts() {
    let counts: Record<PrivacyLevel, number> = {
      PRIVATE: 0,
      PERSONAL: 0,
      BUSINESS: 0,
      IDEAS: 0
    };

    state.subscribe(s => {
      counts = getMatchCountsByLevel(s.matches);
    })();

    return counts;
  }

  return {
    subscribe: state.subscribe,
    scan,
    setContent,
    clear,
    getCounts
  };
}

/**
 * Global privacy store instance
 * Can be imported and used across components
 */
export const privacyStore = createPrivacyStore();

/**
 * Derived store: matches by level
 */
export const matchesByLevel = derived(
  privacyStore,
  $store => ({
    PRIVATE: $store.matches.filter(m => m.level === 'PRIVATE'),
    PERSONAL: $store.matches.filter(m => m.level === 'PERSONAL'),
    BUSINESS: $store.matches.filter(m => m.level === 'BUSINESS'),
    IDEAS: [] as PrivacyMatch[]
  })
);

/**
 * Derived store: match counts
 */
export const matchCounts = derived(
  privacyStore,
  $store => getMatchCountsByLevel($store.matches)
);

/**
 * Derived store: current privacy level
 */
export const currentLevel = derived(
  privacyStore,
  $store => $store.level
);

/**
 * Derived store: has privacy issues
 */
export const hasPrivacyIssues = derived(
  privacyStore,
  $store => $store.matches.length > 0
);

/**
 * Derived store: performance status
 */
export const performanceStatus = derived(
  privacyStore,
  $store => ({
    scanTime: $store.scanTime,
    isWithinTarget: $store.scanTime < 50, // 50ms target
    lastScanned: $store.lastScanned
  })
);
