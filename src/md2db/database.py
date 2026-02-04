from typing import List
from .models import Question

def export_to_sql(questions: List[Question]) -> str:
    """Export questions to SQL INSERT statements with SQL injection protection."""
    sql_statements = []

    for i, question in enumerate(questions):
        # 转义字符串值中的单引号来防止SQL注入
        # 这是SQL注入防护的基本方法，适用于当前生成静态SQL文件的场景
        content = question.content.replace("'", "''")
        question_type = question.question_type.replace("'", "''")

        options_str = ",".join(question.options) if question.options else ""
        options_str = options_str.replace("'", "''")

        images_str = ",".join(question.images) if question.images else ""
        images_str = images_str.replace("'", "''")

        sql = f"""INSERT INTO questions (id, content, question_type, options, images)
VALUES ({i}, '{content}', '{question_type}', '{options_str}', '{images_str}');"""
        sql_statements.append(sql)

    return "\n".join(sql_statements)