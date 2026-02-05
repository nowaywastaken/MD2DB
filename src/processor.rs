//! Single-machine multi-core processor for parallel question processing
//!
//! This module provides a high-performance processor that automatically detects
//! CPU core count and distributes work across multiple cores using Rayon for
//! CPU-intensive tasks and Tokio for I/O-intensive tasks.
//!
//! # Architecture
//!
//! The processor uses a hybrid concurrency model:
//! - **Rayon**: For CPU-intensive parsing operations (Markdown parsing, LaTeX extraction)
//! - **Tokio**: For I/O-intensive operations (file reading, ZIP extraction, database writes)
//! - **Semaphore**: For controlling concurrency and preventing resource exhaustion
//!
//! # Performance Optimizations
//!
//! - Automatic CPU core detection
//! - Batched database writes to reduce transaction overhead
//! - Parallel parsing with work-stealing scheduler
//! - Content-addressed storage for image deduplication
//! - Backpressure-aware async stream processing

use crate::database::QuestionRepository;
use crate::models::Question;
use crate::parser::{parse_markdown, MarkdownParser};
use crate::zip::{ZipEntry, ZipProcessor};
use anyhow::{Context, Result};
use futures::stream::{self, StreamExt};
use rayon::prelude::*;
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Semaphore;
use tracing::{debug, info, warn};

/// Configuration for the single-machine processor
#[derive(Debug, Clone)]
pub struct ProcessorConfig {
    /// Maximum number of CPU workers for parsing (defaults to CPU core count)
    pub max_cpu_workers: usize,
    /// Maximum number of I/O workers for file/database operations (defaults to CPU core count * 2)
    pub max_io_workers: usize,
    /// Batch size for database writes (defaults to 100)
    pub batch_size: usize,
    /// Maximum concurrent ZIP file processing (defaults to 4)
    pub max_concurrent_zips: usize,
}

impl Default for ProcessorConfig {
    fn default() -> Self {
        let cpu_cores = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(4);

        Self {
            max_cpu_workers: cpu_cores,
            max_io_workers: cpu_cores * 2,
            batch_size: 100,
            max_concurrent_zips: 4,
        }
    }
}

impl ProcessorConfig {
    /// Create a new configuration with specified CPU workers
    pub fn with_cpu_workers(mut self, workers: usize) -> Self {
        self.max_cpu_workers = workers.max(1);
        self
    }

    /// Create a new configuration with specified I/O workers
    pub fn with_io_workers(mut self, workers: usize) -> Self {
        self.max_io_workers = workers.max(1);
        self
    }

    /// Create a new configuration with specified batch size
    pub fn with_batch_size(mut self, batch_size: usize) -> Self {
        self.batch_size = batch_size.max(1);
        self
    }

    /// Create a new configuration with specified max concurrent ZIP files
    pub fn with_max_concurrent_zips(mut self, max: usize) -> Self {
        self.max_concurrent_zips = max.max(1);
        self
    }
}

/// Result of a processing operation
#[derive(Debug)]
pub struct ProcessResult {
    /// Total number of questions processed
    pub total_questions: usize,
    /// Number of questions successfully saved
    pub saved_questions: usize,
    /// Number of questions that failed to save
    pub failed_questions: usize,
    /// Number of images processed
    pub total_images: usize,
    /// Warnings generated during processing
    pub warnings: Vec<String>,
    /// Processing time in milliseconds
    pub processing_time_ms: u64,
}

impl ProcessResult {
    /// Create a new empty result
    fn new() -> Self {
        Self {
            total_questions: 0,
            saved_questions: 0,
            failed_questions: 0,
            total_images: 0,
            warnings: Vec::new(),
            processing_time_ms: 0,
        }
    }

    /// Add a warning to the result
    fn add_warning(&mut self, warning: String) {
        self.warnings.push(warning);
    }

    /// Check if processing was successful
    pub fn is_success(&self) -> bool {
        self.failed_questions == 0
    }

    /// Get the success rate as a percentage
    pub fn success_rate(&self) -> f64 {
        if self.total_questions == 0 {
            100.0
        } else {
            (self.saved_questions as f64 / self.total_questions as f64) * 100.0
        }
    }
}

/// Input source for processing
#[derive(Debug, Clone)]
pub enum InputSource {
    /// Single Markdown file content
    Markdown { content: String, source: String },
    /// Multiple Markdown file contents
    MultipleMarkdown { contents: Vec<(String, String)> },
    /// ZIP file data
    Zip { data: Vec<u8>, source: String },
    /// Multiple ZIP files
    MultipleZip { files: Vec<(Vec<u8>, String)> },
}

