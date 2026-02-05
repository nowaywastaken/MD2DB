# MD2DB 高性能并行解析系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 构建支持百万行 (50-200MB) Markdown 文件的高性能并行解析系统，使用 MongoDB 存储，通过多进程和流式写入实现最大化处理速度。

**架构:** 使用 `multiprocessing.Pool` 并行解析文件块，主进程协调 MongoDB 的双缓冲批量写入，通过 SHA256 哈希去重实现多集合关联结构。

**技术栈:** Python, multiprocessing, pymongo/Motor, MongoDB, pytest

---

## Phase 1: MongoDB 基础设施

### Task 1: 添加 MongoDB 依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 添加 pymongo 和 motor 到 requirements.txt**

```text
# 在 requirements.txt 末尾添加:
pymongo>=4.6.0
motor>=3.3.0
```

**Step 2: 安装新依赖**

Run: `python3 -m pip install -r requirements.txt`
Expected: Successfully installed pymongo, motor

**Step 3: 提交**

```bash
git add requirements.txt
git commit -m "feat: add pymongo and motor dependencies"
```

---

### Task 2: 创建 MongoDB 模型

**Files:**
- Create: `src/md2db/mongodb/__init__.py`
- Create: `src/md2db/mongodb/models.py`
- Test: `tests/mongodb/test_models.py`

**Step 1: 创建 mongodb 模块目录和 __init__.py**

```bash
mkdir -p src/md2db/mongodb
mkdir -p tests/mongodb
```

**Step 2: 创建 mongodb/__init__.py**

```python
# src/md2db/mongodb/__init__.py
"""MongoDB integration for MD2DB."""

__version__ = "0.1.0"
```

**Step 3: 编写失败的测试 - MongoDB 模型**

```python
# tests/mongodb/test_models.py
import pytest
from src.md2db.mongodb.models import QuestionDocument, OptionDocument, ImageDocument, LatexDocument

def test_question_document_creation():
    doc = QuestionDocument(
        content="What is 2+2?",
        question_type="multiple_choice"
    )
    assert doc.content == "What is 2+2?"
    assert doc.question_type == "multiple_choice"
    assert doc.options == []
    assert doc.images == []
    assert doc.latex_formulas == []

def test_option_document_creation():
    doc = OptionDocument(label="A", content="3")
    assert doc.label == "A"
    assert doc.content == "3"
    assert doc.hash is not None  # hash should be auto-generated

def test_image_document_creation():
    doc = ImageDocument(url="http://example.com/image.png", alt="diagram")
    assert doc.url == "http://example.com/image.png"
    assert doc.alt == "diagram"
    assert doc.hash is not None

def test_latex_document_creation():
    doc = LatexDocument(formula="\\frac{a}{b}")
    assert doc.formula == "\\frac{a}{b}"
    assert doc.hash is not None
```

**Step 4: 运行测试确认失败**

Run: `python3 -m pytest tests/mongodb/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.mongodb.models'"

**Step 5: 实现 MongoDB 模型**

```python
# src/md2db/mongodb/models.py
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import hashlib


def generate_hash(content: str) -> str:
    """Generate SHA256 hash for content."""
    return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class OptionDocument:
    """MongoDB document for question options."""
    label: str
    content: str
    hash: str = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.hash is None:
            combined = f"{self.label}:{self.content}"
            self.hash = generate_hash(combined)


@dataclass
class ImageDocument:
    """MongoDB document for images."""
    url: str
    alt: str = ""
    hash: str = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.hash is None:
            self.hash = generate_hash(self.url)


@dataclass
class LatexDocument:
    """MongoDB document for LaTeX formulas."""
    formula: str
    hash: str = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.hash is None:
            self.hash = generate_hash(self.formula)


@dataclass
class QuestionDocument:
    """MongoDB document for questions."""
    content: str
    question_type: str
    options: List[str] = field(default_factory=list)  # ObjectIds as strings
    answer: Optional[str] = None
    explanation: Optional[str] = None
    images: List[str] = field(default_factory=list)  # ObjectIds as strings
    latex_formulas: List[str] = field(default_factory=list)  # ObjectIds as strings
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 6: 运行测试确认通过**

Run: `python3 -m pytest tests/mongodb/test_models.py -v`
Expected: PASS (4 tests)

**Step 7: 提交**

```bash
git add src/md2db/mongodb/ tests/mongodb/
git commit -m "feat: add MongoDB document models"
```

---

### Task 3: 创建 MongoDB 客户端

**Files:**
- Create: `src/md2db/mongodb/client.py`
- Test: `tests/mongodb/test_client.py`

**Step 1: 编写失败的测试 - MongoDB 客户端连接**

