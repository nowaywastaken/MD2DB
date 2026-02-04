import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_extract_image_urls():
    """Test extracting image URLs from markdown."""
    from md2db.image_processor import extract_images

    content = "Question with image ![alt](http://example.com/image.png)"
    images = extract_images(content)
    assert len(images) == 1
    assert images[0] == "http://example.com/image.png"

def test_extract_multiple_images():
    """Test extracting multiple image URLs."""
    from md2db.image_processor import extract_images

    content = """Question with images:
![first](http://example.com/image1.png)
![second](http://example.com/image2.png)"""
    images = extract_images(content)
    assert len(images) == 2
    assert "http://example.com/image1.png" in images
    assert "http://example.com/image2.png" in images

def test_extract_local_images():
    """Test extracting local image paths."""
    from md2db.image_processor import extract_images

    content = "Question with local image ![diagram](./images/diagram.png)"
    images = extract_images(content)
    assert len(images) == 1
    assert images[0] == "./images/diagram.png"