/// Single-machine multi-core processor
///
/// This processor automatically distributes work across available CPU cores
/// and manages concurrent I/O operations for optimal throughput.
pub struct SingleMachineProcessor<R> {
    /// Database repository for persisting questions
    repository: Arc<R>,
    /// Processor configuration
    config: ProcessorConfig,
    /// ZIP processor for handling ZIP archives
    zip_processor: ZipProcessor,
    /// Semaphore for limiting CPU-intensive work
    cpu_semaphore: Arc<Semaphore>,
    /// Semaphore for limiting I/O-intensive work
    io_semaphore: Arc<Semaphore>,
}

impl<R> SingleMachineProcessor<R>
where
    R: QuestionRepository + Send + Sync,
{
    /// Create a new processor with default configuration
    pub fn new(repository: R) -> Self {
        Self::with_config(repository, ProcessorConfig::default())
    }

    /// Create a new processor with custom configuration
    pub fn with_config(repository: R, config: ProcessorConfig) -> Self {
        let cpu_workers = config.max_cpu_workers;
        let io_workers = config.max_io_workers;

        // Configure Rayon thread pool
        rayon::ThreadPoolBuilder::new()
            .num_threads(cpu_workers)
            .build_global()
            .unwrap_or_else(|e| {
                warn!("Failed to set global Rayon thread pool: {}", e);
            });

        // Configure ZIP processor
        let zip_processor = ZipProcessor::with_workers(cpu_workers);

        Self {
            repository: Arc::new(repository),
            config,
            zip_processor,
            cpu_semaphore: Arc::new(Semaphore::new(cpu_workers)),
            io_semaphore: Arc::new(Semaphore::new(io_workers)),
        }
    }

    /// Process an input source and save questions to the database
    ///
    /// This is the main entry point for processing operations. It automatically
    /// selects the appropriate processing strategy based on the input type.
    pub async fn process(&self, input: InputSource) -> Result<ProcessResult> {
        let start = std::time::Instant::now();

        info!("Starting processing with config: {:?}", self.config);

        let (questions, images, warnings) = match input {
            InputSource::Markdown { content, source } => {
                self.process_single_markdown(content, source).await?
            }
            InputSource::MultipleMarkdown { contents } => {
                self.process_multiple_markdown(contents).await?
            }
            InputSource::Zip { data, source } => {
                self.process_single_zip(data, source).await?
            }
            InputSource::MultipleZip { files } => {
                self.process_multiple_zips(files).await?
            }
        };

        // Save questions to database in batches
        let saved = self.save_questions_batched(questions).await?;

        let elapsed = start.elapsed();
        let result = ProcessResult {
            total_questions: saved.total + saved.failed,
            saved_questions: saved.total,
            failed_questions: saved.failed,
            total_images: images.len(),
            warnings,
            processing_time_ms: elapsed.as_millis() as u64,
        };

        info!(
            "Processing complete: {} questions saved, {} failed in {}ms",
            result.saved_questions,
            result.failed_questions,
            result.processing_time_ms
        );

        Ok(result)
    }

    /// Process a single Markdown file
    async fn process_single_markdown(
        &self,
        content: String,
        source: String,
    ) -> Result<(Vec<Question>, HashMap<String, Vec<u8>>, Vec<String>)> {
        debug!("Processing single Markdown file: {}", source);

        let questions = tokio::task::spawn_blocking(move || {
            parse_markdown(&content)
        })
        .await
        .context("Failed to parse Markdown")??;

        debug!("Parsed {} questions from Markdown", questions.len());

        Ok((questions, HashMap::new(), Vec::new()))
    }

    /// Process multiple Markdown files in parallel using Rayon
    async fn process_multiple_markdown(
        &self,
        contents: Vec<(String, String)>,
    ) -> Result<(Vec<Question>, HashMap<String, Vec<u8>>, Vec<String>)> {
        info!("Processing {} Markdown files in parallel", contents.len());

        let semaphore = self.cpu_semaphore.clone();
        let cpu_workers = self.config.max_cpu_workers;

        let results = stream::iter(contents)
            .map(|(content, source)| {
                let sem = semaphore.clone();
                async move {
                    let _permit = sem.acquire().await.unwrap();

                    tokio::task::spawn_blocking(move || {
                        let result = parse_markdown(&content);
                        (result, source)
                    })
                    .await
                }
            })
            .buffer_unordered(cpu_workers)
            .collect::<Vec<_>>()
            .await;

        let mut all_questions = Vec::new();
        let mut warnings = Vec::new();

        for result in results {
            match result {
                Ok((Ok(questions), source)) => {
                    debug!("Parsed {} questions from {}", questions.len(), source);
                    all_questions.extend(questions);
                }
                Ok((Err(e), source)) => {
                    warn!("Failed to parse {}: {}", source, e);
                    warnings.push(format!("Failed to parse {}: {}", source, e));
                }
                Err(e) => {
                    warn!("Task failed: {}", e);
                    warnings.push(format!("Task failed: {}", e));
                }
            }
        }

        Ok((all_questions, HashMap::new(), warnings))
    }

    /// Process a single ZIP file
    async fn process_single_zip(
        &self,
        data: Vec<u8>,
        source: String,
    ) -> Result<(Vec<Question>, HashMap<String, Vec<u8>>, Vec<String>)> {
        debug!("Processing single ZIP file: {}", source);

        let zip_result = self.zip_processor.process_zip(data).await?;

        debug!(
            "Extracted {} questions and {} images from ZIP",
            zip_result.questions.len(),
            zip_result.images.len()
        );

        Ok((
            zip_result.questions,
            zip_result.images,
            zip_result.warnings,
        ))
    }

    /// Process multiple ZIP files in parallel
    async fn process_multiple_zips(
        &self,
        files: Vec<(Vec<u8>, String)>,
    ) -> Result<(Vec<Question>, HashMap<String, Vec<u8>>, Vec<String>)> {
        info!("Processing {} ZIP files in parallel", files.len());

        let semaphore = self.cpu_semaphore.clone();
        let max_concurrent = self.config.max_concurrent_zips;

        let results = stream::iter(files)
            .map(|(data, source)| {
                let sem = semaphore.clone();
                let processor = &self.zip_processor;
                async move {
                    let _permit = sem.acquire().await.unwrap();
                    processor.process_zip(data).await
                }
            })
            .buffer_unordered(max_concurrent)
            .collect::<Vec<_>>()
            .await;

        let mut all_questions = Vec::new();
        let mut all_images = HashMap::new();
        let mut all_warnings = Vec::new();

        for result in results {
            match result {
                Ok(zip_result) => {
                    all_questions.extend(zip_result.questions);
                    all_images.extend(zip_result.images);
                    all_warnings.extend(zip_result.warnings);
                }
                Err(e) => {
                    warn!("Failed to process ZIP: {}", e);
                    all_warnings.push(format!("Failed to process ZIP: {}", e));
                }
            }
        }

        debug!(
            "Total from all ZIPs: {} questions, {} images",
            all_questions.len(),
            all_images.len()
        );

        Ok((all_questions, all_images, all_warnings))
    }

    /// Save questions to database in batches
    async fn save_questions_batched(&self, questions: Vec<Question>) -> Result<BatchSaveResult> {
        if questions.is_empty() {
            return Ok(BatchSaveResult {
                total: 0,
                failed: 0,
            });
        }

        info!(
            "Saving {} questions to database in batches of {}",
            questions.len(),
            self.config.batch_size
        );

        let semaphore = self.io_semaphore.clone();
        let batch_size = self.config.batch_size;
        let repository = self.repository.clone();

        // Split questions into batches
        let batches: Vec<_> = questions
            .chunks(batch_size)
            .enumerate()
            .map(|(i, chunk)| (i, chunk.to_vec()))
            .collect();

        let results = stream::iter(batches)
            .map(|(batch_idx, batch)| {
                let sem = semaphore.clone();
                let repo = repository.clone();
                async move {
                    let _permit = sem.acquire().await.unwrap();

                    match repo.save_batch(&batch).await {
                        Ok(ids) => {
                            debug!(
                                "Saved batch {} with {} questions",
                                batch_idx,
                                ids.len()
                            );
                            BatchSaveResult {
                                total: ids.len(),
                                failed: 0,
                            }
                        }
                        Err(e) => {
                            warn!("Failed to save batch {}: {}", batch_idx, e);
                            BatchSaveResult {
                                total: 0,
                                failed: batch.len(),
                            }
                        }
                    }
                }
            })
            .buffer_unordered(self.config.max_io_workers)
            .collect::<Vec<_>>()
            .await;

        let mut total_saved = 0;
        let mut total_failed = 0;

        for result in results {
            total_saved += result.total;
            total_failed += result.failed;
        }

        Ok(BatchSaveResult {
            total: total_saved,
            failed: total_failed,
        })
    }

    /// Get the processor configuration
    pub fn config(&self) -> &ProcessorConfig {
        &self.config
    }

    /// Get the number of available CPU cores
    pub fn cpu_cores(&self) -> usize {
        self.config.max_cpu_workers
    }
}