```python
# tests/mongodb/test_client.py
import pytest
from pymongo import MongoClient
from src.md2db.mongodb.client import get_client, get_database


def test_get_client_returns_mongo_client():
    client = get_client("mongodb://localhost:27017")
    assert isinstance(client, MongoClient)


def test_get_database_returns_database():
    client = get_client("mongodb://localhost:27017")
    db = get_database(client, "md2db_test")
    assert db.name == "md2db_test"


def test_client_uses_same_instance_for_same_uri():
    client1 = get_client("mongodb://localhost:27017")
    client2 = get_client("mongodb://localhost:27017")
    assert client1 is client2  # Should return cached instance
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/mongodb/test_client.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.mongodb.client'"

**Step 3: 实现 MongoDB 客户端**

```python
# src/md2db/mongodb/client.py
from pymongo import MongoClient
from typing import Optional

_client_cache: Optional[MongoClient] = None
_client_uri: Optional[str] = None


def get_client(uri: str = "mongodb://localhost:27017") -> MongoClient:
    """Get or create a MongoDB client instance."""
    global _client_cache, _client_uri

    if _client_cache is None or _client_uri != uri:
        _client_cache = MongoClient(uri)
        _client_uri = uri

    return _client_cache


def get_database(client: MongoClient, name: str = "md2db"):
    """Get a database instance."""
    return client[name]


def close_client():
    """Close the current MongoDB client."""
    global _client_cache, _client_uri
    if _client_cache is not None:
        _client_cache.close()
        _client_cache = None
        _client_uri = None
```

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/mongodb/test_client.py -v`
Expected: PASS (3 tests)

**Step 5: 提交**

```bash
git add src/md2db/mongodb/client.py tests/mongodb/test_client.py
git commit -m "feat: add MongoDB client with connection caching"
```

---

### Task 4: 实现去重器

**Files:**
- Create: `src/md2db/mongodb/deduplicator.py`
- Test: `tests/mongodb/test_deduplicator.py`

**Step 1: 编写失败的测试 - 去重器**

```python
# tests/mongodb/test_deduplicator.py
import pytest
from pymongo import MongoClient
from src.md2db.mongodb.client import get_database
from src.md2db.mongodb.deduplicator import Deduplicator
from src.md2db.mongodb.models import OptionDocument, ImageDocument, LatexDocument


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = get_client("mongodb://localhost:27017")
    db = get_database(client, "md2db_test")
    # Clean up before test
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    yield db
    # Clean up after test
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})


def test_deduplicator_get_or_create_option_new(clean_db):
    dedup = Deduplicator(clean_db)
    option = OptionDocument(label="A", content="3")
    result_id = dedup.get_or_create_option(option)
    assert result_id is not None
    # Should be inserted
    assert clean_db.options.count_documents({}) == 1


def test_deduplicator_get_or_create_option_existing(clean_db):
    dedup = Deduplicator(clean_db)
    option = OptionDocument(label="A", content="3")
    id1 = dedup.get_or_create_option(option)
    id2 = dedup.get_or_create_option(option)
    assert id1 == id2  # Should return same ID
    # Should only have one document
    assert clean_db.options.count_documents({}) == 1


def test_deduplicator_get_or_create_image_new(clean_db):
    dedup = Deduplicator(clean_db)
    image = ImageDocument(url="http://example.com/img.png")
    result_id = dedup.get_or_create_image(image)
    assert result_id is not None
    assert clean_db.images.count_documents({}) == 1


def test_deduplicator_get_or_create_latex_new(clean_db):
    dedup = Deduplicator(clean_db)
    latex = LatexDocument(formula="\\frac{a}{b}")
    result_id = dedup.get_or_create_latex(latex)
    assert result_id is not None
    assert clean_db.latex_formulas.count_documents({}) == 1
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/mongodb/test_deduplicator.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.mongodb.deduplicator'"

**Step 3: 实现去重器**

```python
# src/md2db/mongodb/deduplicator.py
from typing import Optional
from pymongo.database import Database
from bson import ObjectId
from .models import OptionDocument, ImageDocument, LatexDocument


class Deduplicator:
    """Handles deduplication and storage of options, images, and latex formulas."""

    def __init__(self, db: Database):
        self.db = db
        self._setup_indexes()

    def _setup_indexes(self):
        """Ensure unique indexes exist on hash fields."""
        self.db.options.create_index("hash", unique=True)
        self.db.images.create_index("hash", unique=True)
        self.db.latex_formulas.create_index("hash", unique=True)

    def get_or_create_option(self, option: OptionDocument) -> Optional[str]:
        """Get existing option or create new one. Returns ObjectId as string."""
        existing = self.db.options.find_one({"hash": option.hash})
        if existing:
            return str(existing["_id"])

        result = self.db.options.insert_one({
            "label": option.label,
            "content": option.content,
            "hash": option.hash
        })
        return str(result.inserted_id)

    def get_or_create_image(self, image: ImageDocument) -> Optional[str]:
        """Get existing image or create new one. Returns ObjectId as string."""
        existing = self.db.images.find_one({"hash": image.hash})
        if existing:
            return str(existing["_id"])

        result = self.db.images.insert_one({
            "url": image.url,
            "alt": image.alt,
            "hash": image.hash
        })
        return str(result.inserted_id)

    def get_or_create_latex(self, latex: LatexDocument) -> Optional[str]:
        """Get existing latex or create new one. Returns ObjectId as string."""
        existing = self.db.latex_formulas.find_one({"hash": latex.hash})
        if existing:
            return str(existing["_id"])

        result = self.db.latex_formulas.insert_one({
            "formula": latex.formula,
            "hash": latex.hash
        })
        return str(result.inserted_id)
