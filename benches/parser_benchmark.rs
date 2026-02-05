// Criterion benchmarks for MD2DB parser performance
//
// Run with: cargo bench --bench parser_benchmark

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use md2db::parser::parse_markdown;

/// Generate test markdown content with specified number of questions
fn generate_test_questions(count: usize) -> String {
    let mut questions = String::new();

    for i in 0..count {
        let q_type = i % 4;
        match q_type {
            0 => {
                // Multiple Choice
                questions.push_str(&format!(
                    "{}. What is {} + {}?\n\n\
                     A. {}\n\
                     B. {}\n\
                     C. {}\n\
                     D. {}\n\n\
                     Answer: B\n\n",
                    i + 1,
                    i,
                    i,
                    i,
                    i * 2,
                    i * 3,
                    i * 4
                ));
            }
            1 => {
                // True/False
                questions.push_str(&format!(
                    "{}. The value of {} + {} equals {}.\n\n\
                     True\n\n",
                    i + 1,
                    i,
                    i,
                    i * 2
                ));
            }
            2 => {
                // Fill in the blank
                questions.push_str(&format!(
                    "{}. The capital of country {} is _____.\n\n\
                     Answer: Capital {}\n\n",
                    i + 1, i, i
                ));
            }
            _ => {
                // Subjective with LaTeX
                questions.push_str(&format!(
                    "{}. Explain the mathematical formula: $x^2 + y^2 = z^2$\n\n\
                     Answer: This is the Pythagorean theorem.\n\n",
                    i + 1
                ));
            }
        }
    }

    questions
}

/// Benchmark parsing with different file sizes
fn bench_parse_file_sizes(c: &mut Criterion) {
    let mut group = c.benchmark_group("parse_file_sizes");

    for size in [10, 50, 100, 500, 1000].iter() {
        let content = generate_test_questions(*size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &content, |b, content| {
            b.iter(|| parse_markdown(black_box(content)))
        });
    }

    group.finish();
}

/// Benchmark parsing with different question types
fn bench_parse_question_types(c: &mut Criterion) {
    let mut group = c.benchmark_group("parse_question_types");

    // Multiple choice questions
    let mc_questions: String = (0..100)
        .map(|i| {
            format!(
                "{}. What is {} + {}?\n\n* A. {}\n* B. {}\n* C. {}\n",
                i + 1,
                i,
                i,
                i,
                i * 2,
                i * 3
            )
        })
        .collect();
    group.bench_function("multiple_choice_100", |b| {
        b.iter(|| parse_markdown(black_box(&mc_questions)))
    });

    // True/False questions
    let tf_questions: String = (0..100)
        .map(|i| {
            format!(
                "{}. The value of {} + {} equals {}.\n\nTrue\n",
                i + 1,
                i,
                i,
                i * 2
            )
        })
        .collect();
    group.bench_function("true_false_100", |b| {
        b.iter(|| parse_markdown(black_box(&tf_questions)))
    });

    // Questions with LaTeX
    let latex_questions: String = (0..100)
        .map(|i| {
            format!(
                "{}. Explain: $x^2 + y^2 = z^2$ and `\\frac{{a}}{{b}}`\n",
                i + 1
            )
        })
        .collect();
    group.bench_function("with_latex_100", |b| {
        b.iter(|| parse_markdown(black_box(&latex_questions)))
    });

    // Mixed questions
    let mixed = generate_test_questions(100);
    group.bench_function("mixed_100", |b| {
        b.iter(|| parse_markdown(black_box(&mixed)))
    });

    group.finish();
}

/// Benchmark memory allocation patterns
fn bench_memory_allocation(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_allocation");

    let content = generate_test_questions(1000);

    group.bench_function("parse_1000_questions", |b| {
        b.iter(|| parse_markdown(black_box(&content)))
    });

    group.finish();
}

/// Compare single-threaded vs multi-threaded parsing (if parallel features exist)
#[cfg(feature = "parallel")]
fn bench_parallel_parsing(c: &mut Criterion) {
    use rayon::prelude::*;

    let mut group = c.benchmark_group("parallel_parsing");

    let contents: Vec<String> = (0..10).map(|i| generate_test_questions(100)).collect();

    group.bench_function("sequential_10_files", |b| {
        b.iter(|| {
            contents
                .iter()
                .map(|content| parse_markdown(content).unwrap())
                .collect::<Vec<_>>()
        })
    });

    group.bench_function("parallel_10_files", |b| {
        b.iter(|| {
            contents
                .par_iter()
                .map(|content| parse_markdown(content).unwrap())
                .collect::<Vec<_>>()
        })
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_parse_file_sizes,
    bench_parse_question_types,
    bench_memory_allocation
);

// Include parallel benchmarks if the feature is enabled
#[cfg(feature = "parallel")]
criterion_group!(parallel_benches, bench_parallel_parsing);

criterion_main!(benches);
