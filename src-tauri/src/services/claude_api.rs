//! Claude API integration service
//! Handles communication with Anthropic's Claude API

use crate::error::{ClaudeApiError, Result};
use parking_lot::Mutex;
use reqwest::{Client, header};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::{Duration, Instant};

/// Claude API configuration
const CLAUDE_API_URL: &str = "https://api.anthropic.com/v1/messages";
const CLAUDE_API_VERSION: &str = "2023-06-01";
const DEFAULT_MODEL: &str = "claude-3-5-sonnet-20241022";
const DEFAULT_MAX_TOKENS: u32 = 4096;
const KEYRING_SERVICE: &str = "braindump";
const KEYRING_USERNAME: &str = "claude_api_key";

/// System prompt for Rogerian-style journaling assistant
const SYSTEM_PROMPT: &str = r#"You are a Rogerian-style journaling assistant. Your role is to:

- Validate thoughts without judgment
- Reflect back what you hear
- Focus on clearing mental space, not adding tasks
- Use timestamps for timeline reference
- Help users process their thoughts and feelings
- Create a safe space for self-reflection

Be empathetic, non-directive, and supportive. Your goal is to help users understand themselves better, not to solve their problems or give advice unless explicitly asked."#;

/// Message role in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    User,
    Assistant,
}

/// Message in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: String,
}

impl Message {
    pub fn user(content: impl Into<String>) -> Self {
        Self {
            role: Role::User,
            content: content.into(),
        }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            role: Role::Assistant,
            content: content.into(),
        }
    }
}

/// Claude API request payload
#[derive(Debug, Serialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: u32,
    messages: Vec<Message>,
    system: String,
}

/// Claude API response content block
#[derive(Debug, Deserialize)]
struct ContentBlock {
    #[serde(rename = "type")]
    content_type: String,
    text: String,
}

/// Claude API response
#[derive(Debug, Deserialize)]
struct ClaudeResponse {
    id: String,
    content: Vec<ContentBlock>,
    model: String,
    stop_reason: Option<String>,
    usage: Usage,
}

/// API usage statistics
#[derive(Debug, Deserialize)]
struct Usage {
    input_tokens: u32,
    output_tokens: u32,
}

/// Rate limiting state
struct RateLimiter {
    last_request: Option<Instant>,
    min_interval: Duration,
}

impl RateLimiter {
    fn new(requests_per_minute: u32) -> Self {
        let min_interval = Duration::from_secs(60) / requests_per_minute;
        Self {
            last_request: None,
            min_interval,
        }
    }

    fn wait_if_needed(&mut self) {
        if let Some(last) = self.last_request {
            let elapsed = last.elapsed();
            if elapsed < self.min_interval {
                let wait_time = self.min_interval - elapsed;
                std::thread::sleep(wait_time);
            }
        }
        self.last_request = Some(Instant::now());
    }
}

/// Claude API client
#[derive(Clone)]
pub struct ClaudeClient {
    client: Client,
    rate_limiter: Arc<Mutex<RateLimiter>>,
}

impl ClaudeClient {
    /// Create a new Claude API client
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(60))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            rate_limiter: Arc::new(Mutex::new(RateLimiter::new(50))), // 50 requests per minute
        }
    }

    /// Store API key securely in system keyring
    pub fn store_api_key(api_key: &str) -> Result<()> {
        let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
            .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

        entry
            .set_password(api_key)
            .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

        Ok(())
    }

    /// Retrieve API key from system keyring
    pub fn get_api_key() -> Result<String> {
        let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
            .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

        entry
            .get_password()
            .map_err(|e| match e {
                keyring::Error::NoEntry => ClaudeApiError::ApiKeyNotFound.into(),
                _ => ClaudeApiError::KeyringError(e.to_string()).into(),
            })
    }

    /// Delete API key from system keyring
    pub fn delete_api_key() -> Result<()> {
        let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
            .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

        entry
            .delete_password()
            .map_err(|e| ClaudeApiError::KeyringError(e.to_string()))?;

        Ok(())
    }

    /// Check if an API key is stored
    pub fn has_api_key() -> bool {
        Self::get_api_key().is_ok()
    }

    /// Test the API key by making a simple request
    pub async fn test_api_key(&self) -> Result<bool> {
        let test_message = Message::user("Hello");
        match self.send_message(vec![test_message]).await {
            Ok(_) => Ok(true),
            Err(e) => match e {
                crate::error::BrainDumpError::ClaudeApi(ClaudeApiError::InvalidApiKey) => Ok(false),
                crate::error::BrainDumpError::ClaudeApi(ClaudeApiError::ApiKeyNotFound) => Ok(false),
                _ => Err(e),
            },
        }
    }

    /// Send a message to Claude API and get a response
    pub async fn send_message(&self, messages: Vec<Message>) -> Result<String> {
        // Get API key
        let api_key = Self::get_api_key()?;

        // Rate limiting
        self.rate_limiter.lock().wait_if_needed();

        // Build request
        let request = ClaudeRequest {
            model: DEFAULT_MODEL.to_string(),
            max_tokens: DEFAULT_MAX_TOKENS,
            messages,
            system: SYSTEM_PROMPT.to_string(),
        };

        // Send request
        let response = self
            .client
            .post(CLAUDE_API_URL)
            .header(header::CONTENT_TYPE, "application/json")
            .header("x-api-key", api_key)
            .header("anthropic-version", CLAUDE_API_VERSION)
            .json(&request)
            .send()
            .await
            .map_err(|e| {
                if e.is_timeout() {
                    ClaudeApiError::Timeout
                } else if e.is_connect() {
                    ClaudeApiError::ConnectionFailed(e.to_string())
                } else {
                    ClaudeApiError::RequestFailed(e.to_string())
                }
            })?;

        // Check status code
        let status = response.status();
        if !status.is_success() {
            return Err(match status.as_u16() {
                401 => ClaudeApiError::InvalidApiKey.into(),
                429 => ClaudeApiError::RateLimitExceeded.into(),
                _ => {
                    let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                    ClaudeApiError::RequestFailed(format!("HTTP {}: {}", status, error_text)).into()
                }
            });
        }

        // Parse response
        let claude_response: ClaudeResponse = response
            .json()
            .await
            .map_err(|e| ClaudeApiError::InvalidResponse(e.to_string()))?;

        // Extract text from first content block
        let text = claude_response
            .content
            .first()
            .map(|block| block.text.clone())
            .ok_or_else(|| ClaudeApiError::InvalidResponse("No content in response".to_string()))?;

        Ok(text)
    }
}

impl Default for ClaudeClient {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_message_creation() {
        let user_msg = Message::user("Hello");
        assert!(matches!(user_msg.role, Role::User));
        assert_eq!(user_msg.content, "Hello");

        let assistant_msg = Message::assistant("Hi there!");
        assert!(matches!(assistant_msg.role, Role::Assistant));
        assert_eq!(assistant_msg.content, "Hi there!");
    }

    #[tokio::test]
    async fn test_client_creation() {
        let client = ClaudeClient::new();
        assert!(client.rate_limiter.lock().last_request.is_none());
    }
}
