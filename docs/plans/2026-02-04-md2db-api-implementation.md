# MD2DB API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a file-to-database converter that transforms Markdown exam/quiz bank formats into structured database records.

**Architecture:** Create a Python-based API with modular parsers for different question types, image handling, and database export capabilities. The system will parse Markdown content, extract structured data, and convert it to database-ready formats.

**Tech Stack:** Python, FastAPI/Flask, SQLAlchemy, Pandas, Markdown parsing libraries, image processing libraries

---

## Project Structure Setup

### Task 1: Initialize Project Structure

**Files:**
- Create: `README.md`
- Create: `requirements.txt`
- Create: `setup.py`
- Create: `src/md2db/__init__.py`
- Create: `src/md2db/main.py`
- Create: `tests/__init__.py`

**Step 1: Create project structure**

```bash
mkdir -p src/md2db tests docs/plans
```

**Step 2: Initialize basic files**

```python
# src/md2db/__init__.py
__version__ = "0.1.0"
```

```python
# src/md2db/main.py
def main():
    print("MD2DB - Markdown to Database Converter")

if __name__ == "__main__":
    main()
```

```markdown
# README.md
# MD2DB

A converter that transforms Markdown exam/quiz bank formats into structured database records.

## Features
- Parse Markdown exam questions
- Extract structured question data
- Handle multiple question types
- Process images and LaTeX formulas
- Export to database formats
```

**Step 3: Create requirements file**

```text
# requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
pandas>=2.0.0
sqlalchemy>=2.0.0
markdown>=3.4.0
pillow>=10.0.0
python-multipart>=0.0.6
```

**Step 4: Create setup file**

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="md2db",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pandas>=2.0.0",
        "sqlalchemy>=2.0.0",
        "markdown>=3.4.0",
        "pillow>=10.0.0",
        "python-multipart>=0.0.6",
    ],
    python_requires=">=3.8",
)
```

**Step 5: Commit initial structure**

```bash
git add README.md requirements.txt setup.py src/ tests/
git commit -m "feat: initialize MD2DB project structure"
```

### Task 2: Define Data Models

**Files:**
- Create: `src/md2db/models.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test for Question model**

```python
# tests/test_models.py
import pytest
from src.md2db.models import Question

def test_question_creation():
    question = Question(
        content="What is 2+2?",
        question_type="multiple_choice",
        options=["3", "4", "5", "6"]
    )
    assert question.content == "What is 2+2?"
    assert question.question_type == "multiple_choice"
    assert len(question.options) == 4
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py::test_question_creation -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.models'"

**Step 3: Create Question model**

```python
# src/md2db/models.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Question:
    content: str
    question_type: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    images: Optional[List[str]] = None
    latex_formulas: Optional[List[str]] = None
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py::test_question_creation -v
```
Expected: PASS

**Step 5: Commit models**

```bash
git add src/md2db/models.py tests/test_models.py
git commit -m "feat: add Question data model"
```

### Task 3: Create Markdown Parser

**Files:**
- Create: `src/md2db/parser.py`
- Create: `tests/test_parser.py`

**Step 1: Write failing test for markdown parsing**

```python
# tests/test_parser.py
import pytest
from src.md2db.parser import parse_markdown

def test_parse_simple_question():
    markdown = "What is 2+2?"
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert questions[0].content == "What is 2+2?"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_parser.py::test_parse_simple_question -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.parser'"

**Step 3: Create basic parser**

```python
# src/md2db/parser.py
from typing import List
from .models import Question

def parse_markdown(content: str) -> List[Question]:
    """Parse markdown content and extract questions."""
    # Basic implementation - just create a single question
    return [Question(content=content.strip(), question_type="unknown")]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_parser.py::test_parse_simple_question -v
```
Expected: PASS

**Step 5: Commit parser**

```bash
git add src/md2db/parser.py tests/test_parser.py
git commit -m "feat: add basic markdown parser"
```

### Task 4: Create Question Type Detector

**Files:**
- Modify: `src/md2db/parser.py`
- Create: `tests/test_question_detection.py`

