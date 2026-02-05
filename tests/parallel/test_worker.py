import pytest
from src.md2db.parallel.worker import parse_chunk


def test_parse_chunk_single_question():
    """Test parsing a chunk with a single question."""
    chunk_content = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    result = parse_chunk(chunk_content)

    assert len(result) == 1
    assert result[0]["content"] == "What is 2+2?"
    assert result[0]["question_type"] == "multiple_choice"


def test_parse_chunk_multiple_questions():
    """Test parsing a chunk with multiple questions."""
    chunk_content = """1. What is 2+2?
A. 3
B. 4

2. What is 3+3?
A. 5
B. 6
"""
    result = parse_chunk(chunk_content)

    assert len(result) == 2
    assert result[0]["content"] == "What is 2+2?"
    assert result[1]["content"] == "What is 3+3?"


def test_parse_chunk_with_images():
    """Test parsing a chunk with images."""
    chunk_content = "Question ![img](http://example.com/img.png) with image"
    result = parse_chunk(chunk_content)

    assert len(result) == 1
    assert "http://example.com/img.png" in result[0]["images"]


def test_parse_chunk_returns_serializable_dicts():
    """Test that parse_chunk returns serializable dicts, not objects."""
    chunk_content = "What is 2+2?\nA. 3"
    result = parse_chunk(chunk_content)

    # Result should be a list of dicts, not QuestionDocument objects
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert "content" in result[0]
    assert "question_type" in result[0]
