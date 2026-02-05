from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from functools import lru_cache
from .parser import parse_markdown
from .models import Question
import hashlib

app = FastAPI(title="MD2DB API", version="0.1.0")

class ParseRequest(BaseModel):
    markdown: str

class ParseResponse(BaseModel):
    questions: List[Dict[str, Any]]

class QuestionResponse(BaseModel):
    content: str
    question_type: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    images: Optional[List[str]] = None
    latex_formulas: Optional[List[str]] = None

def _question_to_dict(question: Question) -> Dict[str, Any]:
    """Convert Question to dict, handling None values properly."""
    return {
        "content": question.content,
        "question_type": question.question_type,
        "options": question.options,
        "answer": question.answer,
        "explanation": question.explanation,
        "images": question.images,
        "latex_formulas": question.latex_formulas
    }

# Simple in-memory cache using dict for async-safe operations
_response_cache: Dict[str, List[Dict[str, Any]]] = {}
_cache_max_size = 128

def _get_cache_key(content: str) -> str:
    """Generate cache key from content."""
    return hashlib.sha256(content.encode()).hexdigest()

def _cache_get(key: str) -> Optional[List[Dict[str, Any]]]:
    """Get value from cache."""
    return _response_cache.get(key)

def _cache_set(key: str, value: List[Dict[str, Any]]) -> None:
    """Set value in cache with LRU eviction."""
    if len(_response_cache) >= _cache_max_size:
        # Remove first (oldest) entry
        oldest_key = next(iter(_response_cache))
        del _response_cache[oldest_key]
    _response_cache[key] = value

@app.post("/parse", response_model=ParseResponse)
async def parse_markdown_endpoint(request: ParseRequest):
    """Parse markdown content and return structured questions."""
    cache_key = _get_cache_key(request.markdown)

    # Check cache
    cached = _cache_get(cache_key)
    if cached is not None:
        return {"questions": cached}

    # Parse markdown
    questions = parse_markdown(request.markdown)
    result = [_question_to_dict(q) for q in questions]

    # Cache result
    _cache_set(cache_key, result)

    return {"questions": result}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return {
        "size": len(_response_cache),
        "max_size": _cache_max_size
    }

@app.post("/cache/clear")
async def cache_clear():
    """Clear the cache."""
    _response_cache.clear()
    return {"status": "cache cleared"}