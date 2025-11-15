/**
 * Template variable substitution utilities
 *
 * This module provides functions to substitute variables in prompt templates
 * with actual values like date, time, and user-provided data.
 */

export interface TemplateVariables {
  DATE?: string;
  TIME?: string;
  SUDS?: string;
  [key: string]: string | undefined;
}

/**
 * Substitute variables in a template string
 *
 * Supported variables:
 * - {{DATE}} → 2025-11-15 (ISO format)
 * - {{TIME}} → 14:30 (24-hour format)
 * - {{SUDS}} → user input or "N/A"
 *
 * @param template - The template string with {{VARIABLE}} placeholders
 * @param vars - Object containing variable values
 * @returns The template string with variables substituted
 */
export function substituteVariables(template: string, vars: TemplateVariables = {}): string {
  let result = template;

  // {{DATE}} → 2025-11-15
  result = result.replace(/\{\{DATE\}\}/g, vars.DATE || getCurrentDate());

  // {{TIME}} → 14:30
  result = result.replace(/\{\{TIME\}\}/g, vars.TIME || getCurrentTime());

  // {{SUDS}} → user input or "N/A"
  result = result.replace(/\{\{SUDS\}\}/g, vars.SUDS || 'N/A');

  // Handle any custom variables
  for (const [key, value] of Object.entries(vars)) {
    if (value && !['DATE', 'TIME', 'SUDS'].includes(key)) {
      const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
      result = result.replace(regex, value);
    }
  }

  return result;
}

/**
 * Get current date in ISO format (YYYY-MM-DD)
 */
function getCurrentDate(): string {
  return new Date().toLocaleDateString('en-CA'); // en-CA gives YYYY-MM-DD format
}

/**
 * Get current time in 24-hour format (HH:MM)
 */
function getCurrentTime(): string {
  return new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}

/**
 * Extract all variable names from a template
 *
 * @param template - The template string
 * @returns Array of variable names found in the template
 */
export function extractVariables(template: string): string[] {
  const regex = /\{\{([A-Z_]+)\}\}/g;
  const matches = [];
  let match;

  while ((match = regex.exec(template)) !== null) {
    if (!matches.includes(match[1])) {
      matches.push(match[1]);
    }
  }

  return matches;
}