/// Result of a batch save operation
#[derive(Debug)]
struct BatchSaveResult {
    /// Number of successfully saved questions
    total: usize,
    /// Number of failed questions
    failed: usize,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::database::MockRepository;

    fn create_test_markdown() -> String {
        r#"# What is 2+2?

* A. 3
* B. 4
* C. 5

# What is the capital of France?

* A. London
* B. Berlin
* C. Paris"#
            .to_string()
    }

    #[test]
    fn test_processor_config_default() {
        let config = ProcessorConfig::default();
        assert!(config.max_cpu_workers > 0);
        assert!(config.max_io_workers > 0);
        assert_eq!(config.batch_size, 100);
        assert_eq!(config.max_concurrent_zips, 4);
    }

    #[test]
    fn test_processor_config_builder() {
        let config = ProcessorConfig::default()
            .with_cpu_workers(8)
            .with_io_workers(16)
            .with_batch_size(50)
            .with_max_concurrent_zips(2);

        assert_eq!(config.max_cpu_workers, 8);
        assert_eq!(config.max_io_workers, 16);
        assert_eq!(config.batch_size, 50);
        assert_eq!(config.max_concurrent_zips, 2);
    }

    #[test]
    fn test_process_result_empty() {
        let result = ProcessResult::new();
        assert_eq!(result.total_questions, 0);
        assert_eq!(result.saved_questions, 0);
        assert_eq!(result.failed_questions, 0);
        assert!(result.is_success());
        assert_eq!(result.success_rate(), 100.0);
    }

