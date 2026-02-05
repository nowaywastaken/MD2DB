from typing import Optional
from pymongo.database import Database
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
