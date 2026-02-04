# MD2DB Usage Guide

MD2DB is a Python package that converts Markdown exam/quiz bank formats into structured database records. This guide covers both command-line and API usage.

## Command Line Interface

The command-line interface allows you to process Markdown files directly from your terminal.

### Basic Usage

```bash
# Parse a markdown file and output SQL to console
python -m md2db exam.md

# Parse and save SQL output to a file
python -m md2db exam.md --output questions.sql
python -m md2db exam.md -o questions.sql
```

### Example

Given a Markdown file `exam.md`:

```markdown
What is 2+2?

A) 3
B) 4
C) 5
D) 6

Answer: B
```

Running:
```bash
python -m md2db exam.md
```

Will output SQL statements like:
```sql
INSERT INTO questions (question_text, options, correct_answer, question_type) VALUES ('What is 2+2?', '["3", "4", "5", "6"]', 'B', 'multiple_choice');
```

### CLI Options

- `file`: (required) Path to the Markdown file to process
- `--output`, `-o`: (optional) Output file path for SQL statements

## API Usage

MD2DB also provides a FastAPI-based REST API for programmatic access.

### Starting the API Server

```bash
uvicorn src.md2db.api:app --reload
```

This starts the server on `http://localhost:8000` with auto-reload enabled for development.

### API Endpoints

#### Parse Markdown

**Endpoint:** `POST /parse`

Parse Markdown content and return structured questions.

**Request Body:**
```json
{
  "markdown": "What is 2+2?\n\nA) 3\nB) 4\nC) 5\nD) 6\n\nAnswer: B"
}
```

**Response:**
```json
{
  "questions": [
    {
      "question_text": "What is 2+2?",
      "options": ["3", "4", "5", "6"],
      "correct_answer": "B",
      "question_type": "multiple_choice"
    }
  ]
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "What is 2+2?"}'
```

#### Health Check

**Endpoint:** `GET /health`

Check if the API server is running.

**Response:**
```json
{
  "status": "healthy"
}
```

**Example using curl:**
```bash
curl "http://localhost:8000/health"
```

### API Documentation

When the API server is running, you can access interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Supported Markdown Formats

MD2DB supports various exam question formats:

### Multiple Choice Questions

```markdown
What is the capital of France?

A) London
B) Berlin
C) Paris
D) Madrid

Answer: C
```

### True/False Questions

```markdown
Python is a compiled language.

Answer: False
```

### Short Answer Questions

```markdown
What does HTML stand for?

Answer: HyperText Markup Language
```

## Output Formats

Currently, MD2DB supports SQL output format with the following schema:

```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    options TEXT, -- JSON array for multiple choice
    correct_answer TEXT,
    question_type TEXT
);
```

## Error Handling

- Invalid Markdown files will raise parsing errors
- Missing files will result in file not found errors
- API endpoints return appropriate HTTP status codes (200, 400, 500)

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure you've installed dependencies with `pip install -r requirements.txt`
2. **API server won't start**: Check that port 8000 is available
3. **File encoding issues**: Ensure Markdown files use UTF-8 encoding

### Getting Help

For additional support, check the project repository or create an issue with:
- The Markdown content causing problems
- Error messages received
- Your operating system and Python version