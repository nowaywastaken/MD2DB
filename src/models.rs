//! Core data models for MD2DB
//!
//! This module defines the fundamental data structures used throughout
//! the application, including questions, options, and media references.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// The type of question
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum QuestionType {
    /// Single choice question
    Choice,
    /// Multiple choice question
    MultipleChoice,
    /// True/False question
    TrueFalse,
    /// Fill in the blank question
    FillInTheBlank,
    /// Subjective/essay question
    Subjective,
}

/// An option for a multiple choice or true/false question
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuestionOption {
    /// The content of the option
    pub content: String,
    /// Sort order for display
    pub sort_order: i32,
    /// Whether this option is correct
    pub is_correct: bool,
}

/// Reference to an image, either remote or local
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ImageRef {
    /// Remote URL reference
    Remote { url: String },
    /// Local file reference with content hash
    Local {
        /// SHA-256 hash of the image content
        hash: String,
        /// Original file path
        original_path: String,
    },
}

/// A complete question with all its components
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Question {
    /// Unique identifier
    pub id: Uuid,
    /// Type of question
    #[serde(rename = "type")]
    pub qtype: QuestionType,
    /// The question stem/prompt
    pub stem: String,
    /// Options for choice questions
    #[serde(default)]
    pub options: Vec<QuestionOption>,
    /// The answer (if applicable)
    pub answer: Option<String>,
    /// Detailed explanation/analysis
    pub analysis: Option<String>,
    /// Images referenced in the question
    #[serde(default)]
    pub images: Vec<ImageRef>,
    /// LaTeX formulas extracted from the question
    #[serde(default)]
    pub latex: Vec<String>,
    /// When this question was created/processed
    pub created_at: DateTime<Utc>,
}

impl Default for Question {
    fn default() -> Self {
        Self {
            id: Uuid::new_v4(),
            qtype: QuestionType::Subjective,
            stem: String::new(),
            options: Vec::new(),
            answer: None,
            analysis: None,
            images: Vec::new(),
            latex: Vec::new(),
            created_at: Utc::now(),
        }
    }
}

/// Result of a classification operation with confidence
#[derive(Debug, Clone)]
pub struct ClassificationResult {
    /// The determined question type
    pub qtype: QuestionType,
    /// Confidence score (0.0 to 1.0)
    pub confidence: f32,
    /// Whether this result needs manual review
    pub needs_review: bool,
}

impl ClassificationResult {
    /// Create a new classification result
    pub fn new(qtype: QuestionType, confidence: f32) -> Self {
        let needs_review = confidence < 0.8;
        Self {
            qtype,
            confidence,
            needs_review,
        }
    }

    /// Create a high-confidence result
    pub fn certain(qtype: QuestionType) -> Self {
        Self::new(qtype, 1.0)
    }

    /// Create a low-confidence result that needs review
    pub fn uncertain(qtype: QuestionType, confidence: f32) -> Self {
        Self::new(qtype, confidence)
    }
}
