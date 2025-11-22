/**
 * Privacy Scanner
 * Adapter for privacy-rules.ts that provides the interface expected by App.svelte
 */

import { scanText as scanTextFromRules, type PrivacyMatch, type PrivacyLevel } from './privacy-rules';

export interface PrivacyScanMatch {
  type: string;
  value: string;
  start: number;
  end: number;
  severity: 'danger' | 'caution' | 'info';
  description: string;
}

/**
 * Map privacy levels to severity levels
 */
function mapLevelToSeverity(level: PrivacyLevel): 'danger' | 'caution' | 'info' {
  switch (level) {
    case 'PRIVATE':
      return 'danger';
    case 'PERSONAL':
    case 'BUSINESS':
      return 'caution';
    case 'IDEAS':
    default:
      return 'info';
  }
}

/**
 * Scan text for privacy issues
 * Returns matches with severity levels
 */
export function scanText(text: string): PrivacyScanMatch[] {
  const matches = scanTextFromRules(text);

  return matches.map(match => ({
    type: match.type,
    value: match.value,
    start: match.start,
    end: match.end,
    severity: mapLevelToSeverity(match.level),
    description: match.description
  }));
}

/**
 * Highlight privacy matches in text with HTML spans
 */
export function highlightMatches(text: string, matches: PrivacyScanMatch[]): string {
  if (!text || matches.length === 0) {
    return text;
  }

  // Sort matches by start position (reverse order for correct replacement)
  const sortedMatches = [...matches].sort((a, b) => b.start - a.start);

  let result = text;
  sortedMatches.forEach(match => {
    const before = result.substring(0, match.start);
    const highlighted = result.substring(match.start, match.end);
    const after = result.substring(match.end);

    const className = `privacy-match privacy-${match.severity}`;
    const title = `${match.type}: ${match.description}`;

    result = `${before}<span class="${className}" title="${title}">${highlighted}</span>${after}`;
  });

  return result;
}
