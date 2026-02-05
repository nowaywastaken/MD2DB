from typing import List, Dict, Any
from ..parser import parse_markdown
from ..mongodb.models import QuestionDocument
from ..image_processor import extract_images, extract_latex_formulas


def parse_chunk(chunk_content: str) -> List[Dict[str, Any]]:
    """Parse a chunk of markdown content into QuestionDocument objects.

    This function runs in worker processes. Returns serializable dicts
    to avoid pickling issues with multiprocessing.

    Args:
        chunk_content: The markdown content to parse

    Returns:
        List of dicts representing QuestionDocument objects
    """
    # Use existing parser
    questions = parse_markdown(chunk_content)

    # Convert to serializable dicts
    documents = []
    for q in questions:
        # Extract images and latex from original chunk content
        images = extract_images(chunk_content)
        latex = extract_latex_formulas(chunk_content)

        doc = {
            "content": q.content,
            "question_type": q.question_type,
            "options": q.options or [],
            "answer": q.answer,
            "explanation": q.explanation,
            "images": images,  # List of URLs
            "latex_formulas": latex  # List of formulas
        }
        documents.append(doc)

    return documents
