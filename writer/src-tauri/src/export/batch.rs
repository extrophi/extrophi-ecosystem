use crate::db::models::{ChatSession, Message};
use super::{ExportFormat, ExportOptions, Exporter, sanitize_filename};
use super::pdf::PDFExporter;
use super::docx::DocxExporter;
use super::html::HTMLExporter;
use super::markdown::MarkdownExporter;
use std::fs::File;
use std::io::{Write, Read};
use std::path::PathBuf;
use zip::write::FileOptions;
use zip::ZipWriter;

pub struct BatchExporter;

impl BatchExporter {
    pub fn new() -> Self {
        Self
    }

    pub fn export_multiple(
        &self,
        sessions_with_messages: Vec<(ChatSession, Vec<Message>)>,
        output_zip: PathBuf,
        options: &ExportOptions,
    ) -> Result<(), String> {
        // Create zip file
        let file = File::create(&output_zip)
            .map_err(|e| format!("Failed to create ZIP file: {}", e))?;

        let mut zip = ZipWriter::new(file);
        let zip_options: FileOptions<()> = FileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated)
            .unix_permissions(0o755);

        // Create temporary directory for exports
        let temp_dir = std::env::temp_dir().join(format!("braindump_export_{}", uuid::Uuid::new_v4()));
        std::fs::create_dir_all(&temp_dir)
            .map_err(|e| format!("Failed to create temp directory: {}", e))?;

        // Get the appropriate exporter
        let exporter: Box<dyn Exporter> = match options.format {
            ExportFormat::PDF => Box::new(PDFExporter::new()),
            ExportFormat::DOCX => Box::new(DocxExporter::new()),
            ExportFormat::HTML => Box::new(HTMLExporter::new()),
            ExportFormat::Markdown => Box::new(MarkdownExporter::new()),
        };

        // Export each session
        for (session, messages) in sessions_with_messages {
            let title = session.title.as_deref().unwrap_or("untitled");
            let safe_title = sanitize_filename(title);
            let date_prefix = session.created_at.format("%Y-%m-%d");
            let filename = format!("{}_{}.{}", date_prefix, safe_title, options.format.extension());

            // Export to temp file
            let temp_path = temp_dir.join(&filename);

            exporter.export(&session, &messages, temp_path.clone(), options)?;

            // Add to ZIP
            zip.start_file(&filename, zip_options)
                .map_err(|e| format!("Failed to add file to ZIP: {}", e))?;

            let mut content = Vec::new();
            let mut temp_file = File::open(&temp_path)
                .map_err(|e| format!("Failed to read temp file: {}", e))?;
            temp_file
                .read_to_end(&mut content)
                .map_err(|e| format!("Failed to read temp file content: {}", e))?;

            zip.write_all(&content)
                .map_err(|e| format!("Failed to write to ZIP: {}", e))?;
        }

        // Finalize ZIP
        zip.finish()
            .map_err(|e| format!("Failed to finalize ZIP: {}", e))?;

        // Cleanup temp directory
        std::fs::remove_dir_all(&temp_dir).ok();

        Ok(())
    }

    pub fn export_sessions_separately(
        &self,
        sessions_with_messages: Vec<(ChatSession, Vec<Message>)>,
        output_dir: PathBuf,
        options: &ExportOptions,
    ) -> Result<Vec<PathBuf>, String> {
        // Create output directory if it doesn't exist
        std::fs::create_dir_all(&output_dir)
            .map_err(|e| format!("Failed to create output directory: {}", e))?;

        // Get the appropriate exporter
        let exporter: Box<dyn Exporter> = match options.format {
            ExportFormat::PDF => Box::new(PDFExporter::new()),
            ExportFormat::DOCX => Box::new(DocxExporter::new()),
            ExportFormat::HTML => Box::new(HTMLExporter::new()),
            ExportFormat::Markdown => Box::new(MarkdownExporter::new()),
        };

        let mut exported_paths = Vec::new();

        // Export each session
        for (session, messages) in sessions_with_messages {
            let title = session.title.as_deref().unwrap_or("untitled");
            let safe_title = sanitize_filename(title);
            let date_prefix = session.created_at.format("%Y-%m-%d");
            let filename = format!("{}_{}.{}", date_prefix, safe_title, options.format.extension());

            let output_path = output_dir.join(&filename);

            exporter.export(&session, &messages, output_path.clone(), options)?;

            exported_paths.push(output_path);
        }

        Ok(exported_paths)
    }
}

// Add uuid dependency for temp directory naming
use uuid::Uuid;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_batch_exporter_creation() {
        let exporter = BatchExporter::new();
        assert!(std::mem::size_of_val(&exporter) == 0); // Zero-sized type
    }
}