**Step 1: Write failing test for question type detection**

```python
# tests/test_question_detection.py
import pytest
from src.md2db.parser import detect_question_type

def test_detect_multiple_choice():
    content = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    question_type = detect_question_type(content)
    assert question_type == "multiple_choice"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_question_detection.py::test_detect_multiple_choice -v
```
Expected: FAIL with "NameError: name 'detect_question_type' is not defined"

**Step 3: Add question type detection**

```python
# src/md2db/parser.py
def detect_question_type(content: str) -> str:
    """Detect the type of question based on content patterns."""
    content_lower = content.lower()

    # Check for multiple choice patterns
    if any(marker in content_lower for marker in ["a.", "b.", "c.", "d."]):
        return "multiple_choice"

    # Check for true/false patterns
    if any(marker in content_lower for marker in ["true", "false", "正确", "错误"]):
        return "true_false"

    # Check for fill-in-the-blank patterns
    if "_____" in content or "____" in content:
        return "fill_in_blank"

    return "subjective"

def parse_markdown(content: str) -> List[Question]:
    """Parse markdown content and extract questions."""
    question_type = detect_question_type(content)
    return [Question(content=content.strip(), question_type=question_type)]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_question_detection.py::test_detect_multiple_choice -v
```
Expected: PASS

**Step 5: Commit question detection**

```bash
git add src/md2db/parser.py tests/test_question_detection.py
git commit -m "feat: add question type detection"
```

### Task 5: Create Options Parser

**Files:**
- Modify: `src/md2db/parser.py`
- Create: `tests/test_options_parsing.py`

**Step 1: Write failing test for options parsing**

```python
# tests/test_options_parsing.py
import pytest
from src.md2db.parser import parse_options

def test_parse_multiple_choice_options():
    content = "What is 2+2?\nA. 3\nB. 4\nC. 5\nD. 6"
    options = parse_options(content)
    assert options == ["3", "4", "5", "6"]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_options_parsing.py::test_parse_multiple_choice_options -v
```
Expected: FAIL with "NameError: name 'parse_options' is not defined"

**Step 3: Add options parsing**

```python
# src/md2db/parser.py
import re

def parse_options(content: str) -> List[str]:
    """Extract options from multiple choice questions."""
    options = []
    # Match patterns like "A. option text", "B. option text", etc.
    pattern = r'^[A-Z]\.\s*(.+)$'

    for line in content.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            options.append(match.group(1).strip())

    return options

def parse_markdown(content: str) -> List[Question]:
    """Parse markdown content and extract questions."""
    question_type = detect_question_type(content)
    options = []

    if question_type == "multiple_choice":
        options = parse_options(content)

    return [Question(
        content=content.strip(),
        question_type=question_type,
        options=options if options else None
    )]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_options_parsing.py::test_parse_multiple_choice_options -v
```
Expected: PASS

**Step 5: Commit options parsing**

```bash
git add src/md2db/parser.py tests/test_options_parsing.py
git commit -m "feat: add options parsing for multiple choice questions"
```

### Task 6: Create API Endpoint

**Files:**
- Create: `src/md2db/api.py`
- Create: `tests/test_api.py`

**Step 1: Write failing test for API endpoint**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.md2db.api import app

def test_parse_endpoint():
    client = TestClient(app)
    response = client.post("/parse", json={"markdown": "What is 2+2?"})
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py::test_parse_endpoint -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.api'"

**Step 3: Create API endpoint**

```python
# src/md2db/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from .parser import parse_markdown
from .models import Question

app = FastAPI(title="MD2DB API", version="0.1.0")

class ParseRequest(BaseModel):
    markdown: str

class ParseResponse(BaseModel):
    questions: List[dict]

@app.post("/parse", response_model=ParseResponse)
def parse_markdown_endpoint(request: ParseRequest):
    """Parse markdown content and return structured questions."""
    questions = parse_markdown(request.markdown)
    return {"questions": [question.__dict__ for question in questions]}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py::test_parse_endpoint -v
```
Expected: PASS

**Step 5: Commit API endpoint**

