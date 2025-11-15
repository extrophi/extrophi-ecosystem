//! Prompt Template Loader for BrainDump v3.0
//!
//! This module handles loading markdown prompt templates from the `/prompts/` directory.
//! It supports multiple fallback locations and provides a default prompt if templates are not found.

use std::fs;
use std::path::PathBuf;
use crate::error::BrainDumpError;

/// Default fallback prompt when template files are not found
const DEFAULT_PROMPT: &str = "You are a helpful, empathetic assistant. Listen carefully and respond with understanding.";

/// Load a prompt template by name
///
/// # Arguments
/// * `name` - The template name (without the `_prompt.md` suffix)
///
/// # Examples
/// ```
/// let prompt = load_prompt_template("brain_dump")?;
/// let prompt = load_prompt_template("end_of_day")?;
/// ```
///
/// # Returns
/// The prompt template content as a String, or falls back to DEFAULT_PROMPT if not found
pub fn load_prompt_template(name: &str) -> Result<String, BrainDumpError> {
    let filename = format!("{}_prompt.md", name);

    // Try multiple locations for the prompt file
    let prompts_dir = get_prompts_dir();
    let filepath = prompts_dir.join(&filename);

    crate::logging::info("Prompts", &format!("Loading template '{}' from: {}", name, filepath.display()));

    // Try to read the file
    match fs::read_to_string(&filepath) {
        Ok(content) => {
            crate::logging::info("Prompts", &format!("Successfully loaded template '{}' ({} bytes)", name, content.len()));

            // Validate content is not empty
            if content.trim().is_empty() {
                crate::logging::warn("Prompts", &format!("Template '{}' is empty, using default", name));
                Ok(DEFAULT_PROMPT.to_string())
            } else {
                Ok(content)
            }
        }
        Err(e) => {
            crate::logging::warn("Prompts", &format!("Failed to load template '{}': {}. Using default prompt.", name, e));
            // Fallback to default prompt instead of erroring
            Ok(DEFAULT_PROMPT.to_string())
        }
    }
}

/// List all available prompt templates in the prompts directory
///
/// # Returns
/// A vector of template names (without the `_prompt.md` suffix)
///
/// # Examples
/// ```
/// let templates = list_prompt_templates()?;
/// // Returns: vec!["brain_dump", "end_of_day", "end_of_month"]
/// ```
pub fn list_prompt_templates() -> Result<Vec<String>, BrainDumpError> {
    let prompts_dir = get_prompts_dir();

    crate::logging::info("Prompts", &format!("Scanning directory: {}", prompts_dir.display()));

    // Check if directory exists
    if !prompts_dir.exists() {
        crate::logging::warn("Prompts", &format!("Prompts directory not found at: {}", prompts_dir.display()));
        return Ok(Vec::new());
    }

    // Read directory entries
    let entries = fs::read_dir(&prompts_dir)
        .map_err(|e| BrainDumpError::Io(format!("Failed to read prompts directory: {}", e)))?;

    let mut templates = Vec::new();

    for entry in entries {
        let entry = entry.map_err(|e| BrainDumpError::Io(format!("Failed to read directory entry: {}", e)))?;
        let path = entry.path();

        // Only process .md files
        if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("md") {
            if let Some(filename) = path.file_name().and_then(|s| s.to_str()) {
                // Extract template name (remove _prompt.md suffix)
                if let Some(name) = filename.strip_suffix("_prompt.md") {
                    templates.push(name.to_string());
                }
            }
        }
    }

    // Sort alphabetically for consistent ordering
    templates.sort();

    crate::logging::info("Prompts", &format!("Found {} templates: {:?}", templates.len(), templates));

    Ok(templates)
}

/// Get the default brain dump prompt
///
/// This is a convenience function that loads the "brain_dump" template.
pub fn get_default_prompt() -> Result<String, BrainDumpError> {
    load_prompt_template("brain_dump")
}

