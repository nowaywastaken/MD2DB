from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Question:
    content: str
    question_type: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    images: Optional[List[str]] = None
    latex_formulas: Optional[List[str]] = None