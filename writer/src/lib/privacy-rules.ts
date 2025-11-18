/**
 * Privacy Classification Rules
 * 4-level system: PRIVATE, PERSONAL, BUSINESS, IDEAS
 *
 * Scan order: PRIVATE → PERSONAL → BUSINESS → IDEAS
 * First match wins (most restrictive classification)
 */

export type PrivacyLevel = 'PRIVATE' | 'PERSONAL' | 'BUSINESS' | 'IDEAS';

export interface PrivacyPattern {
  name: string;
  regex: RegExp;
  level: PrivacyLevel;
  description: string;
}

export interface PrivacyMatch {
  type: string;
  value: string;
  start: number;
  end: number;
  level: PrivacyLevel;
  description: string;
}

/**
 * PRIVATE (RED) - Personally Identifiable Information (PII)
 * SSN, emails, credit cards, phone numbers, government IDs
 */
const PRIVATE_PATTERNS: PrivacyPattern[] = [
  {
    name: 'SSN',
    regex: /\b\d{3}-\d{2}-\d{4}\b/g,
    level: 'PRIVATE',
    description: 'Social Security Number'
  },
  {
    name: 'Email',
    regex: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g,
    level: 'PRIVATE',
    description: 'Email address'
  },
  {
    name: 'Credit Card',
    regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
    level: 'PRIVATE',
    description: 'Credit card number'
  },
  {
    name: 'Phone Number',
    regex: /(?<!\d)(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
    level: 'PRIVATE',
    description: 'Phone number'
  },
  {
    name: 'Passport Number',
    regex: /\b[A-Z]{1,2}\d{6,9}\b/g,
    level: 'PRIVATE',
    description: 'Passport number'
  },
  {
    name: 'Account Number',
    regex: /\b(?:account|acct)[\s#:]*\d{8,}\b/gi,
    level: 'PRIVATE',
    description: 'Account number'
  },
  {
    name: 'Driver License',
    regex: /\b(?:DL|license|lic)[:\s#]*[A-Z0-9]{7,15}\b/gi,
    level: 'PRIVATE',
    description: 'Driver license number'
  },
  {
    name: 'Street Address',
    regex: /\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b/g,
    level: 'PRIVATE',
    description: 'Physical street address'
  },
  {
    name: 'IP Address',
    regex: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
    level: 'PRIVATE',
    description: 'IP address'
  }
];

/**
 * PERSONAL (ORANGE) - Emotional content, family, health, personal experiences
 */
const PERSONAL_PATTERNS: PrivacyPattern[] = [
  {
    name: 'Emotional Expression',
    regex: /\b(?:I feel|I felt|I'm feeling|I think|I thought|I believe|I believed|I worry|I worried|I'm afraid|I fear)\b/gi,
    level: 'PERSONAL',
    description: 'Personal emotional expression'
  },
  {
    name: 'Family Reference',
    regex: /\b(?:my (?:wife|husband|spouse|partner|child|son|daughter|kid|parent|mom|mother|dad|father|brother|sister|sibling|family))\b/gi,
    level: 'PERSONAL',
    description: 'Family member reference'
  },
  {
    name: 'Personal Pronoun Context',
    regex: /\b(?:I am|I'm|I was|I've been|I have|I had|my own|myself)\b/gi,
    level: 'PERSONAL',
    description: 'Personal pronoun usage'
  },
  {
    name: 'Health Information',
    regex: /\b(?:my (?:health|diagnosis|condition|illness|disease|symptoms?|medication|treatment|therapy|doctor|physician))\b/gi,
    level: 'PERSONAL',
    description: 'Personal health information'
  },
  {
    name: 'Personal Experience',
    regex: /\b(?:when I|after I|before I|if I|since I|as I|while I)\b/gi,
    level: 'PERSONAL',
    description: 'Personal experience narrative'
  },
  {
    name: 'Mental Health',
    regex: /\b(?:anxious|depressed|stressed|overwhelmed|burnout|mental health|therapy session)\b/gi,
    level: 'PERSONAL',
    description: 'Mental health content'
  }
];

/**
 * BUSINESS (YELLOW) - Client names, projects, strategies, financial info
 */
const BUSINESS_PATTERNS: PrivacyPattern[] = [
  {
    name: 'Client Reference',
    regex: /\b(?:client|customer)(?:\s+(?:name|project|account|meeting))?\b/gi,
    level: 'BUSINESS',
    description: 'Client or customer reference'
  },
  {
    name: 'Project Keyword',
    regex: /\b(?:project|initiative|campaign|launch|deadline|deliverable)(?:\s+[A-Z][a-z]+)?\b/gi,
    level: 'BUSINESS',
    description: 'Project or initiative'
  },
  {
    name: 'Financial Information',
    regex: /\$[\d,]+(?:\.\d{2})?|\b(?:revenue|profit|loss|expense|budget|pricing|cost)\b/gi,
    level: 'BUSINESS',
    description: 'Financial information'
  },
  {
    name: 'Business Strategy',
    regex: /\b(?:strategy|roadmap|plan|goal|objective|KPI|metric|target|forecast)\b/gi,
    level: 'BUSINESS',
    description: 'Business strategy or planning'
  },
  {
    name: 'Competitive Information',
    regex: /\b(?:competitor|competition|market share|industry|sector|advantage)\b/gi,
    level: 'BUSINESS',
    description: 'Competitive intelligence'
  },
  {
    name: 'Internal Process',
    regex: /\b(?:internal|proprietary|confidential|NDA|non-disclosure)\b/gi,
    level: 'BUSINESS',
    description: 'Internal business process'
  }
];

/**
 * IDEAS (GREEN) - Default publishable content
 * General thoughts, philosophies, educational content, public-safe information
 * No explicit patterns - this is the default if nothing else matches
 */

/**
 * Compiled pattern sets for efficient scanning
 */
export const PRIVACY_PATTERNS = {
  PRIVATE: PRIVATE_PATTERNS,
  PERSONAL: PERSONAL_PATTERNS,
  BUSINESS: BUSINESS_PATTERNS,
  IDEAS: [] as PrivacyPattern[] // Default level, no patterns needed
};

/**
 * Scan text for privacy issues
 * Returns matches in order of detection
 *
 * @param text - Text to scan
 * @returns Array of privacy matches
 */
export function scanText(text: string): PrivacyMatch[] {
  if (!text || text.trim().length === 0) {
    return [];
  }

  const matches: PrivacyMatch[] = [];

  // Scan in order: PRIVATE → PERSONAL → BUSINESS
  const scanOrder: Array<{ level: PrivacyLevel; patterns: PrivacyPattern[] }> = [
    { level: 'PRIVATE', patterns: PRIVATE_PATTERNS },
    { level: 'PERSONAL', patterns: PERSONAL_PATTERNS },
    { level: 'BUSINESS', patterns: BUSINESS_PATTERNS }
  ];

  scanOrder.forEach(({ patterns }) => {
    patterns.forEach(pattern => {
      // Reset regex state
      pattern.regex.lastIndex = 0;

      let match: RegExpExecArray | null;
      while ((match = pattern.regex.exec(text)) !== null) {
        matches.push({
          type: pattern.name,
          value: match[0],
          start: match.index,
          end: match.index + match[0].length,
          level: pattern.level,
          description: pattern.description
        });
      }
    });
  });

  // Sort by position in text
  matches.sort((a, b) => a.start - b.start);

  return matches;
}

/**
 * Classify text into privacy level (highest match wins)
 * Returns the most restrictive privacy level found
 *
 * @param text - Text to classify
 * @returns Privacy level (PRIVATE, PERSONAL, BUSINESS, or IDEAS)
 */
export function classifyText(text: string): PrivacyLevel {
  if (!text || text.trim().length === 0) {
    return 'IDEAS';
  }

  const matches = scanText(text);

  if (matches.length === 0) {
    return 'IDEAS';
  }

  // Return most restrictive level (first match in priority order)
  if (matches.some(m => m.level === 'PRIVATE')) {
    return 'PRIVATE';
  }
  if (matches.some(m => m.level === 'PERSONAL')) {
    return 'PERSONAL';
  }
  if (matches.some(m => m.level === 'BUSINESS')) {
    return 'BUSINESS';
  }

  return 'IDEAS';
}

/**
 * Get counts by privacy level
 *
 * @param matches - Array of privacy matches
 * @returns Object with counts for each level
 */
export function getMatchCountsByLevel(matches: PrivacyMatch[]): Record<PrivacyLevel, number> {
  return {
    PRIVATE: matches.filter(m => m.level === 'PRIVATE').length,
    PERSONAL: matches.filter(m => m.level === 'PERSONAL').length,
    BUSINESS: matches.filter(m => m.level === 'BUSINESS').length,
    IDEAS: 0 // Ideas is default, no matches counted
  };
}

/**
 * Get color for privacy level (for UI display)
 *
 * @param level - Privacy level
 * @returns CSS color value
 */
export function getLevelColor(level: PrivacyLevel): string {
  const colors: Record<PrivacyLevel, string> = {
    PRIVATE: '#dc3545',   // Red
    PERSONAL: '#ff8c00',  // Orange
    BUSINESS: '#ffc107',  // Yellow
    IDEAS: '#28a745'      // Green
  };
  return colors[level];
}

/**
 * Get label for privacy level
 *
 * @param level - Privacy level
 * @returns Human-readable label
 */
export function getLevelLabel(level: PrivacyLevel): string {
  const labels: Record<PrivacyLevel, string> = {
    PRIVATE: 'Private',
    PERSONAL: 'Personal',
    BUSINESS: 'Business',
    IDEAS: 'Ideas'
  };
  return labels[level];
}

/**
 * Get description for privacy level
 *
 * @param level - Privacy level
 * @returns Description of what the level means
 */
export function getLevelDescription(level: PrivacyLevel): string {
  const descriptions: Record<PrivacyLevel, string> = {
    PRIVATE: 'Contains personally identifiable information (PII) - emails, phone numbers, SSN, etc.',
    PERSONAL: 'Contains emotional content, family references, or personal experiences',
    BUSINESS: 'Contains client names, projects, strategies, or financial information',
    IDEAS: 'General thoughts and philosophies - safe to publish'
  };
  return descriptions[level];
}
