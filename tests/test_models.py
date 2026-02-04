import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_question_creation():
    """Test that Question model can be created with basic fields."""
    from md2db.models import Question

    question = Question(
        content="What is 2+2?",
        question_type="multiple_choice",
        options=["3", "4", "5", "6"]
    )
    assert question.content == "What is 2+2?"
    assert question.question_type == "multiple_choice"
    assert len(question.options) == 4

def test_question_with_images():
    """Test that Question model handles images."""
    from md2db.models import Question

    question = Question(
        content="Question with image",
        question_type="multiple_choice",
        images=["http://example.com/image.png"]
    )
    assert question.images == ["http://example.com/image.png"]

def test_question_with_latex():
    """Test that Question model handles LaTeX formulas."""
    from md2db.models import Question

    question = Question(
        content="Question with formula",
        question_type="subjective",
        latex_formulas=["\\sqrt{x^2 + y^2}"]
    )
    assert question.latex_formulas == ["\\sqrt{x^2 + y^2}"]