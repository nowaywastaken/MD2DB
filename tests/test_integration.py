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

def test_api_integration():
    """Test API integration with complete workflow."""
    from fastapi.testclient import TestClient
    from md2db.api import app

    client = TestClient(app)

    markdown = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    response = client.post("/parse", json={"markdown": markdown})

    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 1
    assert data["questions"][0]["question_type"] == "multiple_choice"
    assert len(data["questions"][0]["options"]) == 3

def test_cli_integration():
    """Test CLI integration with file processing."""
    from md2db.main import process_file

    # Create test file
    test_content = """Question with image:
![diagram](http://example.com/diagram.png)

What is the result?
A. Option A
B. Option B
"""

    with open("test_integration.md", "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        result = process_file("test_integration.md")
        assert "questions" in result
        assert "sql" in result
        assert len(result["questions"]) == 1
        assert "http://example.com/diagram.png" in result["sql"]
        assert "Option A" in result["sql"]
    finally:
        # Clean up
        if os.path.exists("test_integration.md"):
            os.remove("test_integration.md")