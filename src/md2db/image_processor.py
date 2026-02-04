import re
from typing import List

def extract_images(content: str) -> List[str]:
    """Extract image URLs from markdown content."""
    # Match markdown image syntax: ![alt](url)
    pattern = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(pattern, content)
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
            # Additional validation: ensure it's a valid LaTeX formula
            if is_valid_latex(formula):
                formulas.append(formula)
                seen_formulas.add(formula)

    def is_valid_latex(formula: str) -> bool:
        """Validate if string contains valid LaTeX pattern."""
        # Check if it looks like a mathematical expression
        # Should contain at least one LaTeX command or mathematical symbol
        latex_patterns = [
            r'\\[a-zA-Z]+',  # LaTeX commands like \frac, \int
            r'[{}]',          # Braces
            r'[\\^\\_]',    # Superscript/subscript
            r'[+\\\\*/=]',     # Mathematical operators (removed hyphen)
        ]

        # Also check for common LaTeX structures
        common_patterns = [
            r'\\begin\{', r'\\end\{', r'\\\[', r'\\\]'
        ]

        for pattern in latex_patterns + common_patterns:
            if re.search(pattern, formula):
                return True

        # If it's just text, it's probably not a LaTeX formula
        # Allow simple mathematical expressions like x^2
        if len(formula) > 1 and any(c in formula for c in '^_[](){}'):
            return True

        return False

    # First extract display LaTeX formulas ($$...$$)
    display_pattern = r'\$\$(.*?)\$\$'
    display_matches = re.findall(display_pattern, content, re.DOTALL)
    for match in display_matches:
        add_formula(match.strip())

    # Extract inline LaTeX formulas ($...$)
    # Use a simpler approach that handles most cases
    inline_pattern = r'\$(.*?)\$'
    inline_matches = re.findall(inline_pattern, content)
    for match in inline_matches:
        formula = match.strip()
        # Skip obvious false positives
        if (formula and
            not formula.startswith('$') and
            not formula.endswith('$') and
            '$' not in formula):
            add_formula(formula)

    return formulas