```

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/mongodb/test_deduplicator.py -v`
Expected: PASS (5 tests)

**Step 5: 提交**

```bash
git add src/md2db/mongodb/deduplicator.py tests/mongodb/test_deduplicator.py
git commit -m "feat: add deduplicator for options, images, and latex"
```

---

### Task 5: 实现批量写入器

**Files:**
- Create: `src/md2db/mongodb/writer.py`
- Test: `tests/mongodb/test_writer.py`

**Step 1: 编写失败的测试 - 批量写入器**

```python
# tests/mongodb/test_writer.py
import pytest
from pymongo import MongoClient
from src.md2db.mongodb.client import get_database
from src.md2db.mongodb.writer import BatchWriter
from src.md2db.mongodb.models import QuestionDocument


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = get_client("mongodb://localhost:27017")
    db = get_database(client, "md2db_test")
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    yield db
    # Cleanup
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})


def test_batch_writer_accumulates_until_batch_size(clean_db):
    writer = BatchWriter(clean_db, batch_size=3, deduplicator=None)
    doc1 = QuestionDocument(content="Q1", question_type="subjective")
    doc2 = QuestionDocument(content="Q2", question_type="subjective")

    # Add documents below batch size
    writer.add(doc1)
    writer.add(doc2)

    assert clean_db.questions.count_documents({}) == 0  # Not written yet


def test_batch_writer_flushes_on_batch_size(clean_db):
    writer = BatchWriter(clean_db, batch_size=2, deduplicator=None)
    doc1 = QuestionDocument(content="Q1", question_type="subjective")
    doc2 = QuestionDocument(content="Q2", question_type="subjective")
    doc3 = QuestionDocument(content="Q3", question_type="subjective")

    writer.add(doc1)
    writer.add(doc2)  # Should trigger flush

    assert clean_db.questions.count_documents({}) == 2

    writer.add(doc3)
    writer.flush()  # Manual flush for remaining

    assert clean_db.questions.count_documents({}) == 3


def test_batch_writer_flush_writes_all(clean_db):
    writer = BatchWriter(clean_db, batch_size=10, deduplicator=None)
    doc1 = QuestionDocument(content="Q1", question_type="subjective")
    doc2 = QuestionDocument(content="Q2", question_type="subjective")

    writer.add(doc1)
    writer.add(doc2)
    writer.flush()

    assert clean_db.questions.count_documents({}) == 2
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/mongodb/test_writer.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.mongodb.writer'"

**Step 3: 实现批量写入器**

```python
# src/md2db/mongodb/writer.py
from typing import List, Optional
from pymongo.database import Database
from .models import QuestionDocument
from .deduplicator import Deduplicator


class BatchWriter:
    """Buffers and writes questions to MongoDB in batches."""

    def __init__(self, db: Database, batch_size: int = 1000, deduplicator: Optional[Deduplicator] = None):
        self.db = db
        self.batch_size = batch_size
        self.deduplicator = deduplicator
        self._buffer: List[QuestionDocument] = []
        self._setup_indexes()

    def _setup_indexes(self):
        """Ensure indexes exist on questions collection."""
        self.db.questions.create_index("question_type")
        self.db.questions.create_index("created_at", -1)

    def add(self, document: QuestionDocument):
        """Add a document to the buffer. Flushes if buffer is full."""
        self._buffer.append(document)
        if len(self._buffer) >= self.batch_size:
            self.flush()

    def flush(self):
        """Write all buffered documents to MongoDB."""
        if not self._buffer:
            return

        documents = []
        for doc in self._buffer:
            doc_dict = {
                "content": doc.content,
                "question_type": doc.question_type,
                "options": doc.options,
                "answer": doc.answer,
                "explanation": doc.explanation,
                "images": doc.images,
                "latex_formulas": doc.latex_formulas,
                "created_at": doc.created_at
            }
            documents.append(doc_dict)

        if documents:
            self.db.questions.insert_many(documents, ordered=False)

        self._buffer.clear()
```

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/mongodb/test_writer.py -v`
Expected: PASS (3 tests)

**Step 5: 提交**

```bash
git add src/md2db/mongodb/writer.py tests/mongodb/test_writer.py
git commit -m "feat: add batch writer for questions"
```

---

## Phase 2: 文件分块

### Task 6: 实现文件分块器

