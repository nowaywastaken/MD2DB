import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_process_file():
    """Test processing a markdown file."""
    from md2db.main import process_file

    # Create a test markdown file
    test_content = "What is 2+2?"
    with open("test_exam.md", "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        result = process_file("test_exam.md")
        assert "questions" in result
        assert "sql" in result
        assert len(result["questions"]) == 1
        assert "INSERT INTO" in result["sql"]
    finally:
        # Clean up test file
        if os.path.exists("test_exam.md"):
            os.remove("test_exam.md")