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

def test_extract_latex_inline():
    """Test extracting inline LaTeX formulas."""
    from md2db.parser import parse_markdown

    markdown = "Solve the equation: $x^2 + y^2 = z^2$"
    questions = parse_markdown(markdown)

    assert len(questions) == 1
    assert questions[0].latex_formulas is not None
    assert len(questions[0].latex_formulas) == 1
    assert questions[0].latex_formulas[0] == "x^2 + y^2 = z^2"

def test_extract_latex_display():
    """Test extracting display LaTeX formulas."""
    from md2db.parser import parse_markdown

    markdown = "Integral formula: $$\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$"
    questions = parse_markdown(markdown)

    assert len(questions) == 1
    assert questions[0].latex_formulas is not None
    assert len(questions[0].latex_formulas) == 1
    assert questions[0].latex_formulas[0] == "\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}"

def test_extract_multiple_latex_formulas():
    """Test extracting multiple LaTeX formulas."""
    from md2db.parser import parse_markdown

    markdown = "Derivative: $\\frac{dy}{dx}$ and integral: $$\\int f(x) dx$$"
    questions = parse_markdown(markdown)

    assert len(questions) == 1
    assert questions[0].latex_formulas is not None
    assert len(questions[0].latex_formulas) == 2
    assert "\\frac{dy}{dx}" in questions[0].latex_formulas
    assert "\\int f(x) dx" in questions[0].latex_formulas

def test_detect_multiple_choice_with_single_option():
    """Test that single option doesn't trigger multiple choice detection."""
    from md2db.parser import detect_question_type

    # This should NOT be detected as multiple choice
    content = "What is the capital of France?\nA. Paris"
    question_type = detect_question_type(content)
    assert question_type == "subjective"

def test_detect_multiple_choice_with_two_options():
    """Test that two options trigger multiple choice detection."""
    from md2db.parser import detect_question_type

    # This should be detected as multiple choice
    content = "What is the capital of France?\nA. Paris\nB. London"
    question_type = detect_question_type(content)
    assert question_type == "multiple_choice"

def test_detect_multiple_choice_with_four_options():
    """Test that four options trigger multiple choice detection."""
    from md2db.parser import detect_question_type

    # This should be detected as multiple choice
    content = "What is 2+2?\nA. 3\nB. 4\nC. 5\nD. 6"
    question_type = detect_question_type(content)
    assert question_type == "multiple_choice"

def test_avoid_false_positive_multiple_choice():
    """Test that text containing 'a.' or 'b.' doesn't trigger false positive."""
    from md2db.parser import detect_question_type

    # These should NOT be detected as multiple choice
    test_cases = [
        "This is a. simple text",
        "The answer is b. correct",
        "Item a. and item b. are both valid",
        "First point a. Second point b. Third point c."
    ]

    for content in test_cases:
        question_type = detect_question_type(content)
        assert question_type != "multiple_choice", f"False positive for: {content}"

def test_true_false_detection_still_works():
    """Test that true/false detection still works correctly."""
    from md2db.parser import detect_question_type

    content = "Is the Earth flat?\nTrue\nFalse"
    question_type = detect_question_type(content)
    assert question_type == "true_false"

def test_fill_in_blank_detection_still_works():
    """Test that fill-in-the-blank detection still works correctly."""
    from md2db.parser import detect_question_type

    content = "Complete the sentence: The capital of France is _____"
    question_type = detect_question_type(content)
    assert question_type == "fill_in_blank"

def test_multiple_choice_with_mixed_case():
    """Test multiple choice detection with mixed case options."""
    from md2db.parser import detect_question_type

    # Test uppercase options
    content_upper = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    question_type = detect_question_type(content_upper)
    assert question_type == "multiple_choice"

    # Test lowercase options
    content_lower = "What is 2+2?\na. 3\nb. 4\nc. 5"
    question_type = detect_question_type(content_lower)
    assert question_type == "multiple_choice"

def test_multiple_choice_with_tabs():
    """Test multiple choice detection with tabs after options."""
    from md2db.parser import detect_question_type

    content = "What is 2+2?\nA.\t3\nB.\t4\nC.\t5"
    question_type = detect_question_type(content)
    assert question_type == "multiple_choice"

def test_multiple_choice_with_extra_spaces():
    """Test multiple choice detection with extra spaces."""
    from md2db.parser import detect_question_type

    content = "What is 2+2?\n  A.   3\n  B.   4\n  C.   5"
    question_type = detect_question_type(content)
    assert question_type == "multiple_choice"

def test_not_multiple_choice_with_options_in_middle():
    """Test that options in the middle of sentences don't trigger detection."""
    from md2db.parser import detect_question_type

    content = "The answer is A. correct but B. is also possible"
    question_type = detect_question_type(content)
    assert question_type != "multiple_choice"