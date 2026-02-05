# MD2DB

A high-performance converter that transforms Markdown exam/quiz bank formats into structured database records. Written in Rust for speed and efficiency.

## Features

- **Parse Markdown exam questions** - Extract questions from various Markdown formats
- **Multiple question types** - Support for single choice, multiple choice, true/false, fill-in-blank, and subjective questions
- **Advanced classification** - Multi-level classifier with structural, semantic, and NLP analysis
- **Media processing** - Handle embedded images and LaTeX formulas
- **Database integration** - Export to PostgreSQL, MongoDB, or use the mock repository
- **RESTful API** - Upload and process files via HTTP API
- **Docker support** - Easy deployment with Docker and Docker Compose

## Architecture

This is a **high-performance Rust implementation** of MD2DB, featuring:

- **Multi-stage classification**: Structural → Semantic Rule → NLP analysis
- **Parallel processing** using Rayon for CPU-bound tasks
- **Async I/O** with Tokio for efficient network operations
- **Minimal dependencies** - No heavy ML libraries required

## Installation

### Native Installation

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build the project
cargo build --release

# Run the application
./target/release/md2db
```

### Docker Deployment (Recommended)

See [DOCKER.md](DOCKER.md) for detailed Docker deployment instructions.

**Quick start with Docker Compose:**

```bash
# Copy environment file
cp .env.example .env

# Start all services (application + PostgreSQL + optional MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f md2db

# Access API at http://localhost:8080
```

**Build for specific architecture:**

```bash
# Build for current platform
docker build -t md2db:latest .

# Build for multiple platforms (ARM64 + AMD64)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t md2db:latest .
```

## Usage

### Quick Start (Native)

1. **Build and run the application:**
   ```bash
   cargo run --release
   ```

2. **Upload and process files via API:**
   ```bash
   curl -X POST http://localhost:8080/api/upload \
     -F "file=@exam.md" \
     -F "parse_images=true" \
     -F "parse_latex=true"
   ```

3. **Query the API:**
   ```bash
   # Get all questions
   curl http://localhost:8080/api/questions

   # Get questions by type
   curl http://localhost:8080/api/questions?type=choice

   # Get specific question
   curl http://localhost:8080/api/questions/{id}
   ```

### Docker Compose

```bash
# Start with PostgreSQL
docker-compose up -d

# Start with admin tools (pgAdmin, Mongo Express)
docker-compose --profile admin up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f md2db
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload and parse Markdown file |
| GET | `/api/questions` | Get all questions (with filters) |
| GET | `/api/questions/{id}` | Get specific question |
| GET | `/health` | Health check endpoint |
| GET | `/metrics` | Performance metrics |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API server port | `8080` |
| `HOST` | Bind address | `0.0.0.0` |
| `RUST_LOG` | Log level (trace/debug/info/warn/error) | `info` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `MONGODB_URI` | MongoDB connection string | - |
| `POSTGRES_ENABLED` | Enable PostgreSQL | `true` |
| `MONGODB_ENABLED` | Enable MongoDB | `false` |

See [`.env.example`](.env.example) for all available options.

## Question Classification

MD2DB uses a three-tier classification strategy:

### 1. Structural Classifier
Fast pattern matching for explicit markers:
- `[单选]`, `[多选]`, `[判断]`, `[填空]` tags
- Binary option detection (正确/错误)
- Letter-prefixed options (A., B., C., ...)

### 2. Semantic Rule Classifier
Context-based reasoning:
- Parenthesis patterns `()` for true/false or fill-in-blank
- Underscore patterns `___` for fill-in-blank
- Letter prefix detection

### 3. NLP Classifier
Keyword-based semantic analysis (new):
- **Multiple choice detection**: "以下全部正确", "select all that apply"
- **Single choice detection**: "最佳答案", "best answer"
- **True/false detection**: "判断题", "true or false"
- **Fill-in-blank detection**: "填空", "fill in the blank"
- **Confidence scoring** with adjustable thresholds

### Example Classification

```rust
use md2db::classifier::NlpClassifier;

let stem = "以下全部正确的是：";
let options = vec![
    "A. 选项1".to_string(),
    "B. 选项2".to_string(),
    "C. 选项3".to_string(),
    "D. 选项4".to_string(),
];

let result = NlpClassifier::classify(stem, &options);
// Returns: ClassificationResult {
//     qtype: MultipleChoice,
//     confidence: 0.95,
//     needs_review: false
// }
```

## Database Support

### PostgreSQL (Default)

```bash
# Using Docker Compose
docker-compose up -d postgres md2db

# Manual connection
export DATABASE_URL="postgresql://user:pass@localhost:5432/md2db"
```

### MongoDB (Optional)

For large file processing and parallel operations:

```bash
# Enable in .env
MONGODB_ENABLED=true

# Using Docker Compose
docker-compose up -d mongodb md2db
```

### Mock Repository

For testing and development (no database required):

```rust
// In main.rs
let repository: Arc<dyn database::QuestionRepository> =
    Arc::new(database::MockRepository::new());
```

## Development

### Running Tests

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_nlp_multiple_choice
```

### Benchmarking

```bash
# Run benchmarks
cargo bench

# With specific filter
cargo bench -- bench_parse
```

### Code Formatting

```bash
# Format code
cargo fmt

# Check formatting without changes
cargo fmt --check
```

### Linting

```bash
# Run Clippy linter
cargo clippy

# Fix warnings automatically
cargo clippy --fix
```

## Performance

The Rust implementation offers significant performance improvements:

| Feature | Python | Rust |
|---------|--------|------|
| Startup time | ~2s | <100ms |
| Memory usage | ~150MB | ~10MB |
| File parsing | 1x | 10-50x faster |
| Concurrent requests | Limited | Highly scalable |

## Docker Deployment

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd md2db

# 2. Create environment file
cp .env.example .env

# 3. Start services
docker-compose up -d

# 4. Access API
curl http://localhost:8080/health
```

### Multi-Architecture Support

The Dockerfile supports both ARM64 and AMD64 platforms:

```bash
# Build for both platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t md2db:latest \
  --push .
```

### Admin Tools

Enable database management UIs:

```bash
# Start with pgAdmin and Mongo Express
docker-compose --profile admin up -d

# Access pgAdmin at http://localhost:5050
# Access Mongo Express at http://localhost:8081
```

For detailed Docker deployment instructions, see [DOCKER.md](DOCKER.md).

## Python Legacy

The Python implementation is available for reference and comparison:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Python version
python -m md2db your_exam.md
```

See [docs/MONGODB.md](docs/MONGODB.md) for Python-specific MongoDB integration details.

## Documentation

- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [API_TESTING.md](API_TESTING.md) - API testing guide
- [SQL_INJECTION_PROTECTION_README.md](SQL_INJECTION_PROTECTION_README.md) - Security documentation
- [PROGRESS.md](PROGRESS.md) - Development progress

## Contributing

Contributions are welcome! Please ensure:

1. Code passes `cargo clippy` and `cargo fmt`
2. Tests pass with `cargo test`
3. Documentation is updated
4. Commit messages follow conventional commits

## License

[Your License Here]

## Support

For issues, questions, or contributions, please open an issue on GitHub.
