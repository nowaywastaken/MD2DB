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

def parse_markdown(content: str) -> List[Question]:
    """Parse markdown content and extract questions."""
    question_type = detect_question_type(content)
    options = []
    images = extract_images(content)

    if question_type == "multiple_choice":
        options = parse_options(content)

    # Remove image tags from content
    clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', content).strip()

    return [Question(
        content=clean_content,
        question_type=question_type,
        options=options if options else None,
        images=images if images else None
    )]