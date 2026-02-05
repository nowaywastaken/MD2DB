# MD2DB MongoDB Integration

## Overview

MD2DB supports high-performance parallel processing with MongoDB storage for large markdown files.

## Setup

### Install MongoDB

```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# Linux
sudo apt-get install mongodb
sudo systemctl start mongodb

# Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Process with 4 workers (default)
python -m md2db exam.md --parallel

# Custom worker count
python -m md2db exam.md --parallel --workers 8

# Custom chunk size
python -m md2db exam.md --parallel --chunk-size 20

# Custom MongoDB URI
python -m md2db exam.md --parallel --mongodb-uri "mongodb://user:pass@host:port"

# Custom database name
python -m md2db exam.md --parallel --database mydb
```

### Python API

```python
from src.md2db.parallel.coordinator import ParallelProcessor

processor = ParallelProcessor(
    file_path="exam.md",
    database_uri="mongodb://localhost:27017",
    database_name="md2db",
    num_workers=4,
    chunk_size_mb=10
)

result = processor.process()
print(f"Processed {result['questions_processed']} questions")
print(f"Using {result['num_workers']} workers across {result['chunks_processed']} chunks")
```

## Database Structure

The system uses a multi-collection structure with deduplication:

### Collections

1. **questions** - Main question data
   ```javascript
   {
     "_id": ObjectId("..."),
     "content": "What is 2+2?",
     "question_type": "multiple_choice",
     "options": [ObjectId("..."), ...],  // References to options
     "answer": "B",
     "explanation": "2+2 equals 4",
     "images": [ObjectId("..."), ...],   // References to images
     "latex_formulas": [ObjectId("..."), ...],  // References to latex
     "created_at": ISODate("...")
   }
   ```

2. **options** - Deduplicated options
   ```javascript
   {
     "_id": ObjectId("..."),
     "label": "A",
     "content": "3",
     "hash": "sha256:..."  // For deduplication
   }
   ```

3. **images** - Deduplicated image references
   ```javascript
   {
     "_id": ObjectId("..."),
     "url": "http://example.com/image.png",
     "alt": "diagram",
     "hash": "sha256:..."  // For deduplication
   }
   ```

4. **latex_formulas** - Deduplicated LaTeX formulas
   ```javascript
   {
     "_id": ObjectId("..."),
     "formula": "\\frac{a}{b}",
     "hash": "sha256:..."  // For deduplication
   }
   ```

### Indexes

Indexes are automatically created on first run:
- `questions.question_type` - For filtering by question type
- `questions.created_at` - For sorting by creation time
- `options.hash` - Unique index for deduplication
- `images.hash` - Unique index for deduplication
- `latex_formulas.hash` - Unique index for deduplication

## Performance

For large files (50-200 MB):

- **Worker count**: Use 4-8 workers for optimal performance
- **Chunk size**: Adjust based on question density (default: 10MB)
- **Memory usage**: Approximately 100-200MB per worker
- **Processing speed**: ~1000-5000 questions/second (depending on complexity)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Process                             │
│  - Reads file and divides into chunks                       │
│  - Adjusts chunk boundaries to question separators          │
│  - Dispatches chunks to worker processes                    │
│  - Coordinates MongoDB batch writes                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Worker 1    │      │  Worker 2    │      │  Worker N    │
│  Parse chunk │      │  Parse chunk │      │  Parse chunk │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  MongoDB Batch   │
                    │  Write + Dedup   │
                    └──────────────────┘
```

## Examples

### Basic Usage

```bash
# Process a small file
python -m md2db small_exam.md --parallel

# Process a large file with more workers
python -m md2db large_exam.md --parallel --workers 8 --chunk-size 20
```

### With Docker

```bash
# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Process file
python -m md2db exam.md --parallel --mongodb-uri "mongodb://localhost:27017"
```

## Troubleshooting

### MongoDB Connection Issues

If you see `ServerSelectionTimeoutError`:
1. Ensure MongoDB is running: `brew services list` (macOS) or `systemctl status mongodb` (Linux)
2. Check the connection URI: `mongodb://localhost:27017`
3. Verify MongoDB is listening on port 27017

### Memory Issues

For very large files:
- Reduce `--workers` count
- Reduce `--chunk-size`
- Increase system swap space

### Performance Tips

1. **Use local MongoDB**: Network latency affects performance
2. **Tune chunk size**: Smaller chunks = better parallelism but more overhead
3. **Monitor memory**: Each worker uses memory for parsing
4. **Index optimization**: Ensure indexes are created before bulk inserts
