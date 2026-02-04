#!/usr/bin/env python3
"""Demo script to showcase MD2DB functionality."""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from md2db.parser import parse_markdown

def main():
    print("=== MD2DB Demo ===\n")

    # Demo 1: Simple question
    print("1. Simple subjective question:")
    markdown1 = "What is the capital of France?"
    questions1 = parse_markdown(markdown1)
    for q in questions1:
        print(f"   Content: {q.content}")
        print(f"   Type: {q.question_type}")
    print()

    # Demo 2: Multiple choice question
    print("2. Multiple choice question:")
    markdown2 = """What is 2+2?
A. 3
B. 4
C. 5
D. 6"""
    questions2 = parse_markdown(markdown2)
    for q in questions2:
        print(f"   Content: {q.content}")
        print(f"   Type: {q.question_type}")
        print(f"   Options: {q.options}")
    print()

    # Demo 3: True/False question
    print("3. True/False question:")
    markdown3 = "Paris is the capital of France. True or False?"
    questions3 = parse_markdown(markdown3)
    for q in questions3:
        print(f"   Content: {q.content}")
        print(f"   Type: {q.question_type}")
    print()

    # Demo 4: Fill in the blank
    print("4. Fill in the blank:")
    markdown4 = "The capital of Germany is _____."
    questions4 = parse_markdown(markdown4)
    for q in questions4:
        print(f"   Content: {q.content}")
        print(f"   Type: {q.question_type}")
    print()

    # Demo 5: Question with images
    print("5. Question with images:")
    markdown5 = """What is the area of this shape?
![shape](http://example.com/shape.png)
A. 10 cm²
B. 15 cm²
C. 20 cm²"""
    questions5 = parse_markdown(markdown5)
    for q in questions5:
        print(f"   Content: {q.content}")
        print(f"   Type: {q.question_type}")
        print(f"   Options: {q.options}")
        print(f"   Images: {q.images}")

if __name__ == "__main__":
    main()