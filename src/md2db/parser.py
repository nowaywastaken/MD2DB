from typing import List
import re
from .models import Question
from .image_processor import extract_all

# Pre-compiled regex patterns for performance
_NUMBERED_PATTERN = re.compile(r'(?:^|\n)(\d+\.\s+.*?)(?=\n\d+\.|\n\s*---|\n\s*\n+|\Z)', re.DOTALL)
_SEPARATOR_PATTERN = re.compile(r'(?:^|\n\s*---\s*\n)(.*?)(?=\n\s*---|\n\d+\.|\n\s*\n+|\Z)', re.DOTALL)
_OPTION_PATTERN = re.compile(r'^[A-Z]\.\s*(.+)$')
_LEADING_NUMBER_PATTERN = re.compile(r'^\s*\d+\.\s*', re.MULTILINE)
_OPTION_MARKER_PATTERN = re.compile(r'^[A-Z]\.\s')
_IMAGE_TAG_PATTERN = re.compile(r'!\[.*?\]\(.*?\)')
_EMPTY_LINE_SPLIT_PATTERN = re.compile(r'\n\s*\n\s*\n+')

def detect_question_type(content: str) -> str:
    """Detect the type of question based on content patterns."""
    content_lower = content.lower()

    # Check for multiple choice patterns
    # Only detect as multiple choice if there are at least 2 options
    # and they appear at the start of lines (not in the middle of sentences)
    option_patterns = ["a.", "b.", "c.", "d.", "e.", "f."]
    option_count = 0

    # Split content into lines and check for option markers at line beginnings
    lines = content_lower.split('\n')
    for line in lines:
        line = line.strip()
        # Check if line starts with an option marker followed by space
        for pattern in option_patterns:
            if line.startswith(pattern + ' ') or line.startswith(pattern + '\t'):
                option_count += 1
                break  # Only count one option per line

    # Require at least 2 distinct option markers to be considered multiple choice
    if option_count >= 2:
        return "multiple_choice"

    # Check for true/false patterns
    if any(marker in content_lower for marker in ["true", "false", "正确", "错误"]):
        return "true_false"

    # Check for fill-in-the-blank patterns
    if "_____" in content or "____" in content:
        return "fill_in_blank"

    return "subjective"

def parse_options(content: str) -> List[str]:
    """Extract options from multiple choice questions."""
    options = []

    for line in content.split('\n'):
        match = _OPTION_PATTERN.match(line.strip())
        if match:
            options.append(match.group(1).strip())

    return options

def split_questions(content: str) -> List[str]:
    """Split markdown content into individual questions.

    Args:
        content: Markdown content containing one or more questions

    Returns:
        List of individual question strings
    """
    # Find all question boundaries using multiple patterns
    questions = []

    # Find numbered questions first
    matches = _NUMBERED_PATTERN.findall(content)
    if matches:
        questions = [match.strip() for match in matches if match.strip()]
        if len(questions) > 1:
            return questions

    # If no numbered questions, try separator pattern
    matches = _SEPARATOR_PATTERN.findall(content)
    if matches:
        questions = [match.strip() for match in matches if match.strip()]
        if len(questions) > 1:
            return questions

    # If still no good split, try splitting by multiple empty lines
    questions = _EMPTY_LINE_SPLIT_PATTERN.split(content)
    questions = [q.strip() for q in questions if q.strip()]
    if len(questions) > 1:
        return questions

    # If no clear splitting pattern is found, treat as single question
    return [content.strip()]


def clean_question_content(content: str) -> str:
    """Clean and normalize question content.

    Args:
        content: Raw question content

    Returns:
        Cleaned question content
    """
    # Remove leading numbering like "1.", "2." etc. (support multiline)
    cleaned = _LEADING_NUMBER_PATTERN.sub('', content)

    # Extract just the question text (before options start)
    # For multiple choice questions, look for the first option marker
    lines = cleaned.strip().split('\n')
    question_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check if this line starts with an option marker (A., B., etc.)
        if _OPTION_MARKER_PATTERN.match(line):
            break  # Stop at first option
        question_lines.append(line)

    return ' '.join(question_lines).strip()


def parse_markdown(content: str) -> List[Question]:
    """Parse markdown content and extract questions."""
    questions_content = split_questions(content)
    questions = []

    for q_content in questions_content:
        question_type = detect_question_type(q_content)
        options = []

        # Extract all media content in a single pass
        extracted = extract_all(q_content)
        images = extracted.images
        latex_formulas = extracted.latex_formulas

        if question_type == "multiple_choice":
            options = parse_options(q_content)

        # Remove image tags from content
        clean_content = _IMAGE_TAG_PATTERN.sub('', q_content).strip()

        # Clean and normalize the question content
        clean_content = clean_question_content(clean_content)

        questions.append(Question(
            content=clean_content,
            question_type=question_type,
            options=options if options else None,
            images=images if images else None,
            latex_formulas=latex_formulas if latex_formulas else None
        ))

    return questions