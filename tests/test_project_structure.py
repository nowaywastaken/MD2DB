import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_md2db_module_exists():
    """Test that md2db module can be imported."""
    import md2db
    assert hasattr(md2db, '__version__')

def test_main_function_exists():
    """Test that main function exists."""
    from md2db.main import main
    assert callable(main)