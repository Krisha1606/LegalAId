import pytest
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/language/process"

def send_request(text: str, output_language: str = "en"):
    payload = {"text": text, "output_language": output_language}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return resp.status, body

def test_landlord_unlawful_rent_query():
    status_code, body = send_request("My landlord is charging rent in excess of the agreed standard rent.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for unlawful standard rent query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" not in explanation.lower()
    acts = [l.get("act", "") for l in laws]
    assert any("Rent" in a or "Transfer of Property" in a for a in acts)

def test_landlord_essential_supply_cutoff():
    status_code, body = send_request("My landlord cut off the electricity and water supply to my rented apartment. What legal action can I take?")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for essential supply cutoff query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" not in explanation.lower()
    acts = [l.get("act", "") for l in laws]
    assert any("Rent" in a for a in acts)

def test_security_deposit_gap_safely_rejected():
    status_code, body = send_request("My landlord has not returned my security deposit.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) == 0, "Expected 0 laws since security deposit statutory provisions are not in current KB"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" in explanation.lower()
