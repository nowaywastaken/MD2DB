//! API layer for MD2DB web service
//!
//! This module provides REST API endpoints using Axum.

use crate::database::QuestionRepository;
use crate::models::Question;
use crate::parser::parse_markdown;
use axum::{
    extract::{Multipart, State},
    http::StatusCode,
    response::{IntoResponse, Json},
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
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, message) = match self {
            ApiError::ParseError(msg) => (StatusCode::BAD_REQUEST, msg),
            ApiError::DatabaseError(msg) => (StatusCode::INTERNAL_SERVER_ERROR, msg),
            ApiError::InvalidFile(msg) => (StatusCode::BAD_REQUEST, msg),
        };

        let body = Json(serde_json::json!({
            "error": message,
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

/// Health check response
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
}

/// Create the API router
pub fn create_router() -> Router<Arc<dyn QuestionRepository>> {
    Router::new()
        .route("/parse", post(parse_markdown_endpoint))
        .route("/health", get(health_check))
}

/// Parse markdown endpoint
pub async fn parse_markdown_endpoint(
    State(repo): State<Arc<dyn QuestionRepository>>,
    Json(req): Json<ParseRequest>,
) -> Result<Json<ParseResponse>, ApiError> {
    let questions = parse_markdown(&req.markdown)?;

    let ids = repo.save_batch(&questions).await.map_err(|e| ApiError::DatabaseError(e.to_string()))?;

    Ok(Json(ParseResponse {
        count: ids.len(),
        question_ids: ids,
        questions,
        warnings: Vec::new(),
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

    #[tokio::test]
    async fn test_health_check() {
        let response = health_check().await;
        assert_eq!(response.status, "ok");
    }

    #[tokio::test]
    async fn test_parse_endpoint() {
        let repo = Arc::new(MockRepository::new()) as Arc<dyn QuestionRepository>;
        let req = ParseRequest {
            markdown: "# Test\n\nA. Option1\nB. Option2".to_string(),
        };

        let result = parse_markdown_endpoint(State(repo), Json(req)).await;
        assert!(result.is_ok());

        let response = result.unwrap();
        assert_eq!(response.count, 1);
    }
}
