import pytest
from fastapi.testclient import TestClient
from src.schemas.language import LanguageCode

def test_process_consumer_english_to_hindi(client: TestClient):
    response = client.post("/api/language/process", json={
        "text": "The seller refused to refund me for a defective phone.",
        "output_language": "hi"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["language"]["input"] == "en"
    assert data["language"]["output"] == "hi"
    assert "Consumer Protection Act, 2019" in data["applicable_laws"][0]["act"]
    assert "Section 35" in data["applicable_laws"][0]["section"]
    assert "[Hindi Translation of: The consumer has the right" in data["rights_explanation"]
    assert "शैक्षिक उद्देश्यों के लिए" in data["disclaimer"]

def test_process_labour_roman_hindi_to_english(client: TestClient):
    response = client.post("/api/language/process", json={
        "text": "Mere employer ne 2 mahine se salary nahi di",
        "output_language": "en"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["language"]["input"] == "roman_hi"
    assert data["language"]["output"] == "en"
    assert "Payment of Wages Act, 1936" in data["applicable_laws"][0]["act"]
    assert "My employer has not paid my salary." in data["normalized_text"]
    assert "does not constitute legal advice" in data["disclaimer"]

def test_document_translation(client: TestClient):
    response = client.post("/api/language/document", json={
        "document_type": "legal_notice",
        "source_language": "en",
        "target_language": "hi",
        "content": "The consumer may have rights. Under Section 35."
    })
    data = response.json()
    assert data["document"]["language"] == "hi"
    assert "Section 35" in data["document"]["content"] # Ensured by entity protector

def test_process_hindi_to_english(client: TestClient):
    response = client.post("/api/language/process", json={
        "text": "मेरे नियोक्ता ने मेरा वेतन नहीं दिया है।",
        "output_language": "en"
    })
    assert response.status_code == 200
    assert response.json()["language"]["input"] == "hi"
    assert response.json()["language"]["output"] == "en"

def test_process_hinglish_to_hindi(client: TestClient):
    response = client.post("/api/language/process", json={
        "text": "Mere landlord ne security deposit return nahi kiya.",
        "output_language": "hi"
    })
    assert response.status_code == 200
    assert response.json()["language"]["input"] == "roman_hi"
    assert response.json()["language"]["output"] == "hi"

def test_process_malformed_empty(client: TestClient):
    response = client.post("/api/language/process", json={
        "text": "   ",
        "output_language": "hi"
    })
    assert response.status_code == 400

def test_document_malformed_empty(client: TestClient):
    response = client.post("/api/language/document", json={
        "document_type": "legal_notice",
        "source_language": "en",
        "target_language": "hi",
        "content": "   "
    })
    assert response.status_code == 400

def test_process_entity_preservation(client: TestClient):
    response = client.post("/api/language/document", json={
        "document_type": "legal_notice",
        "source_language": "en",
        "target_language": "hi",
        "content": "Rahul Patel paid ₹30,000 on 15 July 2026 for 2 months."
    })
    assert response.status_code == 200
    content = response.json()["document"]["content"]
    assert "Rahul Patel" in content
    assert "₹30,000" in content
    assert "15 July 2026" in content
    assert "2" in content

from unittest.mock import patch

def test_translation_failure(client: TestClient):
    with patch("src.adapters.translation_provider.MockTranslationProvider.translate", side_effect=Exception("Translation service unavailable")):
        response = client.post("/api/language/document", json={
            "document_type": "legal_notice",
            "source_language": "en",
            "target_language": "hi",
            "content": "Valid content"
        })
        assert response.status_code == 503
        assert "Translation service unavailable" in response.json()["detail"]

def test_legal_engine_failure(client: TestClient):
    with patch("src.adapters.mock_legal_engine.MockLegalEngine.get_response", side_effect=Exception("Legal engine unavailable")):
        response = client.post("/api/language/process", json={
            "text": "Valid legal text",
            "output_language": "hi"
        })
        assert response.status_code == 503
        assert "Legal engine unavailable" in response.json()["detail"]
