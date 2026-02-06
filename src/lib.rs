//! MD2DB - Markdown to Database converter library
//!
//! High-performance Rust implementation for converting exam questions
//! from Markdown format into structured data records.
//!
//! # Example
//!
//! ```
//! use md2db::{parse_markdown_text, models::Question};
//!
//! let markdown = r#"
//! # 单选题
//!
//! 以下哪个是算法的时间复杂度？
//!
//! * A. O(n)
//! * B. O(log n)
//! "#;
//!
//! let questions = parse_markdown_text(markdown);
//! assert!(!questions.is_empty());
//! ```

pub mod models;
pub mod parser;
pub mod database;
pub mod media;
pub mod classifier;
pub mod zip;
pub mod processor;
pub mod api;

pub use models::{Question, QuestionType, QuestionOption, ImageRef};

/// Parse markdown text into questions
///
/// Returns a vector of parsed questions from the given Markdown content.
///
/// # Example
///
/// ```rust
/// use md2db::parse_markdown_text;
///
/// let markdown = r#"
/// # 单选题
///
/// 以下哪个是算法的时间复杂度？
///
/// * A. O(n)
/// * B. O(log n)
/// "#;
///
/// let questions = parse_markdown_text(markdown);
/// ```
pub fn parse_markdown_text(text: &str) -> anyhow::Result<Vec<Question>> {
    parser::parse_markdown(text)
}

/// Parse markdown from a ZIP file bytes
///
/// Takes the raw bytes of a ZIP file containing Markdown files
/// and returns a ZipProcessResult with all parsed questions.
pub async fn parse_markdown_zip(data: &[u8]) -> anyhow::Result<zip::ZipProcessResult> {
    let processor = zip::ZipProcessor::new();
    processor.process_zip(data.to_vec()).await
}
