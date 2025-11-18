/**
 * Card UI Types
 * 6-category classification system for brain dump cards
 */

import type { PrivacyLevel } from './privacy-rules';

export type CardCategory =
  | 'UNASSIMILATED'
  | 'PROGRAM'
  | 'CATEGORIZED'
  | 'GRIT'
  | 'TOUGH'
  | 'JUNK';

export interface Card {
  id: string;
  content: string;
  category: CardCategory;
  privacy_level: PrivacyLevel;
  created_at: string;
  updated_at: string;
}

export interface CategoryConfig {
  name: CardCategory;
  label: string;
  color: string;
  bgColor: string;
  description: string;
}

/**
 * Category configuration with colors and labels
 */
export const CATEGORY_CONFIGS: Record<CardCategory, CategoryConfig> = {
  UNASSIMILATED: {
    name: 'UNASSIMILATED',
    label: 'Unassimilated',
    color: '#666666',
    bgColor: '#ffffff',
    description: 'Raw brain dump - unprocessed thoughts',
  },
  PROGRAM: {
    name: 'PROGRAM',
    label: 'Program',
    color: '#2563eb',
    bgColor: '#dbeafe',
    description: 'Actionable systems and processes',
  },
  CATEGORIZED: {
    name: 'CATEGORIZED',
    label: 'Categorized',
    color: '#16a34a',
    bgColor: '#dcfce7',
    description: 'Organized knowledge and insights',
  },
  GRIT: {
    name: 'GRIT',
    label: 'Grit',
    color: '#ea580c',
    bgColor: '#ffedd5',
    description: 'Challenges and struggles to overcome',
  },
  TOUGH: {
    name: 'TOUGH',
    label: 'Tough',
    color: '#dc2626',
    bgColor: '#fee2e2',
    description: 'Hard truths and contrarian perspectives',
  },
  JUNK: {
    name: 'JUNK',
    label: 'Junk',
    color: '#9ca3af',
    bgColor: '#f3f4f6',
    description: 'Discard pile - irrelevant content',
  },
};

/**
 * Get category config by name
 */
export function getCategoryConfig(category: CardCategory): CategoryConfig {
  return CATEGORY_CONFIGS[category];
}

/**
 * Get all categories in display order
 */
export function getAllCategories(): CardCategory[] {
  return [
    'UNASSIMILATED',
    'PROGRAM',
    'CATEGORIZED',
    'GRIT',
    'TOUGH',
    'JUNK',
  ];
}
