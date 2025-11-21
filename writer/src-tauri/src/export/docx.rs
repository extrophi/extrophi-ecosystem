use crate::db::models::{ChatSession, Message, MessageRole};
use super::{Exporter, ExportOptions};
use docx_rs::*;
use std::fs::File;
use std::path::PathBuf;

pub struct DocxExporter;

impl DocxExporter {
    pub fn new() -> Self {
        Self
    }
}

impl Exporter for DocxExporter {
    fn export(
        &self,
        session: &ChatSession,
        messages: &[Message],
        output_path: PathBuf,
        options: &ExportOptions,
    ) -> Result<(), String> {
        let title = session.title.as_deref().unwrap_or("Untitled Session");

        let mut doc = Docx::new();

        // Add title
        doc = doc.add_paragraph(
            Paragraph::new()
                .add_run(
                    Run::new()
                        .add_text(title)
                        .size(48)
                        .bold()
                )
        );

        // Add metadata if requested
        if options.include_metadata {
            doc = doc.add_paragraph(
                Paragraph::new()
                    .add_run(
                        Run::new()
                            .add_text(&format!(
                                "Created: {}",
                                session.created_at.format("%Y-%m-%d %H:%M")
                            ))
                            .size(20)
                            .color("666666")
                    )
            );

            doc = doc.add_paragraph(
                Paragraph::new()
                    .add_run(
                        Run::new()
                            .add_text(&format!("Messages: {}", messages.len()))
                            .size(20)
                            .color("666666")
                    )
            );

            // Calculate word count
            let word_count: usize = messages
                .iter()
                .map(|m| m.content.split_whitespace().count())
                .sum();

            doc = doc.add_paragraph(
                Paragraph::new()
                    .add_run(
                        Run::new()
                            .add_text(&format!("Word Count: {}", word_count))
                            .size(20)
                            .color("666666")
                    )
            );

            // Add spacing
            doc = doc.add_paragraph(Paragraph::new());
        }

        // Add separator
        doc = doc.add_paragraph(
            Paragraph::new()
                .add_run(
                    Run::new()
                        .add_text("───────────────────────────────────────")
                        .color("CCCCCC")
                )
        );

        // Add "Conversation" heading
        doc = doc.add_paragraph(
            Paragraph::new()
                .add_run(
                    Run::new()
                        .add_text("Conversation")
                        .size(32)
                        .bold()
                )
        );

        doc = doc.add_paragraph(Paragraph::new());

        // Add messages if requested
        if options.include_chat {
            for msg in messages {
                let role = match msg.role {
                    MessageRole::User => "User",
                    MessageRole::Assistant => "Assistant",
                };
                let timestamp = msg.created_at.format("%H:%M");

                // Add role and timestamp
                doc = doc.add_paragraph(
                    Paragraph::new()
                        .add_run(
                            Run::new()
                                .add_text(&format!("{} ({})", role, timestamp))
                                .size(24)
                                .bold()
                                .color(match msg.role {
                                    MessageRole::User => "4F46E5",
                                    MessageRole::Assistant => "059669",
                                })
                        )
                );

                // Add message content
                doc = doc.add_paragraph(
                    Paragraph::new()
                        .add_run(
                            Run::new()
                                .add_text(&msg.content)
                                .size(22)
                        )
                );

                // Add spacing between messages
                doc = doc.add_paragraph(Paragraph::new());
            }
        }

        // Add footer
        doc = doc.add_paragraph(
            Paragraph::new()
                .add_run(
                    Run::new()
                        .add_text("───────────────────────────────────────")
                        .color("CCCCCC")
                )
        );

        doc = doc.add_paragraph(
            Paragraph::new()
                .add_run(
                    Run::new()
                        .add_text(&format!(
                            "Generated: {} | BrainDump v3.0",
                            chrono::Local::now().format("%Y-%m-%d %H:%M")
                        ))
                        .size(18)
                        .color("999999")
                )
        );

        // Save the document
        let file = File::create(&output_path)
            .map_err(|e| format!("Failed to create DOCX file: {}", e))?;

        doc.build()
            .pack(file)
            .map_err(|e| format!("Failed to save DOCX: {}", e))?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_docx_exporter_creation() {
        let exporter = DocxExporter::new();
        assert!(std::mem::size_of_val(&exporter) == 0); // Zero-sized type
    }
}
