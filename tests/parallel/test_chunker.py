import pytest
import tempfile
import os
from src.md2db.parallel.chunker import FileChunker, QUESTION_SEPARATORS


def test_question_separators_pattern():
    """Verify that question separator patterns are defined."""
    assert len(QUESTION_SEPARATORS) == 3
    assert r'^\d+\.\s+' in QUESTION_SEPARATORS
    assert r'^\s*---\s*$' in QUESTION_SEPARATORS


def test_file_chunker_creates_chunks():
    """Test that chunker divides file into chunks."""
    # Create a test file with multiple questions
    content = """1. First question
Some content here.

2. Second question
More content.

3. Third question
Even more content.
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        chunker = FileChunker(temp_path, chunk_size_mb=0.001)  # Very small chunks
        chunks = chunker.create_chunks()

        # Should create at least 1 chunk
        assert len(chunks) >= 1

        # Verify chunks are in order
        for i in range(len(chunks) - 1):
            assert chunks[i][0] < chunks[i][1]
            assert chunks[i][1] <= chunks[i + 1][0]

    finally:
        os.unlink(temp_path)


def test_file_chunker_single_chunk_for_small_file():
    """Test that small files get single chunk."""
    content = "Small content"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        chunker = FileChunker(temp_path, chunk_size_mb=10)
        chunks = chunker.create_chunks()

        # Should create exactly 1 chunk for small file
        assert len(chunks) == 1
        assert chunks[0] == (0, len(content))

    finally:
        os.unlink(temp_path)
