//! Integration tests for the MD2DB API server
//!
//! This test suite validates all API endpoints with a real HTTP server.

use axum::{
    body::Body,
    http::{StatusCode, Method},
    response::IntoResponse,
};
use md2db::api::create_router;
use md2db::database::MockRepository;
use std::sync::Arc;
use tower::ServiceExt;

/// Helper function to create a test app with mock repository
async fn create_test_app() -> axum::Router {
    let repository: Arc<dyn md2db::database::QuestionRepository> =
        Arc::new(MockRepository::new());
    create_router().with_state(repository)
}

/// Helper to make a request and get response
async fn make_request(
    app: &axum::Router,
    method: Method,
    uri: &str,
    body: Option<serde_json::Value>,
) -> axum::http::Response<Body> {
    let mut request_builder = axum::http::Request::builder().method(method).uri(uri);

    if let Some(json_body) = body {
        request_builder = request_builder.header("content-type", "application/json");
        app.clone().oneshot(
            request_builder
                .body(Body::from(json_body.to_string()))
                .unwrap(),
        )
        .await
        .unwrap()
    } else {
        app.clone().oneshot(request_builder.body(Body::empty()).unwrap())
            .await
            .unwrap()
    }
}

#[tokio::test]
async fn test_root_endpoint() {
    let app = create_test_app().await;
    let response = make_request(&app, Method::GET, "/", None).await;

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();

    assert_eq!(json["name"], "MD2DB API");
    assert!(json["endpoints"].is_object());
}

#[tokio::test]
async fn test_health_endpoint() {
    let app = create_test_app().await;
    let response = make_request(&app, Method::GET, "/health", None).await;

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();

    assert_eq!(json["status"], "ok");
}

#[tokio::test]
async fn test_parse_endpoint_simple_question() {
    let app = create_test_app().await;

    let markdown = r#"# What is 2+2?

* A. 3
* B. 4
* C. 5"#;

    let response = make_request(
        &app,
        Method::POST,
        "/parse",
        Some(serde_json::json!({ "markdown": markdown })),
    )
    .await;

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();

    assert_eq!(json["count"], 1);
    assert_eq!(json["questions"][0]["stem"], "What is 2+2?");
}

#[tokio::test]
async fn test_parse_endpoint_multiple_questions() {
    let app = create_test_app().await;

    let markdown = r#"# Question 1

* A. Option 1
* B. Option 2

# Question 2

* A. Option A
* B. Option B"#;

    let response = make_request(
        &app,
        Method::POST,
        "/parse",
        Some(serde_json::json!({ "markdown": markdown })),
    )
    .await;

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();

    assert_eq!(json["count"], 2);
}

#[tokio::test]
async fn test_parse_endpoint_empty_markdown() {
    let app = create_test_app().await;

    let response = make_request(
        &app,
        Method::POST,
        "/parse",
        Some(serde_json::json!({ "markdown": "" })),
    )
    .await;

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();

    assert_eq!(json["count"], 0);
}

#[tokio::test]
async fn test_404_on_nonexistent_endpoint() {
    let app = create_test_app().await;

    let response = make_request(&app, Method::GET, "/nonexistent", None).await;

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

#[tokio::test]
async fn test_parse_endpoint_with_latex() {
    let app = create_test_app().await;

    let markdown = r#"# What is the derivative of $x^2$?

* A. $x$
* B. $2x$
* C. $x^2$"#;

    let response = make_request(
        &app,
        Method::POST,
        "/parse",
        Some(serde_json::json!({ "markdown": markdown })),
    )
    .await;

    assert_eq!(response.status(), StatusCode::OK);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();

    assert_eq!(json["count"], 1);
    // LaTeX formulas should be extracted
    assert!(json["questions"][0]["latex"].is_array());
}

#[tokio::test]
async fn test_error_response_invalid_method() {
    let app = create_test_app().await;

    let response = make_request(&app, Method::DELETE, "/parse", None).await;

    // Should return method not allowed or 404
    assert!(
        response.status() == StatusCode::METHOD_NOT_ALLOWED
            || response.status() == StatusCode::NOT_FOUND
    );
}
