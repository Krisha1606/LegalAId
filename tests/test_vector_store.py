import numpy as np
import pytest

from src.chunker import chunk_dataset
from src.data_loader import load_raw_legal_data
from src.embedder import EmbeddedChunk, LegalEmbedder
from src.normalizer import normalize_dataset
from src.vector_store import FAISSVectorStore


@pytest.fixture(scope="module")
def embedded_chunks():
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)
    embedder = LegalEmbedder()
    return embedder.embed_chunks(chunks)


def test_1_faiss_index_creation(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    assert store.index is not None
    assert store.ntotal > 0


def test_2_index_dimension_matches_embeddings(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    assert store.dimension == embedded_chunks[0].embedding_dimension


def test_3_correct_number_of_vectors_added(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    assert store.ntotal == len(embedded_chunks)


def test_4_metadata_mapping_count_matches(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    assert len(store.metadata_map) == len(embedded_chunks)


def test_5_chunk_ids_preserved(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    for pos, ec in enumerate(embedded_chunks):
        meta = store.get_chunk_by_position(pos)
        assert meta["chunk_id"] == ec.chunk_id


def test_6_document_ids_preserved(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    for pos, ec in enumerate(embedded_chunks):
        meta = store.get_chunk_by_position(pos)
        assert meta["document_id"] == ec.document_id


def test_7_act_section_metadata_preserved(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    meta0 = store.get_chunk_by_position(0)
    assert meta0["act"] == embedded_chunks[0].chunk.act
    assert meta0["section"] == embedded_chunks[0].chunk.section


def test_8_source_and_url_preserved(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    meta0 = store.get_chunk_by_position(0)
    assert meta0["source"] == embedded_chunks[0].chunk.source
    assert meta0["source_url"] == embedded_chunks[0].chunk.source_url


def test_9_custom_metadata_preserved(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    meta0 = store.get_chunk_by_position(0)
    assert meta0["metadata"] == embedded_chunks[0].chunk.metadata


def test_10_11_save_index_and_metadata(embedded_chunks, tmp_path):
    store = FAISSVectorStore(dir_path=tmp_path)
    store.build_index(embedded_chunks)
    idx_path, meta_path = store.save()

    assert idx_path.is_file()
    assert meta_path.is_file()


def test_12_13_14_15_16_load_index_and_metadata(embedded_chunks, tmp_path):
    store = FAISSVectorStore(dir_path=tmp_path)
    store.build_index(embedded_chunks)
    store.save()

    loaded_store = FAISSVectorStore(dir_path=tmp_path)
    loaded_store.load()

    assert loaded_store.ntotal == len(embedded_chunks)
    assert loaded_store.dimension == embedded_chunks[0].embedding_dimension
    assert len(loaded_store.metadata_map) == loaded_store.ntotal


def test_17_rejects_duplicate_chunk_ids(embedded_chunks):
    store = FAISSVectorStore()
    duplicate_chunks = [embedded_chunks[0], embedded_chunks[0]]
    with pytest.raises(ValueError) as exc_info:
        store.build_index(duplicate_chunks)
    assert "Duplicate chunk_id" in str(exc_info.value)


def test_18_rejects_inconsistent_dimensions(embedded_chunks):
    store = FAISSVectorStore()
    bad_ec = EmbeddedChunk(
        chunk_id="BAD-001",
        document_id="BAD-001",
        embedding=np.zeros((100,), dtype=np.float32),
        embedding_dimension=100,
        chunk=embedded_chunks[0].chunk,
    )
    with pytest.raises(ValueError) as exc_info:
        store.build_index([embedded_chunks[0], bad_ec])
    assert "Embedding dimension mismatch" in str(exc_info.value)


def test_19_empty_input_handling():
    store = FAISSVectorStore()
    with pytest.raises(ValueError) as exc_info:
        store.build_index([])
    assert "empty list" in str(exc_info.value)


def test_20_persistence_roundtrip(embedded_chunks, tmp_path):
    store = FAISSVectorStore(dir_path=tmp_path)
    store.build_index(embedded_chunks)
    store.save()

    roundtrip = FAISSVectorStore(dir_path=tmp_path)
    roundtrip.load()

    assert roundtrip.ntotal == store.ntotal
    assert roundtrip.dimension == store.dimension
    for pos in range(roundtrip.ntotal):
        assert roundtrip.get_chunk_by_position(pos) == store.get_chunk_by_position(pos)


def test_21_dummy_flag_preserved_across_roundtrip(embedded_chunks, tmp_path):
    store = FAISSVectorStore(dir_path=tmp_path)
    store.build_index(embedded_chunks)
    store.save()

    loaded = FAISSVectorStore(dir_path=tmp_path)
    loaded.load()

    for pos in range(loaded.ntotal):
        meta = loaded.get_chunk_by_position(pos)
        assert meta["is_dummy"] is True


def test_22_self_search_index_validation(embedded_chunks):
    store = FAISSVectorStore()
    store.build_index(embedded_chunks)

    target_vec = embedded_chunks[0].embedding
    distances, indices = store.search_raw_vector(target_vec, top_k=1)

    assert indices[0][0] == 0
    assert float(distances[0][0]) > 0.99
