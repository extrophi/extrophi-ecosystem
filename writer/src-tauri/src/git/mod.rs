//! Git publish module - selective sync of BUSINESS + IDEAS cards only
//!
//! Privacy Rules:
//! - PRIVATE: NEVER sync (stays local only)
//! - PERSONAL: NEVER sync (stays local only)
//! - BUSINESS: Sync to GitHub
//! - IDEAS: Sync to GitHub

use crate::db::models::{Card, PrivacyLevel};
use crate::db::repository::Repository;
use crate::error::GitError;
use chrono::Utc;
use git2::{Commit, Cred, Repository as GitRepository, Signature};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

// Implement conversions for git module specific errors
impl From<std::io::Error> for GitError {
    fn from(err: std::io::Error) -> Self {
        GitError::IoError(err.to_string())
    }
}

impl From<git2::Error> for GitError {
    fn from(err: git2::Error) -> Self {
        GitError::Git2Error(err.to_string())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PublishResult {
    pub cards_published: usize,
    pub commit_sha: String,
    pub pushed: bool,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PublishStatus {
    pub publishable_count: usize,
    pub published_count: usize,
    pub last_publish_at: Option<String>,
    pub last_commit_sha: Option<String>,
}

/// Git publisher for cards
pub struct GitPublisher {
    repo_path: PathBuf,
    content_dir: PathBuf,
}

impl GitPublisher {
    /// Create a new Git publisher
    pub fn new(repo_path: impl Into<PathBuf>) -> Self {
        let repo_path = repo_path.into();
        let content_dir = repo_path.join("content");

        Self {
            repo_path,
            content_dir,
        }
    }

    /// Initialize the Git repository if it doesn't exist
    pub fn initialize_repository(&self) -> Result<(), GitError> {
        // Check if repo already exists
        if self.repo_path.join(".git").exists() {
            return Ok(());
        }

        // Initialize new repository
        GitRepository::init(&self.repo_path)?;

        // Create content directory
        fs::create_dir_all(&self.content_dir)?;

        // Create .gitignore
        let gitignore_path = self.repo_path.join(".gitignore");
        fs::write(gitignore_path, "# BrainDump Published Content\n\n# Ignore system files\n.DS_Store\nThumbs.db\n")?;

        // Create initial README
        let readme_path = self.repo_path.join("README.md");
        fs::write(
            readme_path,
            "# BrainDump Published Content\n\nThis repository contains published cards from BrainDump.\n\n**Privacy Levels Published:**\n- BUSINESS: Work-related content\n- IDEAS: Public-safe ideas and concepts\n\n**Privacy Levels NOT Published:**\n- PRIVATE: Contains PII (SSN, email, credit cards)\n- PERSONAL: Personal references (\"I feel\", family)\n",
        )?;

        // Initial commit
        let repo = GitRepository::open(&self.repo_path)?;
        let mut index = repo.index()?;
        index.add_path(Path::new(".gitignore"))?;
        index.add_path(Path::new("README.md"))?;
        index.write()?;

        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        let signature = Signature::now("BrainDump", "braindump@local")?;

        repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            "Initial commit - BrainDump content repository",
            &tree,
            &[],
        )?;

        Ok(())
    }

    /// Filter cards by privacy level (BUSINESS + IDEAS only)
    pub fn filter_publishable_cards(&self, cards: &[Card]) -> Vec<Card> {
        cards
            .iter()
            .filter(|card| {
                matches!(
                    card.privacy_level,
                    Some(PrivacyLevel::Business) | Some(PrivacyLevel::Ideas)
                )
            })
            .cloned()
            .collect()
    }

    /// Export card to markdown file
    pub fn export_card_to_markdown(&self, card: &Card) -> Result<PathBuf, GitError> {
        // Ensure content directory exists
        fs::create_dir_all(&self.content_dir)?;

        // Generate filename from card ID
        let card_id = card
            .id
            .ok_or_else(|| GitError::GitOperationFailed("Card has no ID".to_string()))?;
        let filename = format!("card-{}.md", card_id);
        let filepath = self.content_dir.join(&filename);

        // Create markdown content
        let privacy_level = card
            .privacy_level
            .as_ref()
            .map(|p| p.as_str())
            .unwrap_or("UNKNOWN");
        let category = card
            .category
            .as_ref()
            .map(|c| c.as_str())
            .unwrap_or("UNCATEGORIZED");

        let markdown = format!(
            "---\nid: {}\nprivacy: {}\ncategory: {}\ncreated: {}\nupdated: {}\n---\n\n# Card {}\n\n{}\n",
            card_id,
            privacy_level,
            category,
            card.created_at.format("%Y-%m-%d %H:%M:%S"),
            card.updated_at.format("%Y-%m-%d %H:%M:%S"),
            card_id,
            card.content
        );

        // Write to file
        fs::write(&filepath, markdown)?;

        Ok(filepath)
    }

    /// Export all publishable cards to markdown files
    pub fn export_all_publishable_cards(&self, cards: &[Card]) -> Result<Vec<PathBuf>, GitError> {
        let publishable = self.filter_publishable_cards(cards);

        if publishable.is_empty() {
            return Err(GitError::NoPublishableCards);
        }

        let mut exported_files = Vec::new();
        for card in publishable {
            let filepath = self.export_card_to_markdown(&card)?;
            exported_files.push(filepath);
        }

        Ok(exported_files)
    }

    /// Git add files to staging area
    pub fn git_add(&self, files: &[PathBuf]) -> Result<(), GitError> {
        let repo = GitRepository::open(&self.repo_path)?;
        let mut index = repo.index()?;

        for file in files {
            // Get relative path from repo root
            let relative_path = file
                .strip_prefix(&self.repo_path)
                .map_err(|e| GitError::GitOperationFailed(format!("Invalid file path: {}", e)))?;
            index.add_path(relative_path)?;
        }

        index.write()?;
        Ok(())
    }

    /// Git commit with message
    pub fn git_commit(&self, message: &str) -> Result<String, GitError> {
        let repo = GitRepository::open(&self.repo_path)?;
        let mut index = repo.index()?;
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;

        let signature = Signature::now("BrainDump", "braindump@local")?;

        // Get parent commit
        let parent_commit = self.get_head_commit(&repo)?;

        let commit_id = repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &[&parent_commit],
        )?;

        Ok(commit_id.to_string())
    }

    /// Get HEAD commit
    fn get_head_commit<'repo>(&self, repo: &'repo GitRepository) -> Result<Commit<'repo>, GitError> {
        let head = repo.head()?;
        let commit = head.peel_to_commit()?;
        Ok(commit)
    }

    /// Git push to remote
    pub fn git_push(&self, remote_name: &str, branch: &str) -> Result<(), GitError> {
        let repo = GitRepository::open(&self.repo_path)?;

        // Get remote
        let mut remote = repo
            .find_remote(remote_name)
            .map_err(|e| GitError::GitOperationFailed(format!("Remote '{}' not found: {}", remote_name, e)))?;

        // Setup callbacks for authentication
        let mut callbacks = RemoteCallbacks::new();
        callbacks.credentials(|_url, username_from_url, _allowed_types| {
            Cred::ssh_key_from_agent(username_from_url.unwrap_or("git"))
        });

        let mut push_options = PushOptions::new();
        push_options.remote_callbacks(callbacks);

        // Push
        let refspec = format!("refs/heads/{}:refs/heads/{}", branch, branch);
        remote.push(&[&refspec], Some(&mut push_options))?;

        Ok(())
    }

    /// Publish cards: export, commit, and optionally push
    pub fn publish_cards(
        &self,
        cards: &[Card],
        commit_message: &str,
        should_push: bool,
        remote_name: &str,
        branch: &str,
    ) -> Result<PublishResult, GitError> {
        // Filter and export publishable cards
        let exported_files = self.export_all_publishable_cards(cards)?;
        let cards_published = exported_files.len();

        // Git add
        self.git_add(&exported_files)?;

        // Git commit
        let commit_sha = self.git_commit(commit_message)?;

        // Git push (optional)
        let pushed = if should_push {
            match self.git_push(remote_name, branch) {
                Ok(_) => true,
                Err(e) => {
                    eprintln!("Warning: Failed to push: {}", e);
                    false
                }
            }
        } else {
            false
        };

        Ok(PublishResult {
            cards_published,
            commit_sha,
            pushed,
            timestamp: Utc::now().to_rfc3339(),
        })
    }

    /// Get publish status
    pub fn get_status(&self, repository: &Repository) -> Result<PublishStatus, GitError> {
        // Get publishable cards count
        let publishable_cards = repository
            .get_publishable_cards(1000)
            .map_err(|e| GitError::DatabaseError(e.to_string()))?;
        let publishable_count = publishable_cards.len();

        // Count already published cards
        let published_count = publishable_cards.iter().filter(|c| c.published).count();

        // Get last commit info if repo exists
        let (last_commit_sha, last_publish_at) = if self.repo_path.join(".git").exists() {
            match GitRepository::open(&self.repo_path) {
                Ok(repo) => match self.get_head_commit(&repo) {
                    Ok(commit) => {
                        let sha = commit.id().to_string();
                        let time = commit.time();
                        let timestamp = chrono::DateTime::from_timestamp(time.seconds(), 0)
                            .map(|dt| dt.to_rfc3339());
                        (Some(sha), timestamp)
                    }
                    Err(_) => (None, None),
                },
                Err(_) => (None, None),
            }
        } else {
            (None, None)
        };

        Ok(PublishStatus {
            publishable_count,
            published_count,
            last_publish_at,
            last_commit_sha,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::models::CardCategory;
    use chrono::Utc;
    use tempfile::TempDir;

    fn create_test_card(id: i64, privacy_level: PrivacyLevel, content: &str) -> Card {
        Card {
            id: Some(id),
            content: content.to_string(),
            privacy_level: Some(privacy_level),
            published: false,
            git_sha: None,
            category: Some(CardCategory::Ideas),
            session_id: None,
            message_id: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        }
    }

    #[test]
    fn test_filter_publishable_cards() {
        let temp_dir = TempDir::new().unwrap();
        let publisher = GitPublisher::new(temp_dir.path());

        let cards = vec![
            create_test_card(1, PrivacyLevel::Private, "Private content with SSN"),
            create_test_card(2, PrivacyLevel::Personal, "Personal: I feel sad"),
            create_test_card(3, PrivacyLevel::Business, "Client meeting notes"),
            create_test_card(4, PrivacyLevel::Ideas, "New product idea"),
        ];

        let publishable = publisher.filter_publishable_cards(&cards);

        assert_eq!(publishable.len(), 2);
        assert_eq!(publishable[0].id, Some(3));
        assert_eq!(publishable[1].id, Some(4));
    }

    #[test]
    fn test_export_card_to_markdown() {
        let temp_dir = TempDir::new().unwrap();
        let publisher = GitPublisher::new(temp_dir.path());

        let card = create_test_card(42, PrivacyLevel::Business, "Test business content");

        let filepath = publisher.export_card_to_markdown(&card).unwrap();

        assert!(filepath.exists());
        assert_eq!(filepath.file_name().unwrap(), "card-42.md");

        let content = fs::read_to_string(&filepath).unwrap();
        assert!(content.contains("privacy: BUSINESS"));
        assert!(content.contains("Test business content"));
    }

    #[test]
    fn test_initialize_repository() {
        let temp_dir = TempDir::new().unwrap();
        let publisher = GitPublisher::new(temp_dir.path());

        publisher.initialize_repository().unwrap();

        assert!(temp_dir.path().join(".git").exists());
        assert!(temp_dir.path().join("content").exists());
        assert!(temp_dir.path().join(".gitignore").exists());
        assert!(temp_dir.path().join("README.md").exists());
    }
}
