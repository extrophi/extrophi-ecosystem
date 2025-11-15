//! OpenAI API integration service
//! Handles communication with OpenAI's GPT-4 API

use crate::error::{OpenAiApiError, Result};
use parking_lot::Mutex;
use reqwest::{Client, header};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::{Duration, Instant};

/// OpenAI API configuration
const OPENAI_API_URL: &str = "https://api.openai.com/v1/chat/completions";
const DEFAULT_MODEL: &str = "gpt-4-turbo-preview";
const DEFAULT_MAX_TOKENS: u32 = 4096;
const KEYRING_SERVICE: &str = "braindump-openai";
const KEYRING_USERNAME: &str = "openai_api_key";

/// Message role in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    User,
    Assistant,
    System,
}

/// Message in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

impl ChatMessage {
    pub fn user(content: impl Into<String>) -> Self {
        Self {
            role: "user".to_string(),
            content: content.into(),
        }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            role: "assistant".to_string(),
            content: content.into(),
        }
    }

    pub fn system(content: impl Into<String>) -> Self {
        Self {
            role: "system".to_string(),
            content: content.into(),
        }
    }
}

/// OpenAI API request payload
#[derive(Debug, Serialize)]
struct OpenAiRequest {
    model: String,
    messages: Vec<ChatMessage>,
    max_tokens: u32,
}

/// OpenAI API response choice
#[derive(Debug, Deserialize)]
struct Choice {
    message: ChatMessage,
    finish_reason: Option<String>,
}

/// OpenAI API response
#[derive(Debug, Deserialize)]
struct OpenAiResponse {
    id: String,
    choices: Vec<Choice>,
    usage: Usage,
}

/// API usage statistics
#[derive(Debug, Deserialize)]
struct Usage {
    prompt_tokens: u32,
    completion_tokens: u32,
    total_tokens: u32,
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

/// OpenAI API client
#[derive(Clone)]
pub struct OpenAiClient {
    client: Client,
    rate_limiter: Arc<Mutex<RateLimiter>>,
}

impl OpenAiClient {
    /// Create a new OpenAI API client
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(60))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            rate_limiter: Arc::new(Mutex::new(RateLimiter::new(60))), // 60 requests per minute
        }
    }

    /// Store API key securely in system keyring
    pub fn store_api_key(api_key: &str) -> Result<()> {
        let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
            .map_err(|e| OpenAiApiError::KeyringError(e.to_string()))?;

        entry
            .set_password(api_key)
            .map_err(|e| OpenAiApiError::KeyringError(e.to_string()))?;

        Ok(())
    }

    /// Retrieve API key from system keyring
    pub fn get_api_key() -> Result<String> {
        let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
            .map_err(|e| OpenAiApiError::KeyringError(e.to_string()))?;

        entry
            .get_password()
            .map_err(|e| match e {
                keyring::Error::NoEntry => OpenAiApiError::ApiKeyNotFound,
                _ => OpenAiApiError::KeyringError(e.to_string()),
            })
    }

    /// Delete API key from system keyring
    pub fn delete_api_key() -> Result<()> {
        let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USERNAME)
            .map_err(|e| OpenAiApiError::KeyringError(e.to_string()))?;

        entry
            .delete_credential()
            .map_err(|e| OpenAiApiError::KeyringError(e.to_string()))?;

        Ok(())
    }

    /// Check if an API key is stored
    pub fn has_api_key() -> bool {
        Self::get_api_key().is_ok()
    }

    /// Test the API key by making a simple request
    pub async fn test_connection(&self) -> Result<bool> {
        let test_message = ChatMessage::user("Hello");
        match self.send_message(vec![test_message], None).await {
            Ok(_) => Ok(true),
            Err(e) => match e {
                crate::error::BrainDumpError::OpenAiApi(OpenAiApiError::InvalidApiKey) => Ok(false),
                crate::error::BrainDumpError::OpenAiApi(OpenAiApiError::ApiKeyNotFound) => Ok(false),
                _ => Err(e),
            },
        }
    }

    /// Send a message to OpenAI API and get a response
    pub async fn send_message(
        &self,
        messages: Vec<ChatMessage>,
        system_prompt: Option<String>,
    ) -> Result<String> {
        // Get API key
        let api_key = Self::get_api_key()?;

        // Rate limiting
        self.rate_limiter.lock().wait_if_needed();

        // Build messages with optional system prompt
        let mut all_messages = Vec::new();
        if let Some(prompt) = system_prompt {
            all_messages.push(ChatMessage::system(prompt));
        }
        all_messages.extend(messages);

        // Build request
        let request = OpenAiRequest {
            model: DEFAULT_MODEL.to_string(),
            messages: all_messages,
            max_tokens: DEFAULT_MAX_TOKENS,
        };

        // Send request
        let response = self
            .client
            .post(OPENAI_API_URL)
            .header(header::CONTENT_TYPE, "application/json")
            .header(header::AUTHORIZATION, format!("Bearer {}", api_key))
            .json(&request)
            .send()
            .await
            .map_err(|e| {
                if e.is_timeout() {
                    OpenAiApiError::Timeout
                } else if e.is_connect() {
                    OpenAiApiError::ConnectionFailed(e.to_string())
                } else {
                    OpenAiApiError::RequestFailed(e.to_string())
                }
            })?;

        // Check status code
        let status = response.status();
        if !status.is_success() {
            return Err(match status.as_u16() {
                401 => OpenAiApiError::InvalidApiKey.into(),
                429 => OpenAiApiError::RateLimitExceeded.into(),
                _ => {
                    let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                    OpenAiApiError::RequestFailed(format!("HTTP {}: {}", status, error_text)).into()
                }
            });
        }

        // Parse response
        let openai_response: OpenAiResponse = response
            .json()
            .await
            .map_err(|e| OpenAiApiError::InvalidResponse(e.to_string()))?;

        // Extract text from first choice
        let text = openai_response
            .choices
            .first()
            .map(|choice| choice.message.content.clone())
            .ok_or_else(|| OpenAiApiError::InvalidResponse("No choices in response".to_string()))?;

        Ok(text)
    }
}

impl Default for OpenAiClient {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_message_creation() {
        let user_msg = ChatMessage::user("Hello");
        assert_eq!(user_msg.role, "user");
        assert_eq!(user_msg.content, "Hello");

        let assistant_msg = ChatMessage::assistant("Hi there!");
        assert_eq!(assistant_msg.role, "assistant");
        assert_eq!(assistant_msg.content, "Hi there!");

        let system_msg = ChatMessage::system("You are a helpful assistant");
        assert_eq!(system_msg.role, "system");
        assert_eq!(system_msg.content, "You are a helpful assistant");
    }

    #[test]
    fn test_client_creation() {
        let client = OpenAiClient::new();
        assert!(client.rate_limiter.lock().last_request.is_none());
    }
}
