import pytest
import urllib.request
import json

def test_multilingual_output_hindi():
    """Test A: Input English, Output Hindi produces real Hindi without placeholder."""
    query = "My employer is paying me less than the minimum wage prescribed by law. What are my legal rights and what action can I take?"
    payload = {
        "text": query,
        "input_language": "en",
        "output_language": "hi"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/language/process",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("language", {}).get("output") == "hi"
        
        rights_exp = data.get("rights_explanation", "")
        # Must not contain placeholder
        assert "[Hindi Translation of:" not in rights_exp
        assert "_X_ENT_" not in rights_exp
        assert "__PROTECTED_" not in rights_exp
        
        # Must contain Hindi characters
        has_hindi = any("\u0900" <= c <= "\u097f" for c in rights_exp)
        assert has_hindi, f"Expected Hindi characters in rights_explanation: {rights_exp[:100]}"
        
        # Recommended actions must also be in Hindi without placeholder
        actions = data.get("recommended_actions", [])
        assert len(actions) > 0
        for act in actions:
            assert "[Hindi Translation of:" not in act

def test_multilingual_output_english():
    """Test B: Input English, Output English produces standard English response."""
    query = "My employer is paying me less than the minimum wage prescribed by law. What are my legal rights and what action can I take?"
    payload = {
        "text": query,
        "input_language": "en",
        "output_language": "en"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/language/process",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("language", {}).get("output") == "en"
        
        rights_exp = data.get("rights_explanation", "")
        assert "[Hindi Translation of:" not in rights_exp
        # Must NOT contain Devanagari script in English mode
        has_hindi = any("\u0900" <= c <= "\u097f" for c in rights_exp)
        assert not has_hindi, "English response should not contain Devanagari characters"
