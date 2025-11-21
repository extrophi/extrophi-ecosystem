//! Research API integration service
//! Handles communication with the Research backend FastAPI for content enrichment

use crate::error::Result;
use reqwest::{header, Client};
use serde::{Deserialize, Serialize};
use std::time::Duration;

/// Research API configuration
const DEFAULT_TIMEOUT_SECS: u64 = 30;

/// Enrichment request payload
#[derive(Debug, Clone, Serialize)]
pub struct EnrichmentRequest {
    pub content: String,
    pub enrichment_type: String, // "expand", "summarize", "analyze"
}

/// Enrichment response from Research API
#[derive(Debug, Deserialize)]
pub struct EnrichmentResponse {
    pub enriched_content: String,
    pub metadata: serde_json::Value,
    pub job_id: String,
}

/// Job status response
#[derive(Debug, Deserialize)]
pub struct JobStatusResponse {
    pub status: String,
    pub result: Option<serde_json::Value>,
}

/// Research API client
#[derive(Clone)]
pub struct ResearchClient {
    client: Client,
    base_url: String,
}

impl ResearchClient {
    /// Create a new Research API client
    pub fn new(base_url: String) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(DEFAULT_TIMEOUT_SECS))
            .build()
            .expect("Failed to create HTTP client");

        Self { client, base_url }
    }

    /// Get the base URL from environment variable or default
    pub fn get_base_url() -> String {
        std::env::var("RESEARCH_API_URL")
            .unwrap_or_else(|_| "http://localhost:8001".to_string())
    }

    /// Enrich content via Research API
    pub async fn enrich_content(
        &self,
        request: EnrichmentRequest,
    ) -> Result<EnrichmentResponse> {
        let url = format!("{}/api/enrich", self.base_url);

        let response = self
            .client
            .post(&url)
            .header(header::CONTENT_TYPE, "application/json")
            .json(&request)
            .send()
            .await
            .map_err(|e| {
                if e.is_timeout() {
                    crate::error::BrainDumpError::Other("Request timeout".to_string())
                } else if e.is_connect() {
                    crate::error::BrainDumpError::Other(format!(
                        "Connection failed: {}. Is the Research API running?",
                        e
                    ))
                } else {
                    crate::error::BrainDumpError::Other(format!("Request failed: {}", e))
                }
            })?;

        // Check status code
        let status = response.status();
        if !status.is_success() {
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            return Err(crate::error::BrainDumpError::Other(format!(
                "API error (HTTP {}): {}",
                status, error_text
            )));
        }

        // Parse response
        let enrichment = response.json::<EnrichmentResponse>().await.map_err(|e| {
            crate::error::BrainDumpError::Other(format!("Invalid response format: {}", e))
        })?;

        Ok(enrichment)
    }

    /// Check job status
    pub async fn check_status(&self, job_id: &str) -> Result<String> {
        let url = format!("{}/api/enrich/status/{}", self.base_url, job_id);

        let response = self.client.get(&url).send().await.map_err(|e| {
            crate::error::BrainDumpError::Other(format!("Status check failed: {}", e))
        })?;

        if !response.status().is_success() {
            return Err(crate::error::BrainDumpError::Other(format!(
                "Status check failed: HTTP {}",
                response.status()
            )));
        }

        let status_response: JobStatusResponse = response.json().await.map_err(|e| {
            crate::error::BrainDumpError::Other(format!("Invalid status response: {}", e))
        })?;

        Ok(status_response.status)
    }

    /// Enrich content with automatic retry logic
    pub async fn enrich_content_with_retry(
        &self,
        request: EnrichmentRequest,
        max_retries: u32,
    ) -> Result<EnrichmentResponse> {
        let mut attempts = 0;
        let mut last_error = None;

        while attempts <= max_retries {
            match self.enrich_content(request.clone()).await {
                Ok(response) => return Ok(response),
                Err(e) => {
                    last_error = Some(e);
                    attempts += 1;

                    if attempts <= max_retries {
                        // Exponential backoff: 2^attempts seconds
                        let backoff_secs = 2_u64.pow(attempts);
                        tokio::time::sleep(Duration::from_secs(backoff_secs)).await;
                    }
                }
            }
        }

        // Return the last error if all retries failed
        Err(last_error.unwrap_or_else(|| {
            crate::error::BrainDumpError::Other("All retry attempts failed".to_string())
        }))
    }

    /// Test the connection to Research API
    pub async fn test_connection(&self) -> Result<bool> {
        let url = format!("{}/health", self.base_url);

        match self.client.get(&url).send().await {
            Ok(response) => Ok(response.status().is_success()),
            Err(_) => Ok(false),
        }
    }
}

impl Default for ResearchClient {
    fn default() -> Self {
        Self::new(Self::get_base_url())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = ResearchClient::new("http://localhost:8001".to_string());
        assert_eq!(client.base_url, "http://localhost:8001");
    }

    #[test]
    fn test_default_base_url() {
        let url = ResearchClient::get_base_url();
        assert_eq!(url, "http://localhost:8001");
    }

    #[tokio::test]
    async fn test_enrichment_request_serialization() {
        let request = EnrichmentRequest {
            content: "Test content".to_string(),
            enrichment_type: "expand".to_string(),
        };

        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("Test content"));
        assert!(json.contains("expand"));
    }
}
