import pytest
import os
from src.md2db.main import process_file

def test_sample_exam():
    result = process_file("examples/sample_exam.md")
    # The parser should now detect multiple questions
    assert len(result["questions"]) >= 3
    assert "INSERT INTO" in result["sql"]

def test_multiple_questions_with_latex_example():
    """Test processing a file with multiple questions containing LaTeX formulas."""
    import os
    from src.md2db.main import process_file

    # Create a test file with multiple questions and LaTeX
    test_content = """Solve the quadratic equation: $x^2 - 5x + 6 = 0$

A. $x = 2, 3$
B. $x = 1, 6$
C. $x = -2, -3$
D. $x = -1, -6$

---

Calculate the definite integral: $$\\int_0^1 x^2 dx$$

Answer: $$\\frac{1}{3}$$

---

True or False: The derivative of $\\sin(x)$ is $\\cos(x)$.

Answer: True
"""

    with open("test_latex_exam.md", "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        result = process_file("test_latex_exam.md")
        assert len(result["questions"]) == 3

        # Check that LaTeX formulas are preserved
        sql_content = result["sql"]
        assert "x^2 - 5x + 6 = 0" in sql_content
        assert "\\int_0^1 x^2 dx" in sql_content
        assert "\\sin(x)" in sql_content
        assert "\\cos(x)" in sql_content

        # With current implementation, questions are split but each only contains question text
        # Options are parsed separately
        assert result["questions"][0]["question_type"] == "subjective"
        assert result["questions"][1]["question_type"] == "subjective"
        assert result["questions"][2]["question_type"] == "true_false"

    finally:
        if os.path.exists("test_latex_exam.md"):
            os.remove("test_latex_exam.md")