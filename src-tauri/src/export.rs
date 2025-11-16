use crate::db::models::{ChatSession, Message};
use crate::error::BrainDumpError;
use chrono::Local;
use std::fs;
use std::path::PathBuf;

/// Export a chat session to markdown
pub fn export_session_to_markdown(
    session: &ChatSession,
    messages: &[Message],
) -> Result<PathBuf, BrainDumpError> {
    let markdown = generate_markdown(session, messages);
    let file_path = get_export_path(session)?;

    // Create directory if it doesn't exist
    if let Some(parent) = file_path.parent() {
        fs::create_dir_all(parent)?;
    }

    fs::write(&file_path, markdown)?;
    Ok(file_path)
}

fn generate_markdown(session: &ChatSession, messages: &[Message]) -> String {
    let mut md = String::new();

    // Title
    let title = session.title.as_deref().unwrap_or("Untitled Session");
    md.push_str(&format!("# {}\n\n", title));

    // Metadata
    md.push_str(&format!(
        "**Created:** {}\n",
        session.created_at.format("%Y-%m-%d %H:%M")
    ));
    md.push_str(&format!("**Messages:** {}\n", messages.len()));

    // Calculate word count
    let word_count: usize = messages
        .iter()
        .map(|m| m.content.split_whitespace().count())
        .sum();
    md.push_str(&format!("**Word Count:** {}\n", word_count));

    // Duration (first to last message)
    if let (Some(first), Some(last)) = (messages.first(), messages.last()) {
        let duration = last.created_at.signed_duration_since(first.created_at);
        let minutes = duration.num_minutes();
        md.push_str(&format!("**Duration:** {} minutes\n", minutes));
    }

    md.push_str("\n---\n\n");
    md.push_str("## Conversation\n\n");

    // Messages
    for msg in messages {
        let role = match msg.role {
            crate::db::models::MessageRole::User => "User",
            crate::db::models::MessageRole::Assistant => "Assistant",
        };
        let timestamp = msg.created_at.format("%H:%M");

        md.push_str(&format!("**{} ({})**\n", role, timestamp));
        md.push_str(&format!("{}\n\n", msg.content));
    }

    // Footer
    md.push_str("---\n\n");
    md.push_str(&format!(
        "**Generated:** {}\n",
        Local::now().format("%Y-%m-%d %H:%M")
    ));
    md.push_str("**Tool:** BrainDump v3.0\n");

    md
}

fn get_export_path(session: &ChatSession) -> Result<PathBuf, BrainDumpError> {
    // Export to ~/Documents/BrainDump/
    let home = dirs::home_dir()
        .ok_or_else(|| BrainDumpError::Other("Could not find home directory".to_string()))?;

    let export_dir = home.join("Documents").join("BrainDump");

    // Filename: YYYY-MM-DD_session_title.md
    let date_prefix = session.created_at.format("%Y-%m-%d");
    let title = session.title.as_deref().unwrap_or("untitled");
    let safe_title = sanitize_filename(title);
    let filename = format!("{}_{}.md", date_prefix, safe_title);

    Ok(export_dir.join(filename))
}

fn sanitize_filename(title: &str) -> String {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sanitize_filename() {
        assert_eq!(
            sanitize_filename("Brain Dump 2025-11-15"),
            "Brain_Dump_2025-11-15"
        );
        assert_eq!(sanitize_filename("Test: Session!"), "Test-_Session-");
    }
}
