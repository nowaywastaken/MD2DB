import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_parse_multiple_choice_options():
    """Test parsing options from multiple choice questions."""
    from md2db.parser import parse_options

    content = "What is 2+2?\nA. 3\nB. 4\nC. 5\nD. 6"
    options = parse_options(content)
    assert options == ["3", "4", "5", "6"]

def test_parse_options_with_spaces():
    """Test parsing options with extra spaces."""
    from md2db.parser import parse_options

    content = "Question?\nA.   Option 1  \nB. Option 2"
    options = parse_options(content)
    assert options == ["Option 1", "Option 2"]