from fastapi.testclient import TestClient
import pytest

from phase10_multilingual.src.main import app
from phase10_multilingual.src.schemas.language import LanguageCode

client = TestClient(app)


def test_1_root_serves_frontend_html():
    """Verifies GET / serves index.html frontend UI with HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "LegalAId" in response.text
    assert "queryForm" in response.text


def test_2_api_process_english_query():
    """Verifies POST /api/language/process handles English queries through live RAG pipeline."""
    payload = {
        "text": "My landlord has not returned my security deposit.",
        "output_language": "en"
    }
    response = client.post("/api/language/process", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["language"]["input"] == "en"
    assert data["language"]["output"] == "en"
    assert len(data["rights_explanation"]) > 0
    assert "applicable_laws" in data
    assert "recommended_actions" in data
    assert "disclaimer" in data


def test_3_api_process_hindi_query():
    """Verifies POST /api/language/process handles Hindi Devanagari queries through RAG pipeline."""
    payload = {
        "text": "मेरे मकान मालिक ने मेरी सिक्योरिटी डिपॉजिट वापस नहीं की है।",
        "output_language": "hi"
    }
    response = client.post("/api/language/process", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["language"]["input"] == "hi"
    assert data["language"]["output"] == "hi"
    assert len(data["rights_explanation"]) > 0


def test_4_api_process_roman_hindi_query():
    """Verifies POST /api/language/process handles Roman Hindi / Hinglish queries."""
    payload = {
        "text": "Mere landlord ne mera security deposit wapas nahi kiya.",
        "output_language": "en"
    }
    response = client.post("/api/language/process", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["language"]["input"] == "roman_hi"
    assert data["normalized_text"] == "My landlord has not returned my security deposit."


def test_5_api_process_empty_query_validation():
    """Verifies POST /api/language/process rejects empty queries with HTTP 400 Bad Request."""
    payload = {
        "text": "   ",
        "output_language": "en"
    }
    response = client.post("/api/language/process", json=payload)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()
