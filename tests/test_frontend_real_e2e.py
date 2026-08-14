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

def test_q1_unpaid_salary_real_http():
    status_code, body = send_request("My employer has not paid my salary for two months.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for unpaid salary query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" not in explanation.lower()
    acts = [l.get("act", "") for l in laws]
    assert any("Wages" in a or "Industrial Relations" in a for a in acts)

def test_q2_terminated_without_wages_real_http():
    status_code, body = send_request("My employer terminated me without paying my wages.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for terminated without wages query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" not in explanation.lower()

def test_q3_defective_product_real_http():
    status_code, body = send_request("I was injured because of a defective product.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for defective product query"
    acts = [l.get("act", "") for l in laws]
    assert any("Consumer Protection" in a for a in acts)

def test_q4_security_deposit_insufficient_retrieval_real_http():
    status_code, body = send_request("My landlord has not returned my security deposit.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) == 0, "Expected 0 applicable laws for security deposit coverage gap"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" in explanation.lower()

def test_q5_chocolate_cake_non_legal_real_http():
    status_code, body = send_request("What is the recipe for baking a chocolate cake?")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) == 0, "Expected 0 applicable laws for out-of-domain recipe query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" in explanation.lower()
