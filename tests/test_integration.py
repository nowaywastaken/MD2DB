import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_complete_question_parsing():
    """Test complete question parsing workflow."""
    from md2db.parser import parse_markdown

    markdown = """
What is the capital of France?

A. London
B. Berlin
C. Paris
D. Madrid

Answer: C
Explanation: Paris is the capital and largest city of France.
"""
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert questions[0].question_type == "multiple_choice"
    assert len(questions[0].options) == 4
    assert "Paris" in questions[0].options

def test_multiple_questions_with_latex():
    """Test parsing multiple questions with LaTeX formulas."""
    from md2db.parser import parse_markdown

    # Test case 1: Multiple questions with separator lines
    markdown1 = """
What is the solution to the equation $x^2 + 2x + 1 = 0$?

A. $x = -1$
B. $x = 1$
C. $x = 0$
D. $x = 2$

---

Calculate the integral $\\int_0^1 x^2 dx$.

Answer: $\\frac{1}{3}$

---

What is the derivative of $f(x) = \\sin(x)$?

Answer: $f'(x) = \\cos(x)$
"""
    questions1 = parse_markdown(markdown1)
    assert len(questions1) == 3

    # With current implementation, each question contains only the question text
    # Options are parsed separately

    # Question 1: Should contain LaTeX in question text
    assert "x^2 + 2x + 1 = 0" in questions1[0].content
    assert questions1[0].latex_formulas is not None
    assert len(questions1[0].latex_formulas) >= 1

    # Question 2: Subjective with LaTeX
    assert "integral" in questions1[1].content.lower()
    assert questions1[1].latex_formulas is not None
    assert "\\int_0^1 x^2 dx" in questions1[1].latex_formulas

    # Question 3: Subjective with LaTeX
    assert "derivative" in questions1[2].content.lower()
    assert questions1[2].latex_formulas is not None
    assert any("\\sin(x)" in latex for latex in questions1[2].latex_formulas)

    # Test case 2: Single multiple choice question with LaTeX options
    markdown2 = """
Solve the quadratic equation: $x^2 - 4 = 0$

A. $x = 2$
B. $x = -2$
C. $x = \\pm 2$
D. $x = 0$
"""
    questions2 = parse_markdown(markdown2)
    assert len(questions2) == 1
    assert questions2[0].question_type == "multiple_choice"
    assert len(questions2[0].options) == 4
    # Options should contain LaTeX formulas
    assert any("x = 2" in option for option in questions2[0].options)
    assert any("x = -2" in option for option in questions2[0].options)
    assert any("\\pm 2" in option for option in questions2[0].options)

def test_api_integration_with_multiple_questions():
    """Test API integration with multiple questions workflow."""
    from fastapi.testclient import TestClient
    from md2db.api import app

    client = TestClient(app)

    markdown = """
1. What is 2+2?
A. 3
B. 4
C. 5

2. What is the capital of France?
A. London
B. Paris
C. Berlin

3. True or False: Python is a programming language.
"""
    response = client.post("/parse", json={"markdown": markdown})

    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    assert data["questions"][0]["question_type"] == "multiple_choice"
    assert data["questions"][1]["question_type"] == "multiple_choice"
    assert data["questions"][2]["question_type"] == "true_false"

def test_cli_integration_with_multiple_questions():
    """Test CLI integration with multiple questions file processing."""
    from md2db.main import process_file
    import os

    # Create test file with multiple questions
    test_content = """Question 1:
What is the solution to $x^2 = 4$?
A. $x = 2$
B. $x = -2$
C. Both A and B

---

Question 2:
Calculate $\\int x dx$.

Answer: $\\frac{x^2}{2} + C$

---

Question 3:
True or False: $e^{i\\pi} = -1$
"""

    with open("test_multiple_questions.md", "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        result = process_file("test_multiple_questions.md")
        assert "questions" in result
        assert "sql" in result
        assert len(result["questions"]) == 3

        # Check that LaTeX formulas are preserved in SQL
        sql_content = result["sql"]
        assert "x^2 = 4" in sql_content
        assert "\\int x dx" in sql_content
        assert "e^{i\\pi} = -1" in sql_content

        # Check question types
        assert result["questions"][0]["question_type"] == "multiple_choice"
        assert result["questions"][1]["question_type"] == "subjective"
        assert result["questions"][2]["question_type"] == "true_false"

    finally:
        # Clean up
        if os.path.exists("test_multiple_questions.md"):
            os.remove("test_multiple_questions.md")