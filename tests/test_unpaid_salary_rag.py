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

def test_unpaid_salary_short_query():
    status_code, body = send_request("My employer has not paid my salary for two months.")
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for unpaid salary query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" not in explanation.lower()
    acts = [l.get("act", "") for l in laws]
    assert any("Wages" in a or "Industrial Relations" in a for a in acts)

def test_unpaid_salary_long_natural_query():
    long_query = (
        "My employer has not paid my salary for the last two months. "
        "I have repeatedly asked my employer about the pending salary, but they have not given me a clear response. "
        "I am working as a full-time employee and depend on this salary for my basic expenses. "
        "What legal rights do I have and what action can I take to recover my unpaid salary?"
    )
    status_code, body = send_request(long_query)
    assert status_code == 200
    laws = body.get("applicable_laws", [])
    assert len(laws) > 0, "Expected applicable laws for long unpaid salary query"
    explanation = body.get("rights_explanation", "")
    assert "could not find sufficiently relevant" not in explanation.lower()
    acts = [l.get("act", "") for l in laws]
    assert any("Wages" in a for a in acts)
