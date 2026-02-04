#!/usr/bin/env python3
"""
Test script to verify LaTeX formula extraction functionality
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from md2db.parser import parse_markdown
from md2db.image_processor import extract_latex_formulas

def test_latex_extraction():
    """Test LaTeX formula extraction functionality"""

    print("Testing LaTeX formula extraction...\n")

    # Test case 1: Inline LaTeX
    print("1. Testing inline LaTeX ($...$)")
    content1 = "Solve the equation: $x^2 + y^2 = z^2$"
    formulas1 = extract_latex_formulas(content1)
    print(f"   Input: {content1}")
    print(f"   Extracted formulas: {formulas1}")
    print()

    # Test case 2: Display LaTeX ($$...$$)
    print("2. Testing display LaTeX ($$...$$)")
    content2 = "Integral formula: $$\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$"
    formulas2 = extract_latex_formulas(content2)
    print(f"   Input: {content2}")
    print(f"   Extracted formulas: {formulas2}")
    print()

    # Test case 3: Mixed LaTeX formulas
    print("3. Testing multiple LaTeX formulas")
    content3 = "Derivative: $\\frac{dy}{dx}$ and integral: $$\\int f(x) dx$$"
    formulas3 = extract_latex_formulas(content3)
    print(f"   Input: {content3}")
    print(f"   Extracted formulas: {formulas3}")
    print()

    # Test case 4: Parse markdown with LaTeX
    print("4. Testing parse_markdown with LaTeX")
    markdown_content = """
1. Solve the equation: $x^2 + y^2 = z^2$
2. Calculate the integral: $$\\int_{0}^{1} x^2 dx$$
3. Find the derivative: $\\frac{d}{dx} e^x$
    """
    questions = parse_markdown(markdown_content)
    print(f"   Number of questions: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"   Question {i}: {q.content[:50]}...")
        if q.latex_formulas:
            print(f"     LaTeX formulas: {q.latex_formulas}")
        else:
            print(f"     No LaTeX formulas found")
    print()

    # Test case 5: Complex LaTeX with newlines
    print("5. Testing complex LaTeX with newlines")
    content5 = """Matrix equation:
$$\nX = \\begin{pmatrix}\na & b \\\nc & d\n\\end{pmatrix}$$"""
    formulas5 = extract_latex_formulas(content5)
    print(f"   Input: {content5}")
    print(f"   Extracted formulas: {formulas5}")
    print()

if __name__ == "__main__":
    test_latex_extraction()
    print("All tests completed successfully!")