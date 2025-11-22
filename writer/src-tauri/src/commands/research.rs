//! Research database integration commands
//! Provides access to the research knowledge base (PostgreSQL + pgvector)

use crate::error::{BrainDumpError, Result};
use serde::{Deserialize, Serialize};
use std::env;

/// Research search result from the knowledge base
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResearchResult {
    pub content_id: String,
    pub source_id: String,
    pub text_content: String,
    pub similarity_score: f32,
    pub platform: String,
    pub url: Option<String>,
    pub title: Option<String>,
    pub author: Option<String>,
    pub published_at: Option<String>,
    pub word_count: Option<i32>,
    pub concepts: Vec<String>,
}

/// Research database statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResearchStats {
    #[serde(rename = "totalResults")]
    pub total_results: i64,
    pub platforms: std::collections::HashMap<String, i64>,
}

/// Test connection to research database
#[tauri::command]
pub async fn test_research_db_connection() -> Result<bool> {
    // Get database URL from environment or default
    let db_url = env::var("RESEARCH_DB_URL")
        .unwrap_or_else(|_| "postgresql://postgres:password@localhost:5432/research".to_string());

    // Try to connect using tokio_postgres
    match tokio_postgres::connect(&db_url, tokio_postgres::NoTls).await {
        Ok((client, connection)) => {
            // Spawn connection handler
            tokio::spawn(async move {
                if let Err(e) = connection.await {
                    eprintln!("Connection error: {}", e);
                }
            });

            // Test query
            match client.query_one("SELECT 1", &[]).await {
                Ok(_) => Ok(true),
                Err(e) => {
                    eprintln!("Test query failed: {}", e);
                    Ok(false)
                }
            }
        }
        Err(e) => {
            eprintln!("Failed to connect to research database: {}", e);
            Ok(false)
        }
    }
}

/// Search the knowledge base using semantic similarity
#[tauri::command]
pub async fn search_knowledge(query: String, limit: Option<i32>) -> Result<Vec<ResearchResult>> {
    let limit = limit.unwrap_or(10);

    // Get database URL from environment or default
    let db_url = env::var("RESEARCH_DB_URL")
        .unwrap_or_else(|_| "postgresql://postgres:password@localhost:5432/research".to_string());

    // Get OpenAI API key for embeddings
    let openai_key = env::var("OPENAI_API_KEY").map_err(|_| {
        BrainDumpError::Other(
            "OPENAI_API_KEY not set. Required for semantic search.".to_string(),
        )
    })?;

    // Generate embedding for the query using OpenAI
    let embedding = generate_embedding(&query, &openai_key).await?;

    // Connect to database
    let (client, connection) = tokio_postgres::connect(&db_url, tokio_postgres::NoTls)
        .await
        .map_err(|e| BrainDumpError::Other(format!("Database connection failed: {}", e)))?;

    // Spawn connection handler
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("Connection error: {}", e);
        }
    });

    // Prepare embedding as PostgreSQL vector string
    let embedding_str = format!("[{}]", embedding.iter().map(|f| f.to_string()).collect::<Vec<_>>().join(","));

    // Query using the find_similar_content function
    let query_sql = r#"
        SELECT
            content_id::text,
            source_id::text,
            text_content,
            similarity_score,
            platform,
            url,
            title,
            author,
            published_at::text,
            NULL::int as word_count,
            ARRAY[]::text[] as concepts
        FROM find_similar_content($1::vector(1536), 0.7, $2)
        ORDER BY similarity_score DESC
    "#;

    let rows = client
        .query(query_sql, &[&embedding_str, &limit])
        .await
        .map_err(|e| BrainDumpError::Other(format!("Query failed: {}", e)))?;

    let mut results = Vec::new();
    for row in rows {
        let result = ResearchResult {
            content_id: row.get(0),
            source_id: row.get(1),
            text_content: row.get(2),
            similarity_score: row.get(3),
            platform: row.get(4),
            url: row.get(5),
            title: row.get(6),
            author: row.get(7),
            published_at: row.get(8),
            word_count: row.get(9),
            concepts: extract_concepts(&row.get::<_, String>(2)), // Extract from content
        };
        results.push(result);
    }

    Ok(results)
}

