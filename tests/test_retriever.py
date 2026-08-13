import numpy as np
import pytest

from src.chunker import chunk_dataset
from src.data_loader import load_raw_legal_data
from src.embedder import LegalEmbedder
from src.normalizer import normalize_dataset
from src.retriever import LegalRetriever, RetrievalResult
from src.vector_store import FAISSVectorStore


@pytest.fixture(scope="module")
def prepared_retriever(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("retriever_test_store")
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)
    embedder = LegalEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks)

    store = FAISSVectorStore(dir_path=tmp_dir)
    store.build_index(embedded_chunks)
    store.save()

    return LegalRetriever(embedder=embedder, vector_store=store)


def test_1_retriever_initializes_successfully(prepared_retriever):
    assert prepared_retriever is not None
    assert prepared_retriever.vector_store.ntotal > 0


def test_2_query_embedded_successfully(prepared_retriever):
    q_vec = prepared_retriever.embedder.embed_query("Defective mobile phone refund")
    assert isinstance(q_vec, np.ndarray)


def test_3_query_vector_dimension_matches_faiss(prepared_retriever):
    q_vec = prepared_retriever.embedder.embed_query("Defective mobile phone refund")
    assert q_vec.shape[0] == prepared_retriever.vector_store.dimension


def test_4_retrieval_returns_ranked_results(prepared_retriever):
    res = prepared_retriever.retrieve("I bought a defective product and need a refund")
    assert isinstance(res, RetrievalResult)
    assert len(res.candidates) > 0
    assert res.candidates[0].rank == 1


def test_5_results_contain_scores(prepared_retriever):
    res = prepared_retriever.retrieve("Unpaid salary for two months")
    assert all(isinstance(c.score, float) for c in res.candidates)


def test_6_results_preserve_chunk_ids(prepared_retriever):
    res = prepared_retriever.retrieve("Landlord security deposit refund")
    assert all(bool(c.chunk_id) for c in res.candidates)


def test_7_results_preserve_document_ids(prepared_retriever):
    res = prepared_retriever.retrieve("Landlord security deposit refund")
    assert all(bool(c.document_id) for c in res.candidates)


def test_8_results_preserve_act_and_section(prepared_retriever):
    res = prepared_retriever.retrieve("Landlord security deposit refund")
    c0 = res.candidates[0]
    assert bool(c0.act)
    assert bool(c0.section)


def test_9_results_preserve_source_and_url(prepared_retriever):
    res = prepared_retriever.retrieve("Landlord security deposit refund")
    c0 = res.candidates[0]
    assert bool(c0.source)
    assert bool(c0.source_url)


def test_10_results_preserve_custom_metadata(prepared_retriever):
    res = prepared_retriever.retrieve("Unpaid salary monthly salary")
    for c in res.candidates:
        if c.document_id == "DUMMY-LAB-001":
            assert c.metadata.get("enforcement_level") == "Strict"


def test_11_top_k_limit_respected(prepared_retriever):
    res = prepared_retriever.retrieve("Workplace safety equipment", top_k=3)
    assert len(res.candidates) == 3


def test_12_top_k_le_zero_raises_error(prepared_retriever):
    with pytest.raises(ValueError):
        prepared_retriever.retrieve("Test query", top_k=0)


def test_13_top_k_larger_than_ntotal_handled_safely(prepared_retriever):
    res = prepared_retriever.retrieve("Test query", top_k=500)
    assert len(res.candidates) == prepared_retriever.vector_store.ntotal


def test_14_results_ordered_descending_score(prepared_retriever):
    res = prepared_retriever.retrieve("Overtime pay compensation double rate")
    scores = [c.score for c in res.candidates]
    assert scores == sorted(scores, reverse=True)


def test_15_similarity_threshold_filtering(prepared_retriever):
    res = prepared_retriever.retrieve("Defective smartphone refund", similarity_threshold=0.40)
    assert all(c.score >= 0.40 for c in res.qualified_chunks)


def test_16_raw_candidates_remain_inspectable(prepared_retriever):
    res = prepared_retriever.retrieve(
        "Defective smartphone refund", top_k=5, similarity_threshold=0.99
    )
    assert len(res.candidates) == 5
    assert len(res.qualified_chunks) == 0


def test_17_insufficient_retrieval_status_detected(prepared_retriever):
    res = prepared_retriever.retrieve("Unrelated nonsense query xyz123", similarity_threshold=0.99)
    assert res.status == "insufficient_retrieval"
    assert len(res.qualified_chunks) == 0


def test_18_query_dimension_mismatch_detected(prepared_retriever):
    bad_vec = np.zeros((10,), dtype=np.float32)
    with pytest.raises(ValueError):
        prepared_retriever.vector_store.search_raw_vector(bad_vec)


def test_19_empty_query_rejected(prepared_retriever):
    with pytest.raises(ValueError):
        prepared_retriever.retrieve("   ")


def test_20_dummy_flag_preserved(prepared_retriever):
    res = prepared_retriever.retrieve("Maternity leave rights")
    assert all(c.is_dummy is True for c in res.candidates)


def test_21_repeated_query_stable_ranking(prepared_retriever):
    q = "Rent increase middle of lease notice period"
    res1 = prepared_retriever.retrieve(q)
    res2 = prepared_retriever.retrieve(q)

    ids1 = [c.chunk_id for c in res1.candidates]
    ids2 = [c.chunk_id for c in res2.candidates]
    assert ids1 == ids2


def test_22_consumer_query_retrieves_consumer_chunk(prepared_retriever):
    res = prepared_retriever.retrieve("I bought a defective smartphone and seller refuses refund")
    top_ids = [c.chunk_id for c in res.candidates[:3]]
    assert "DUMMY-CONS-001-chunk-0" in top_ids


def test_23_tenant_query_retrieves_tenant_chunk(prepared_retriever):
    res = prepared_retriever.retrieve("Landlord refuses to return my rental security deposit")
    top_ids = [c.chunk_id for c in res.candidates[:3]]
    assert "DUMMY-TEN-001-chunk-0" in top_ids


def test_24_labour_query_retrieves_labour_chunk(prepared_retriever):
    res = prepared_retriever.retrieve("My employer has not paid my monthly salary for two months")
    top_ids = [c.chunk_id for c in res.candidates[:3]]
    assert "DUMMY-LAB-001-chunk-0" in top_ids
