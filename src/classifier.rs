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

/// NLP Classifier - Keyword-based semantic analysis
///
/// This classifier uses lightweight keyword matching and semantic patterns
/// to detect question types without requiring heavy ML libraries.
pub struct NlpClassifier;

impl NlpClassifier {
    /// Multiple choice indicator keywords (Chinese and English)
    const MULTIPLE_CHOICE_KEYWORDS: &'static [&'static str] = &[
        // Chinese indicators
        "以下全部正确",
        "以下都正确",
        "下列全部正确",
        "下列都正确",
        "全部正确",
        "都正确",
        "多选",
        "多项选择",
        "选择所有正确",
        "选择所有适用",
        "以下哪些",
        "下列哪些",
        "哪些正确",
        "哪些错误",
        "多选题",
        "复选题",
        // English indicators
        "all of the above",
        "all that apply",
        "select all that apply",
        "choose all that apply",
        "multiple correct",
        "which of the following",
        "which are true",
        "select all correct",
        "all correct",
        "all are correct",
    ];

    /// Single choice indicator keywords
    const SINGLE_CHOICE_KEYWORDS: &'static [&'static str] = &[
        // Chinese indicators
        "单项选择",
        "单选",
        "最佳答案",
        "最合适",
        "最准确",
        "下列哪一项",
        "以下哪一项",
        "哪一项正确",
        "哪一项错误",
        // English indicators
        "single choice",
        "best",
        "best answer",
        "most appropriate",
        "most accurate",
        "which one",
        "which of the following is",
        "choose the best",
    ];

    /// True/False indicator keywords
    const TRUE_FALSE_KEYWORDS: &'static [&'static str] = &[
        // Chinese indicators
        "判断",
        "判断题",
        "对错",
        "是否正确",
        "正误",
        "是非",
        // English indicators
        "true or false",
        "true/false",
        "correct or incorrect",
        "yes or no",
        "right or wrong",
    ];

    /// Fill-in-blank indicator keywords
    const FILL_BLANK_KEYWORDS: &'static [&'static str] = &[
        // Chinese indicators
        "填空",
        "填空题",
        "补充完整",
        "完成句子",
        "填入",
        // English indicators
        "fill in the blank",
        "fill-in-the-blank",
        "complete the",
        "fill in",
        "blank",
    ];

    /// Classify using keyword matching and semantic analysis
    pub fn classify(stem: &str, options: &[String]) -> Option<ClassificationResult> {
        let stem_lower = stem.to_lowercase();
        let original_stem = stem;

        // Calculate confidence scores for each question type
        let mc_score = Self::calculate_score(&stem_lower, Self::MULTIPLE_CHOICE_KEYWORDS, options);
        let sc_score = Self::calculate_score(&stem_lower, Self::SINGLE_CHOICE_KEYWORDS, options);
        let tf_score = Self::calculate_score(&stem_lower, Self::TRUE_FALSE_KEYWORDS, options);
        let fb_score = Self::calculate_score(&stem_lower, Self::FILL_BLANK_KEYWORDS, options);

        // Find the highest scoring type
        let scores = [
            (mc_score, QuestionType::MultipleChoice),
            (sc_score, QuestionType::Choice),
            (tf_score, QuestionType::TrueFalse),
            (fb_score, QuestionType::FillInTheBlank),
        ];

        let (best_score, best_type) = scores
            .iter()
            .max_by(|a, b| a.0.partial_cmp(&b.0).unwrap())
            .unwrap();

        // Only return if we have reasonable confidence (>= 0.5)
        if *best_score >= 0.5 {
            // Boost confidence based on additional patterns
            let adjusted_confidence = Self::adjust_confidence(
                *best_score,
                original_stem,
                options,
                *best_type,
            );
            Some(ClassificationResult::new(*best_type, adjusted_confidence))
        } else {
            None
        }
    }

    /// Calculate confidence score based on keyword matches
    fn calculate_score(text: &str, keywords: &[&str], options: &[String]) -> f32 {
        let mut score = 0.0;

        // Check for keyword matches in stem
        for keyword in keywords {
            if text.contains(keyword) {
                // Longer keywords get higher weight
                let weight = (keyword.len() as f32) / 10.0;
                score += weight;
            }
        }

        // Boost score based on option count patterns
        match options.len() {
            0 => score *= 0.8,  // No options reduces confidence
            2 => {
                // Two options might be true/false
                if !keywords.iter().any(|k| text.contains(k)) {
                    score *= 0.3; // Low confidence for 2 options without keywords
                }
            }
            3..=4 => score *= 1.2,  // 3-4 options is typical for choice questions
            5.. => score *= 1.5,  // 5+ options strongly suggest choice/multiple choice
            _ => {}
        }

        // Normalize score to 0-1 range (capped at 1.0)
        (score / 3.0).min(1.0)
    }

    /// Adjust confidence based on contextual patterns
    fn adjust_confidence(
        base_score: f32,
        stem: &str,
        options: &[String],
        qtype: QuestionType,
    ) -> f32 {
        let mut confidence = base_score;

        // Check for explicit markers (high confidence boost)
        if stem.contains("[") && stem.contains("]") {
            confidence = (confidence + 0.3).min(1.0);
        }

        // Check for exclamation marks (often indicate emphasis)
        if stem.contains('！') || stem.contains('!') {
            confidence = (confidence + 0.1).min(1.0);
        }

        // Check for question marks
        if stem.contains('？') || stem.contains('?') {
            confidence = (confidence + 0.05).min(1.0);
        }

        // Option-based adjustments
        match qtype {
            QuestionType::MultipleChoice => {
                // "以下全部正确" is very specific to multiple choice
                if stem.to_lowercase().contains("以下全部正确")
                    || stem.to_lowercase().contains("all of the above")
                {
                    confidence = (confidence + 0.2).min(1.0);
                }
                // Multiple choice typically has more options
                if options.len() >= 4 {
                    confidence = (confidence + 0.1).min(1.0);
                }
            }
            QuestionType::Choice => {
                // Single choice with "best" keyword is very specific
                if stem.to_lowercase().contains("最佳")
                    || stem.to_lowercase().contains("best")
                {
                    confidence = (confidence + 0.15).min(1.0);
                }
            }
            QuestionType::TrueFalse => {
                // Binary options strongly indicate true/false
                if options.len() == 2 && StructuralClassifier::is_binary_options(options) {
                    confidence = (confidence + 0.3).min(1.0);
                }
            }
            QuestionType::FillInTheBlank => {
                // Underscores or parentheses indicate fill-in-blank
                if stem.contains("___")
                    || stem.contains("（）")
                    || stem.contains("()")
                {
                    confidence = (confidence + 0.2).min(1.0);
                }
            }
            QuestionType::Subjective => {}
        }

        confidence
    }

    /// Get detailed classification analysis (useful for debugging)
    pub fn analyze(stem: &str, options: &[String]) -> NlpAnalysis {
        let stem_lower = stem.to_lowercase();

        NlpAnalysis {
            multiple_choice_matches: Self::find_matches(&stem_lower, Self::MULTIPLE_CHOICE_KEYWORDS),
            single_choice_matches: Self::find_matches(&stem_lower, Self::SINGLE_CHOICE_KEYWORDS),
            true_false_matches: Self::find_matches(&stem_lower, Self::TRUE_FALSE_KEYWORDS),
            fill_blank_matches: Self::find_matches(&stem_lower, Self::FILL_BLANK_KEYWORDS),
            option_count: options.len(),
            recommended_type: Self::classify(stem, options).map(|r| r.qtype),
        }
    }

    /// Find matching keywords in text
    fn find_matches(text: &str, keywords: &[&str]) -> Vec<String> {
        keywords
            .iter()
            .filter(|kw| text.contains(*kw))
            .map(|s| s.to_string())
            .collect()
    }
}