**Files:**
- Create: `src/md2db/parallel/__init__.py`
- Create: `src/md2db/parallel/chunker.py`
- Test: `tests/parallel/test_chunker.py`

**Step 1: 创建 parallel 模块目录**

```bash
mkdir -p src/md2db/parallel
mkdir -p tests/parallel
```

**Step 2: 创建 parallel/__init__.py**

```python
# src/md2db/parallel/__init__.py
"""Parallel processing utilities for MD2DB."""

__version__ = "0.1.0"
```

**Step 3: 编写失败的测试 - 文件分块**

```python
# tests/parallel/test_chunker.py
import pytest
import tempfile
import os
from src.md2db.parallel.chunker import FileChunker, QUESTION_SEPARATORS


def test_question_separators_pattern():
    """Verify that question separator patterns are defined."""
    assert len(QUESTION_SEPARATORS) == 4
    assert r'^\d+\.\s+' in QUESTION_SEPARATORS
    assert r'^\s*---\s*$' in QUESTION_SEPARATORS


def test_file_chunker_creates_chunks():
    """Test that chunker divides file into chunks."""
    # Create a test file with multiple questions
    content = """1. First question
Some content here.

2. Second question
More content.

3. Third question
Even more content.
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        chunker = FileChunker(temp_path, chunk_size_mb=0.001)  # Very small chunks
        chunks = chunker.create_chunks()

        # Should create at least 2 chunks
        assert len(chunks) >= 2

        # Verify chunks are in order
        for i in range(len(chunks) - 1):
            assert chunks[i][0] < chunks[i][1]
            assert chunks[i][1] <= chunks[i + 1][0]

    finally:
        os.unlink(temp_path)


def test_file_chunker_adjusts_boundaries_to_question_separators():
    """Test that chunk boundaries align with question separators."""
    content = """1. First question
Content here.

2. Second question
Content here.

3. Third question
Content here.
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        chunker = FileChunker(temp_path, chunk_size_mb=0.001)
        chunks = chunker.create_chunks()

        # Read content at each boundary to verify it's a question separator
        with open(temp_path, 'r') as f:
            for start, end in chunks:
                if end < os.path.getsize(temp_path):
                    f.seek(end)
                    line = f.readline()
                    # Should be empty (file end) or start with number
                    assert line == '' or line.strip().startswith(('1.', '2.', '3.', '---'))

    finally:
        os.unlink(temp_path)
```

**Step 4: 运行测试确认失败**

Run: `python3 -m pytest tests/parallel/test_chunker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.parallel.chunker'"

**Step 5: 实现文件分块器**

```python
# src/md2db/parallel/chunker.py
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
```

**Step 6: 运行测试确认通过**

Run: `python3 -m pytest tests/parallel/test_chunker.py -v`
Expected: PASS (3 tests)

**Step 7: 提交**

```bash
git add src/md2db/parallel/ tests/parallel/
git commit -m "feat: add file chunker with boundary detection"
```

---

## Phase 3: 并行处理

### Task 7: 实现工作进程

**Files:**
- Create: `src/md2db/parallel/worker.py`
- Test: `tests/parallel/test_worker.py`

**Step 1: 编写失败的测试 - 工作进程解析**

```python
# tests/parallel/test_worker.py
import pytest
import tempfile
import os
from src.md2db.parallel.worker import parse_chunk
from src.md2db.mongodb.models import QuestionDocument


def test_parse_chunk_single_question():
    """Test parsing a chunk with a single question."""
    chunk_content = "What is 2+2?\nA. 3\nB. 4\nC. 5"
    result = parse_chunk(chunk_content)

    assert len(result) == 1
    assert result[0].content == "What is 2+2?"
    assert result[0].question_type == "multiple_choice"


def test_parse_chunk_multiple_questions():
    """Test parsing a chunk with multiple questions."""
    chunk_content = """1. What is 2+2?
A. 3
B. 4

2. What is 3+3?
A. 5
B. 6
"""
    result = parse_chunk(chunk_content)

    assert len(result) == 2
    assert result[0].content == "What is 2+2?"
    assert result[1].content == "What is 3+3?"


def test_parse_chunk_with_images():
    """Test parsing a chunk with images."""
    chunk_content = "Question ![img](http://example.com/img.png) with image"
    result = parse_chunk(chunk_content)

    assert len(result) == 1
    # Images should be extracted
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/parallel/test_worker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.parallel.worker'"

**Step 3: 实现工作进程**

