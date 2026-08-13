import pytest

from src.data_loader import load_raw_legal_data
from src.normalizer import (
    NormalizedLegalDocument,
    normalize_dataset,
    normalize_document,
)


def test_normalize_valid_document():
    """Test that a complete valid raw record normalizes correctly."""
    raw = {
        "id": "DUMMY-CONS-001",
        "domain": "Consumer",
        "issue": "Defective product replacement",
        "act": "Dummy Consumer Rights Act, 2024",
        "section": "Dummy Section 12",
        "section_title": "Right to Refund",
        "legal_text": "Seller must replace defective item.",
        "plain_explanation": "You get a refund if product is defective.",
        "applicability": "Applies to retail items.",
        "jurisdiction": "Dummy National Forum",
        "source": "Dummy Repository",
        "source_url": "https://dummy.test/12",
        "verified": True,
        "is_dummy": True,
    }

    doc = normalize_document(raw)

    assert isinstance(doc, NormalizedLegalDocument)
    assert doc.id == "DUMMY-CONS-001"
    assert doc.domain == "Consumer"
    assert doc.issue == "Defective product replacement"
    assert doc.act == "Dummy Consumer Rights Act, 2024"
    assert doc.section == "Dummy Section 12"
    assert doc.section_title == "Right to Refund"
    assert doc.legal_text == "Seller must replace defective item."
    assert doc.plain_explanation == "You get a refund if product is defective."
    assert doc.applicability == "Applies to retail items."
    assert doc.jurisdiction == "Dummy National Forum"
    assert doc.source == "Dummy Repository"
    assert doc.source_url == "https://dummy.test/12"
    assert doc.verified is True
    assert doc.is_dummy is True
    assert doc.metadata == {}


def test_required_fields_preserved():
    """Test that only required fields are necessary and all preserved."""
    minimal_raw = {
        "id": "MIN-001",
        "domain": "Labour",
        "issue": "Wages",
        "act": "Dummy Labour Act",
        "section": "Sec 1",
        "section_title": "Scope",
        "legal_text": "Wages must be paid.",
    }

    doc = normalize_document(minimal_raw)

    assert doc.id == "MIN-001"
    assert doc.domain == "Labour"
    assert doc.issue == "Wages"
    assert doc.act == "Dummy Labour Act"
    assert doc.section == "Sec 1"
    assert doc.section_title == "Scope"
    assert doc.legal_text == "Wages must be paid."
    # Optional fields should be preserved as None (not invented)
    assert doc.plain_explanation is None
    assert doc.applicability is None
    assert doc.jurisdiction is None
    assert doc.source is None
    assert doc.source_url is None
    assert doc.verified is None
    assert doc.is_dummy is None


def test_extra_metadata_preserved():
    """Test that arbitrary unknown/extra fields are preserved inside metadata."""
    raw_with_extras = {
        "id": "META-001",
        "domain": "Tenant/Rental",
        "issue": "Deposit",
        "act": "Dummy Tenancy Act",
        "section": "Sec 8",
        "section_title": "Deposit Cap",
        "legal_text": "Deposit max 2 months.",
        "custom_tag": "high_priority",
        "effective_year": 2024,
        "metadata": {"internal_code": "TEN_DEP_08"},
    }

    doc = normalize_document(raw_with_extras)

    assert doc.metadata.get("custom_tag") == "high_priority"
    assert doc.metadata.get("effective_year") == 2024
    assert doc.metadata.get("internal_code") == "TEN_DEP_08"


def test_missing_required_fields():
    """Test that missing required fields raise a ValueError."""
    invalid_raw = {
        "id": "INVALID-001",
        "domain": "Consumer",
        # Missing 'issue', 'act', 'section', 'section_title', 'legal_text'
    }

    with pytest.raises(ValueError) as exc_info:
        normalize_document(invalid_raw)

    err_msg = str(exc_info.value)
    assert "Missing or empty required field(s)" in err_msg
    assert "issue" in err_msg
    assert "act" in err_msg


def test_integration_load_and_normalize():
    """Test loading dummy dataset and normalizing all records successfully."""
    raw_records = load_raw_legal_data()
    assert len(raw_records) >= 15

    normalized_docs = normalize_dataset(raw_records)
    assert len(normalized_docs) == len(raw_records)

    for doc in normalized_docs:
        assert doc.id
        assert doc.domain.lower() in [
            "consumer",
            "labour",
            "tenant/rental",
            "tenant",
            "tenant_property",
        ]
        assert doc.legal_text
