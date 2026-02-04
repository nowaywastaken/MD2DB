# MD2DB

A converter that transforms Markdown exam/quiz bank formats into structured database records.

## Features
- Parse Markdown exam questions
- Extract structured question data
- Handle multiple question types
- Process images and LaTeX formulas
- Export to database formats

## Installation

```bash
pip install -r requirements.txt
```

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