/// Detailed analysis result from NLP classification
#[derive(Debug, Clone)]
pub struct NlpAnalysis {
    /// Keywords that matched multiple choice patterns
    pub multiple_choice_matches: Vec<String>,
    /// Keywords that matched single choice patterns
    pub single_choice_matches: Vec<String>,
    /// Keywords that matched true/false patterns
    pub true_false_matches: Vec<String>,
    /// Keywords that matched fill-in-blank patterns
    pub fill_blank_matches: Vec<String>,
    /// Number of options provided
    pub option_count: usize,
    /// Recommended question type (if confident)
    pub recommended_type: Option<QuestionType>,
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

    // NLP Classifier tests

    #[test]
    fn test_nlp_multiple_choice_chinese() {
        let stem = "以下全部正确的是：";
        let options = vec![
            "A. 选项1".to_string(),
            "B. 选项2".to_string(),
            "C. 选项3".to_string(),
            "D. 选项4".to_string(),
        ];
        let result = NlpClassifier::classify(stem, &options);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::MultipleChoice);
    }

    #[test]
    fn test_nlp_multiple_choice_english() {
        let stem = "Select all that apply:";
        let options = vec![
            "A. Option 1".to_string(),
            "B. Option 2".to_string(),
            "C. Option 3".to_string(),
        ];
        let result = NlpClassifier::classify(stem, &options);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::MultipleChoice);
    }

    #[test]
    fn test_nlp_single_choice_best_answer() {
        let stem = "Which of the following is the best approach?";
        let options = vec![
            "A. Approach 1".to_string(),
            "B. Approach 2".to_string(),
            "C. Approach 3".to_string(),
        ];
        let result = NlpClassifier::classify(stem, &options);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::Choice);
    }

    #[test]
    fn test_nlp_fill_in_blank() {
        let stem = "Please fill in the blank: The capital of France is ____.";
        let result = NlpClassifier::classify(stem, &[]);
        assert!(result.is_some());
        assert_eq!(result.unwrap().qtype, QuestionType::FillInTheBlank);
    }

    #[test]
    fn test_nlp_confidence_scoring() {
        let stem = "以下全部正确";
        let options = vec!["A. 1".to_string(), "B. 2".to_string(), "C. 3".to_string()];
        let result = NlpClassifier::classify(stem, &options).unwrap();
        // Should have high confidence for explicit keyword match
        assert!(result.confidence >= 0.7);
    }

    #[test]
    fn test_nlp_analysis() {
        let stem = "以下全部正确的是哪些？";
        let options = vec!["A. 1".to_string(), "B. 2".to_string()];
        let analysis = NlpClassifier::analyze(stem, &options);
        assert!(!analysis.multiple_choice_matches.is_empty());
        assert_eq!(analysis.option_count, 2);
    }

    #[test]
    fn test_nlp_low_confidence_returns_none() {
        let stem = "This is a very generic question without clear indicators.";
        let options = vec!["Option A".to_string()];
        let result = NlpClassifier::classify(stem, &options);
        // Should return None when confidence is too low
        assert!(result.is_none());
    }
}
