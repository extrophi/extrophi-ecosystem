use crate::db::models::{ChatSession, Message, MessageRole};
use super::{Exporter, ExportOptions};
use printpdf::*;
use std::fs::File;
use std::io::BufWriter;
use std::path::PathBuf;

pub struct PDFExporter;

impl PDFExporter {
    pub fn new() -> Self {
        Self
    }

    fn add_text_block(
        &self,
        current_layer: &PdfLayerReference,
        text: &str,
        font: &IndirectFontRef,
        x: Mm,
        y: Mm,
        font_size: f32,
        max_width: Mm,
    ) -> Mm {
        let line_height = Mm(font_size as f64 * 0.4);
        let mut current_y = y;

        // Simple word wrapping
        let words: Vec<&str> = text.split_whitespace().collect();
        let mut current_line = String::new();
        let chars_per_line = (max_width.0 / (font_size as f64 * 0.5)) as usize;

        for word in words {
            let test_line = if current_line.is_empty() {
                word.to_string()
            } else {
                format!("{} {}", current_line, word)
            };

            if test_line.len() > chars_per_line && !current_line.is_empty() {
                current_layer.use_text(
                    current_line.clone(),
                    font_size as f64,
                    x,
                    current_y,
                    font,
                );
                current_y = current_y - line_height;
                current_line = word.to_string();
            } else {
                current_line = test_line;
            }
        }

        // Add remaining text
        if !current_line.is_empty() {
            current_layer.use_text(
                current_line,
                font_size as f64,
                x,
                current_y,
                font,
            );
            current_y = current_y - line_height;
        }

        current_y
    }
}

impl Exporter for PDFExporter {
    fn export(
        &self,
        session: &ChatSession,
        messages: &[Message],
        output_path: PathBuf,
        options: &ExportOptions,
    ) -> Result<(), String> {
        let title = session.title.as_deref().unwrap_or("Untitled Session");

        let (doc, page1, layer1) = PdfDocument::new(
            title,
            Mm(210.0), // A4 width
            Mm(297.0), // A4 height
            "Layer 1",
        );

        let font = doc
            .add_builtin_font(BuiltinFont::Helvetica)
            .map_err(|e| format!("Failed to add font: {}", e))?;

        let font_bold = doc
            .add_builtin_font(BuiltinFont::HelveticaBold)
            .map_err(|e| format!("Failed to add bold font: {}", e))?;

        let current_layer = doc.get_page(page1).get_layer(layer1);
        let mut current_y = Mm(280.0);
        let margin_x = Mm(15.0);
        let max_width = Mm(180.0);

        // Add title
        current_layer.use_text(
            title,
            24.0,
            margin_x,
            current_y,
            &font_bold,
        );
        current_y = current_y - Mm(10.0);

        // Add metadata if requested
        if options.include_metadata {
            current_layer.use_text(
                &format!("Created: {}", session.created_at.format("%Y-%m-%d %H:%M")),
                10.0,
                margin_x,
                current_y,
                &font,
            );
            current_y = current_y - Mm(5.0);

            current_layer.use_text(
                &format!("Messages: {}", messages.len()),
                10.0,
                margin_x,
                current_y,
                &font,
            );
            current_y = current_y - Mm(10.0);
        }

        // Add separator
        let line = Line {
            points: vec![
                (Point::new(margin_x, current_y), false),
                (Point::new(Mm(195.0), current_y), false),
            ],
            is_closed: false,
        };
        current_layer.add_shape(line);
        current_y = current_y - Mm(10.0);

        // Add messages if requested
        if options.include_chat {
            for msg in messages {
                // Check if we need a new page
                if current_y < Mm(30.0) {
                    let (page, layer) = doc.add_page(Mm(210.0), Mm(297.0), "Layer 1");
                    let current_layer = doc.get_page(page).get_layer(layer);
                    current_y = Mm(280.0);
                }

                let role = match msg.role {
                    MessageRole::User => "User",
                    MessageRole::Assistant => "Assistant",
                };
                let timestamp = msg.created_at.format("%H:%M");

                // Add role and timestamp
                current_layer.use_text(
                    &format!("{} ({})", role, timestamp),
                    11.0,
                    margin_x,
                    current_y,
                    &font_bold,
                );
                current_y = current_y - Mm(5.0);

                // Add message content
                current_y = self.add_text_block(
                    &current_layer,
                    &msg.content,
                    &font,
                    margin_x + Mm(5.0),
                    current_y,
                    10.0,
                    max_width - Mm(5.0),
                );
                current_y = current_y - Mm(5.0);
            }
        }

        // Add footer on last page
        current_y = Mm(15.0);
        current_layer.use_text(
            &format!("Generated: {} | BrainDump v3.0", chrono::Local::now().format("%Y-%m-%d %H:%M")),
            8.0,
            margin_x,
            current_y,
            &font,
        );

        // Save the PDF
        let file = File::create(&output_path)
            .map_err(|e| format!("Failed to create PDF file: {}", e))?;

        doc.save(&mut BufWriter::new(file))
            .map_err(|e| format!("Failed to save PDF: {}", e))?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    #[test]
    fn test_pdf_exporter_creation() {
        let exporter = PDFExporter::new();
        assert!(std::mem::size_of_val(&exporter) == 0); // Zero-sized type
    }
}
