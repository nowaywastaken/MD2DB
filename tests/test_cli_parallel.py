import pytest
import tempfile
import os
from src.md2db.main import process_file_parallel


def test_process_file_parallel_basic():
    """Test parallel file processing via CLI (requires MongoDB)."""
    # Create a test file
    content = """1. Question 1?
A. Option A
B. Option B

2. Question 2?
A. Option C
B. Option D
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        # This test requires MongoDB to be running
        # If MongoDB is not available, the test will fail gracefully
        result = process_file_parallel(
            temp_path,
            database_uri="mongodb://localhost:27017",
            database_name="md2db_test",
            num_workers=2,
            chunk_size_mb=0.001
        )

        assert "questions_processed" in result
        assert "chunks_processed" in result
        assert "num_workers" in result

    finally:
        os.unlink(temp_path)


def test_process_file_parallel_parameters():
    """Test that parallel function accepts all parameters."""
    # This is a smoke test to verify the function signature
    content = "1. Question?"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        # Just verify the function can be called with all parameters
        # (actual MongoDB connection may fail if MongoDB is not running)
        from unittest.mock import patch, MagicMock

        with patch('src.md2db.main.ParallelProcessor') as mock_processor:
            mock_instance = MagicMock()
            mock_instance.process.return_value = {
                "questions_processed": 1,
                "chunks_processed": 1,
                "num_workers": 4
            }
            mock_processor.return_value = mock_instance

            result = process_file_parallel(
                temp_path,
                database_uri="mongodb://custom:27017",
                database_name="custom_db",
                num_workers=8,
                chunk_size_mb=20
            )

            # Verify ParallelProcessor was called with correct parameters
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["file_path"] == temp_path
            assert call_kwargs["database_uri"] == "mongodb://custom:27017"
            assert call_kwargs["database_name"] == "custom_db"
            assert call_kwargs["num_workers"] == 8
            assert call_kwargs["chunk_size_mb"] == 20

            assert result["questions_processed"] == 1

    finally:
        os.unlink(temp_path)
