use crate::db::models::{ChatSession, Message, MessageRole};
use super::{Exporter, ExportOptions};
use handlebars::Handlebars;
use serde_json::json;
use std::fs;
use std::path::PathBuf;

pub struct HTMLExporter {
    handlebars: Handlebars<'static>,
}

impl HTMLExporter {
    pub fn new() -> Self {
        let mut handlebars = Handlebars::new();

        // Register default template
        let template_content = include_str!("../templates/session.hbs");
        handlebars
            .register_template_string("session", template_content)
            .expect("Failed to register session template");

        Self { handlebars }
    }

    pub fn register_custom_template(&mut self, name: &str, template: &str) -> Result<(), String> {
        self.handlebars
            .register_template_string(name, template)
            .map_err(|e| format!("Failed to register template: {}", e))
    }
}

impl Exporter for HTMLExporter {
    fn export(
        &self,
        session: &ChatSession,
        messages: &[Message],
        output_path: PathBuf,
        options: &ExportOptions,
    ) -> Result<(), String> {
        let title = session.title.as_deref().unwrap_or("Untitled Session");

        // Calculate word count
        let word_count: usize = messages
            .iter()
            .map(|m| m.content.split_whitespace().count())
            .sum();

        // Prepare messages data
        let messages_data: Vec<_> = messages
            .iter()
            .map(|msg| {
                let role = match msg.role {
                    MessageRole::User => "user",
                    MessageRole::Assistant => "assistant",
                };
                let role_display = match msg.role {
                    MessageRole::User => "User",
                    MessageRole::Assistant => "Assistant",
                };

                json!({
                    "role": role,
                    "role_display": role_display,
                    "content": msg.content,
                    "timestamp": msg.created_at.format("%H:%M").to_string(),
                })
            })
            .collect();

        let data = json!({
            "title": title,
            "created_at": session.created_at.format("%Y-%m-%d %H:%M").to_string(),
            "message_count": messages.len(),
            "word_count": word_count,
            "include_metadata": options.include_metadata,
            "include_chat": options.include_chat,
            "messages": messages_data,
            "generated_at": chrono::Local::now().format("%Y-%m-%d %H:%M").to_string(),
        });

        // Use custom template if provided, otherwise use default
        let template_name = options.template.as_deref().unwrap_or("session");

        let html = self
            .handlebars
            .render(template_name, &data)
            .map_err(|e| format!("Failed to render template: {}", e))?;

        // Create directory if it doesn't exist
        if let Some(parent) = output_path.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("Failed to create directory: {}", e))?;
        }

        fs::write(&output_path, html)
            .map_err(|e| format!("Failed to write HTML file: {}", e))?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_html_exporter_creation() {
        let exporter = HTMLExporter::new();
        assert!(exporter.handlebars.has_template("session"));
    }

    #[test]
    fn test_custom_template_registration() {
        let mut exporter = HTMLExporter::new();
        let result = exporter.register_custom_template(
            "custom",
            "<html><body>{{title}}</body></html>"
        );
        assert!(result.is_ok());
        assert!(exporter.handlebars.has_template("custom"));
    }
}
