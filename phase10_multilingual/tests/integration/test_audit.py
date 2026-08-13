import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.schemas.language import LanguageCode

client = TestClient(app)

def test_language_detection_fallback():
    # Test English input
    res = client.post("/api/language/process", json={"text": "Hello, I need legal help.", "output_language": "en"})
    assert res.status_code == 200
    assert res.json()["language"]["input"] == "en"

    # Test unsupported/unknown language (falls back to English in mock, handled safely)
    res = client.post("/api/language/process", json={"text": "xyz abc", "output_language": "en"})
    assert res.status_code == 200
    assert res.json()["language"]["input"] == "en"

def test_input_normalization_preserves_meaning():
    # "Landlord is threatening to remove me"
    # Using mock normalizer logic (we'll just ensure it returns standard text and mock engine handles it)
    res = client.post("/api/language/process", json={"text": "Mere landlord ne deposit", "output_language": "en"})
    assert res.status_code == 200
    assert "My landlord has not returned my security deposit." in res.json()["normalized_text"]

def test_protected_entities_coverage():
    # Test URLs, Case numbers, Companies, Addresses
    content = "Email test@test.com at ABC Company. See https://example.com. Case No. 123/45. Address 12 Main St."
    res = client.post("/api/language/document", json={
        "document_type": "legal_notice",
        "source_language": "en",
        "target_language": "hi",
        "content": content
    })
    assert res.status_code == 200
    doc_content = res.json()["document"]["content"]
    assert "test@test.com" in doc_content
    assert "ABC Company" in doc_content
    assert "https://example.com" in doc_content
    assert "Case No. 123/45" in doc_content
    assert "12 Main St" in doc_content

def test_disclaimer_preservation():
    res_en = client.post("/api/language/process", json={"text": "salary", "output_language": "en"})
    assert "does not constitute legal advice" in res_en.json()["disclaimer"]

    res_hi = client.post("/api/language/process", json={"text": "salary", "output_language": "hi"})
    assert "शैक्षिक उद्देश्यों के लिए" in res_hi.json()["disclaimer"]

def test_output_language_combinations():
    combos = [
        ("en", "en"), ("en", "hi"),
        ("hi", "en"), ("hi", "hi")
    ]
    texts = {
        "en": "My employer has not paid my salary.",
        "hi": "मेरे नियोक्ता ने मेरा वेतन नहीं दिया है।"
    }
    
    for in_lang, out_lang in combos:
        res = client.post("/api/language/process", json={
            "text": texts[in_lang],
            "output_language": out_lang
        })
        assert res.status_code == 200
        assert res.json()["language"]["output"] == out_lang

def test_unicode_hindi_strings():
    hindi_text = "आपके अधिकार कानूनी नोटिस लागू कानून धारा उपभोक्ता नियोक्ता किरायेदार मकान मालिक"
    res = client.post("/api/language/document", json={
        "document_type": "legal_notice",
        "source_language": "hi",
        "target_language": "en",
        "content": hindi_text
    })
    assert res.status_code == 200
    assert hindi_text in res.json()["document"]["content"] # mock translates to "[Hindi Translation of: ...]" so unicode is preserved

def test_api_security_max_length():
    # > 5000 chars should fail validation
    long_text = "A" * 5001
    res = client.post("/api/language/process", json={"text": long_text, "output_language": "en"})
    assert res.status_code == 422 # FastAPI validation error

def test_api_invalid_language_code():
    res = client.post("/api/language/process", json={"text": "valid", "output_language": "french"})
    assert res.status_code == 422 # Pydantic Enum validation failure

def test_document_same_language():
    res = client.post("/api/language/document", json={
        "document_type": "notice",
        "source_language": "en",
        "target_language": "en",
        "content": "No change needed"
    })
    assert res.status_code == 200
    assert res.json()["document"]["content"] == "No change needed"
