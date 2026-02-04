from typing import List
import re
from .models import Question
from .image_processor import extract_images

def detect_question_type(content: str) -> str:
    """Detect the type of question based on content patterns."""
    content_lower = content.lower()

    # Check for multiple choice patterns
    if any(marker in content_lower for marker in ["a.", "b.", "c.", "d."]):
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
    # Match patterns like "A. option text", "B. option text", etc.
    pattern = r'^[A-Z]\.\s*(.+)$'

    for line in content.split('\n'):
        match = re.match(pattern, line.strip())
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

    # Pattern for numbered questions: "1. " at the start of a line
    numbered_pattern = r'(?:^|\n)(\d+\.\s+.*?)(?=\n\d+\.|\n\s*---|\n\s*\n+|\Z)'

    # Pattern for questions with separators
    separator_pattern = r'(?:^|\n\s*---\s*\n)(.*?)(?=\n\s*---|\n\d+\.|\n\s*\n+|\Z)'

    # Find numbered questions first
    matches = re.findall(numbered_pattern, content, re.DOTALL)
    if matches:
        questions = [match.strip() for match in matches if match.strip()]
        if len(questions) > 1:
            return questions

    # If no numbered questions, try separator pattern
    matches = re.findall(separator_pattern, content, re.DOTALL)
    if matches:
        questions = [match.strip() for match in matches if match.strip()]
        if len(questions) > 1:
            return questions

    # If still no good split, try splitting by multiple empty lines
    questions = re.split(r'\n\s*\n\s*\n+', content)
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
    cleaned = re.sub(r'^\s*\d+\.\s*', '', content, flags=re.MULTILINE)

    # Extract just the question text (before options start)
    # For multiple choice questions, look for the first option marker
    lines = cleaned.strip().split('\n')
    question_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check if this line starts with an option marker (A., B., etc.)
        if re.match(r'^[A-Z]\.\s', line):
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
        images = extract_images(q_content)

        if question_type == "multiple_choice":
            options = parse_options(q_content)

        # Remove image tags from content
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', q_content).strip()

        # Clean and normalize the question content
        clean_content = clean_question_content(clean_content)

        questions.append(Question(
            content=clean_content,
            question_type=question_type,
            options=options if options else None,
            images=images if images else None
        ))

    return questions