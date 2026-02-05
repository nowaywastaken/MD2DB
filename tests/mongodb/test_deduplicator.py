import pytest
from pymongo import MongoClient
from src.md2db.mongodb.deduplicator import Deduplicator
from src.md2db.mongodb.models import OptionDocument, ImageDocument, LatexDocument


@pytest.fixture
def clean_db():
    """Provide a clean database for testing."""
    client = MongoClient("mongodb://localhost:27017")
    db = client["md2db_test"]
    # Clean up before test
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    yield db
    # Clean up after test
    db.options.delete_many({})
    db.images.delete_many({})
    db.latex_formulas.delete_many({})
    client.close()


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


def test_deduplicator_get_or_create_image_existing(clean_db):
    dedup = Deduplicator(clean_db)
    image = ImageDocument(url="http://example.com/img.png")
    id1 = dedup.get_or_create_image(image)
    id2 = dedup.get_or_create_image(image)
    assert id1 == id2
    assert clean_db.images.count_documents({}) == 1


def test_deduplicator_get_or_create_latex_new(clean_db):
    dedup = Deduplicator(clean_db)
    latex = LatexDocument(formula="\\frac{a}{b}")
    result_id = dedup.get_or_create_latex(latex)
    assert result_id is not None
    assert clean_db.latex_formulas.count_documents({}) == 1


def test_deduplicator_get_or_create_latex_existing(clean_db):
    dedup = Deduplicator(clean_db)
    latex = LatexDocument(formula="\\frac{a}{b}")
    id1 = dedup.get_or_create_latex(latex)
    id2 = dedup.get_or_create_latex(latex)
    assert id1 == id2
    assert clean_db.latex_formulas.count_documents({}) == 1
