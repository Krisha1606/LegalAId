import pytest
import json
import urllib.request
import io
from pypdf import PdfReader

from phase10_multilingual.src.adapters.document_adapter import LegalDocumentAdapter, detect_document_type
from backend.document_generator import generate as generate_doc_fields, SUPPORTED_DOCUMENT_TYPES
from backend.pdf_generator import generate_pdf

BASE_URL = "http://127.0.0.1:8000"

def test_1_document_type_detection():
    # Labour query
    labour_analysis = {
        "normalized_text": "My employer has not paid my salary for two months.",
        "applicable_laws": [{"act": "The Code on Wages, 2019", "section": "Section 17"}]
    }
    assert detect_document_type(labour_analysis) == "labour_notice"

    # Consumer query
    consumer_analysis = {
        "normalized_text": "I was injured because of a defective product.",
        "applicable_laws": [{"act": "The Consumer Protection Act, 2019", "section": "Section 84"}]
    }
    assert detect_document_type(consumer_analysis) == "consumer_notice"

    # Tenant query
    tenant_analysis = {
        "normalized_text": "My landlord has not returned my security deposit.",
        "applicable_laws": [{"act": "Rent Control Act", "section": "Section 10"}]
    }
    assert detect_document_type(tenant_analysis) == "tenant_notice"

def test_2_adapter_and_template_generation_all_types():
    for doc_type in ["labour_notice", "consumer_notice", "tenant_notice"]:
        sample_analysis = {
            "normalized_text": f"Test factual problem for {doc_type}",
            "rights_explanation": "You have a legal right under Indian law to seek redressal.",
            "applicable_laws": [{"act": "Test Act", "section": "Section 1", "explanation": "Test explanation", "source": "https://india.gov.in"}],
            "recommended_actions": ["Preserve records", "Send notice"]
        }
        legal_json = LegalDocumentAdapter.to_legal_json(
            analysis_data=sample_analysis,
            document_type=doc_type,
            user_info={"name": "Test Client", "address": "New Delhi"},
            opposite_party={"name": "Test Respondent", "address": "Mumbai"}
        )
        assert legal_json["document_type"] == doc_type
        assert legal_json["user"]["name"] == "Test Client"
        
        doc_fields = generate_doc_fields(legal_json)
        assert doc_fields["document_type"] == doc_type
        assert "template_title" in doc_fields
        assert "subject" in doc_fields
        assert "opening" in doc_fields
        assert "closing" in doc_fields

        pdf_bytes = generate_pdf(doc_fields)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 2000
        
        # Verify PDF readability with PyPDF
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 1
        page_text = reader.pages[0].extract_text()
        assert "Test Client" in page_text
        assert "Test Respondent" in page_text

def test_3_api_post_generate_document():
    req_body = {
        "query": "My employer has not paid my salary for two months.",
        "analysis": {
            "normalized_text": "My employer has not paid my salary for two months.",
            "rights_explanation": "According to Section 17 of The Code on Wages, 2019, wages must be paid promptly.",
            "applicable_laws": [
                {
                    "act": "The Code on Wages, 2019",
                    "section": "Section 17",
                    "explanation": "Payment of wages and time limit",
                    "source": "https://labour.gov.in"
                }
            ],
            "recommended_actions": ["Preserve payslips", "Issue demand notice"]
        },
        "document_type": "labour_notice",
        "user_info": {"name": "Amit Verma", "address": "Sector 62, Noida"},
        "opposite_party": {"name": "Infosolutions Ltd.", "address": "Cyber City, Gurugram"}
    }
    
    data = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/documents/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert "id" in res
        assert res["type"] == "labour_notice"
        assert "Amit Verma" in res["content"]
        assert "Infosolutions Ltd." in res["content"]
        assert "The Code on Wages, 2019" in res["content"]
        
        doc_id = res["id"]
        
        # Test 4A: Download Original PDF
        download_req = urllib.request.Request(f"{BASE_URL}/api/documents/download/{doc_id}")
        with urllib.request.urlopen(download_req, timeout=10) as d_resp:
            assert d_resp.status == 200
            assert d_resp.headers.get("Content-Type") == "application/pdf"
            pdf_data = d_resp.read()
            assert pdf_data.startswith(b"%PDF-")
            
            reader = PdfReader(io.BytesIO(pdf_data))
            text = reader.pages[0].extract_text()
            assert "Amit Verma" in text
            assert "The Code on Wages, 2019" in text

        # Test 4B: Save / Update document content (PUT /api/documents/{id})
        updated_content = res["content"] + "\n\nCUSTOM CLAUSE: Immediate payment within 7 days required."
        put_req = urllib.request.Request(
            f"{BASE_URL}/api/documents/{doc_id}",
            data=json.dumps({"content": updated_content}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        with urllib.request.urlopen(put_req, timeout=10) as p_resp:
            assert p_resp.status == 200
            p_res = json.loads(p_resp.read().decode("utf-8"))
            assert p_res["id"] == doc_id
            assert "CUSTOM CLAUSE" in p_res["content"]

        # Test 4C: Download Regenerated PDF reflecting saved edits
        with urllib.request.urlopen(download_req, timeout=10) as d_resp2:
            assert d_resp2.status == 200
            pdf_data2 = d_resp2.read()
            assert pdf_data2.startswith(b"%PDF-")
            reader2 = PdfReader(io.BytesIO(pdf_data2))
            text2 = reader2.pages[0].extract_text()
            assert "CUSTOM CLAUSE" in text2

def test_5_api_post_generate_pdf_direct():
    payload = {
        "document_type": "consumer_notice",
        "user": {"name": "Pooja Hegde", "address": "Mumbai"},
        "opposite_party": {"name": "Retail Corp", "address": "Pune"},
        "issue": {"title": "Defective TV", "description": "TV screen broke on arrival", "amount": "Rs. 45000"},
        "facts": ["Ordered TV on 1st Aug", "Delivered damaged screen"],
        "rights": ["Consumer right to replacement"],
        "laws": [{"act": "Consumer Protection Act", "section": "Section 84", "title": "Section 84", "explanation": "Product Liability"}],
        "relief_requested": ["Full refund of Rs. 45000"]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/documents/generate-pdf",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "application/pdf"
        pdf_bytes = resp.read()
        assert pdf_bytes.startswith(b"%PDF-")