/// Get research database statistics
#[tauri::command]
pub async fn get_research_stats() -> Result<ResearchStats> {
    let db_url = env::var("RESEARCH_DB_URL")
        .unwrap_or_else(|_| "postgresql://postgres:password@localhost:5432/research".to_string());

    // Connect to database
    let (client, connection) = tokio_postgres::connect(&db_url, tokio_postgres::NoTls)
        .await
        .map_err(|e| BrainDumpError::Other(format!("Database connection failed: {}", e)))?;

    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("Connection error: {}", e);
        }
    });

    // Get statistics using the database function
    let stats_sql = r#"
        SELECT
            platform,
            content_count
        FROM get_content_statistics()
    "#;

    let rows = client
        .query(stats_sql, &[])
        .await
        .map_err(|e| BrainDumpError::Other(format!("Stats query failed: {}", e)))?;

    let mut total_results = 0i64;
    let mut platforms = std::collections::HashMap::new();

    for row in rows {
        let platform: String = row.get(0);
        let count: i64 = row.get(1);
        total_results += count;
        platforms.insert(platform, count);
    }

    Ok(ResearchStats {
        total_results,
        platforms,
    })
}

/// Generate OpenAI embedding for a text query
async fn generate_embedding(text: &str, api_key: &str) -> Result<Vec<f32>> {
    use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};

    let client = reqwest::Client::new();

    let mut headers = HeaderMap::new();
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
    headers.insert(
        AUTHORIZATION,
        HeaderValue::from_str(&format!("Bearer {}", api_key))
            .map_err(|e| BrainDumpError::Other(format!("Invalid API key: {}", e)))?,
    );

    let request_body = serde_json::json!({
        "input": text,
        "model": "text-embedding-ada-002"
    });

    let response = client
        .post("https://api.openai.com/v1/embeddings")
        .headers(headers)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| BrainDumpError::Other(format!("Embedding request failed: {}", e)))?;

    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
        return Err(BrainDumpError::Other(format!(
            "OpenAI API error: {}",
            error_text
        )));
    }

    let response_json: serde_json::Value = response
        .json()
        .await
        .map_err(|e| BrainDumpError::Other(format!("Failed to parse response: {}", e)))?;

    let embedding = response_json["data"][0]["embedding"]
        .as_array()
        .ok_or_else(|| BrainDumpError::Other("Invalid embedding response".to_string()))?
        .iter()
        .map(|v| v.as_f64().unwrap_or(0.0) as f32)
        .collect();

    Ok(embedding)
}

/// Extract key concepts from content (simple heuristic)
fn extract_concepts(text: &str) -> Vec<String> {
    // Simple concept extraction - look for key phrases
    let keywords = vec![
        "content creation",
        "audience building",
        "personal brand",
        "social media",
        "marketing",
        "storytelling",
        "engagement",
        "monetization",
        "creator economy",
        "digital products",
    ];

    let text_lower = text.to_lowercase();
    keywords
        .into_iter()
        .filter(|k| text_lower.contains(k))
        .map(|s| s.to_string())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_concepts() {
        let text = "This article discusses content creation and audience building strategies.";
        let concepts = extract_concepts(text);
        assert!(concepts.contains(&"content creation".to_string()));
        assert!(concepts.contains(&"audience building".to_string()));
    }

    #[tokio::test]
    async fn test_connection() {
        // This test requires a running PostgreSQL database
        // Skip in CI environments
        if env::var("CI").is_ok() {
            return;
        }

        let result = test_research_db_connection().await;
        // Don't fail the test if DB is not available
        match result {
            Ok(connected) => println!("Database connection test: {}", connected),
            Err(e) => println!("Database connection test error: {}", e),
        }
    }
}
