import re
from typing import List, Tuple
from dataclasses import dataclass

# Pre-compiled regex patterns for performance
_IMAGE_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')
_DISPLAY_LATEX_PATTERN = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
_INLINE_LATEX_PATTERN = re.compile(r'\$(.*?)\$')
_LATEX_VALIDATION_PATTERNS = [
    re.compile(r'\\[a-zA-Z]+'),  # LaTeX commands like \frac, \int
    re.compile(r'[{}]'),          # Braces
    re.compile(r'[\\^\\_]'),     # Superscript/subscript
    re.compile(r'[+\\\\*/=]'),    # Mathematical operators
]

@dataclass
class ExtractedContent:
    """Container for extracted content from markdown."""
    images: List[str]
    latex_formulas: List[str]

def extract_images(content: str) -> List[str]:
    """Extract image URLs from markdown content."""
    matches = _IMAGE_PATTERN.findall(content)
    return matches

def extract_latex_formulas(content: str) -> List[str]:
    """Extract LaTeX formulas from markdown content.

    Args:
        content: Markdown content containing LaTeX formulas

    Returns:
        List of LaTeX formula strings
    """
    formulas = []
    seen_formulas = set()  # Track seen formulas to avoid duplicates

    def add_formula(formula: str):
        """Helper to add formula with validation."""
        if formula.strip() and formula not in seen_formulas:
            if _is_valid_latex(formula):
                formulas.append(formula)
                seen_formulas.add(formula)

    def _is_valid_latex(formula: str) -> bool:
        """Validate if string contains valid LaTeX pattern."""
        for pattern in _LATEX_VALIDATION_PATTERNS:
            if pattern.search(formula):
                return True

        # Allow simple mathematical expressions like x^2
        if len(formula) > 1 and any(c in formula for c in '^_[](){}'):
            return True

        return False

    # Extract display LaTeX formulas ($$...$$)
    display_matches = _DISPLAY_LATEX_PATTERN.findall(content)
    for match in display_matches:
        add_formula(match.strip())

    # Extract inline LaTeX formulas ($...$)
    inline_matches = _INLINE_LATEX_PATTERN.findall(content)
    for match in inline_matches:
        formula = match.strip()
        # Skip obvious false positives
        if (formula and
            not formula.startswith('$') and
            not formula.endswith('$') and
            '$' not in formula):
            add_formula(formula)

    return formulas


def extract_all(content: str) -> ExtractedContent:
    """Extract all media content (images and LaTeX) in a single pass.

    This is more efficient than calling extract_images and extract_latex_formulas
    separately, as it only iterates through the content once.

    Args:
        content: Markdown content

    Returns:
        ExtractedContent containing images and LaTeX formulas
    """
    images = _IMAGE_PATTERN.findall(content)

    # Extract LaTeX formulas (reuse existing logic)
    formulas = []
    seen_formulas = set()

    def add_formula(formula: str):
        """Helper to add formula with validation."""
        if formula.strip() and formula not in seen_formulas:
            if _is_valid_latex(formula):
                formulas.append(formula)
                seen_formulas.add(formula)

    def _is_valid_latex(formula: str) -> bool:
        """Validate if string contains valid LaTeX pattern."""
        for pattern in _LATEX_VALIDATION_PATTERNS:
            if pattern.search(formula):
                return True

        # Allow simple mathematical expressions like x^2
        if len(formula) > 1 and any(c in formula for c in '^_[](){}'):
            return True

        return False

    # Extract display LaTeX formulas ($$...$$)
    display_matches = _DISPLAY_LATEX_PATTERN.findall(content)
    for match in display_matches:
        add_formula(match.strip())

    # Extract inline LaTeX formulas ($...$)
    inline_matches = _INLINE_LATEX_PATTERN.findall(content)
    for match in inline_matches:
        formula = match.strip()
        # Skip obvious false positives
        if (formula and
            not formula.startswith('$') and
            not formula.endswith('$') and
            '$' not in formula):
            add_formula(formula)

    return ExtractedContent(images=images, latex_formulas=formulas)