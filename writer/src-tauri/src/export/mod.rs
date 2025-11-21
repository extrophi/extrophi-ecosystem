pub mod markdown;
pub mod pdf;
pub mod docx;
pub mod html;
pub mod batch;

use crate::db::models::{ChatSession, Message};
use std::path::PathBuf;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ExportFormat {
    PDF,
    DOCX,
    HTML,
    Markdown,
}

impl ExportFormat {
    pub fn extension(&self) -> &str {
        match self {
            ExportFormat::PDF => "pdf",
            ExportFormat::DOCX => "docx",
            ExportFormat::HTML => "html",
            ExportFormat::Markdown => "md",
        }
    }
}

#[derive(Debug, Clone)]
pub struct ExportOptions {
    pub format: ExportFormat,
    pub include_metadata: bool,
    pub include_chat: bool,
    pub template: Option<String>,
}

impl Default for ExportOptions {
    fn default() -> Self {
        Self {
            format: ExportFormat::Markdown,
            include_metadata: true,
            include_chat: true,
            template: None,
        }
    }
}

pub trait Exporter {
    fn export(
        &self,
        session: &ChatSession,
        messages: &[Message],
        output_path: PathBuf,
        options: &ExportOptions,
    ) -> Result<(), String>;
}

/// Helper function to sanitize filenames
pub fn sanitize_filename(title: &str) -> String {
    title
        .chars()
        .map(|c| match c {
            'a'..='z' | 'A'..='Z' | '0'..='9' | '-' | '_' => c,
            ' ' => '_',
            _ => '-',
        })
        .collect::<String>()
        .chars()
        .take(50) // Limit length
        .collect()
}

/// Helper function to get default export directory
pub fn get_default_export_dir() -> Result<PathBuf, String> {
    let home = dirs::home_dir()
        .ok_or_else(|| "Could not find home directory".to_string())?;
    Ok(home.join("Documents").join("BrainDump"))
}
