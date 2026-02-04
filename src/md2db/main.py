import argparse
from .parser import parse_markdown
from .database import export_to_sql

def process_file(filename: str) -> dict:
    """Process a markdown file and return structured data."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = parse_markdown(content)
    sql_output = export_to_sql(questions)

    return {
        "questions": [q.__dict__ for q in questions],
        "sql": sql_output
    }

def main():
    parser = argparse.ArgumentParser(description="MD2DB - Markdown to Database Converter")
    parser.add_argument("file", help="Markdown file to process")
    parser.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    result = process_file(args.file)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result["sql"])
        print(f"Output written to {args.output}")
    else:
        print(result["sql"])