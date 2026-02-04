import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_parse_simple_question():
    """Test parsing a simple question."""
    from md2db.parser import parse_markdown

    markdown = "What is 2+2?"
    questions = parse_markdown(markdown)

    assert len(questions) == 1
    assert questions[0].content == "What is 2+2?"
    assert questions[0].question_type == "subjective"

def test_parse_multiple_choice():
    """Test parsing multiple choice question."""
    from md2db.parser import parse_markdown

    markdown = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    questions = parse_markdown(markdown)

    assert len(questions) == 1
    assert questions[0].question_type == "multiple_choice"
    assert len(questions[0].options) == 3
    assert "3" in questions[0].options
    assert "4" in questions[0].options
    assert "5" in questions[0].options