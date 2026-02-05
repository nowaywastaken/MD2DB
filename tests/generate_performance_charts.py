#!/usr/bin/env python3
"""
Generate performance comparison charts for MD2DB.

This script creates visual representations of the performance data.
"""

import json
import sys
from pathlib import Path

# Try to import matplotlib, fall back to text-based charts if not available
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def load_results(json_file: str = "performance_results.json") -> list:
    """Load performance results from JSON file."""
    with open(json_file) as f:
        return json.load(f)


def generate_text_charts(results: list):
    """Generate text-based performance charts."""
    print("\n" + "="*80)
    print("Performance Visualization")
    print("="*80)

    # Throughput Chart
    print("\nQuestions per Second (Throughput):")
    print("-"*60)
    max_qps = max(r['questions_per_second'] for r in results)

    for r in results:
        qps = r['questions_per_second']
        bar_length = int((qps / max_qps) * 50)
        bar = "█" * bar_length
        print(f"{r['questions']:>6}q: {bar} {qps:,.0f} q/s")

    # Memory Usage Chart
    print("\nMemory Usage (MB):")
    print("-"*60)
    max_mem = max(r['avg_memory_mb'] for r in results)

    for r in results:
        mem = r['avg_memory_mb']
        bar_length = int((mem / max_mem) * 50)
        bar = "█" * bar_length
        print(f"{r['questions']:>6}q: {bar} {mem:.3f} MB")

    # Time Comparison Chart
    print("\nProcessing Time (ms) - Log Scale:")
    print("-"*60)

    for r in results:
        time_ms = r['avg_time_ms']
        # Use log scale for visualization
        if time_ms > 0:
            bar_length = int(min((time_ms / 100) * 50, 50))
        else:
            bar_length = 1
        bar = "█" * bar_length
        print(f"{r['questions']:>6}q: {bar} {time_ms:.2f} ms (±{r['std_time_ms']:.2f})")


def generate_matplotlib_charts(results: list, output_dir: str = "."):
    """Generate matplotlib charts if available."""
    if not HAS_MATPLOTLIB:
        print("\nNote: Install matplotlib for graphical charts:")
        print("  pip install matplotlib")
        return

    questions = [r['questions'] for r in results]
    times = [r['avg_time_ms'] for r in results]
    throughput = [r['questions_per_second'] for r in results]
    memory = [r['avg_memory_mb'] for r in results]

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('MD2DB Performance Analysis', fontsize=16, fontweight='bold')

    # 1. Processing Time vs File Size
    ax1.plot(questions, times, marker='o', linewidth=2, markersize=8)
    ax1.set_xlabel('Number of Questions', fontsize=12)
    ax1.set_ylabel('Processing Time (ms)', fontsize=12)
    ax1.set_title('Processing Time Scalability', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')

    # 2. Throughput
    colors = plt.cm.viridis([i/len(throughput) for i in range(len(throughput))])
    ax2.bar(range(len(questions)), throughput, color=colors)
    ax2.set_xlabel('Number of Questions', fontsize=12)
    ax2.set_ylabel('Throughput (questions/sec)', fontsize=12)
    ax2.set_title('Parsing Throughput', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(questions)))
    ax2.set_xticklabels([str(q) for q in questions])
    ax2.grid(True, axis='y', alpha=0.3)

    # Add value labels on bars
    for i, v in enumerate(throughput):
        ax2.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=9)

    # 3. Memory Usage
    ax3.plot(questions, memory, marker='s', color='orange', linewidth=2, markersize=8)
    ax3.fill_between(questions, 0, memory, alpha=0.3, color='orange')
    ax3.set_xlabel('Number of Questions', fontsize=12)
    ax3.set_ylabel('Memory Usage (MB)', fontsize=12)
    ax3.set_title('Memory Efficiency', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # 4. Performance per Question (time/question in microseconds)
    time_per_question = [t / q * 1000 for t, q in zip(times, questions)]
    ax4.plot(questions, time_per_question, marker='^', color='green', linewidth=2, markersize=8)
    ax4.set_xlabel('Number of Questions', fontsize=12)
    ax4.set_ylabel('Time per Question (μs)', fontsize=12)
    ax4.set_title('Per-Question Processing Time', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save the figure
    output_file = Path(output_dir) / "performance_charts.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Charts saved to: {output_file}")

    # Create a summary statistics chart
    fig2, ax = plt.subplots(figsize=(10, 6))
    fig2.suptitle('Performance Summary Statistics', fontsize=16, fontweight='bold')

    # Summary table
    summary_data = [
        ['Average Throughput', f'{sum(throughput)/len(throughput):,.0f} q/s'],
        ['Peak Throughput', f'{max(throughput):,.0f} q/s'],
        ['Avg Memory/Question', f'{sum(memory)/sum(questions)*1000:.2f} KB'],
        ['Questions/Second', f'{sum(questions)/sum(times)/1000:.0f}'],
        ['Total Time (5K q)', f'{times[-1]:.2f} ms'],
    ]

    table = ax.table(cellText=summary_data, loc='center', cellLoc='left',
                     colWidths=[0.7, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)
    ax.axis('off')

    output_file2 = Path(output_dir) / "performance_summary.png"
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"✓ Summary chart saved to: {output_file2}")


def generate_performance_summary(results: list) -> dict:
    """Generate summary statistics."""
    total_questions = sum(r['questions'] for r in results)
    total_time = sum(r['avg_time_ms'] * r['questions'] for r in results) / 1000  # seconds

    return {
        'total_questions_tested': total_questions,
        'average_throughput': sum(r['questions_per_second'] for r in results) / len(results),
        'peak_throughput': max(r['questions_per_second'] for r in results),
        'average_memory_per_question': sum(r['avg_memory_mb'] for r in results) / sum(r['questions'] for r in results) * 1024,  # KB
        'total_processing_time': total_time,
        'efficiency_score': sum(r['questions_per_second'] for r in results) / len(results) / 1000,  # Arbitrary score
    }


def main():
    """Main execution."""
    results_file = Path(__file__).parent.parent.parent.parent / "performance_results.json"

    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}")
        print("Run performance_analysis.py first to generate results.")
        sys.exit(1)

    results = load_results(str(results_file))

    print("\n" + "="*80)
    print("MD2DB Performance Visualization")
    print("="*80)

    # Generate text charts
    generate_text_charts(results)

    # Generate matplotlib charts if available
    generate_matplotlib_charts(results, output_dir=str(Path(__file__).parent.parent.parent))

    # Print summary
    summary = generate_performance_summary(results)
    print("\n" + "="*80)
    print("Performance Summary")
    print("="*80)
    print(f"Total Questions Tested: {summary['total_questions_tested']:,}")
    print(f"Average Throughput: {summary['average_throughput']:,.0f} questions/second")
    print(f"Peak Throughput: {summary['peak_throughput']:,.0f} questions/second")
    print(f"Memory per Question: {summary['average_memory_per_question']:.2f} KB")
    print(f"Efficiency Score: {summary['efficiency_score']:.2f}")

    # Performance rating
    if summary['average_throughput'] > 50000:
        rating = "★★★★★ Excellent"
    elif summary['average_throughput'] > 20000:
        rating = "★★★★☆ Very Good"
    elif summary['average_throughput'] > 10000:
        rating = "★★★☆☆ Good"
    elif summary['average_throughput'] > 5000:
        rating = "★★☆☆☆ Fair"
    else:
        rating = "★☆☆☆☆ Needs Improvement"

    print(f"\nPerformance Rating: {rating}")


if __name__ == '__main__':
    main()
