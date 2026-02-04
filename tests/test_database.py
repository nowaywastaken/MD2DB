import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_export_to_sql():
    """Test exporting questions to SQL."""
    from md2db.database import export_to_sql
    from md2db.models import Question

    questions = [
        Question(content="Test question", question_type="multiple_choice")
    ]
    sql = export_to_sql(questions)
    assert "INSERT INTO" in sql
    assert "Test question" in sql

def test_export_multiple_questions():
    """Test exporting multiple questions to SQL."""
    from md2db.database import export_to_sql
    from md2db.models import Question

    questions = [
        Question(content="Question 1", question_type="multiple_choice", options=["A", "B"]),
        Question(content="Question 2", question_type="true_false")
    ]
    sql = export_to_sql(questions)
    assert "Question 1" in sql
    assert "Question 2" in sql
    assert sql.count("INSERT INTO") == 2

def test_export_with_images():
    """Test exporting questions with images to SQL."""
    from md2db.database import export_to_sql
    from md2db.models import Question

    questions = [
        Question(
            content="Question with image",
            question_type="multiple_choice",
            images=["http://example.com/image.png"]
        )
    ]
    sql = export_to_sql(questions)
    assert "http://example.com/image.png" in sql