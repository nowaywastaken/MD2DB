//! Media processing for images and ZIP files
//!
//! This module handles extraction and processing of media files.

use anyhow::Result;
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

/// Process an image and generate content-addressed storage
pub fn process_image(img_data: &[u8]) -> Result<ImageRef> {
    // Calculate SHA-256 hash
    let mut hasher = Sha256::new();
    hasher.update(img_data);
    let hash = hasher.finalize();
    let hash_hex = format!("{:x}", hash);

    // Detect file extension from magic bytes
    let ext = detect_extension(img_data)?;

    let filename = format!("{}.{}", hash_hex, ext);

    // TODO: Check if file already exists (CAS deduplication)
    // TODO: Save to CAS storage

    Ok(ImageRef::Local {
        hash: hash_hex,
        original_path: filename,
    })
}

/// Detect file extension from magic bytes
fn detect_extension(data: &[u8]) -> Result<&'static str> {
    if data.len() < 8 {
        return Ok("bin");
    }

    // Check common image format signatures
    match &data[0..8] {
        [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A] => Ok("png"),
        [0xFF, 0xD8, 0xFF, ..] => Ok("jpg"),
        [0x47, 0x49, 0x46, 0x38, ..] => Ok("gif"),
        [0x52, 0x49, 0x46, 0x46, ..] => Ok("webp"), // RIFF
        [0x42, 0x4D, ..] => Ok("bmp"),
        _ => Ok("bin"),
    }
}

/// Normalize a path for cross-platform compatibility
pub fn normalize_path(path: &Path) -> PathBuf {
    let components: Vec<_> = path
        .components()
        .filter(|c| !matches!(c, std::path::Component::CurDir))
        .map(|c| c.as_os_str())
        .collect::<Vec<_>>();

    let path_str = components
        .iter()
        .map(|s| s.to_string_lossy())
        .collect::<Vec<_>>()
        .join("/");

    PathBuf::from(path_str)
}

/// Reference to an image (simplified version)
#[derive(Debug, Clone)]
pub enum ImageRef {
    Local { hash: String, original_path: String },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_png() {
        let png_header = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];
        assert_eq!(detect_extension(&png_header).unwrap(), "png");
    }

    #[test]
    fn test_detect_jpg() {
        let jpg_header = [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46];
        assert_eq!(detect_extension(&jpg_header).unwrap(), "jpg");
    }

    #[test]
    fn test_normalize_path() {
        use std::path::Path;
        let path = Path::new("images/photo.png");
        let normalized = normalize_path(path);
        assert_eq!(normalized.to_str().unwrap(), "images/photo.png");
    }
}
