/**
 * Privacy Rules Test Suite
 * Tests all 4 privacy classification levels
 *
 * Coverage:
 * - PRIVATE: SSN, email, credit card, phone, passport, account, driver license, address, IP
 * - PERSONAL: Emotional expressions, family references, health info, personal experiences
 * - BUSINESS: Client references, projects, financial info, strategies, competitive info
 * - IDEAS: Default level when no patterns match
 * - Performance: < 50ms scan time requirement
 */

import { describe, it, expect } from 'vitest';
import {
  scanText,
  classifyText,
  getMatchCountsByLevel,
  getLevelColor,
  getLevelLabel,
  getLevelDescription,
  type PrivacyLevel
} from '../lib/privacy-rules';

describe('Privacy Rules - PRIVATE Level', () => {
  it('should detect SSN (Social Security Number)', () => {
    const text = 'My SSN is 123-45-6789';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('SSN');
    expect(matches[0].value).toBe('123-45-6789');
  });

  it('should detect email addresses', () => {
    const text = 'Contact me at john.doe@example.com';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('Email');
    expect(matches[0].value).toBe('john.doe@example.com');
  });

  it('should detect credit card numbers (with spaces)', () => {
    const text = 'Card: 4532 1234 5678 9010';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('Credit Card');
  });

  it('should detect credit card numbers (with dashes)', () => {
    const text = 'Card: 4532-1234-5678-9010';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('Credit Card');
  });

  it('should detect phone numbers (various formats)', () => {
    const testCases = [
      '(555) 123-4567',
      '555-123-4567',
      '555.123.4567',
      '+1-555-123-4567'
    ];

    testCases.forEach(phoneNumber => {
      const text = `Call me at ${phoneNumber}`;
      const matches = scanText(text);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches[0].level).toBe('PRIVATE');
      expect(matches[0].type).toBe('Phone Number');
    });
  });

  it('should detect passport numbers', () => {
    const text = 'Passport: A1234567';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('Passport Number');
  });

  it('should detect account numbers', () => {
    const text = 'Account #12345678901';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('Account Number');
  });

  it('should detect street addresses', () => {
    const text = 'I live at 123 Main Street';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('Street Address');
  });

  it('should detect IP addresses', () => {
    const text = 'Server IP: 192.168.1.1';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PRIVATE');
    expect(matches[0].type).toBe('IP Address');
  });

  it('should classify text as PRIVATE when PII is present', () => {
    const text = 'Email me at test@example.com';
    const level = classifyText(text);
    expect(level).toBe('PRIVATE');
  });
});

describe('Privacy Rules - PERSONAL Level', () => {
  it('should detect emotional expressions', () => {
    const testCases = [
      'I feel sad today',
      'I think this is wrong',
      'I believe we can do better',
      "I'm feeling anxious",
      'I worry about the future'
    ];

    testCases.forEach(text => {
      const matches = scanText(text);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches[0].level).toBe('PERSONAL');
      expect(matches[0].type).toBe('Emotional Expression');
    });
  });

  it('should detect family references', () => {
    const testCases = [
      'my wife is amazing',
      'my husband works here',
      'my child is sick',
      'my mom called me',
      'my dad told me'
    ];

    testCases.forEach(text => {
      const matches = scanText(text);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches[0].level).toBe('PERSONAL');
      expect(matches[0].type).toBe('Family Reference');
    });
  });

  it('should detect personal pronoun context', () => {
    const text = "I am working on this project";
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PERSONAL');
    expect(matches[0].type).toBe('Personal Pronoun Context');
  });

  it('should detect health information', () => {
    const text = 'my health is improving';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PERSONAL');
    expect(matches[0].type).toBe('Health Information');
  });

  it('should detect personal experiences', () => {
    const text = 'when I was younger';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PERSONAL');
    expect(matches[0].type).toBe('Personal Experience');
  });

  it('should detect mental health content', () => {
    const text = 'feeling anxious about work';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('PERSONAL');
    expect(matches[0].type).toBe('Mental Health');
  });

  it('should classify text as PERSONAL when personal content is present', () => {
    const text = 'I feel happy today';
    const level = classifyText(text);
    expect(level).toBe('PERSONAL');
  });
});

