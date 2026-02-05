//! ZIP file processing for batch question imports
//!
//! This module handles ZIP extraction and parallel processing
//! of multiple Markdown files with associated images.

use crate::media::process_image;
use crate::models::Question;
use crate::parser::parse_markdown;
use anyhow::{anyhow, Result};
use futures::stream::{self, StreamExt};
use std::collections::HashMap;
use std::io::{Cursor, Read};
use std::path::PathBuf;
use tokio::sync::Semaphore;

/// Entry extracted from a ZIP file
#[derive(Debug, Clone)]
pub struct ZipEntry {
    /// Path of the file within the ZIP
    pub path: PathBuf,
    /// Raw file content
    pub content: Vec<u8>,
    /// Whether this is a Markdown file
    pub is_markdown: bool,
    /// Whether this is an image file
    pub is_image: bool,
}

impl ZipEntry {
    /// Create a new ZIP entry
    pub fn new(path: PathBuf, content: Vec<u8>) -> Self {
        let path_str = path.to_string_lossy().to_lowercase();
        let is_markdown = path_str.ends_with(".md");
        let is_image = path_str.ends_with(".png")
            || path_str.ends_with(".jpg")
            || path_str.ends_with(".jpeg")
            || path_str.ends_with(".gif")
            || path_str.ends_with(".webp");

        Self {
            path,
            content,
            is_markdown,
            is_image,
        }
    }

    /// Get the file content as a string
    pub fn as_string(&self) -> Result<String> {
        String::from_utf8(self.content.clone())
            .map_err(|e| anyhow!("Invalid UTF-8 in file {:?}: {}", self.path, e))
    }
}

/// Result of processing a ZIP file
#[derive(Debug)]
pub struct ZipProcessResult {
    /// All parsed questions
    pub questions: Vec<Question>,
    /// Images that were processed (hash -> content)
    pub images: HashMap<String, Vec<u8>>,
    /// Warnings generated during processing
    pub warnings: Vec<String>,
}

/// ZIP processor with configurable parallelism
pub struct ZipProcessor {
    /// Maximum number of concurrent file processing tasks
    max_workers: usize,
}

impl ZipProcessor {
    /// Create a new ZIP processor
    pub fn new() -> Self {
        // Default to number of CPU cores
        let workers = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(4);

        Self {
            max_workers: workers,
        }
    }

    /// Create a ZIP processor with specific worker count
    pub fn with_workers(workers: usize) -> Self {
        Self {
            max_workers: workers,
        }
    }

    /// Process a ZIP file from raw bytes
    pub async fn process_zip(&self, zip_data: Vec<u8>) -> Result<ZipProcessResult> {
        // Extract all entries using tokio task for blocking I/O
        let entries = tokio::task::spawn_blocking(move || {
            Self::extract_all_entries_sync(zip_data)
        })
        .await??;

        // Separate Markdown files and images
        let (md_entries, image_entries): (Vec<_>, Vec<_>) = entries
            .into_iter()
            .partition(|e| e.is_markdown);

        // Process images and Markdown files in parallel
        let (images_result, questions_result) = tokio::join!(
            self.process_images(image_entries),
            self.process_markdown_files(md_entries)
        );

        let images = images_result?;
        let questions = questions_result?;

        Ok(ZipProcessResult {
            questions,
            images,
            warnings: Vec::new(),
        })
    }

    /// Extract all entries from a ZIP archive (synchronous)
    fn extract_all_entries_sync(zip_data: Vec<u8>) -> Result<Vec<ZipEntry>> {
        use zip::read::ZipArchive;

        let cursor = Cursor::new(zip_data);
        let mut archive = ZipArchive::new(cursor)?;

        let mut entries = Vec::new();

        for i in 0..archive.len() {
            let mut file = archive.by_index(i)?;
            let path = PathBuf::from(file.name());

            // Skip directories and macOS metadata files
            let path_str = path.to_string_lossy();
            if path_str.ends_with('/')
                || path_str.starts_with("__MACOSX/")
                || path_str.starts_with("._")
            {
                continue;
            }

            // Read file content
            let mut content = Vec::new();
            file.read_to_end(&mut content)?;

            entries.push(ZipEntry::new(path, content));
        }

        Ok(entries)
    }

    /// Process image entries with content-addressed storage
    async fn process_images(&self, image_entries: Vec<ZipEntry>) -> Result<HashMap<String, Vec<u8>>> {
        let semaphore = std::sync::Arc::new(Semaphore::new(self.max_workers));

        let results = stream::iter(image_entries)
            .map(|entry| {
                let sem = semaphore.clone();
                async move {
                    // Acquire permit to limit concurrency
                    let _permit = sem.acquire().await.unwrap();

                    // Process image (compute hash, detect format)
                    if let Ok(crate::media::ImageRef::Local { hash, .. }) = process_image(&entry.content) {
                        Some((hash, entry.content))
                    } else {
                        None
                    }
                }
            })
            .buffer_unordered(self.max_workers)
            .collect::<Vec<_>>()
            .await;

        Ok(results.into_iter().filter_map(|x| x).collect())
    }

    /// Process Markdown files in parallel
    async fn process_markdown_files(&self, md_entries: Vec<ZipEntry>) -> Result<Vec<Question>> {
        let semaphore = std::sync::Arc::new(Semaphore::new(self.max_workers));

        let results = stream::iter(md_entries)
            .map(|entry| {
                let sem = semaphore.clone();
                async move {
                    // Acquire permit to limit concurrency
                    let _permit = sem.acquire().await.unwrap();

                    // Parse the Markdown file
                    let content = entry.as_string()?;
                    parse_markdown(&content)
                }
            })
            .buffer_unordered(self.max_workers)
            .collect::<Vec<_>>()
            .await;

        // Collect all questions from all files
        let mut all_questions = Vec::new();
        for result in results {
            all_questions.extend(result?);
        }

        Ok(all_questions)
    }
}

impl Default for ZipProcessor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_zip_entry_detection() {
        let md_entry = ZipEntry::new(PathBuf::from("test.md"), b"# Test".to_vec());
        assert!(md_entry.is_markdown);
        assert!(!md_entry.is_image);

        let png_entry = ZipEntry::new(PathBuf::from("image.png"), vec![0x89, 0x50, 0x4E, 0x47]);
        assert!(!png_entry.is_markdown);
        assert!(png_entry.is_image);

        let txt_entry = ZipEntry::new(PathBuf::from("readme.txt"), b"Hello".to_vec());
        assert!(!txt_entry.is_markdown);
        assert!(!txt_entry.is_image);
    }

    #[test]
    fn test_zip_entry_as_string() {
        let entry = ZipEntry::new(PathBuf::from("test.md"), b"Hello, world!".to_vec());
        let s = entry.as_string().unwrap();
        assert_eq!(s, "Hello, world!");
    }

    #[tokio::test]
    async fn test_zip_processor_creation() {
        let processor = ZipProcessor::new();
        assert!(processor.max_workers > 0);

        let custom = ZipProcessor::with_workers(8);
        assert_eq!(custom.max_workers, 8);
    }
}
