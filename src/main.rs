mod models;
mod parser;
mod database;
mod api;
mod media;
mod classifier;
mod zip;
mod processor;

use anyhow::Result;
use std::net::SocketAddr;
use std::sync::Arc;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;
use tower::ServiceBuilder;
use tower_http::{
    compression::CompressionLayer,
    trace::TraceLayer,
};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();

    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");

    info!("MD2DB Rust - Starting up...");

    // Get configuration from environment
    let port = std::env::var("PORT")
        .unwrap_or_else(|_| "8080".to_string())
        .parse::<u16>()
        .unwrap_or(8080);

    let host = std::env::var("HOST")
        .unwrap_or_else(|_| "0.0.0.0".to_string());

    // Use mock repository by default (can be configured for PostgreSQL/MongoDB)
    let repository: Arc<dyn database::QuestionRepository> =
        Arc::new(database::MockRepository::new());

    // Create API router with repository state
    let app = api::create_router()
        .with_state(repository.clone())
        .layer(
            ServiceBuilder::new()
                .layer(TraceLayer::new_for_http())
                .layer(CompressionLayer::new())
        );

    // Bind to address
    let addr = SocketAddr::new(host.parse()?, port);
    info!("Server listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app)
        .await?;

    Ok(())
}