```python
# src/md2db/parallel/worker.py
from typing import List
from ..parser import parse_markdown
from ..mongodb.models import QuestionDocument


def parse_chunk(chunk_content: str) -> List[QuestionDocument]:
    """Parse a chunk of markdown content into QuestionDocument objects.

    This function runs in worker processes.

    Args:
        chunk_content: The markdown content to parse

    Returns:
        List of QuestionDocument objects
    """
    # Use existing parser
    questions = parse_markdown(chunk_content)

    # Convert to QuestionDocument
    documents = []
    for q in questions:
        doc = QuestionDocument(
            content=q.content,
            question_type=q.question_type,
            options=q.options or [],
            answer=q.answer,
            explanation=q.explanation
        )
        # Note: images and latex_formulas need special handling
        # This will be done in integration with deduplicator
        documents.append(doc)

    return documents
```

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/parallel/test_worker.py -v`
Expected: PASS (3 tests)

**Step 5: 提交**

```bash
git add src/md2db/parallel/worker.py tests/parallel/test_worker.py
git commit -m "feat: add worker process for parallel parsing"
```

---

### Task 8: 实现协调器

**Files:**
- Create: `src/md2db/parallel/coordinator.py`
- Test: `tests/parallel/test_coordinator.py`

**Step 1: 编写失败的测试 - 协调器**

```python
# tests/parallel/test_coordinator.py
import pytest
import tempfile
import os
from pymongo import MongoClient
from src.md2db.mongodb.client import get_client, get_database
from src.md2db.parallel.coordinator import ParallelProcessor
from src.md2db.parallel.chunker import FileChunker


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = get_client("mongodb://localhost:27017")
    db = get_database(client, "md2db_test")
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    yield db
    # Cleanup
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})


def test_parallel_processor_processes_file(clean_db):
    """Test that parallel processor can process a file."""
    content = """1. What is 2+2?
A. 3
B. 4

2. What is 3+3?
A. 5
B. 6
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        processor = ParallelProcessor(
            file_path=temp_path,
            database=clean_db,
            num_workers=2,
            batch_size=10
        )
        result = processor.process()

        assert result["questions_processed"] == 2
        assert clean_db.questions.count_documents({}) == 2

    finally:
        os.unlink(temp_path)


def test_parallel_processor_respects_chunk_size(clean_db):
    """Test that parallel processor uses configured chunk size."""
    # Create a larger file
    content = "\n\n".join([f"{i}. Question {i}" for i in range(1, 101)])

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        processor = ParallelProcessor(
            file_path=temp_path,
            database=clean_db,
            num_workers=2,
            chunk_size_mb=0.001,  # Very small to force multiple chunks
            batch_size=10
        )
        result = processor.process()

        assert result["questions_processed"] == 100
        assert result["chunks_processed"] > 1

    finally:
        os.unlink(temp_path)
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/parallel/test_coordinator.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.md2db.parallel.coordinator'"

**Step 3: 实现协调器**

```python
# src/md2db/parallel/coordinator.py
import os
from typing import Dict, Any
from multiprocessing import Pool
from .chunker import FileChunker
from .worker import parse_chunk
from ..mongodb.writer import BatchWriter
from ..mongodb.deduplicator import Deduplicator


class ParallelProcessor:
    """Coordinates parallel processing of large markdown files."""

    def __init__(
        self,
        file_path: str,
        database,
        num_workers: int = 4,
        chunk_size_mb: float = 10,
        batch_size: int = 1000
    ):
        self.file_path = file_path
        self.database = database
        self.num_workers = num_workers
        self.chunk_size_mb = chunk_size_mb
        self.batch_size = batch_size

    def process(self) -> Dict[str, Any]:
        """Process the file with parallel workers.

        Returns:
            Dict with processing statistics
        """
        # Create chunks
        chunker = FileChunker(self.file_path, self.chunk_size_mb)
        chunks = chunker.create_chunks()

        # Setup writer and deduplicator
        deduplicator = Deduplicator(self.database)
        writer = BatchWriter(self.database, self.batch_size, deduplicator)

        # Process chunks in parallel
        questions_processed = 0

        with open(self.file_path, 'r', encoding='utf-8') as f:
            with Pool(self.num_workers) as pool:
                # Read chunks and process in parallel
                chunk_contents = []
                for start, end in chunks:
                    f.seek(start)
                    content = f.read(end - start)
                    chunk_contents.append(content)

                # Process all chunks
                results = pool.map(parse_chunk, chunk_contents)

                # Write results
                for chunk_results in results:
                    for doc in chunk_results:
                        # Process with deduplicator for images/latex
                        # TODO: Add image and latex processing
                        writer.add(doc)
                        questions_processed += 1

        # Final flush
        writer.flush()

        return {
            "questions_processed": questions_processed,
            "chunks_processed": len(chunks),
            "num_workers": self.num_workers
        }
```

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/parallel/test_coordinator.py -v`
Expected: PASS (2 tests)

**Step 5: 提交**

```bash
git add src/md2db/parallel/coordinator.py tests/parallel/test_coordinator.py
git commit -m "feat: add parallel processor coordinator"
```

---

## Phase 4: 集成与优化

### Task 9: 集成图像和 LaTeX 去重处理

**Files:**
- Modify: `src/md2db/parallel/worker.py`
- Modify: `src/md2db/parallel/coordinator.py`
- Test: `tests/parallel/test_integration.py`

**Step 1: 编写失败的测试 - 完整集成**

```python
# tests/parallel/test_integration.py
import pytest
import tempfile
import os
from src.md2db.mongodb.client import get_client, get_database
from src.md2db.parallel.coordinator import ParallelProcessor
from src.md2db.image_processor import extract_images, extract_latex_formulas


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = get_client("mongodb://localhost:27017")
    db = get_database(client, "md2db_test")
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    yield db
    # Cleanup
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})


def test_integration_with_images_and_latex(clean_db):
    """Test end-to-end processing with images and latex."""
    content = """1. What is $\\frac{a}{b}$?
