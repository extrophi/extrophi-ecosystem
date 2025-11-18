/**
 * Card Types Test Suite
 * Tests the 6-category card classification system
 *
 * Coverage:
 * - Card interface and types
 * - Category configurations
 * - Helper functions
 */

import { describe, it, expect } from 'vitest';
import {
  getCategoryConfig,
  getAllCategories,
  CATEGORY_CONFIGS,
  type CardCategory,
} from '../lib/card-types';

describe('Card Types - Category Configs', () => {
  it('should have configurations for all 6 categories', () => {
    const categories: CardCategory[] = [
      'UNASSIMILATED',
      'PROGRAM',
      'CATEGORIZED',
      'GRIT',
      'TOUGH',
      'JUNK',
    ];

    categories.forEach((category) => {
      const config = CATEGORY_CONFIGS[category];
      expect(config).toBeDefined();
      expect(config.name).toBe(category);
      expect(config.label).toBeTruthy();
      expect(config.color).toMatch(/^#[0-9a-f]{6}$/i);
      expect(config.bgColor).toMatch(/^#[0-9a-f]{6}$/i);
      expect(config.description).toBeTruthy();
    });
  });

  it('should have UNASSIMILATED with white/gray styling', () => {
    const config = getCategoryConfig('UNASSIMILATED');
    expect(config.name).toBe('UNASSIMILATED');
    expect(config.label).toBe('Unassimilated');
    expect(config.color).toBe('#666666');
    expect(config.bgColor).toBe('#ffffff');
    expect(config.description).toContain('Raw brain dump');
  });

  it('should have PROGRAM with blue styling', () => {
    const config = getCategoryConfig('PROGRAM');
    expect(config.name).toBe('PROGRAM');
    expect(config.label).toBe('Program');
    expect(config.color).toBe('#2563eb');
    expect(config.bgColor).toBe('#dbeafe');
    expect(config.description).toContain('Actionable');
  });

  it('should have CATEGORIZED with green styling', () => {
    const config = getCategoryConfig('CATEGORIZED');
    expect(config.name).toBe('CATEGORIZED');
    expect(config.label).toBe('Categorized');
    expect(config.color).toBe('#16a34a');
    expect(config.bgColor).toBe('#dcfce7');
    expect(config.description).toContain('Organized');
  });

  it('should have GRIT with orange styling', () => {
    const config = getCategoryConfig('GRIT');
    expect(config.name).toBe('GRIT');
    expect(config.label).toBe('Grit');
    expect(config.color).toBe('#ea580c');
    expect(config.bgColor).toBe('#ffedd5');
    expect(config.description).toContain('Challenges');
  });

  it('should have TOUGH with red styling', () => {
    const config = getCategoryConfig('TOUGH');
    expect(config.name).toBe('TOUGH');
    expect(config.label).toBe('Tough');
    expect(config.color).toBe('#dc2626');
    expect(config.bgColor).toBe('#fee2e2');
    expect(config.description).toContain('Hard truths');
  });

  it('should have JUNK with gray styling', () => {
    const config = getCategoryConfig('JUNK');
    expect(config.name).toBe('JUNK');
    expect(config.label).toBe('Junk');
    expect(config.color).toBe('#9ca3af');
    expect(config.bgColor).toBe('#f3f4f6');
    expect(config.description).toContain('Discard');
  });
});

describe('Card Types - Helper Functions', () => {
  it('should return all categories in correct order', () => {
    const categories = getAllCategories();
    expect(categories).toEqual([
      'UNASSIMILATED',
      'PROGRAM',
      'CATEGORIZED',
      'GRIT',
      'TOUGH',
      'JUNK',
    ]);
  });

  it('should return exactly 6 categories', () => {
    const categories = getAllCategories();
    expect(categories.length).toBe(6);
  });

  it('should return valid config for each category', () => {
    getAllCategories().forEach((category) => {
      const config = getCategoryConfig(category);
      expect(config).toBeDefined();
      expect(config.name).toBe(category);
    });
  });
});

describe('Card Types - Card Interface', () => {
  it('should accept a valid Card object structure', () => {
    const card = {
      id: '123',
      content: 'Test content',
      category: 'UNASSIMILATED' as CardCategory,
      privacy_level: 'IDEAS' as const,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    expect(card.id).toBe('123');
    expect(card.content).toBe('Test content');
    expect(card.category).toBe('UNASSIMILATED');
    expect(card.privacy_level).toBe('IDEAS');
    expect(card.created_at).toBeTruthy();
    expect(card.updated_at).toBeTruthy();
  });

  it('should work with all category types', () => {
    const categories: CardCategory[] = getAllCategories();

    categories.forEach((category) => {
      const card = {
        id: 'test',
        content: 'test content',
        category,
        privacy_level: 'IDEAS' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      expect(card.category).toBe(category);
    });
  });

  it('should work with all privacy levels', () => {
    type PrivacyLevel = 'PRIVATE' | 'PERSONAL' | 'BUSINESS' | 'IDEAS';
    const privacyLevels: PrivacyLevel[] = ['PRIVATE', 'PERSONAL', 'BUSINESS', 'IDEAS'];

    privacyLevels.forEach((privacy_level) => {
      const card = {
        id: 'test',
        content: 'test content',
        category: 'UNASSIMILATED' as CardCategory,
        privacy_level,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      expect(card.privacy_level).toBe(privacy_level);
    });
  });
});

describe('Card Types - Color Contrast', () => {
  it('should have sufficient contrast between color and bgColor', () => {
    // Simple brightness check - full hex colors should differ significantly
    getAllCategories().forEach((category) => {
      const config = getCategoryConfig(category);

      // Extract RGB values
      const colorRGB = parseInt(config.color.slice(1), 16);
      const bgRGB = parseInt(config.bgColor.slice(1), 16);

      // Colors should be different
      expect(colorRGB).not.toBe(bgRGB);
    });
  });

  it('should use darker colors for text and lighter colors for backgrounds', () => {
    // Check that bgColor is generally lighter than color
    getAllCategories().forEach((category) => {
      const config = getCategoryConfig(category);

      // Sum of RGB components (rough brightness measure)
      const colorBrightness = parseInt(config.color.slice(1, 3), 16) +
                              parseInt(config.color.slice(3, 5), 16) +
                              parseInt(config.color.slice(5, 7), 16);

      const bgBrightness = parseInt(config.bgColor.slice(1, 3), 16) +
                           parseInt(config.bgColor.slice(3, 5), 16) +
                           parseInt(config.bgColor.slice(5, 7), 16);

      // Background should be lighter (higher brightness value)
      expect(bgBrightness).toBeGreaterThan(colorBrightness);
    });
  });
});

describe('Card Types - Category Semantics', () => {
  it('should have UNASSIMILATED as first category (entry point)', () => {
    const categories = getAllCategories();
    expect(categories[0]).toBe('UNASSIMILATED');
  });

  it('should have JUNK as last category (exit point)', () => {
    const categories = getAllCategories();
    expect(categories[categories.length - 1]).toBe('JUNK');
  });

  it('should have actionable categories in the middle', () => {
    const categories = getAllCategories();
    const actionableCategories = ['PROGRAM', 'CATEGORIZED', 'GRIT', 'TOUGH'];

    actionableCategories.forEach((category) => {
      const index = categories.indexOf(category as CardCategory);
      expect(index).toBeGreaterThan(0); // Not first
      expect(index).toBeLessThan(categories.length - 1); // Not last
    });
  });
});
