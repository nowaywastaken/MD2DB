//! Markdown parser for converting exam questions to structured data
//!
//! This module uses pulldown-cmark to parse Markdown and extract questions
//! using an AST-based approach.

use crate::models::{Question, QuestionOption};
use anyhow::Result;
use pulldown_cmark::{Event, Parser, Tag, TagEnd};

/// The main Markdown parser
pub struct MarkdownParser {
    questions: Vec<Question>,
    current_question: Question,
    current_text: String,
    in_list: bool,
    list_items: Vec<String>,
    latex_formulas: Vec<String>,
}

impl MarkdownParser {
    /// Create a new parser instance
    pub fn new() -> Self {
        Self {
            questions: Vec::new(),
            current_question: Question::default(),
            current_text: String::new(),
            in_list: false,
            list_items: Vec::new(),
            latex_formulas: Vec::new(),
        }
    }

    /// Parse Markdown content and extract questions
    pub fn parse(&mut self, markdown: &str) -> Result<&[Question]> {
        let parser = Parser::new(markdown);

        for event in parser {
            match event {
                Event::Start(Tag::Heading { level, .. }) => {
                    self.on_heading_start(level as i32);
                }
                Event::End(TagEnd::Heading(_)) => {
                    self.on_heading_end();
                }
                Event::Start(Tag::Paragraph) => {
                    self.current_text.clear();
                }
                Event::End(TagEnd::Paragraph) => {
                    self.on_paragraph_end();
                }
                Event::Text(text) => {
                    self.current_text.push_str(&text);
                }
                Event::Code(code) => {
                    self.on_code(&code);
                }
                Event::Start(Tag::List(_)) => {
                    self.in_list = true;
                }
                Event::End(TagEnd::List(_)) => {
                    self.in_list = false;
                    self.on_list_end();
                }
                Event::Start(Tag::Item) => {
                    self.current_text.clear();
                }
                Event::End(TagEnd::Item) => {
                    if self.in_list {
                        self.list_items.push(self.current_text.clone());
                    }
                }
                Event::Start(Tag::Image { .. }) => {
                    // TODO: Extract image URLs
                }
                _ => {}
            }
        }

        // Don't forget the last question
        self.finalize_question();

        Ok(&self.questions)
    }

    fn on_heading_start(&mut self, level: i32) {
        // New question detected (typically headings indicate question boundaries)
        if level <= 3 && !self.current_question.stem.is_empty() {
            self.finalize_question();
        }
        self.current_text.clear();
    }

    fn on_heading_end(&mut self) {
        // Heading text becomes the question stem
        if !self.current_text.is_empty() {
            self.current_question.stem = self.current_text.trim().to_string();
        }
    }

    fn on_paragraph_end(&mut self) {
        // Paragraph text after heading gets appended to stem
        if !self.current_text.is_empty() && self.current_question.stem.is_empty() {
            self.current_question.stem = self.current_text.trim().to_string();
        } else if !self.current_text.is_empty() {
            // Additional paragraphs (could be analysis/answer)
            let text = self.current_text.trim();
            if self.current_question.analysis.is_none() {
                self.current_question.analysis = Some(text.to_string());
            }
        }
    }

    fn on_code(&mut self, code: &str) {
        // Check if it's a LaTeX formula
        let trimmed = code.trim();
        if trimmed.starts_with('$') && trimmed.ends_with('$') {
            self.latex_formulas.push(trimmed.to_string());
        } else if trimmed.contains('\\') {
            // Likely LaTeX even without $ delimiters
            self.latex_formulas.push(format!("${}$", trimmed));
        }
    }

    fn on_list_end(&mut self) {
        // Process list items as options
        for (idx, item) in self.list_items.drain(..).enumerate() {
            let option = QuestionOption {
                content: item.trim().to_string(),
                sort_order: idx as i32,
                is_correct: false, // Will be determined later
            };
            self.current_question.options.push(option);
        }
    }

    fn finalize_question(&mut self) {
        if !self.current_question.stem.is_empty() {
            self.current_question.latex = self.latex_formulas.drain(..).collect();
            self.questions.push(self.current_question.clone());
            self.current_question = Question::default();
        }
    }
}

impl Default for MarkdownParser {
    fn default() -> Self {
        Self::new()
    }
}

/// Convenience function to parse Markdown and get questions
pub fn parse_markdown(markdown: &str) -> Result<Vec<Question>> {
    let mut parser = MarkdownParser::new();
    parser.parse(markdown)?;
    Ok(parser.questions.drain(..).collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_question() {
        // Use proper Markdown list format
        let markdown = "# What is 2+2?\n\n* A. 3\n* B. 4\n* C. 5";
        let questions = parse_markdown(markdown).unwrap();
        assert_eq!(questions.len(), 1);
        assert_eq!(questions[0].stem, "What is 2+2?");
        assert_eq!(questions[0].options.len(), 3);
    }
}
