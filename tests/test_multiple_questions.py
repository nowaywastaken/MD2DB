"""Test cases for multiple questions parsing functionality."""
import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_parse_multiple_numbered_questions():
    """Test parsing multiple questions with numeric numbering."""
    from md2db.parser import parse_markdown

    markdown = """1. What is 2+2?
A. 3
B. 4
C. 5

2. What is the capital of France?
A. London
B. Paris
C. Berlin

3. True or False: The Earth is flat."""

    questions = parse_markdown(markdown)

    # This test currently fails - we expect 3 questions but currently get 1
    assert len(questions) == 3

    # Question 1
    assert questions[0].content == "What is 2+2?"
    assert questions[0].question_type == "multiple_choice"
    assert len(questions[0].options) == 3

    # Question 2
    assert questions[1].content == "What is the capital of France?"
    assert questions[1].question_type == "multiple_choice"
    assert len(questions[1].options) == 3

    # Question 3
    assert questions[2].content == "True or False: The Earth is flat."
    assert questions[2].question_type == "true_false"


def test_parse_multiple_questions_with_separators():
    """Test parsing multiple questions with separator lines."""
    from md2db.parser import parse_markdown

    markdown = """What is 2+2?
A. 3
B. 4
C. 5

---

What is the capital of France?
A. London
B. Paris
C. Berlin

---

True or False: The Earth is flat."""

    questions = parse_markdown(markdown)

    # This test currently fails - we expect 3 questions but currently get 1
    assert len(questions) == 3

    assert questions[0].content == "What is 2+2?"
    assert questions[0].question_type == "multiple_choice"

    assert questions[1].content == "What is the capital of France?"
    assert questions[1].question_type == "multiple_choice"

    assert questions[2].content == "True or False: The Earth is flat."
    assert questions[2].question_type == "true_false"


def test_parse_mixed_question_types():
    """Test parsing mixed question types in single markdown."""
    from md2db.parser import parse_markdown

    markdown = """1. What is 2+2?
A. 3
B. 4

2. Complete: The capital of France is _____.

3. True or False: Python is a programming language."""

    questions = parse_markdown(markdown)

    # This test currently fails - we expect 3 questions but currently get 1
    assert len(questions) == 3

    assert questions[0].content == "What is 2+2?"
    assert questions[0].question_type == "multiple_choice"

    assert questions[1].content == "Complete: The capital of France is _____."
    assert questions[1].question_type == "fill_in_blank"

    assert questions[2].content == "True or False: Python is a programming language."
    assert questions[2].question_type == "true_false"


def test_parse_empty_lines_between_questions():
    """Test parsing questions with empty lines as separators."""
    from md2db.parser import parse_markdown

    markdown = """What is 2+2?
A. 3
B. 4


What is the capital of France?
A. London
B. Paris


True or False: The Earth is flat."""

    questions = parse_markdown(markdown)

    # This test currently fails - we expect 3 questions but currently get 1
    assert len(questions) == 3

    assert questions[0].content == "What is 2+2?"
    assert questions[1].content == "What is the capital of France?"
    assert questions[2].content == "True or False: The Earth is flat."


def test_single_question_still_works():
    """Test that single question parsing still works after changes."""
    from md2db.parser import parse_markdown

    markdown = "What is 2+2?"
    questions = parse_markdown(markdown)

    # This should still work
    assert len(questions) == 1
    assert questions[0].content == "What is 2+2?"
    assert questions[0].question_type == "subjective"