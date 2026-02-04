from typing import List
from .models import Question

def export_to_sql(questions: List[Question]) -> str:
    """Export questions to SQL INSERT statements."""
    sql_statements = []

    for i, question in enumerate(questions):
        options_str = ",".join(question.options) if question.options else ""
        images_str = ",".join(question.images) if question.images else ""

        sql = f"""INSERT INTO questions (id, content, question_type, options, images)
VALUES ({i}, '{question.content}', '{question.question_type}', '{options_str}', '{images_str}');"""
        sql_statements.append(sql)

    return "\n".join(sql_statements)