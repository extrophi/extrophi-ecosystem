/**
 * Card Template System
 * Provides predefined and custom templates for card creation
 */

import type { CardCategory } from '../card-types';

export interface TemplateVariable {
  name: string;
  placeholder: string;
  description: string;
}

export interface CardTemplate {
  id?: number;
  name: string;
  title: string;
  content: string;
  category?: CardCategory;
  is_system: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Available template variables that can be used in templates
 */
export const TEMPLATE_VARIABLES: TemplateVariable[] = [
  {
    name: 'date',
    placeholder: '{{date}}',
    description: 'Current date (YYYY-MM-DD)',
  },
  {
    name: 'time',
    placeholder: '{{time}}',
    description: 'Current time (HH:MM)',
  },
  {
    name: 'datetime',
    placeholder: '{{datetime}}',
    description: 'Current date and time',
  },
  {
    name: 'user',
    placeholder: '{{user}}',
    description: 'Your name or username',
  },
  {
    name: 'weekday',
    placeholder: '{{weekday}}',
    description: 'Day of the week (Monday, Tuesday, etc.)',
  },
];

/**
 * Substitute template variables with actual values
 */
export function substituteVariables(
  content: string,
  userName: string = 'User'
): string {
  const now = new Date();

  const substitutions: Record<string, string> = {
    '{{date}}': now.toLocaleDateString('en-CA'), // YYYY-MM-DD format
    '{{time}}': now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }),
    '{{datetime}}': now.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    '{{user}}': userName,
    '{{weekday}}': now.toLocaleDateString('en-US', { weekday: 'long' }),
  };

  let result = content;
  for (const [variable, value] of Object.entries(substitutions)) {
    result = result.replaceAll(variable, value);
  }

  return result;
}

/**
 * Predefined system templates
 */
export const PREDEFINED_TEMPLATES: Omit<CardTemplate, 'id' | 'created_at' | 'updated_at'>[] = [
  {
    name: 'daily_journal',
    title: 'Daily Journal',
    content: `# Daily Journal - {{date}}

## What happened today?


## Key insights


## Gratitude
-

## Tomorrow's focus
- `,
    category: 'CATEGORIZED',
    is_system: true,
  },
  {
    name: 'meeting_notes',
    title: 'Meeting Notes',
    content: `# Meeting Notes - {{datetime}}

**Attendees:**

**Agenda:**
-

**Discussion:**


**Action Items:**
- [ ]

**Next Meeting:** `,
    category: 'PROGRAM',
    is_system: true,
  },
  {
    name: 'idea',
    title: 'Idea',
    content: `# Idea - {{date}}

## Core Concept


## Why This Matters


## Next Steps
- [ ]

---
*Captured by {{user}}*`,
    category: 'UNASSIMILATED',
    is_system: true,
  },
  {
    name: 'grit',
    title: 'GRIT Challenge',
    content: `# Challenge - {{date}}

## The Challenge


## Why It's Hard


## My Strategy
1.

## Progress Tracking
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Reflection


---
**Remember:** Growth happens outside your comfort zone.`,
    category: 'GRIT',
    is_system: true,
  },
  {
    name: 'quick_note',
    title: 'Quick Note',
    content: `{{datetime}}

`,
    is_system: true,
  },
  {
    name: 'weekly_review',
    title: 'Weekly Review',
    content: `# Weekly Review - Week of {{date}}

## Wins This Week
-

## Challenges Faced
-

## Lessons Learned


## Focus for Next Week
- [ ]
- [ ]
- [ ]

## Energy & Well-being
Mood:
Energy:
Sleep: `,
    category: 'CATEGORIZED',
    is_system: true,
  },
  {
    name: 'project_planning',
    title: 'Project Planning',
    content: `# Project:

**Start Date:** {{date}}
**Target Completion:**

## Objective


## Scope
**In Scope:**
-

**Out of Scope:**
-

## Milestones
- [ ] Milestone 1
- [ ] Milestone 2
- [ ] Milestone 3

## Resources Needed


## Risks & Mitigation
`,
    category: 'PROGRAM',
    is_system: true,
  },
];

/**
 * Get template by name
 */
export function getTemplateByName(name: string): typeof PREDEFINED_TEMPLATES[number] | undefined {
  return PREDEFINED_TEMPLATES.find(t => t.name === name);
}

/**
 * Get all system templates
 */
export function getSystemTemplates(): typeof PREDEFINED_TEMPLATES {
  return PREDEFINED_TEMPLATES;
}

/**
 * Validate template name (alphanumeric, underscores, hyphens only)
 */
export function validateTemplateName(name: string): boolean {
  return /^[a-z0-9_-]+$/i.test(name);
}

/**
 * Format template name for display
 */
export function formatTemplateName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}