    #[test]
    fn test_process_result_partial_failure() {
        let mut result = ProcessResult::new();
        result.total_questions = 10;
        result.saved_questions = 8;
        result.failed_questions = 2;

        assert!(!result.is_success());
        assert_eq!(result.success_rate(), 80.0);
    }

    #[tokio::test]
    async fn test_processor_creation() {
        let repo = MockRepository::new();
        let processor = SingleMachineProcessor::new(repo);

        assert!(processor.cpu_cores() > 0);
        assert_eq!(processor.config().batch_size, 100);
    }

    #[tokio::test]
    async fn test_processor_with_custom_config() {
        let repo = MockRepository::new();
        let config = ProcessorConfig::default()
            .with_cpu_workers(4)
            .with_batch_size(50);

        let processor = SingleMachineProcessor::with_config(repo, config);

        assert_eq!(processor.cpu_cores(), 4);
        assert_eq!(processor.config().batch_size, 50);
    }

    #[tokio::test]
    async fn test_process_single_markdown() {
        let repo = MockRepository::new();
        let processor = SingleMachineProcessor::new(repo);

        let markdown = create_test_markdown();
        let input = InputSource::Markdown {
            content: markdown,
            source: "test.md".to_string(),
        };

        let result = processor.process(input).await.unwrap();

        assert_eq!(result.total_questions, 2);
        assert_eq!(result.saved_questions, 2);
        assert!(result.is_success());
        assert_eq!(result.success_rate(), 100.0);
    }

    #[tokio::test]
    async fn test_process_multiple_markdown() {
        let repo = MockRepository::new();
        let processor = SingleMachineProcessor::new(repo);

        let contents = vec![
            (create_test_markdown(), "test1.md".to_string()),
            (create_test_markdown(), "test2.md".to_string()),
        ];

        let input = InputSource::MultipleMarkdown { contents };

        let result = processor.process(input).await.unwrap();

        assert_eq!(result.total_questions, 4);
        assert_eq!(result.saved_questions, 4);
        assert!(result.is_success());
    }

    #[test]
    fn test_parse_markdown_parallel() {
        // Test that Rayon parallel parsing works
        let contents: Vec<_> = (0..10)
            .map(|i| {
                (
                    format!("# Question {}?\n\n* A. Option 1\n* B. Option 2", i),
                    format!("test{}.md", i),
                )
            })
            .collect();

        let questions: Vec<_> = contents
            .into_par_iter()
            .filter_map(|(content, _)| parse_markdown(&content).ok())
            .flatten()
            .collect();

        assert_eq!(questions.len(), 10);
    }

    #[tokio::test]
    async fn test_empty_markdown_processing() {
        let repo = MockRepository::new();
        let processor = SingleMachineProcessor::new(repo);

        let input = InputSource::Markdown {
            content: String::new(),
            source: "empty.md".to_string(),
        };

        let result = processor.process(input).await.unwrap();

        assert_eq!(result.total_questions, 0);
        assert!(result.is_success());
    }
}