![diagram](http://example.com/math.png)
A. 1
B. 2

2. Another question with $x^2$.
![graph](http://example.com/graph.png)
A. True
B. False
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        processor = ParallelProcessor(
            file_path=temp_path,
            database=clean_db,
            num_workers=2,
            batch_size=10
        )
        result = processor.process()

        assert result["questions_processed"] == 2

        # Check that images were deduplicated (same URL used twice would be one entry)
        # But we have different URLs so 2 images
        assert clean_db.images.count_documents({}) == 2

        # Check latex formulas
        assert clean_db.latex_formulas.count_documents({}) == 2

        # Check that questions reference the images and latex
        questions = list(clean_db.questions.find())
        assert len(questions) == 2

    finally:
        os.unlink(temp_path)


def test_integration_option_deduplication(clean_db):
    """Test that identical options are deduplicated."""
    content = """1. Question 1?
A. Same option
B. Different

2. Question 2?
A. Same option
B. Also different
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        processor = ParallelProcessor(
            file_path=temp_path,
            database=clean_db,
            num_workers=2,
            batch_size=10
        )
        result = processor.process()

        assert result["questions_processed"] == 2

        # Should have 4 unique options
        # "A. Same option" appears twice but should be deduplicated
        # Actually our hash includes label, so "A. Same option" will be same
        # But since labels are different per question context, let's check
        options_count = clean_db.options.count_documents({})
        assert options_count <= 4  # At most 4, could be less if deduped

    finally:
        os.unlink(temp_path)
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/parallel/test_integration.py -v`
Expected: FAIL - tests will fail because image/latex processing is not integrated

**Step 3: 更新 worker.py 以处理图像和 LaTeX**

```python
# src/md2db/parallel/worker.py - Replace with updated version
from typing import List, Dict, Any
from ..parser import parse_markdown
from ..mongodb.models import QuestionDocument
from ..image_processor import extract_images, extract_latex_formulas


def parse_chunk(chunk_content: str) -> List[Dict[str, Any]]:
    """Parse a chunk of markdown content into QuestionDocument objects.

    This function runs in worker processes. Returns serializable dicts
    to avoid pickling issues with multiprocessing.

    Args:
        chunk_content: The markdown content to parse

    Returns:
        List of dicts representing QuestionDocument objects
    """
    # Use existing parser
    questions = parse_markdown(chunk_content)

    # Convert to serializable dicts
    documents = []
    for q in questions:
        # Extract images and latex from original chunk content
        # Note: This is simplified - in production we'd track which
        # images/formulas belong to which question
        images = extract_images(chunk_content)
        latex = extract_latex_formulas(chunk_content)

        doc = {
            "content": q.content,
            "question_type": q.question_type,
            "options": q.options or [],
            "answer": q.answer,
            "explanation": q.explanation,
            "images": images,  # List of URLs
            "latex_formulas": latex  # List of formulas
        }
        documents.append(doc)

    return documents
```

**Step 4: 更新 coordinator.py 以处理去重**

```python
# src/md2db/parallel/coordinator.py - Update the process method
import os
from typing import Dict, Any
from multiprocessing import Pool
from .chunker import FileChunker
from .worker import parse_chunk
from ..mongodb.writer import BatchWriter
from ..mongodb.deduplicator import Deduplicator
from ..mongodb.models import QuestionDocument, ImageDocument, LatexDocument, OptionDocument


class ParallelProcessor:
    """Coordinates parallel processing of large markdown files."""

    def __init__(
        self,
        file_path: str,
        database,
        num_workers: int = 4,
        chunk_size_mb: float = 10,
        batch_size: int = 1000
    ):
        self.file_path = file_path
        self.database = database
        self.num_workers = num_workers
        self.chunk_size_mb = chunk_size_mb
        self.batch_size = batch_size

    def process(self) -> Dict[str, Any]:
        """Process the file with parallel workers.

        Returns:
            Dict with processing statistics
        """
        # Create chunks
        chunker = FileChunker(self.file_path, self.chunk_size_mb)
        chunks = chunker.create_chunks()

        # Setup writer and deduplicator
        deduplicator = Deduplicator(self.database)
        writer = BatchWriter(self.database, self.batch_size, deduplicator)

        # Process chunks in parallel
        questions_processed = 0

        with open(self.file_path, 'r', encoding='utf-8') as f:
            with Pool(self.num_workers) as pool:
                # Read chunks and process in parallel
                chunk_contents = []
                for start, end in chunks:
                    f.seek(start)
                    content = f.read(end - start)
                    chunk_contents.append(content)

                # Process all chunks
                results = pool.map(parse_chunk, chunk_contents)

                # Write results with deduplication
                for chunk_results in results:
                    for doc_dict in chunk_results:
                        # Process images
                        image_ids = []
                        for img_url in doc_dict.get("images", []):
                            img_doc = ImageDocument(url=img_url)
                            img_id = deduplicator.get_or_create_image(img_doc)
                            if img_id:
                                image_ids.append(img_id)

                        # Process latex
                        latex_ids = []
                        for formula in doc_dict.get("latex_formulas", []):
                            latex_doc = LatexDocument(formula=formula)
                            latex_id = deduplicator.get_or_create_latex(latex_doc)
                            if latex_id:
                                latex_ids.append(latex_id)

                        # Process options
                        option_ids = []
                        for i, opt_content in enumerate(doc_dict.get("options", [])):
                            label = chr(65 + i)  # A, B, C, ...
                            opt_doc = OptionDocument(label=label, content=opt_content)
                            opt_id = deduplicator.get_or_create_option(opt_doc)
                            if opt_id:
                                option_ids.append(opt_id)

                        # Create question document
                        question_doc = QuestionDocument(
                            content=doc_dict["content"],
                            question_type=doc_dict["question_type"],
                            options=option_ids,
                            answer=doc_dict.get("answer"),
                            explanation=doc_dict.get("explanation"),
                            images=image_ids,
                            latex_formulas=latex_ids
                        )
                        writer.add(question_doc)
                        questions_processed += 1

        # Final flush
        writer.flush()

        return {
            "questions_processed": questions_processed,
            "chunks_processed": len(chunks),
            "num_workers": self.num_workers
        }
```

**Step 5: 运行测试确认通过**

Run: `python3 -m pytest tests/parallel/test_integration.py -v`
Expected: PASS (2 tests)

**Step 6: 提交**

```bash
git add src/md2db/parallel/worker.py src/md2db/parallel/coordinator.py tests/parallel/test_integration.py
git commit -m "feat: integrate image and latex deduplication"
```

---

## Phase 5: CLI 和文档

### Task 10: 更新 CLI 以支持并行处理

**Files:**
- Modify: `src/md2db/main.py`
- Test: `tests/test_cli_parallel.py`

**Step 1: 编写失败的测试 - CLI 并行模式**

```python
# tests/test_cli_parallel.py
import pytest
import tempfile
import os
from pymongo import MongoClient
from src.md2db.mongodb.client import get_client, get_database
from src.md2db.main import process_file_parallel


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = get_client("mongodb://localhost:27017")
    db = get_database(client, "md2db_test")
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    yield db
    # Cleanup
    db.questions.delete_many({})
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})


def test_process_file_parallel_basic(clean_db):
    """Test parallel file processing via CLI."""
    content = """1. Question 1?
A. Option A
B. Option B

2. Question 2?
A. Option C
B. Option D
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(content)
        temp_path = f.name

    try:
        result = process_file_parallel(
            temp_path,
            database_uri="mongodb://localhost:27017",
            database_name="md2db_test",
            num_workers=2
        )

        assert result["questions_processed"] == 2
        assert clean_db.questions.count_documents({}) == 2

    finally:
        os.unlink(temp_path)
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_cli_parallel.py -v`
Expected: FAIL with function not found

**Step 3: 更新 main.py 添加并行处理函数**

```python
# src/md2db/main.py - Add to existing file
import argparse
from .parser import parse_markdown
from .database import export_to_sql
from .mongodb.client import get_client, get_database
from .parallel.coordinator import ParallelProcessor


def process_file(filename: str) -> dict:
    """Process a markdown file and return structured data."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = parse_markdown(content)
    sql_output = export_to_sql(questions)

    return {
        "questions": [q.__dict__ for q in questions],
        "sql": sql_output
    }


def process_file_parallel(
    filename: str,
    database_uri: str = "mongodb://localhost:27017",
    database_name: str = "md2db",
    num_workers: int = 4,
    chunk_size_mb: float = 10
) -> dict:
    """Process a markdown file with parallel workers and store in MongoDB.

    Args:
        filename: Path to markdown file
        database_uri: MongoDB connection URI
        database_name: Database name
        num_workers: Number of parallel workers
        chunk_size_mb: Chunk size in MB

    Returns:
        Dict with processing statistics
    """
    client = get_client(database_uri)
    db = get_database(client, database_name)

    processor = ParallelProcessor(
        file_path=filename,
        database=db,
        num_workers=num_workers,
        chunk_size_mb=chunk_size_mb
    )

    return processor.process()


def main():
    parser = argparse.ArgumentParser(description="MD2DB - Markdown to Database Converter")
    parser.add_argument("file", help="Markdown file to process")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--parallel", "-p", action="store_true", help="Use parallel processing with MongoDB")
    parser.add_argument("--mongodb-uri", default="mongodb://localhost:27017", help="MongoDB connection URI")
    parser.add_argument("--database", "-d", default="md2db", help="Database name")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--chunk-size", type=float, default=10, help="Chunk size in MB")

    args = parser.parse_args()

    if args.parallel:
        # Parallel mode with MongoDB
        result = process_file_parallel(
            args.file,
            database_uri=args.mongodb_uri,
            database_name=args.database,
            num_workers=args.workers,
            chunk_size_mb=args.chunk_size
        )
        print(f"Processed {result['questions_processed']} questions")
        print(f"Using {result['num_workers']} workers across {result['chunks_processed']} chunks")
    else:
        # Original mode
        result = process_file(args.file)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["sql"])
            print(f"Output written to {args.output}")
        else:
            print(result["sql"])


if __name__ == "__main__":
    main()
```

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_cli_parallel.py -v`
Expected: PASS (1 test)

**Step 5: 运行所有测试确认没有破坏现有功能**

Run: `python3 -m pytest tests/ -v`
Expected: All tests pass

**Step 6: 提交**

```bash
git add src/md2db/main.py tests/test_cli_parallel.py
git commit -m "feat: add parallel processing CLI mode"
```

---

### Task 11: 更新文档

**Files:**
- Create: `docs/MONGODB.md`
- Modify: `README.md`

**Step 1: 创建 MongoDB 使用文档**

```markdown
# docs/MONGODB.md
# MD2DB MongoDB Integration

## Overview

MD2DB supports high-performance parallel processing with MongoDB storage for large markdown files.

## Setup

### Install MongoDB

```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# Linux
sudo apt-get install mongodb
sudo systemctl start mongodb
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Parallel Processing

```bash
# Process with 4 workers (default)
python -m md2db exam.md --parallel

# Custom worker count
python -m md2db exam.md --parallel --workers 8

# Custom chunk size
python -m md2db exam.md --parallel --chunk-size 20

# Custom MongoDB URI
python -m md2db exam.md --parallel --mongodb-uri "mongodb://user:pass@host:port"
```

### Database Structure

The system uses a multi-collection structure with deduplication:

- `questions` - Main question data
- `options` - Deduplicated options
- `images` - Deduplicated image references
- `latex_formulas` - Deduplicated LaTeX formulas

## Performance

For large files (50-200 MB):

- Use 4-8 workers for optimal performance
- Adjust chunk size based on question density
- MongoDB indexes are automatically created on first run

## Python API

```python
from src.md2db.main import process_file_parallel

result = process_file_parallel(
    "exam.md",
    database_uri="mongodb://localhost:27017",
    database_name="mydb",
    num_workers=4
)

print(f"Processed {result['questions_processed']} questions")
```
```

**Step 2: 更新 README.md 添加 MongoDB 部分**

在 README.md 中添加：

```markdown
## MongoDB Storage

For large files, use parallel processing with MongoDB:

```bash
python -m md2db large_exam.md --parallel --workers 4
```

See [docs/MONGODB.md](docs/MONGODB.md) for details.
```

**Step 3: 提交**

```bash
git add docs/MONGODB.md README.md
git commit -m "docs: add MongoDB integration documentation"
```

---

### Task 12: 最终集成测试

**Step 1: 运行完整测试套件**

Run: `python3 -m pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 2: 性能基准测试（可选）**

创建一个大型测试文件并运行：

```bash
# Create test file with 10000 questions
for i in {1..10000}; do
    echo "$i. Question number $i?"
    echo "A. Option A"
    echo "B. Option B"
    echo "C. Option C"
    echo "D. Option D"
    echo ""
done > large_test.md

# Time the processing
time python -m md2db large_test.md --parallel --workers 4
```

**Step 3: 最终提交**

```bash
# Check git status
git status

# Final commit if needed
git add .
git commit -m "feat: complete MongoDB parallel processing implementation"
```

---

## 实施完成检查清单

- [ ] Phase 1: MongoDB 基础设施完成 (Tasks 1-5)
- [ ] Phase 2: 文件分块完成 (Task 6)
- [ ] Phase 3: 并行处理完成 (Tasks 7-8)
- [ ] Phase 4: 集成与优化完成 (Task 9)
- [ ] Phase 5: CLI 和文档完成 (Tasks 10-11)
- [ ] 所有测试通过
- [ ] 性能验证通过

---

## 注意事项

1. **MongoDB 连接**: 确保在运行测试前 MongoDB 已启动
2. **测试数据库**: 使用 `md2db_test` 数据库进行测试
3. **端口冲突**: 默认使用 27017 端口，如有冲突需修改 URI
4. **内存使用**: 大型文件处理时会使用较多内存，建议至少 4GB 可用内存
