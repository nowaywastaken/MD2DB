import argparse
from .parser import parse_markdown
from .database import export_to_sql
from .parallel.coordinator import ParallelProcessor


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


def process_file_parallel(
    filename: str,
    database_uri: str = "mongodb://localhost:27017",
    database_name: str = "md2db",
    num_workers: int = 4,
    chunk_size_mb: float = 10
) -> dict:
    """Process a markdown file with parallel workers and store in MongoDB.

    Args:
        filename: Path to markdown file
        database_uri: MongoDB connection URI
        database_name: Database name
        num_workers: Number of parallel workers
        chunk_size_mb: Chunk size in MB

    Returns:
        Dict with processing statistics
    """
    processor = ParallelProcessor(
        file_path=filename,
        database_uri=database_uri,
        database_name=database_name,
        num_workers=num_workers,
        chunk_size_mb=chunk_size_mb
    )

    return processor.process()


def main():
    parser = argparse.ArgumentParser(description="MD2DB - Markdown to Database Converter")
    parser.add_argument("file", help="Markdown file to process")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--parallel", "-p", action="store_true", help="Use parallel processing with MongoDB")
    parser.add_argument("--mongodb-uri", default="mongodb://localhost:27017", help="MongoDB connection URI")
    parser.add_argument("--database", "-d", default="md2db", help="Database name")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--chunk-size", type=float, default=10, help="Chunk size in MB")

    args = parser.parse_args()

    if args.parallel:
        # Parallel mode with MongoDB
        result = process_file_parallel(
            args.file,
            database_uri=args.mongodb_uri,
            database_name=args.database,
            num_workers=args.workers,
            chunk_size_mb=args.chunk_size
        )
        print(f"Processed {result['questions_processed']} questions")
        print(f"Using {result['num_workers']} workers across {result['chunks_processed']} chunks")
    else:
        # Original mode
        result = process_file(args.file)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["sql"])
            print(f"Output written to {args.output}")
        else:
            print(result["sql"])