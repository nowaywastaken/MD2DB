import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_version():
    """Test that version is accessible."""
    from md2db import __version__
    assert __version__ == "0.1.0"

def test_main_output(capsys):
    """Test that main function prints expected output."""
    from md2db.main import process_file

    # Create a test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Test question")
        temp_filename = f.name

    try:
        result = process_file(temp_filename)
        assert "questions" in result
        assert "sql" in result
    finally:
        import os
        os.unlink(temp_filename)