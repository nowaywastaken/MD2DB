import pytest
from src.md2db.main import process_file

def test_sample_exam():
    result = process_file("examples/sample_exam.md")
    # The parser treats the entire file as one question block
    assert len(result["questions"]) >= 1
    assert "INSERT INTO" in result["sql"]