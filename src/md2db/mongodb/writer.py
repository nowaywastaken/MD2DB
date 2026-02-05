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
        self.db.questions.create_index([("created_at", -1)])

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
