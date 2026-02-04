from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from .parser import parse_markdown
from .models import Question

app = FastAPI(title="MD2DB API", version="0.1.0")

class ParseRequest(BaseModel):
    markdown: str

class ParseResponse(BaseModel):
    questions: List[dict]

@app.post("/parse", response_model=ParseResponse)
def parse_markdown_endpoint(request: ParseRequest):
    """Parse markdown content and return structured questions."""
    questions = parse_markdown(request.markdown)
    return {"questions": [question.__dict__ for question in questions]}

@app.get("/health")
def health_check():
    return {"status": "healthy"}