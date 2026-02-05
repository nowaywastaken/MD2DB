#!/usr/bin/env python3
"""
Performance analysis and profiling for MD2DB Python implementation.

This script provides detailed performance metrics including:
- Parsing time analysis
- Memory usage profiling
- CPU utilization
- Bottleneck identification
"""

import sys
import time
import statistics
import tracemalloc
import cProfile
import pstats
import io
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from md2db.parser import parse_markdown


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    total_questions: int
    avg_time_ms: float
    std_time_ms: float
    min_time_ms: float
    max_time_ms: float
    questions_per_second: float
    peak_memory_mb: float
    avg_memory_mb: float


def generate_test_questions(count: int, complexity: str = 'mixed') -> str:
    """Generate test markdown with specified number of questions.

    Args:
        count: Number of questions to generate
        complexity: 'simple', 'medium', 'complex', or 'mixed'

    Returns:
        Markdown content string
    """
    questions = []

    for i in range(count):
        if complexity == 'mixed':
            q_type = i % 4
        else:
            q_type = {'simple': 0, 'medium': 1, 'complex': 2}.get(complexity, 0)

        if q_type == 0:
            # Simple multiple choice
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
            # Complex with LaTeX and images
            questions.append(f"""
{i+1}. Explain the mathematical formula: $x^2 + y^2 = z^2$

![Diagram](http://example.com/diag{i}.png)

Also consider: `\\int_0^1 x^2 dx`

Answer: This is the Pythagorean theorem.
""")

    return "\n".join(questions)


def benchmark_parsing(content: str, iterations: int = 10) -> PerformanceMetrics:
    """Benchmark parsing performance with memory tracking.

    Args:
        content: Markdown content to parse
        iterations: Number of times to run the benchmark

    Returns:
        PerformanceMetrics object with detailed metrics
    """
    times = []
    memory_peaks = []

    for _ in range(iterations):
        tracemalloc.start()
        start = time.perf_counter()

        questions = parse_markdown(content)

        elapsed = time.perf_counter() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        times.append(elapsed * 1000)  # Convert to ms
        memory_peaks.append(peak / 1024 / 1024)  # Convert to MB

    return PerformanceMetrics(
        total_questions=len(questions),
        avg_time_ms=statistics.mean(times),
        std_time_ms=statistics.stdev(times) if len(times) > 1 else 0,
        min_time_ms=min(times),
        max_time_ms=max(times),
        questions_per_second=len(questions) / (statistics.mean(times) / 1000),
        peak_memory_mb=max(memory_peaks),
        avg_memory_mb=statistics.mean(memory_peaks),
    )


def profile_bottlenecks(content: str, output_file: str = None):
    """Profile code to identify bottlenecks.

    Args:
        content: Markdown content to parse
        output_file: Optional file to save profiling results
    """
    profiler = cProfile.Profile()
    profiler.enable()

    questions = parse_markdown(content)

    profiler.disable()

    if output_file:
        profiler.dump_stats(output_file)

    # Print top 20 functions by time
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    ps.print_callers(10)  # Top 10 callers

    return s.getvalue()


def run_comprehensive_analysis():
    """Run comprehensive performance analysis."""
    print("\n" + "="*80)
    print("MD2DB Python Implementation Performance Analysis")
    print("="*80)

    # System info
    print(f"\nSystem Information:")
    print(f"  Python Version: {sys.version}")
    print(f"  CPU Cores: {os.cpu_count() if 'os' in sys.modules else 'Unknown'}")

    # Test different file sizes
    test_sizes = [10, 50, 100, 500, 1000, 5000]
    results = []

    print("\n" + "-"*80)
    print("File Size Scalability Test")
    print("-"*80)

    for size in test_sizes:
        content = generate_test_questions(size, complexity='mixed')
        metrics = benchmark_parsing(content, iterations=10)
        results.append((size, metrics))

        print(f"\n{size} questions:")
        print(f"  Avg Time: {metrics.avg_time_ms:.2f} ms (±{metrics.std_time_ms:.2f})")
        print(f"  Min/Max: {metrics.min_time_ms:.2f} / {metrics.max_time_ms:.2f} ms")
        print(f"  Throughput: {metrics.questions_per_second:.2f} questions/sec")
        print(f"  Memory: {metrics.avg_memory_mb:.2f} MB (peak: {metrics.peak_memory_mb:.2f} MB)")

    # Test different complexities
    print("\n" + "-"*80)
    print("Complexity Analysis (100 questions)")
    print("-"*80)

    for complexity in ['simple', 'medium', 'complex', 'mixed']:
        content = generate_test_questions(100, complexity=complexity)
        metrics = benchmark_parsing(content, iterations=10)

        print(f"\n{complexity.capitalize()} questions:")
        print(f"  Avg Time: {metrics.avg_time_ms:.2f} ms")
        print(f"  Throughput: {metrics.questions_per_second:.2f} questions/sec")
        print(f"  Memory: {metrics.avg_memory_mb:.2f} MB")

    # Profile bottlenecks for large file
    print("\n" + "-"*80)
    print("Bottleneck Analysis")
    print("-"*80)

    content = generate_test_questions(1000, complexity='mixed')
    profiling_results = profile_bottlenecks(content)

    print("\nTop 20 Functions by Cumulative Time:")
    print(profiling_results)

    # Generate performance report
    generate_performance_report(results)

    return results