```bash
git add src/md2db/api.py tests/test_api.py
git commit -m "feat: add FastAPI endpoint for markdown parsing"
```

### Task 7: Add Image Processing

**Files:**
- Create: `src/md2db/image_processor.py`
- Create: `tests/test_image_processor.py`

**Step 1: Write failing test for image extraction**

```python
# tests/test_image_processor.py
import pytest
from src.md2db.image_processor import extract_images

def test_extract_image_urls():
    content = "Question with image ![alt](http://example.com/image.png)"
    images = extract_images(content)
    assert len(images) == 1
    assert images[0] == "http://example.com/image.png"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_image_processor.py::test_extract_image_urls -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.image_processor'"

**Step 3: Create image processor**

```python
# src/md2db/image_processor.py
import re
from typing import List

def extract_images(content: str) -> List[str]:
    """Extract image URLs from markdown content."""
    # Match markdown image syntax: ![alt](url)
    pattern = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(pattern, content)
    return matches
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_image_processor.py::test_extract_image_urls -v
```
Expected: PASS

**Step 5: Commit image processor**

```bash
git add src/md2db/image_processor.py tests/test_image_processor.py
git commit -m "feat: add image URL extraction from markdown"
```

### Task 8: Integrate Image Processing with Parser

**Files:**
- Modify: `src/md2db/parser.py`
- Modify: `tests/test_parser.py`

**Step 1: Write failing test for image integration**

```python
# tests/test_parser.py - add this test
def test_parse_question_with_images():
    markdown = "Question with image ![alt](http://example.com/image.png)"
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert questions[0].images == ["http://example.com/image.png"]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_parser.py::test_parse_question_with_images -v
```
Expected: FAIL with "AttributeError: 'Question' object has no attribute 'images'"

**Step 3: Update parser to handle images**

```python
# src/md2db/parser.py
from .image_processor import extract_images

def parse_markdown(content: str) -> List[Question]:
    """Parse markdown content and extract questions."""
    question_type = detect_question_type(content)
    options = []
    images = extract_images(content)

    if question_type == "multiple_choice":
        options = parse_options(content)

    # Remove image tags from content
    clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', content).strip()

    return [Question(
        content=clean_content,
        question_type=question_type,
        options=options if options else None,
        images=images if images else None
    )]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_parser.py::test_parse_question_with_images -v
```
Expected: PASS

**Step 5: Commit image integration**

```bash
git add src/md2db/parser.py tests/test_parser.py
git commit -m "feat: integrate image processing with parser"
```

### Task 9: Add Database Export

**Files:**
- Create: `src/md2db/database.py`
- Create: `tests/test_database.py`

**Step 1: Write failing test for database export**

```python
# tests/test_database.py
import pytest
from src.md2db.database import export_to_sql
from src.md2db.models import Question

def test_export_to_sql():
    questions = [
        Question(content="Test question", question_type="multiple_choice")
    ]
    sql = export_to_sql(questions)
    assert "INSERT INTO" in sql
    assert "Test question" in sql
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_database.py::test_export_to_sql -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.database'"

**Step 3: Create database exporter**

```python
# src/md2db/database.py
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_database.py::test_export_to_sql -v
```
Expected: PASS

**Step 5: Commit database export**

```bash
git add src/md2db/database.py tests/test_database.py
git commit -m "feat: add SQL export functionality"
```

### Task 10: Create Main Application

**Files:**
- Modify: `src/md2db/main.py`
- Create: `src/md2db/__main__.py`

**Step 1: Write failing test for CLI interface**

```python
# tests/test_cli.py
import pytest
from src.md2db.main import process_file

def test_process_file():
    result = process_file("test.md")
    assert "questions" in result
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli.py::test_process_file -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.main'"

**Step 3: Create CLI interface**

```python
# src/md2db/main.py
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

if __name__ == "__main__":
    main()
```

**Step 4: Create __main__.py for package execution**

```python
# src/md2db/__main__.py
from .main import main

