# MD2DB Rust API Server

## Summary

This document describes the complete API server implementation for the MD2DB Rust project.

## Implemented Endpoints

### 1. `GET /`
Root endpoint returning API information.

**Response:**
```json
{
  "name": "MD2DB API",
  "version": "0.1.0",
  "description": "Markdown to Database converter - High performance Rust implementation",
  "endpoints": {
    "POST /parse": "Parse a single markdown text",
    "POST /parse-zip": "Parse a ZIP file containing markdown files",
    "GET /health": "Health check endpoint"
  }
}
```

### 2. `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### 3. `POST /parse`
Parse a single markdown text and return parsed questions.

**Request:**
```json
{
  "markdown": "# What is 2+2?\n\n* A. 3\n* B. 4\n* C. 5\n"
}
```

**Response:**
```json
{
  "count": 1,
  "question_ids": ["uuid-here"],
  "questions": [...],
  "warnings": []
}
```

### 4. `POST /parse-zip`
Parse a ZIP file containing multiple markdown files.

**Request:** Multipart form data with a `file` field containing a `.zip` file.

**Response:**
```json
{
  "count": 5,
  "question_ids": ["uuid1", "uuid2", ...],
  "questions": [...],
  "images_processed": 3,
  "warnings": []
}
```

## Error Handling

All errors follow this format:
```json
{
  "error": "error_type",
  "message": "Detailed error message"
}
```

Error types:
- `parse_error`: Markdown parsing failed (400)
- `database_error`: Database operation failed (500)
- `invalid_file`: File validation failed (400)
- `multipart_error`: Multipart form processing failed (400)

## Server Configuration

The server can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | TCP port to listen on |
| `HOST` | `0.0.0.0` | Host address to bind to |

## How to Start the Server

### Development Mode

```bash
# Run with default settings (port 8080)
cargo run

# Run with custom port
PORT=3000 cargo run

# Run with custom host and port
HOST=127.0.0.1 PORT=9000 cargo run
```

### Production Build

```bash
# Build optimized binary
cargo build --release

# Run the binary
./target/release/md2db
```

## How to Test the Endpoints

### Using curl

#### 1. Health Check
```bash
curl http://localhost:8080/health
```

#### 2. Parse Markdown
```bash
curl -X POST http://localhost:8080/parse \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# What is 2+2?\n\n* A. 3\n* B. 4\n* C. 5\n"}'
```

#### 3. Parse ZIP File
```bash
# Create test ZIP file
echo "# Question 1

* A. Option 1
* B. Option 2" > q1.md

echo "# Question 2

* C. Option 3
* D. Option 4" > q2.md

zip test.zip q1.md q2.md

# Upload ZIP file
curl -X POST http://localhost:8080/parse-zip \
  -F "file=@test.zip"
```

### Using the Test Script

A test script is provided at `test_api.sh`:

```bash
# Make sure the server is running first
cargo run &

# Run the test script
./test_api.sh
```

### Using Integration Tests

```bash
# Run all integration tests
cargo test --test api_integration_test

# Run a specific test
cargo test --test api_integration_test test_health_endpoint

# Run with output
cargo test --test api_integration_test -- --nocapture
```

## Integration Tests

The integration tests are located in `tests/api_integration_test.rs` and cover:

- `test_root_endpoint` - Tests API information endpoint
- `test_health_endpoint` - Tests health check
- `test_parse_endpoint_simple_question` - Tests parsing a single question
- `test_parse_endpoint_multiple_questions` - Tests parsing multiple questions
- `test_parse_endpoint_invalid_json` - Tests error handling for invalid JSON
- `test_parse_endpoint_empty_markdown` - Tests empty markdown handling
- `test_parse_zip_endpoint_without_file` - Tests ZIP endpoint error handling
- `test_404_on_nonexistent_endpoint` - Tests 404 responses
- `test_parse_endpoint_with_latex` - Tests LaTeX formula parsing
- `test_error_response_format` - Tests error response structure

## File Structure

```
src/
├── lib.rs          # Library entry point
├── main.rs         # Server startup and configuration
├── api.rs          # API endpoints and handlers
├── models.rs       # Data models (Question, QuestionType, etc.)
├── parser.rs       # Markdown parser
├── database.rs     # Repository trait and implementations
├── zip.rs          # ZIP file processor
├── processor.rs    # Batch processing with parallelism
├── media.rs        # Image processing
└── classifier.rs   # Question type classification

tests/
└── api_integration_test.rs  # API integration tests
```

## Database Integration

The server uses a repository pattern. By default, it uses `MockRepository` for in-memory storage. To use a real database:

### PostgreSQL

```rust
let repository: Arc<dyn QuestionRepository> = Arc::new(
    PostgresRepository::new("postgresql://user:pass@localhost/db").await?
);
```

### MongoDB

```rust
let repository: Arc<dyn QuestionRepository> = Arc::new(
    MongoRepository::new("mongodb://localhost:27017/md2db").await?
);
```

## Dependencies

Key dependencies from `Cargo.toml`:
- `axum 0.7` - Web framework
- `tokio 1.35` - Async runtime
- `tower-http 0.5` - HTTP middleware (compression, tracing)
- `pulldown-cmark 0.11` - Markdown parsing
- `zip 2.1` - ZIP file processing
- `serde 1.0` - Serialization
- `uuid 1.6` - Unique identifiers
- `tracing 0.1` - Logging
