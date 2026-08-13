from pathlib import Path

from src.data_loader import load_pdf_text, load_raw_legal_data
from src.normalizer import PERSON1_REQUIRED_FIELDS, validate_knowledge_base_record

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_PATH = PROJECT_ROOT / "data" / "legal_knowledge_base.json"
PDF_DIR = PROJECT_ROOT / "data" / "pdfs"


def test_json_validity_and_load():
    """Verify that legal_knowledge_base.json exists and loads as valid JSON."""
    assert KB_PATH.is_file(), f"Dataset file missing at {KB_PATH}"
    records = load_raw_legal_data(KB_PATH)
    assert isinstance(records, list)
    assert len(records) > 0


def test_schema_and_required_14_fields():
    """Verify all 14 required Person 1 fields exist in every generated record."""
    records = load_raw_legal_data(KB_PATH)
    for rec in records:
        errs = validate_knowledge_base_record(rec)
        assert not errs, f"Validation failure in {rec.get('section', 'unknown')}: {errs}"
        for req_field in PERSON1_REQUIRED_FIELDS:
            assert req_field in rec, (
                f"Missing required field '{req_field}' in record {rec.get('section')}"
            )


def test_domain_validity():
    """Verify domain is strictly one of consumer, labour, tenant_property."""
    valid_domains = {"consumer", "labour", "tenant_property"}
    records = load_raw_legal_data(KB_PATH)
    for rec in records:
        assert rec["domain"] in valid_domains, (
            f"Invalid domain '{rec['domain']}' in record {rec.get('section')}"
        )


def test_pdf_extraction_sample():
    """Verify text extraction from sample official PDF works and returns non-empty text."""
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    assert len(pdf_files) > 0, "No PDF files found in data/pdfs"

    sample_pdf = pdf_files[0]
    extracted = load_pdf_text(sample_pdf)
    assert isinstance(extracted, str)
    assert len(extracted.strip()) > 50


def test_cross_domain_and_act_consistency():
    """Verify Act metadata consistency and no cross-domain or cross-Act misassignments."""
    records = load_raw_legal_data(KB_PATH)

    act_domain_map = {
        "The Consumer Protection Act, 2019": "consumer",
        "Consumer Protection (E-Commerce) Rules, 2020": "consumer",
        "The Code on Wages, 2019": "labour",
        "The Industrial Relations Code, 2020": "labour",
        "The Code on Social Security, 2020": "labour",
        "The Occupational Safety, Health and Working Conditions Code, 2020": "labour",
        "The Transfer of Property Act, 1882": "tenant_property",
        "The Registration Act, 1908": "tenant_property",
        "The Specific Relief Act, 1963": "tenant_property",
        "The Bombay Rents, Hotel and Lodging House Rates Control Act, 1947": "tenant_property",
    }

    for rec in records:
        act = rec["act_name"]
        domain = rec["domain"]

        if act in act_domain_map:
            assert domain == act_domain_map[act], (
                f"Cross-domain misassignment: Act '{act}' has domain '{domain}', expected '{act_domain_map[act]}'"
            )

        assert rec["act_name"].strip() != "", f"Empty act_name in record {rec}"
        assert rec["legal_text"].strip() != "", f"Empty legal_text in record {rec['section']}"
        assert rec["plain_summary"].strip() != "", f"Empty plain_summary in record {rec['section']}"
        assert isinstance(rec["keywords"], list) and len(rec["keywords"]) > 0


def test_representative_records():
    """Verify representative records from each domain have correct structure and non-empty content."""
    records = load_raw_legal_data(KB_PATH)

    repr_checks = [
        # CONSUMER
        ("The Consumer Protection Act, 2019", "consumer"),
        ("Consumer Protection (E-Commerce) Rules, 2020", "consumer"),
        # LABOUR
        ("The Code on Wages, 2019", "labour"),
        ("The Industrial Relations Code, 2020", "labour"),
        ("The Code on Social Security, 2020", "labour"),
        ("The Occupational Safety, Health and Working Conditions Code, 2020", "labour"),
        # TENANT/PROPERTY
        ("The Transfer of Property Act, 1882", "tenant_property"),
        ("The Registration Act, 1908", "tenant_property"),
        ("The Specific Relief Act, 1963", "tenant_property"),
        ("The Bombay Rents, Hotel and Lodging House Rates Control Act, 1947", "tenant_property"),
    ]

    for act_name, expected_domain in repr_checks:
        matches = [r for r in records if r["act_name"] == act_name]
        assert len(matches) > 0, f"No records found for representative Act: {act_name}"

        sample_rec = matches[0]
        assert sample_rec["domain"] == expected_domain
        assert sample_rec["act_name"] == act_name
        assert sample_rec["act_number"] != ""
        assert isinstance(sample_rec["year"], int)
        assert sample_rec["section"] != ""
        assert "chapter" in sample_rec
        assert len(sample_rec["legal_text"].strip()) > 0
        assert len(sample_rec["plain_summary"].strip()) > 0
        assert len(sample_rec["keywords"]) > 0

    # Specific check for Consumer definition (Section 2(7))
    sec27_matches = [
        r
        for r in records
        if r["act_name"] == "The Consumer Protection Act, 2019" and "2(7)" in r["section"]
    ]
    assert len(sec27_matches) > 0, "Consumer definition Section 2(7) not found in dataset"
    rec27 = sec27_matches[0]
    assert rec27["domain"] == "consumer"
    assert "consumer" in rec27["plain_summary"].lower() or "buys" in rec27["plain_summary"].lower()
