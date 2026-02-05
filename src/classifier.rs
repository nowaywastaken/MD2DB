//! Question type classifier
//!
//! This module implements a multi-level classification strategy for detecting
//! question types from parsed content.

use crate::models::{ClassificationResult, QuestionType};

/// Structural classifier - Fast pattern matching
pub struct StructuralClassifier;

impl StructuralClassifier {
    /// Classify based on explicit structural patterns
    pub fn classify(stem: &str, options: &[String]) -> Option<ClassificationResult> {
        // Check for explicit type markers
        if stem.contains("[单选]") || stem.contains("[单选题]") {
            return Some(ClassificationResult::certain(QuestionType::Choice));
        }
        if stem.contains("[多选]") || stem.contains("[多选题]") {
            return Some(ClassificationResult::certain(QuestionType::MultipleChoice));
        }
        if stem.contains("[判断]") || stem.contains("[判断题]") {
            return Some(ClassificationResult::certain(QuestionType::TrueFalse));
        }
        if stem.contains("[填空]") || stem.contains("[填空题]") {
            return Some(ClassificationResult::certain(QuestionType::FillInTheBlank));
        }

        // Check for binary options (true/false)
        if options.len() == 2 && Self::is_binary_options(options) {
            return Some(ClassificationResult::certain(QuestionType::TrueFalse));
        }

        // Check for multi-select keywords
        let stem_lower = stem.to_lowercase();
        if stem_lower.contains("多选")
            || stem_lower.contains("以下全部正确")
            || stem_lower.contains("都正确")
        {
            return Some(ClassificationResult::new(QuestionType::MultipleChoice, 0.9));
        }

        None
    }

    /// Check if options form a binary pair (true/false or correct/incorrect)
    fn is_binary_options(options: &[String]) -> bool {
        if options.len() != 2 {
            return false;
        }

        let opt1 = options[0].to_lowercase();
        let opt2 = options[1].to_lowercase();

        // Common binary patterns
        (opt1.contains("正确") || opt1.contains("对") || opt1.contains("true"))
            && (opt2.contains("错误") || opt2.contains("错") || opt2.contains("false"))
    }
}

/// Semantic rule classifier - Context-based reasoning
pub struct SemanticRuleClassifier;

impl SemanticRuleClassifier {
    /// Classify based on semantic context and rules
    pub fn classify(stem: &str, options: &[String]) -> Option<ClassificationResult> {
        // Fill-in-blank vs True-False distinction
        let has_parens = stem.contains("()") || stem.contains("（）");
        let has_binary_options = options.len() == 2 && StructuralClassifier::is_binary_options(options);

        if has_parens && has_binary_options {
            // () with binary options = True-False (fill-in usually has no options)
            return Some(ClassificationResult::new(QuestionType::TrueFalse, 0.85));
        }

        if has_parens && options.is_empty() {
            // () without options = Fill-in-blank
            return Some(ClassificationResult::new(QuestionType::FillInTheBlank, 0.85));
        }

        // Underscore patterns indicate fill-in-blank
        if stem.contains("___") || stem.contains("____") || stem.contains("_____") {
            return Some(ClassificationResult::new(QuestionType::FillInTheBlank, 0.9));
        }

        // Choice questions with letter prefixes (A., B., C., etc.)
        if options.len() >= 2 {
            let has_letter_prefixes = options.iter().all(|opt| {
                let trimmed = opt.trim_start();
                trimmed.starts_with("A.")
                    || trimmed.starts_with("B.")
                    || trimmed.starts_with("C.")
                    || trimmed.starts_with("D.")
                    || trimmed.starts_with("E.")
                    || trimmed.starts_with("F.")
            });

            if has_letter_prefixes {
                // Determine single vs multiple choice based on keywords
                let stem_lower = stem.to_lowercase();
                if stem_lower.contains("全部") || stem_lower.contains("都") {
                    return Some(ClassificationResult::new(QuestionType::MultipleChoice, 0.8));
                }
                return Some(ClassificationResult::new(QuestionType::Choice, 0.8));
            }
        }

        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_explicit_markers() {
        let result = StructuralClassifier::classify("[单选]题目内容", &[]);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::Choice);
    }

    #[test]
    fn test_binary_options() {
        let options = vec!["正确".to_string(), "错误".to_string()];
        let result = StructuralClassifier::classify("题目内容", &options);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::TrueFalse);
    }

    #[test]
    fn test_fill_in_blank_parens() {
        let result = SemanticRuleClassifier::classify("Complete the () sentence", &[]);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::FillInTheBlank);
    }
}