/// Get the prompts directory path
///
/// Tries multiple locations in order of preference:
/// 1. `/prompts/` - Project root (development)
/// 2. `./prompts/` - Relative to executable (production)
/// 3. `~/.braindump/prompts/` - User home directory
/// 4. Bundled in app resources (macOS .app bundle)
///
/// # Returns
/// The first existing directory path, or the primary development path if none exist
fn get_prompts_dir() -> PathBuf {
    // Location 1: Project root (development mode)
    let project_root = std::env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("prompts");

    if project_root.exists() {
        return project_root;
    }

    // Location 2: Relative to executable (production)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let relative_prompts = exe_dir.join("prompts");
            if relative_prompts.exists() {
                return relative_prompts;
            }

            // Location 4: macOS .app bundle - Contents/Resources/prompts/
            if let Some(parent) = exe_dir.parent() {
                let resources_prompts = parent.join("Resources").join("prompts");
                if resources_prompts.exists() {
                    return resources_prompts;
                }
            }
        }
    }

    // Location 3: User home directory
    if let Some(home_dir) = dirs::home_dir() {
        let user_prompts = home_dir.join(".braindump").join("prompts");
        if user_prompts.exists() {
            return user_prompts;
        }
    }

    // Fallback: Return project root path even if it doesn't exist
    // This allows for clear error messages about where we expected to find prompts
    project_root
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_load_brain_dump_prompt() {
        let result = load_prompt_template("brain_dump");
        assert!(result.is_ok(), "Should load brain_dump prompt or return default");

        let prompt = result.unwrap();
        assert!(!prompt.is_empty(), "Prompt should not be empty");
        assert!(prompt.len() > 100, "Prompt should have substantial content");

        // Check for expected content if the file exists
        if prompt != DEFAULT_PROMPT {
            assert!(prompt.contains("Rogerian") || prompt.contains("therapist"),
                    "Brain dump prompt should mention Rogerian or therapist");
        }
    }

    #[test]
    fn test_load_end_of_day_prompt() {
        let result = load_prompt_template("end_of_day");
        assert!(result.is_ok(), "Should load end_of_day prompt or return default");

        let prompt = result.unwrap();
        assert!(!prompt.is_empty(), "Prompt should not be empty");
    }

    #[test]
    fn test_load_end_of_month_prompt() {
        let result = load_prompt_template("end_of_month");
        assert!(result.is_ok(), "Should load end_of_month prompt or return default");

        let prompt = result.unwrap();
        assert!(!prompt.is_empty(), "Prompt should not be empty");
    }

    #[test]
    fn test_load_nonexistent_template() {
        // Should return default prompt instead of erroring
        let result = load_prompt_template("nonexistent_template");
        assert!(result.is_ok(), "Should return default prompt for nonexistent template");

        let prompt = result.unwrap();
        assert_eq!(prompt, DEFAULT_PROMPT, "Should return default prompt");
    }

    #[test]
    fn test_list_templates() {
        let result = list_prompt_templates();
        assert!(result.is_ok(), "Should list templates or return empty vec");

        let templates = result.unwrap();

        // If prompts directory exists, should find our templates
        if !templates.is_empty() {
            assert!(templates.contains(&"brain_dump".to_string()),
                    "Should find brain_dump template");
            assert!(templates.contains(&"end_of_day".to_string()),
                    "Should find end_of_day template");
            assert!(templates.contains(&"end_of_month".to_string()),
                    "Should find end_of_month template");
        }
    }

    #[test]
    fn test_get_default_prompt() {
        let result = get_default_prompt();
        assert!(result.is_ok(), "Should get default prompt");

        let prompt = result.unwrap();
        assert!(!prompt.is_empty(), "Default prompt should not be empty");
    }

    #[test]
    fn test_prompts_dir_path() {
        let dir = get_prompts_dir();
        assert!(dir.ends_with("prompts"), "Should point to prompts directory");
    }
}