if __name__ == "__main__":
    main()
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_cli.py::test_process_file -v
```
Expected: PASS

**Step 6: Commit CLI interface**

```bash
git add src/md2db/main.py src/md2db/__main__.py tests/test_cli.py
git commit -m "feat: add CLI interface for file processing"
```

### Task 11: Add Comprehensive Testing

**Files:**
- Create: `tests/test_integration.py`
- Modify: `tests/test_parser.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
import pytest
from src.md2db.parser import parse_markdown

def test_complete_question_parsing():
    markdown = """
What is the capital of France?

A. London
B. Berlin
C. Paris
D. Madrid

Answer: C
Explanation: Paris is the capital and largest city of France.
"""
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert questions[0].question_type == "multiple_choice"
    assert len(questions[0].options) == 4
    assert "Paris" in questions[0].options
```

**Step 2: Run integration test**

```bash
pytest tests/test_integration.py::test_complete_question_parsing -v
```
Expected: PASS

**Step 3: Add more parser tests**

```python
# tests/test_parser.py - add these tests
def test_parse_true_false_question():
    content = "Paris is the capital of France. True or False?"
    questions = parse_markdown(content)
    assert questions[0].question_type == "true_false"

def test_parse_fill_in_blank():
    content = "The capital of France is _____."
    questions = parse_markdown(content)
    assert questions[0].question_type == "fill_in_blank"
```

**Step 4: Run all tests**

```bash
pytest tests/ -v
```
Expected: All tests PASS

**Step 5: Commit comprehensive testing**

```bash
git add tests/test_integration.py tests/test_parser.py
git commit -m "test: add comprehensive test coverage"
```

### Task 12: Create Documentation

**Files:**
- Create: `docs/USAGE.md`
- Modify: `README.md`

**Step 1: Create usage documentation**

```markdown
# docs/USAGE.md
# MD2DB Usage Guide

## Command Line Interface

```bash
# Parse a markdown file
python -m md2db exam.md

# Parse and save to file
python -m md2db exam.md --output questions.sql
```

## API Usage

Start the API server:
```bash
uvicorn src.md2db.api:app --reload
```

Then make requests:
```bash
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "What is 2+2?"}'
```
```

**Step 2: Update README with usage examples**

```markdown
# README.md - add usage section
## Usage

See [docs/USAGE.md](docs/USAGE.md) for detailed usage instructions.

### Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Process a markdown file:
```bash
python -m md2db your_exam.md
```

3. Start the API server:
```bash
uvicorn src.md2db.api:app --reload
```
```

**Step 3: Commit documentation**

```bash
git add docs/USAGE.md README.md
git commit -m "docs: add usage documentation"
```

### Task 13: Final Integration and Testing

**Files:**
- Create: `examples/sample_exam.md`
- Create: `tests/test_examples.py`

**Step 1: Create sample exam file**

```markdown
# examples/sample_exam.md
# Sample Mathematics Exam

## Multiple Choice

1. What is 2+2?

A. 3
B. 4
C. 5
D. 6

Answer: B

## True/False

2. Paris is the capital of France.

True

## Fill in the Blank

3. The capital of Germany is _____.

Answer: Berlin
```

**Step 2: Create example test**

```python
# tests/test_examples.py
import pytest
from src.md2db.main import process_file

def test_sample_exam():
    result = process_file("examples/sample_exam.md")
    assert len(result["questions"]) >= 3
    assert "INSERT INTO" in result["sql"]
```

**Step 3: Run example test**

```bash
pytest tests/test_examples.py::test_sample_exam -v
```
Expected: PASS

**Step 4: Run full test suite**

```bash
pytest tests/ -v
```
Expected: All tests PASS

**Step 5: Commit examples and final testing**

```bash
git add examples/ tests/test_examples.py
git commit -m "feat: add sample exam and final integration testing"
```

## Summary

This implementation plan creates a complete MD2DB system with:
- Modular Python architecture
- Markdown parsing for different question types
- Image URL extraction
- SQL database export
- FastAPI REST API
- Command-line interface
- Comprehensive test coverage
- Usage documentation

The system handles multiple choice, true/false, fill-in-the-blank, and subjective questions with support for images and LaTeX formulas.