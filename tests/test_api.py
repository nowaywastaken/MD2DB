import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_parse_endpoint():
    """Test the parse endpoint."""
    from fastapi.testclient import TestClient
    from md2db.api import app

    client = TestClient(app)
    response = client.post("/parse", json={"markdown": "What is 2+2?"})
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) == 1
    assert data["questions"][0]["content"] == "What is 2+2?"

def test_health_endpoint():
    """Test the health check endpoint."""
    from fastapi.testclient import TestClient
    from md2db.api import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"