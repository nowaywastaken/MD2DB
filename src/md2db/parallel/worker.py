from typing import List, Dict, Any
from ..parser import parse_markdown


def parse_chunk(chunk_content: str) -> List[Dict[str, Any]]:
    """Parse a chunk of markdown content into QuestionDocument objects.

    This function runs in worker processes. Returns serializable dicts
    to avoid pickling issues with multiprocessing.

    The parser already extracts images and LaTeX formulas for each question
    individually. We simply pass through the data from the Question objects.

    Args:
        chunk_content: The markdown content to parse

    Returns:
        List of dicts representing QuestionDocument objects
    """
    # Use existing parser (already extracts images and latex per question)
    questions = parse_markdown(chunk_content)

    # Convert to serializable dicts
    documents = []
    for q in questions:
        doc = {
            "content": q.content,
            "question_type": q.question_type,
            "options": q.options or [],
            "answer": q.answer,
            "explanation": q.explanation,
            "images": q.images or [],  # Parser already extracted per question
            "latex_formulas": q.latex_formulas or []  # Parser already extracted per question
        }
        documents.append(doc)

    return documents
