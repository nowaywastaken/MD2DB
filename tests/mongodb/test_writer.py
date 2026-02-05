import pytest
from pymongo import MongoClient
from src.md2db.mongodb.writer import BatchWriter
from src.md2db.mongodb.models import QuestionDocument


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = MongoClient("mongodb://localhost:27017")
    db = client["md2db_test"]
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
    client.close()


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


def test_batch_writer_handles_empty_buffer(clean_db):
    writer = BatchWriter(clean_db, batch_size=10, deduplicator=None)
    writer.flush()  # Should not raise error
    assert clean_db.questions.count_documents({}) == 0
