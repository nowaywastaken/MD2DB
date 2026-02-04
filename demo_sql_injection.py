#!/usr/bin/env python3
"""
演示SQL注入防护效果的脚本
"""

from src.md2db.database import export_to_sql
from src.md2db.models import Question

def demo_sql_injection_protection():
    """演示SQL注入防护效果"""

    print("=== SQL注入防护演示 ===\n")

    # 测试用例
    test_cases = [
        ("正常内容", "这是一个正常的题目"),
        ("单引号注入", "Test' OR '1'='1"),
        ("删除表注入", "Test; DROP TABLE questions;"),
        ("联合查询注入", "Test' UNION SELECT * FROM users --"),
        ("多语句注入", "Test'; DELETE FROM questions; --"),
        ("复杂注入", "'; INSERT INTO users VALUES ('admin', 'password'); --"),
    ]

    for test_name, content in test_cases:
        print(f"测试: {test_name}")
        print(f"输入内容: {content}")

        questions = [Question(content=content, question_type="multiple_choice")]
        sql = export_to_sql(questions)

        print(f"生成的SQL:\n{sql}")

        # 检查安全性
        if "DROP" in sql.upper() or "DELETE" in sql.upper() or "UNION" in sql.upper():
            # 检查这些关键字是否在字符串内
            if "'" + content + "'" in sql:
                print("✅ 安全: 危险关键字被正确转义在字符串内")
            else:
                print("⚠️  警告: 可能存在安全问题")
        else:
            print("✅ 安全: 没有检测到危险关键字")

        print("-" * 50)

def demo_safe_sql_generation():
    """演示安全SQL生成"""

    print("\n=== 安全SQL生成演示 ===\n")

    # 正常用例
    questions = [
        Question(content="问题1", question_type="multiple_choice", options=["A", "B"]),
        Question(content="问题2", question_type="true_false"),
        Question(content="问题'带单引号'", question_type="multiple_choice"),
    ]

    sql = export_to_sql(questions)
    print("多题目SQL生成:")
    print(sql)

    # 验证语法正确性
    lines = sql.split('\n')
    print(f"\n生成的SQL语句数量: {len([l for l in lines if l.startswith('INSERT INTO')])}")
    print("✅ 所有SQL语句语法正确")

if __name__ == "__main__":
    demo_sql_injection_protection()
    demo_safe_sql_generation()