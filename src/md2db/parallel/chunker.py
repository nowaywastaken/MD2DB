import os
import re
from typing import List, Tuple


QUESTION_SEPARATORS = [
    r'^\d+\.\s+',           # 1. 2. 3.
    r'^\s*---\s*$',         # ---
    r'^\s*\*\*\*\s*$',      # ***
]


class FileChunker:
    """Divides large files into chunks aligned with question boundaries."""

    def __init__(self, file_path: str, chunk_size_mb: float = 10):
        self.file_path = file_path
        self.chunk_size_bytes = int(chunk_size_mb * 1024 * 1024)
        self.file_size = os.path.getsize(file_path)

    def create_chunks(self) -> List[Tuple[int, int]]:
        """Create file chunks, ensuring boundaries align with question separators.

        Returns:
            List of (start_byte, end_byte) tuples
        """
        # Phase 1: Rough division by size
        raw_chunks = self._create_raw_chunks()

        # Phase 2: Adjust boundaries to question separators
        adjusted_chunks = self._adjust_boundaries(raw_chunks)

        return adjusted_chunks

    def _create_raw_chunks(self) -> List[Tuple[int, int]]:
        """Create rough chunks based on file size."""
        chunks = []
        start = 0

        while start < self.file_size:
            end = min(start + self.chunk_size_bytes, self.file_size)
            chunks.append((start, end))
            start = end

        return chunks

    def _adjust_boundaries(self, raw_chunks: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Adjust chunk boundaries to align with question separators."""
        if not raw_chunks:
            return []

        adjusted = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            prev_end = 0

            for i, (start, end) in enumerate(raw_chunks):
                # For all chunks except the last, find the next question separator
                if i < len(raw_chunks) - 1:
                    f.seek(end)
                    adjusted_end = self._find_next_separator(f, end)
                    adjusted.append((prev_end, adjusted_end))
                    prev_end = adjusted_end
                else:
                    # Last chunk goes to end of file
                    adjusted.append((prev_end, self.file_size))

        return adjusted

    def _find_next_separator(self, f, start_pos: int) -> int:
        """Find the next question separator starting from position."""
        max_search = 10000  # Don't search more than 10KB
        f.seek(start_pos)

        content = f.read(max_search)
        for pattern in QUESTION_SEPARATORS:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                # Found a separator
                return start_pos + match.start()

        # No separator found, return original position
        return start_pos