def generate_performance_report(results: List[tuple]):
    """Generate a detailed performance report.

    Args:
        results: List of (size, metrics) tuples
    """
    print("\n" + "="*80)
    print("Performance Summary Report")
    print("="*80)

    # Create comparison table
    print(f"\n{'Questions':<12} {'Avg Time (ms)':<15} {'Throughput (q/s)':<20} {'Memory (MB)':<15}")
    print("-"*80)

    for size, metrics in results:
        print(f"{size:<12} {metrics.avg_time_ms:<15.2f} {metrics.questions_per_second:<20.2f} {metrics.avg_memory_mb:<15.2f}")

    # Performance insights
    print("\n" + "-"*80)
    print("Performance Insights")
    print("-"*80)

    # Calculate scalability metrics
    if len(results) >= 2:
        size1, metrics1 = results[0]
        size2, metrics2 = results[-1]

        time_ratio = metrics2.avg_time_ms / metrics1.avg_time_ms
        size_ratio = size2 / size1

        print(f"\nScalability Analysis:")
        print(f"  Question count increased by: {size_ratio:.1f}x")
        print(f"  Time increased by: {time_ratio:.1f}x")

        if time_ratio < size_ratio:
            print(f"  ✓ Shows good scalability (sub-linear growth)")
        else:
            print(f"  ⚠ Shows linear or worse scaling")

    # Performance recommendations
    print("\nPerformance Recommendations:")

    avg_qps = statistics.mean([m.questions_per_second for _, m in results])

    if avg_qps > 1000:
        print("  ✓ Excellent performance (>1000 q/s)")
        print("  → Python implementation is highly optimized")
    elif avg_qps > 500:
        print("  ✓ Good performance (500-1000 q/s)")
        print("  → Suitable for most use cases")
    elif avg_qps > 100:
        print("  ⚠ Moderate performance (100-500 q/s)")
        print("  → Consider optimization for large files")
    else:
        print("  ✗ Performance may need improvement (<100 q/s)")
        print("  → Consider Rust implementation for production")

    avg_memory = statistics.mean([m.avg_memory_mb for _, m in results])
    print(f"\nMemory Usage:")
    if avg_memory < 10:
        print(f"  ✓ Excellent ({avg_memory:.2f} MB average)")
    elif avg_memory < 50:
        print(f"  ✓ Good ({avg_memory:.2f} MB average)")
    else:
        print(f"  ⚠ High memory usage ({avg_memory:.2f} MB average)")
        print(f"  → Consider streaming or chunked processing for large files")


def export_results_json(results: List[tuple], filename: str = "performance_results.json"):
    """Export performance results to JSON file.

    Args:
        results: List of (size, metrics) tuples
        filename: Output filename
    """
    export_data = [
        {
            "questions": size,
            "avg_time_ms": metrics.avg_time_ms,
            "std_time_ms": metrics.std_time_ms,
            "min_time_ms": metrics.min_time_ms,
            "max_time_ms": metrics.max_time_ms,
            "questions_per_second": metrics.questions_per_second,
            "peak_memory_mb": metrics.peak_memory_mb,
            "avg_memory_mb": metrics.avg_memory_mb,
        }
        for size, metrics in results
    ]

    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"\nResults exported to {filename}")


if __name__ == '__main__':
    import os

    results = run_comprehensive_analysis()
    export_results_json(results)

    print("\n" + "="*80)
    print("Analysis Complete")
    print("="*80)
