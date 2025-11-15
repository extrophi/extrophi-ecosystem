export interface PrivacyMatch {
  type: string;
  value: string;
  start: number;
  end: number;
  severity: 'caution' | 'danger';
}

interface DetectionPattern {
  name: string;
  regex: RegExp;
  severity: 'caution' | 'danger';
}

const patterns: DetectionPattern[] = [
  // 1. SSN (danger): \d{3}-\d{2}-\d{4}
  {
    name: 'SSN',
    regex: /\b\d{3}-\d{2}-\d{4}\b/g,
    severity: 'danger'
  },

  // 2. Credit card (danger): \d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}
  {
    name: 'Credit Card',
    regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
    severity: 'danger'
  },

  // 3. Email (caution): [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
  {
    name: 'Email',
    regex: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g,
    severity: 'caution'
  },

  // 4. Phone (caution): \(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}
  {
    name: 'Phone Number',
    regex: /(?<!\d)\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b/g,
    severity: 'caution'
  },

  // 5. Address (caution): \d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)
  {
    name: 'Street Address',
    regex: /\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b/g,
    severity: 'caution'
  },

  // 6. Account numbers (danger): Account\s*#?\s*\d{8,}
  {
    name: 'Account Number',
    regex: /\bAccount\s*#?\s*\d{8,}\b/gi,
    severity: 'danger'
  },

  // 7. Passport (danger): [A-Z]{1,2}\d{6,9}
  {
    name: 'Passport Number',
    regex: /\b[A-Z]{1,2}\d{6,9}\b/g,
    severity: 'danger'
  },

  // 8. IP address (caution): \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
  {
    name: 'IP Address',
    regex: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g,
    severity: 'caution'
  }
];

export function scanText(text: string): PrivacyMatch[] {
  const matches: PrivacyMatch[] = [];

  if (!text) {
    return matches;
  }

  patterns.forEach(pattern => {
    // Reset the regex lastIndex to avoid issues with global flag
    pattern.regex.lastIndex = 0;

    let match: RegExpExecArray | null;
    while ((match = pattern.regex.exec(text)) !== null) {
      matches.push({
        type: pattern.name,
        value: match[0],
        start: match.index,
        end: match.index + match[0].length,
        severity: pattern.severity
      });
    }
  });

  // Sort matches by start position for easier rendering
  matches.sort((a, b) => a.start - b.start);

  return matches;
}

/**
 * Highlights privacy matches in text by wrapping them in span elements
 * @param text Original text
 * @param matches Array of privacy matches
 * @returns HTML string with highlighted matches
 */
export function highlightMatches(text: string, matches: PrivacyMatch[]): string {
  if (!text || matches.length === 0) {
    return text;
  }

  let result = '';
  let lastIndex = 0;

  matches.forEach(match => {
    // Add text before the match
    result += escapeHtml(text.substring(lastIndex, match.start));

    // Add highlighted match
    const backgroundColor = match.severity === 'danger' ? '#f8d7da' : '#fff3cd';
    const borderColor = match.severity === 'danger' ? '#f5c2c7' : '#ffeeba';
    result += `<span class="privacy-highlight privacy-${match.severity}" style="background-color: ${backgroundColor}; border-bottom: 2px solid ${borderColor}; padding: 2px 4px; border-radius: 3px; cursor: help;" title="${match.type}: ${escapeHtml(match.value)}">${escapeHtml(match.value)}</span>`;

    lastIndex = match.end;
  });

  // Add remaining text
  result += escapeHtml(text.substring(lastIndex));

  return result;
}

/**
 * Helper function to escape HTML special characters
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
