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
    hash: str = field(default=None)

    def __post_init__(self):
        if self.hash is None:
            combined = f"{self.label}:{self.content}"
            self.hash = generate_hash(combined)


@dataclass
class ImageDocument:
    """MongoDB document for images."""
    url: str
    alt: str = ""
    hash: str = field(default=None)

    def __post_init__(self):
        if self.hash is None:
            self.hash = generate_hash(self.url)


@dataclass
class LatexDocument:
    """MongoDB document for LaTeX formulas."""
    formula: str
    hash: str = field(default=None)

    def __post_init__(self):
        if self.hash is None:
            self.hash = generate_hash(self.formula)


@dataclass
class QuestionDocument:
    """MongoDB document for questions."""
    content: str
    question_type: str
    options: List[str] = field(default_factory=list)
    answer: Optional[str] = None
    explanation: Optional[str] = None
    images: List[str] = field(default_factory=list)
    latex_formulas: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
