#!/usr/bin/env python3
"""
Performance benchmark script for comparing Python and Rust implementations of MD2DB.

This script tests parsing performance with various file sizes and complexity levels.
"""

import time
import sys
import os
import statistics
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple
import tracemalloc

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from md2db.parser import parse_markdown


def generate_test_questions(count: int) -> str:
    """Generate test markdown content with specified number of questions."""
    questions = []
    for i in range(count):
        q_type = i % 4
        if q_type == 0:
            # Multiple Choice
            questions.append(f"""
{i+1}. What is {i} + {i}?

A. {i}
B. {i*2}
C. {i*3}
D. {i*4}

Answer: B
""")
        elif q_type == 1:
            # True/False
            questions.append(f"""
{i+1}. The value of {i} + {i} equals {i*2}.

True
""")
        elif q_type == 2:
            # Fill in the blank
            questions.append(f"""
{i+1}. The capital of country {i} is _____.

Answer: Capital {i}
""")
        else:
            # Subjective with LaTeX
            questions.append(f"""
{i+1}. Explain the mathematical formula: $x^2 + y^2 = z^2$

Answer: This is the Pythagorean theorem.
""")
    return "\n".join(questions)


def create_test_zip(content: str, num_images: int = 5) -> bytes:
    """Create a test ZIP file with markdown and images."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        with zipfile.ZipFile(f.name, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('exam.md', content)
            for i in range(num_images):
                # Create dummy image data
                zf.writestr(f'image{i}.png', b'fake image data ' * 100)
        with open(f.name, 'rb') as rf:
            return rf.read()


def benchmark_python_parsing(content: str, iterations: int = 10) -> dict:
    """Benchmark Python parsing performance."""
    print(f"\n{'='*60}")
    print("Python Performance Test")
    print(f"{'='*60}")

    times = []
    memory_usage = []

    for i in range(iterations):
        tracemalloc.start()
        start = time.perf_counter()

        questions = parse_markdown(content)

        elapsed = time.perf_counter() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        times.append(elapsed)
        memory_usage.append(peak / 1024 / 1024)  # Convert to MB

        if i == 0:
            print(f"  Parsed {len(questions)} questions")

    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0
    avg_memory = statistics.mean(memory_usage)

    return {
        'avg_time': avg_time,
        'std_time': std_time,
        'avg_memory_mb': avg_memory,
        'questions_per_second': len(parse_markdown(content)) / avg_time,
        'question_count': len(parse_markdown(content))
    }


def benchmark_rust_parsing(content: str, iterations: int = 10) -> dict:
    """Benchmark Rust parsing performance by calling the compiled binary."""
    print(f"\n{'='*60}")
    print("Rust Performance Test")
    print(f"{'='*60}")

    # Create temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name

    try:
        times = []
        for i in range(iterations):
            start = time.perf_counter()

            result = subprocess.run(
                ['./target/release/md2db', 'parse', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            elapsed = time.perf_counter() - start
            times.append(elapsed)

            if result.returncode != 0:
                print(f"  Warning: Rust binary returned error: {result.stderr}")
                # Try debug binary if release doesn't exist
                if i == 0:
                    result = subprocess.run(
                        ['./target/debug/md2db', 'parse', temp_file],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode != 0:
                        print("  Rust benchmark failed - binary may need to be compiled")
                        return None

        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0

        # Try to get question count from output
        question_count = 100  # Default assumption
        try:
            import json
            output = json.loads(result.stdout)
            question_count = len(output)
        except:
            pass

        return {
            'avg_time': avg_time,
            'std_time': std_time,
            'questions_per_second': question_count / avg_time,
            'question_count': question_count
        }
    except FileNotFoundError:
        print("  Rust binary not found. Run 'cargo build --release' first.")
        return None
    except subprocess.TimeoutExpired:
        print("  Rust benchmark timed out.")
        return None
    finally:
        os.unlink(temp_file)


def run_comprehensive_benchmark():
    """Run comprehensive benchmark across different file sizes."""
    print("\n" + "="*80)
    print("MD2DB Performance Comparison: Python vs Rust")
    print("="*80)

    # System information
    print("\nSystem Information:")
    print(f"  CPU Cores: {os.cpu_count()}")
    print(f"  Python Version: {sys.version}")

    try:
        rust_version = subprocess.run(['rustc', '--version'], capture_output=True, text=True)
        if rust_version.returncode == 0:
            print(f"  Rust Version: {rust_version.stdout.strip()}")
        else:
            print("  Rust Version: Not installed")
    except FileNotFoundError:
        print("  Rust Version: Not installed")

    test_sizes = [10, 50, 100, 500, 1000]
    results = []

    for size in test_sizes:
        print(f"\n{'='*80}")
        print(f"Testing with {size} questions")
        print(f"{'='*80}")

        content = generate_test_questions(size)

        # Benchmark Python
        python_result = benchmark_python_parsing(content, iterations=10)
        results.append(('Python', size, python_result))

        # Benchmark Rust (if available)
        rust_result = benchmark_rust_parsing(content, iterations=10)
        if rust_result:
            results.append(('Rust', size, rust_result))

            # Calculate speedup
            speedup = python_result['avg_time'] / rust_result['avg_time']
            memory_diff = python_result['avg_memory_mb']  # Rust memory not measured yet

            print(f"\n  Performance Comparison ({size} questions):")
            print(f"    Rust is {speedup:.2f}x faster than Python")
            print(f"    Python memory: {memory_diff:.2f} MB")

    # Print summary table
    print("\n" + "="*80)
    print("Performance Summary")
    print("="*80)
    print(f"{'Implementation':<15} {'Questions':<12} {'Avg Time (s)':<15} {'Q/s':<12} {'Memory (MB)':<12}")
    print("-"*80)

    for impl, size, result in results:
        if result:
            memory = result.get('avg_memory_mb', 'N/A')
            if memory != 'N/A':
                memory = f"{memory:.2f}"
            print(f"{impl:<15} {size:<12} {result['avg_time']:<15.4f} {result['questions_per_second']:<12.2f} {memory:<12}")

    # Calculate overall speedup
    print("\n" + "="*80)
    print("Overall Performance Analysis")
    print("="*80)

    python_results = [r for i, s, r in results if i == 'Python' and r]
    rust_results = [r for i, s, r in results if i == 'Rust' and r]

    if python_results and rust_results:
        avg_python_time = statistics.mean([r['avg_time'] for r in python_results])
        avg_rust_time = statistics.mean([r['avg_time'] for r in rust_results])
        overall_speedup = avg_python_time / avg_rust_time

        print(f"  Average Speedup: {overall_speedup:.2f}x")
        print(f"  Python Average Time: {avg_python_time:.4f}s")
        print(f"  Rust Average Time: {avg_rust_time:.4f}s")

        # Performance recommendations
        print("\nPerformance Recommendations:")
        if overall_speedup > 2:
            print("  ✓ Rust shows significant performance advantage")
            print("  → Recommended for production use with large datasets")
        elif overall_speedup > 1.5:
            print("  ✓ Rust shows moderate performance advantage")
            print("  → Consider Rust for performance-critical applications")
        else:
            print("  → Performance difference is minimal")
            print("  → Choose based on other factors (memory, ecosystem, etc.)")

    return results


if __name__ == '__main__':
    results = run_comprehensive_benchmark()
