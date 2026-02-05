//! API layer for MD2DB web service
//!
//! This module provides REST API endpoints using Axum.

use crate::database::QuestionRepository;
use crate::models::Question;
use crate::parser::parse_markdown;
use crate::zip::ZipProcessor;
use axum::{
    body::Body,
    extract::{Multipart, State},
    http::{header, StatusCode},
    response::{IntoResponse, Json, Response},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

/// API error type
#[derive(Debug)]
pub enum ApiError {
    ParseError(String),
    DatabaseError(String),
    InvalidFile(String),
    MultipartError(String),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_type, message) = match self {
            ApiError::ParseError(msg) => (StatusCode::BAD_REQUEST, "parse_error", msg),
            ApiError::DatabaseError(msg) => (StatusCode::INTERNAL_SERVER_ERROR, "database_error", msg),
            ApiError::InvalidFile(msg) => (StatusCode::BAD_REQUEST, "invalid_file", msg),
            ApiError::MultipartError(msg) => (StatusCode::BAD_REQUEST, "multipart_error", msg),
        };

        let body = Json(serde_json::json!({
            "error": error_type,
            "message": message,
        }));

        (status, body).into_response()
    }
}

impl From<anyhow::Error> for ApiError {
    fn from(err: anyhow::Error) -> Self {
        ApiError::ParseError(err.to_string())
    }
}

/// Parse request for single markdown file
#[derive(Debug, Deserialize)]
pub struct ParseRequest {
    pub markdown: String,
}

/// Response after parsing
#[derive(Debug, Serialize)]
pub struct ParseResponse {
    pub count: usize,
    pub question_ids: Vec<Uuid>,
    pub questions: Vec<Question>,
    pub warnings: Vec<String>,
}

/// ZIP parse response
#[derive(Debug, Serialize)]
pub struct ParseZipResponse {
    pub count: usize,
    pub question_ids: Vec<Uuid>,
    pub questions: Vec<Question>,
    pub images_processed: usize,
    pub warnings: Vec<String>,
}

/// Health check response
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
}

/// Error response structure
#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
    pub message: String,
}

/// Create the API router
pub fn create_router() -> Router<Arc<dyn QuestionRepository>> {
    Router::new()
        .route("/parse", post(parse_markdown_endpoint))
        .route("/parse-zip", post(parse_zip_endpoint))
        .route("/health", get(health_check))
        .route("/", get(root_handler))
}

/// Root handler with API information
pub async fn root_handler() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "name": "MD2DB API",
        "version": env!("CARGO_PKG_VERSION"),
        "description": "Markdown to Database converter - High performance Rust implementation",
        "endpoints": {
            "POST /parse": "Parse a single markdown text",
            "POST /parse-zip": "Parse a ZIP file containing markdown files",
            "GET /health": "Health check endpoint",
        }
    }))
}

/// Parse markdown endpoint
pub async fn parse_markdown_endpoint(
    State(repo): State<Arc<dyn QuestionRepository>>,
    Json(req): Json<ParseRequest>,
) -> Result<Json<ParseResponse>, ApiError> {
    let questions = parse_markdown(&req.markdown)?;

    let ids = repo.save_batch(&questions).await
        .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

    Ok(Json(ParseResponse {
        count: ids.len(),
        question_ids: ids,
        questions,
        warnings: Vec::new(),
    }))
}

/// Parse ZIP endpoint - handles multipart file upload
pub async fn parse_zip_endpoint(
    State(repo): State<Arc<dyn QuestionRepository>>,
    mut multipart: Multipart,
) -> Result<Json<ParseZipResponse>, ApiError> {
    let mut zip_data: Option<Vec<u8>> = None;

    // Process multipart form data
    while let Some(field) = multipart.next_field().await
        .map_err(|e| ApiError::MultipartError(format!("Failed to read multipart field: {}", e)))?
    {
        let name = field.name().unwrap_or("unknown");

        if name == "file" || name == "zip" {
            let filename = field.file_name()
                .ok_or_else(|| ApiError::InvalidFile("Missing filename".to_string()))?
                .to_string();

            // Validate file extension
            if !filename.to_lowercase().ends_with(".zip") {
                return Err(ApiError::InvalidFile(format!(
                    "Invalid file type: expected .zip file, got: {}", filename
                )));
            }

            // Read file content
            let data = field.bytes().await
                .map_err(|e| ApiError::MultipartError(format!("Failed to read file content: {}", e)))?;

            zip_data = Some(data.to_vec());
        }
    }

    // Validate that we received a file
    let zip_data = zip_data
        .ok_or_else(|| ApiError::InvalidFile("No file uploaded".to_string()))?;

    // Process the ZIP file
    let processor = ZipProcessor::new();
    let result = processor.process_zip(zip_data).await
        .map_err(|e| ApiError::ParseError(format!("Failed to process ZIP: {}", e)))?;

    // Save questions to database
    let ids = repo.save_batch(&result.questions).await
        .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

    Ok(Json(ParseZipResponse {
        count: ids.len(),
        question_ids: ids,
        questions: result.questions,
        images_processed: result.images.len(),
        warnings: result.warnings,
    }))
}

/// Health check endpoint
pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::database::MockRepository;
    use axum::{
        body::Body,
        http::{self, StatusCode},
    };
    use tower::ServiceExt;

    #[tokio::test]
    async fn test_health_check() {
        let response = health_check().await;
        assert_eq!(response.status, "ok");
        assert!(!response.version.is_empty());
    }

    #[tokio::test]
    async fn test_root_handler() {
        let response = root_handler().await;
        let value = response.0;
        assert_eq!(value["name"], "MD2DB API");
        assert!(value.get("endpoints").is_some());
    }

    #[tokio::test]
    async fn test_parse_endpoint() {
        let repo = Arc::new(MockRepository::new()) as Arc<dyn QuestionRepository>;
        let req = ParseRequest {
            markdown: "# Test\n\n* A. Option1\n* B. Option2".to_string(),
        };

        let result = parse_markdown_endpoint(State(repo), Json(req)).await;
        assert!(result.is_ok());

        let response = result.unwrap();
        assert_eq!(response.count, 1);
        assert_eq!(response.question_ids.len(), 1);
        assert_eq!(response.questions.len(), 1);
        assert!(response.warnings.is_empty());
    }

    #[tokio::test]
    async fn test_parse_multiple_questions() {
        let repo = Arc::new(MockRepository::new()) as Arc<dyn QuestionRepository>;
        let req = ParseRequest {
            markdown: r#"# Question 1

* A. Option 1
* B. Option 2

# Question 2

* C. Option 3
* D. Option 4
"#.to_string(),
        };

        let result = parse_markdown_endpoint(State(repo), Json(req)).await;
        assert!(result.is_ok());

        let response = result.unwrap();
        assert_eq!(response.count, 2);
        assert_eq!(response.question_ids.len(), 2);
    }

    #[tokio::test]
    async fn test_api_error_into_response() {
        let error = ApiError::ParseError("Test error".to_string());
        let response = error.into_response();

        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
    }

    #[tokio::test]
    async fn test_database_error_into_response() {
        let error = ApiError::DatabaseError("DB error".to_string());
        let response = error.into_response();

        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    #[tokio::test]
    async fn test_invalid_file_error_into_response() {
        let error = ApiError::InvalidFile("Invalid file".to_string());
        let response = error.into_response();

        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
    }
}
