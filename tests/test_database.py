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

def test_sql_injection_protection():
    """Test that SQL injection attempts are properly prevented."""
    from md2db.database import export_to_sql
    from md2db.models import Question

    # 测试SQL注入防护
    malicious_content = "What is 2+2?'; DROP TABLE questions; --"
    question = Question(
        content=malicious_content,
        question_type="multiple_choice",
        options=["A. 3", "B. 4"]
    )

    sql = export_to_sql([question])

    # 验证SQL注入内容被正确转义
    # 单引号应该被转义为两个单引号
    assert "What is 2+2?''; DROP TABLE questions; --" in sql

    # 验证生成的SQL语法正确
    assert sql.startswith("INSERT INTO")
    assert sql.endswith(";")
    assert "VALUES" in sql

    # 确保没有未转义的危险内容
    # DROP TABLE应该出现在字符串值内（被单引号包围）
    assert "'DROP TABLE questions" not in sql

    # 验证单引号被正确转义
    # 检查内容的单引号被转义为两个单引号
    assert "''" in sql