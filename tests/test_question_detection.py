import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_detect_multiple_choice():
    """Test detecting multiple choice questions."""
    from md2db.parser import detect_question_type

    content = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    question_type = detect_question_type(content)
    assert question_type == "multiple_choice"

def test_detect_true_false():
    """Test detecting true/false questions."""
    from md2db.parser import detect_question_type

    content = "Paris is the capital of France. True or False?"
    question_type = detect_question_type(content)
    assert question_type == "true_false"

def test_detect_fill_in_blank():
    """Test detecting fill-in-the-blank questions."""
    from md2db.parser import detect_question_type

    content = "The capital of France is _____."
    question_type = detect_question_type(content)
    assert question_type == "fill_in_blank"