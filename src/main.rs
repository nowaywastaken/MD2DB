mod models;
mod parser;
mod database;
mod api;
mod media;
mod classifier;
mod zip;

use anyhow::Result;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();

    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");

    info!("MD2DB Rust - Starting up...");

    // TODO: Initialize and start the server
    println!("MD2DB Rust - Markdown to Database Converter");
    println!("Version: 0.1.0");
    println!("High-performance Rust implementation\n");

    Ok(())
}
