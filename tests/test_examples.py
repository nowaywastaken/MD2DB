import pytest
from src.md2db.main import process_file

def test_sample_exam():
    result = process_file("examples/sample_exam.md")
    assert len(result["questions"]) >= 3
    assert "INSERT INTO" in result["sql"]