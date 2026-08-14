import pytest

from src.chunker import Chunk, chunk_dataset, chunk_document
from src.data_loader import load_raw_legal_data
from src.normalizer import normalize_dataset, normalize_document


@pytest.fixture
def sample_doc():
    raw = {
        "id": "DUMMY-CONS-001",
        "domain": "Consumer",
        "issue": "Defective product replacement",
        "act": "Dummy Consumer Rights Act, 2024",
        "section": "Dummy Section 12",
        "section_title": "Right to Refund",
        "legal_text": "Where any goods sold to a consumer suffer from a manufacturing defect, the seller shall be liable to replace the item or issue a full monetary refund.",
        "plain_explanation": "You get a refund if product is defective.",
        "applicability": "Applies to retail items.",
        "jurisdiction": "Dummy National Forum",
        "source": "Dummy Repository",
        "source_url": "https://dummy.test/12",
        "verified": True,
        "is_dummy": True,
        "custom_key": "custom_value",
    }
    return normalize_document(raw)


def test_1_normal_document_produces_chunks(sample_doc):
    chunks = chunk_document(sample_doc)
    assert len(chunks) >= 1
    assert isinstance(chunks[0], Chunk)


def test_2_short_text_not_unnecessarily_split(sample_doc):
    chunks = chunk_document(sample_doc, chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].total_chunks == 1
    assert chunks[0].text == sample_doc.legal_text


def test_3_large_text_splits_into_multiple_chunks(sample_doc):
    long_text = "Sentence one. " * 30 + "Sentence two. " * 30
    raw = sample_doc.to_dict()
    raw["legal_text"] = long_text
    doc = normalize_document(raw)

    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=30)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.total_chunks == len(chunks)


def test_4_chunk_ids_are_unique(sample_doc):
    long_text = "First paragraph content. " * 20 + "\n\n" + "Second paragraph content. " * 20
    raw = sample_doc.to_dict()
    raw["legal_text"] = long_text
    doc = normalize_document(raw)

    chunks = chunk_document(doc, chunk_size=150, chunk_overlap=20)
    chunk_ids = [c.chunk_id for c in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert all(c.chunk_id.startswith(doc.id) for c in chunks)


def test_5_chunks_retain_parent_document_id(sample_doc):
    chunks = chunk_document(sample_doc)
    for c in chunks:
        assert c.document_id == sample_doc.id
        assert c.parent_document_id == sample_doc.id


def test_6_legal_metadata_preserved(sample_doc):
    chunks = chunk_document(sample_doc)
    c = chunks[0]
    assert c.domain == sample_doc.domain
    assert c.issue == sample_doc.issue
    assert c.act == sample_doc.act
    assert c.section == sample_doc.section
    assert c.section_title == sample_doc.section_title
    assert c.plain_explanation == sample_doc.plain_explanation
    assert c.applicability == sample_doc.applicability
    assert c.jurisdiction == sample_doc.jurisdiction
    assert c.source == sample_doc.source
    assert c.source_url == sample_doc.source_url
    assert c.verified == sample_doc.verified
    assert c.is_dummy == sample_doc.is_dummy


def test_7_extra_metadata_preserved(sample_doc):
    chunks = chunk_document(sample_doc)
    c = chunks[0]
    assert c.metadata.get("custom_key") == "custom_value"


def test_8_chunk_size_limits_respected(sample_doc):
    long_text = "Word " * 200
    raw = sample_doc.to_dict()
    raw["legal_text"] = long_text
    doc = normalize_document(raw)

    chunk_size = 150
    chunks = chunk_document(doc, chunk_size=chunk_size, chunk_overlap=20)
    for c in chunks:
        assert len(c.text) <= chunk_size + 50


def test_9_overlap_behaves_correctly(sample_doc):
    text = "Alpha beta gamma delta epsilon. Zeta eta theta iota kappa. Lambda mu nu xi omicron."
    raw = sample_doc.to_dict()
    raw["legal_text"] = text
    doc = normalize_document(raw)

    chunks = chunk_document(doc, chunk_size=40, chunk_overlap=15)
    assert len(chunks) > 1
    chunk_texts = [c.text for c in chunks]
    words_c1 = set(chunk_texts[0].split())
    words_c2 = set(chunk_texts[1].split())
    assert len(words_c1.intersection(words_c2)) > 0


def test_10_dataset_chunking():
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)

    assert len(chunks) >= len(docs)
    assert all(isinstance(c, Chunk) for c in chunks)


def test_11_empty_invalid_text_handling(sample_doc):
    raw = sample_doc.to_dict()
    raw["legal_text"] = "   "
    with pytest.raises(ValueError):
        normalize_document(raw)

    with pytest.raises(ValueError):
        chunk_document(sample_doc, chunk_size=0)

    with pytest.raises(ValueError):
        chunk_document(sample_doc, chunk_size=100, chunk_overlap=150)


def test_12_dummy_flag_preserved(sample_doc):
    chunks = chunk_document(sample_doc)
    assert chunks[0].is_dummy is True
