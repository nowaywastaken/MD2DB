import re
from typing import List

def extract_images(content: str) -> List[str]:
    """Extract image URLs from markdown content."""
    # Match markdown image syntax: ![alt](url)
    pattern = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(pattern, content)
    return matches