describe('Privacy Rules - BUSINESS Level', () => {
  it('should detect client references', () => {
    const text = 'met with client yesterday';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('BUSINESS');
    expect(matches[0].type).toBe('Client Reference');
  });

  it('should detect project keywords', () => {
    const text = 'working on project Phoenix';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('BUSINESS');
    expect(matches[0].type).toBe('Project Keyword');
  });

  it('should detect financial information', () => {
    const testCases = [
      'revenue is $50,000',
      'budget of $10,000',
      'profit margin increased',
      'expense report'
    ];

    testCases.forEach(text => {
      const matches = scanText(text);
      expect(matches.length).toBeGreaterThan(0);
      expect(matches[0].level).toBe('BUSINESS');
    });
  });

  it('should detect business strategy terms', () => {
    const text = 'our strategy for next quarter';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('BUSINESS');
    expect(matches[0].type).toBe('Business Strategy');
  });

  it('should detect competitive information', () => {
    const text = 'competitor analysis shows';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('BUSINESS');
    expect(matches[0].type).toBe('Competitive Information');
  });

  it('should detect internal process keywords', () => {
    const text = 'this is confidential information';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].level).toBe('BUSINESS');
    expect(matches[0].type).toBe('Internal Process');
  });

  it('should classify text as BUSINESS when business content is present', () => {
    const text = 'meeting with client tomorrow';
    const level = classifyText(text);
    expect(level).toBe('BUSINESS');
  });
});

describe('Privacy Rules - IDEAS Level', () => {
  it('should classify generic text as IDEAS', () => {
    const text = 'The sky is blue and birds fly high';
    const level = classifyText(text);
    expect(level).toBe('IDEAS');
  });

  it('should classify philosophical content as IDEAS', () => {
    const text = 'Success is built through consistent daily actions';
    const level = classifyText(text);
    expect(level).toBe('IDEAS');
  });

  it('should classify educational content as IDEAS', () => {
    const text = 'Learning to code requires practice and patience';
    const level = classifyText(text);
    expect(level).toBe('IDEAS');
  });

  it('should return empty matches for IDEAS content', () => {
    const text = 'This is general publishable content';
    const matches = scanText(text);
    expect(matches.length).toBe(0);
  });

  it('should default to IDEAS for empty text', () => {
    const level = classifyText('');
    expect(level).toBe('IDEAS');
  });
});

describe('Privacy Rules - Priority and Classification', () => {
  it('should prioritize PRIVATE over PERSONAL', () => {
    const text = 'I feel great! Email me at test@example.com';
    const level = classifyText(text);
    expect(level).toBe('PRIVATE'); // Email is PRIVATE, feeling is PERSONAL
  });

  it('should prioritize PRIVATE over BUSINESS', () => {
    const text = 'Client meeting at 123 Main Street';
    const level = classifyText(text);
    expect(level).toBe('PRIVATE'); // Address is PRIVATE, client is BUSINESS
  });

  it('should prioritize PERSONAL over BUSINESS', () => {
    const text = 'I think the client strategy needs work';
    const level = classifyText(text);
    expect(level).toBe('PERSONAL'); // "I think" is PERSONAL
  });

  it('should detect multiple matches across different levels', () => {
    const text = 'I feel excited about the client project. Email: test@example.com';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(2); // Should find PERSONAL, BUSINESS, and PRIVATE

    const levels = new Set(matches.map(m => m.level));
    expect(levels.has('PRIVATE')).toBe(true);
    expect(levels.has('PERSONAL')).toBe(true);
    expect(levels.has('BUSINESS')).toBe(true);
  });
});

