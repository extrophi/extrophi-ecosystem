//! Integration tests for Research API client
//! Tests the HTTP client functionality for content enrichment

use braindump::services::research_client::{EnrichmentRequest, ResearchClient};

#[test]
fn test_client_initialization() {
    // Test client can be created with custom URL
    let client = ResearchClient::new("http://localhost:8001".to_string());
    assert_eq!(client.base_url, "http://localhost:8001");

    // Test default client creation
    let default_client = ResearchClient::default();
    assert!(!default_client.base_url.is_empty());
}

#[test]
fn test_enrichment_request_creation() {
    let request = EnrichmentRequest {
        content: "Test content for enrichment".to_string(),
        enrichment_type: "expand".to_string(),
    };

    assert_eq!(request.content, "Test content for enrichment");
    assert_eq!(request.enrichment_type, "expand");
}

#[test]
fn test_enrichment_request_serialization() {
    let request = EnrichmentRequest {
        content: "Test content".to_string(),
        enrichment_type: "summarize".to_string(),
    };

    let json = serde_json::to_string(&request).expect("Failed to serialize request");
    assert!(json.contains("Test content"));
    assert!(json.contains("summarize"));
}

#[tokio::test]
async fn test_enrichment_request_clone() {
    let request = EnrichmentRequest {
        content: "Original content".to_string(),
        enrichment_type: "analyze".to_string(),
    };

    let cloned = request.clone();
    assert_eq!(request.content, cloned.content);
    assert_eq!(request.enrichment_type, cloned.enrichment_type);
}

// NOTE: The following tests require the Research API to be running
// They are marked with #[ignore] by default
// Run with: cargo test -- --ignored

#[tokio::test]
#[ignore]
async fn test_research_api_connection() {
    let client = ResearchClient::new("http://localhost:8001".to_string());

    let is_connected = client
        .test_connection()
        .await
        .expect("Failed to test connection");

    assert!(
        is_connected,
        "Research API should be running at http://localhost:8001"
    );
}

#[tokio::test]
#[ignore]
async fn test_enrich_content_expand() {
    let client = ResearchClient::new("http://localhost:8001".to_string());

    let request = EnrichmentRequest {
        content: "AI is transforming software development.".to_string(),
        enrichment_type: "expand".to_string(),
    };

    let result = client
        .enrich_content(request)
        .await
        .expect("Enrichment should succeed");

    assert!(!result.enriched_content.is_empty());
    assert!(!result.job_id.is_empty());
    println!("Enriched content: {}", result.enriched_content);
}

#[tokio::test]
#[ignore]
async fn test_enrich_content_summarize() {
    let client = ResearchClient::new("http://localhost:8001".to_string());

    let long_text = "Artificial intelligence is rapidly transforming the landscape of software development. Machine learning models are being integrated into development workflows to automate repetitive tasks, identify bugs, and even generate code. This technological shift is enabling developers to focus more on creative problem-solving and less on routine maintenance.";

    let request = EnrichmentRequest {
        content: long_text.to_string(),
        enrichment_type: "summarize".to_string(),
    };

    let result = client
        .enrich_content(request)
        .await
        .expect("Enrichment should succeed");

    assert!(!result.enriched_content.is_empty());
    println!("Summary: {}", result.enriched_content);
}

#[tokio::test]
#[ignore]
async fn test_enrich_content_with_retry() {
    let client = ResearchClient::new("http://localhost:8001".to_string());

    let request = EnrichmentRequest {
        content: "Test content with retry logic".to_string(),
        enrichment_type: "expand".to_string(),
    };

    let result = client
        .enrich_content_with_retry(request, 2)
        .await
        .expect("Enrichment with retry should succeed");

    assert!(!result.enriched_content.is_empty());
}

#[tokio::test]
#[ignore]
async fn test_check_job_status() {
    let client = ResearchClient::new("http://localhost:8001".to_string());

    // First enrich some content to get a job ID
    let request = EnrichmentRequest {
        content: "Test content".to_string(),
        enrichment_type: "expand".to_string(),
    };

    let enrichment = client
        .enrich_content(request)
        .await
        .expect("Enrichment should succeed");

    // Check the status of that job
    let status = client
        .check_status(&enrichment.job_id)
        .await
        .expect("Status check should succeed");

    assert!(!status.is_empty());
    println!("Job {} status: {}", enrichment.job_id, status);
}

#[tokio::test]
async fn test_connection_failure() {
    // Use a non-existent URL to test error handling
    let client = ResearchClient::new("http://localhost:9999".to_string());

    let request = EnrichmentRequest {
        content: "Test".to_string(),
        enrichment_type: "expand".to_string(),
    };

    let result = client.enrich_content(request).await;

    assert!(result.is_err(), "Should fail when API is not available");
}

#[test]
fn test_multiple_enrichment_types() {
    let types = vec!["expand", "summarize", "analyze"];

    for enrichment_type in types {
        let request = EnrichmentRequest {
            content: "Test content".to_string(),
            enrichment_type: enrichment_type.to_string(),
        };

        assert_eq!(request.enrichment_type, enrichment_type);
    }
}
