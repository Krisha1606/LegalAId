import numpy as np
import pytest

from src.chunker import chunk_document
from src.data_loader import load_raw_legal_data
from src.embedder import EmbeddedChunk, LegalEmbedder, build_embedding_text
from src.normalizer import normalize_dataset, normalize_document


@pytest.fixture(scope="module")
def embedder():
    return LegalEmbedder()


@pytest.fixture
def sample_chunk():
    raw = {
        "id": "DUMMY-CONS-001",
        "domain": "Consumer",
        "issue": "Defective product replacement",
        "act": "Dummy Consumer Rights Act, 2024",
        "section": "Dummy Section 12",
        "section_title": "Right to Refund",
        "legal_text": "Where any goods sold to a consumer suffer from a manufacturing defect, the seller shall replace the item.",
        "plain_explanation": "You get a refund if product is defective.",
        "applicability": "Applies to retail items.",
        "jurisdiction": "Dummy National Forum",
        "source": "Dummy Repository",
        "source_url": "https://dummy.test/12",
        "verified": True,
        "is_dummy": True,
    }
    doc = normalize_document(raw)
    chunks = chunk_document(doc)
    return chunks[0]


def test_1_model_loads_successfully(embedder):
    assert embedder is not None
    assert isinstance(embedder.embedding_dimension, int)
    assert embedder.embedding_dimension > 0


def test_2_build_embedding_text_contains_context(sample_chunk):
    text = build_embedding_text(sample_chunk)
    assert "Act: Dummy Consumer Rights Act, 2024" in text
    assert "Section: Dummy Section 12" in text
    assert "Section Title: Right to Refund" in text
    assert "Domain: Consumer" in text
    assert "Issue: Defective product replacement" in text
    assert "Applicability: Applies to retail items." in text
    assert "Legal Text: Where any goods sold" in text


def test_3_missing_optional_metadata_handled(sample_chunk):
    sample_chunk.applicability = None
    text = build_embedding_text(sample_chunk)
    assert "Act: Dummy Consumer Rights Act, 2024" in text
    assert "Applicability:" not in text


def test_4_embed_chunk_produces_valid_embedded_chunk(embedder, sample_chunk):
    ec = embedder.embed_chunk(sample_chunk)
    assert isinstance(ec, EmbeddedChunk)
    assert ec.chunk_id == sample_chunk.chunk_id
    assert ec.document_id == sample_chunk.document_id
    assert isinstance(ec.embedding, np.ndarray)


def test_5_vector_dtype_is_float32(embedder, sample_chunk):
    ec = embedder.embed_chunk(sample_chunk)
    assert ec.embedding.dtype == np.float32


def test_6_vector_dimension_matches_model(embedder, sample_chunk):
    ec = embedder.embed_chunk(sample_chunk)
    assert ec.embedding.shape == (embedder.embedding_dimension,)


def test_7_embed_chunks_batch_shape(embedder):
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = [c for d in docs for c in chunk_document(d)]

    embedded_chunks = embedder.embed_chunks(chunks)
    assert len(embedded_chunks) == len(chunks)

    matrix = np.array([ec.embedding for ec in embedded_chunks])
    assert matrix.shape == (len(chunks), embedder.embedding_dimension)
    assert matrix.dtype == np.float32


def test_8_embed_query_dimension(embedder):
    query_vec = embedder.embed_query("Defective product refund request")
    assert isinstance(query_vec, np.ndarray)
    assert query_vec.dtype == np.float32
    assert query_vec.shape == (embedder.embedding_dimension,)


def test_9_query_embedding_determinism(embedder):
    q = "Tenant security deposit refund terms"
    vec1 = embedder.embed_query(q)
    vec2 = embedder.embed_query(q)
    assert np.allclose(vec1, vec2, atol=1e-6)


def test_10_batch_order_preservation(embedder):
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = [c for d in docs[:5] for c in chunk_document(d)]

    embedded = embedder.embed_chunks(chunks)
    for i, c in enumerate(chunks):
        assert embedded[i].chunk_id == c.chunk_id
        assert embedded[i].document_id == c.document_id


def test_11_traceability_association(embedder, sample_chunk):
    ec = embedder.embed_chunk(sample_chunk)
    assert ec.chunk.act == sample_chunk.act
    assert ec.chunk.section == sample_chunk.section
    assert ec.chunk.source == sample_chunk.source


def test_12_empty_invalid_input_handling(embedder):
    with pytest.raises(ValueError):
        embedder.embed_query("   ")

    with pytest.raises(ValueError):
        embedder.embed_text("")


def test_13_dummy_flag_and_metadata_accessible(embedder, sample_chunk):
    ec = embedder.embed_chunk(sample_chunk)
    assert ec.chunk.is_dummy is True


def test_14_original_chunk_text_unmodified(embedder, sample_chunk):
    original_text = str(sample_chunk.text)
    embedder.embed_chunk(sample_chunk)
    assert sample_chunk.text == original_text


def test_15_semantic_sanity_test(embedder):
    """Sanity test verifying that embedding space captures basic semantic differences."""
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)

    cons_doc = next(d for d in docs if d.id == "DUMMY-CONS-001")
    ten_doc = next(d for d in docs if d.id == "DUMMY-TEN-001")

    cons_chunk = chunk_document(cons_doc)[0]
    ten_chunk = chunk_document(ten_doc)[0]

    ec_cons = embedder.embed_chunk(cons_chunk)
    ec_ten = embedder.embed_chunk(ten_chunk)

    query_cons = "I bought a defective product and the seller refuses to issue a refund."
    query_ten = "My landlord has not returned my rental security deposit after moving out."

    q_cons_vec = embedder.embed_query(query_cons)
    q_ten_vec = embedder.embed_query(query_ten)

    sim_cons_query_to_cons_chunk = float(np.dot(q_cons_vec, ec_cons.embedding))
    sim_cons_query_to_ten_chunk = float(np.dot(q_cons_vec, ec_ten.embedding))

    sim_ten_query_to_ten_chunk = float(np.dot(q_ten_vec, ec_ten.embedding))
    sim_ten_query_to_cons_chunk = float(np.dot(q_ten_vec, ec_cons.embedding))

    assert sim_cons_query_to_cons_chunk > sim_cons_query_to_ten_chunk
    assert sim_ten_query_to_ten_chunk > sim_ten_query_to_cons_chunk
