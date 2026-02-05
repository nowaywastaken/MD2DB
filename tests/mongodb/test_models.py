import pytest
from src.md2db.mongodb.models import QuestionDocument, OptionDocument, ImageDocument, LatexDocument


def test_question_document_creation():
    doc = QuestionDocument(
        content="What is 2+2?",
        question_type="multiple_choice"
    )
    assert doc.content == "What is 2+2?"
    assert doc.question_type == "multiple_choice"
    assert doc.options == []
    assert doc.images == []
    assert doc.latex_formulas == []


def test_option_document_creation():
    doc = OptionDocument(label="A", content="3")
    assert doc.label == "A"
    assert doc.content == "3"
    assert doc.hash is not None  # hash should be auto-generated


def test_image_document_creation():
    doc = ImageDocument(url="http://example.com/image.png", alt="diagram")
    assert doc.url == "http://example.com/image.png"
    assert doc.alt == "diagram"
    assert doc.hash is not None


def test_latex_document_creation():
    doc = LatexDocument(formula="\\frac{a}{b}")
    assert doc.formula == "\\frac{a}{b}"
    assert doc.hash is not None