describe('Privacy Rules - Helper Functions', () => {
  it('should return correct match counts by level', () => {
    const text = 'I feel happy. Email: test@example.com. Client meeting.';
    const matches = scanText(text);
    const counts = getMatchCountsByLevel(matches);

    expect(counts.PRIVATE).toBeGreaterThan(0);
    expect(counts.PERSONAL).toBeGreaterThan(0);
    expect(counts.BUSINESS).toBeGreaterThan(0);
    expect(counts.IDEAS).toBe(0);
  });

  it('should return correct colors for each level', () => {
    expect(getLevelColor('PRIVATE')).toBe('#dc3545'); // Red
    expect(getLevelColor('PERSONAL')).toBe('#ff8c00'); // Orange
    expect(getLevelColor('BUSINESS')).toBe('#ffc107'); // Yellow
    expect(getLevelColor('IDEAS')).toBe('#28a745'); // Green
  });

  it('should return correct labels for each level', () => {
    expect(getLevelLabel('PRIVATE')).toBe('Private');
    expect(getLevelLabel('PERSONAL')).toBe('Personal');
    expect(getLevelLabel('BUSINESS')).toBe('Business');
    expect(getLevelLabel('IDEAS')).toBe('Ideas');
  });

  it('should return descriptions for each level', () => {
    const levels: PrivacyLevel[] = ['PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS'];
    levels.forEach(level => {
      const description = getLevelDescription(level);
      expect(description).toBeTruthy();
      expect(description.length).toBeGreaterThan(10);
    });
  });
});

describe('Privacy Rules - Performance', () => {
  it('should scan short text in under 50ms', () => {
    const text = 'This is a short text with email@example.com';
    const startTime = performance.now();
    scanText(text);
    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(50);
  });

  it('should scan medium text (500 words) in under 50ms', () => {
    const text = 'word '.repeat(500) + 'email@example.com';
    const startTime = performance.now();
    scanText(text);
    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(50);
  });

  it('should scan large text (2000 words) efficiently', () => {
    const text = 'word '.repeat(2000) + 'email@example.com I feel happy client meeting';
    const startTime = performance.now();
    scanText(text);
    const endTime = performance.now();
    const duration = endTime - startTime;

    // Allow slightly more time for very large texts, but should still be fast
    expect(duration).toBeLessThan(100);
  });

  it('should classify text quickly', () => {
    const text = 'This is test content with email@example.com';
    const startTime = performance.now();
    classifyText(text);
    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(50);
  });
});

describe('Privacy Rules - Edge Cases', () => {
  it('should handle empty text', () => {
    const matches = scanText('');
    expect(matches.length).toBe(0);
    expect(classifyText('')).toBe('IDEAS');
  });

  it('should handle whitespace-only text', () => {
    const matches = scanText('   \n\t  ');
    expect(matches.length).toBe(0);
    expect(classifyText('   ')).toBe('IDEAS');
  });

  it('should handle text with special characters', () => {
    const text = '!@#$%^&*() test@example.com {}[]|\\';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0); // Should find email
    expect(matches[0].type).toBe('Email');
  });

  it('should handle text with line breaks', () => {
    const text = 'Line 1\nLine 2 test@example.com\nLine 3';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
  });

  it('should not detect false positives for numbers', () => {
    const text = 'The year 2024 has 365 days and 52 weeks';
    const matches = scanText(text);
    expect(matches.length).toBe(0); // No credit cards, SSN, etc.
  });

  it('should handle Unicode characters', () => {
    const text = 'こんにちは test@example.com مرحبا';
    const matches = scanText(text);
    expect(matches.length).toBeGreaterThan(0);
    expect(matches[0].type).toBe('Email');
  });
});

describe('Privacy Rules - Real-World Examples', () => {
  it('should correctly classify a journal entry with PII', () => {
    const text = `
      Today I had a great meeting with my client.
      They emailed me at john@company.com about the new project.
      The budget is $50,000 and we need to deliver by next month.
    `;
    const level = classifyText(text);
    expect(level).toBe('PRIVATE'); // Email is most restrictive
  });

  it('should correctly classify personal journal entry', () => {
    const text = `
      I feel really grateful today. My wife surprised me with breakfast.
      I've been working on my mental health and it's paying off.
    `;
    const level = classifyText(text);
    expect(level).toBe('PERSONAL');
  });

  it('should correctly classify business note', () => {
    const text = `
      Meeting notes from client discussion.
      Project deadline: Q2 2024
      Revenue forecast: positive growth
      Strategy: focus on market expansion
    `;
    const level = classifyText(text);
    expect(level).toBe('BUSINESS');
  });

  it('should correctly classify publishable ideas', () => {
    const text = `
      Success in business comes from consistent action.
      Focus on providing value to others.
      Build systems that scale beyond your time.
    `;
    const level = classifyText(text);
    expect(level).toBe('IDEAS');
  });
});
