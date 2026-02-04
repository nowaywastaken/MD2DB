import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_parse_question_with_images():
    """Test parsing question with images."""
    from md2db.parser import parse_markdown

    markdown = "Question with image ![alt](http://example.com/image.png)"
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert questions[0].images == ["http://example.com/image.png"]

def test_parse_question_with_multiple_images():
    """Test parsing question with multiple images."""
    from md2db.parser import parse_markdown

    markdown = """Question with images:
![first](http://example.com/image1.png)
![second](http://example.com/image2.png)"""
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert len(questions[0].images) == 2
    assert "http://example.com/image1.png" in questions[0].images
    assert "http://example.com/image2.png" in questions[0].images

def test_parse_question_content_without_images():
    """Test that image tags are removed from content."""
    from md2db.parser import parse_markdown

    markdown = "What is 2+2? ![diagram](image.png)"
    questions = parse_markdown(markdown)
    assert len(questions) == 1
    assert "![diagram](image.png)" not in questions[0].content
    assert questions[0].content == "What is 2+2?"
    assert questions[0].images == ["image.png"]