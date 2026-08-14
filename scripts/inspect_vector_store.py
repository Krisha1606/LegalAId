import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.chunker import chunk_dataset  # noqa: E402
from src.data_loader import load_raw_legal_data  # noqa: E402
from src.embedder import LegalEmbedder  # noqa: E402
from src.normalizer import normalize_dataset  # noqa: E402
from src.vector_store import FAISSVectorStore  # noqa: E402


def inspect_vector_store() -> None:
    print("=" * 80)
    print("FAISS VECTOR STORE INSPECTION TOOL")
    print("=" * 80)

    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)

    embedder = LegalEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks)

    store = FAISSVectorStore()
    store.build_index(embedded_chunks)
    idx_path, meta_path = store.save()

    loaded_store = FAISSVectorStore()
    loaded_store.load()

    match_status = loaded_store.ntotal == len(loaded_store.metadata_map)

    print(f"\nEmbedding Model        : {embedder.model_name}")
    print(f"Number of Chunks       : {len(chunks)}")
    print(f"Embedding Dimension    : {embedder.embedding_dimension}")
    print(f"FAISS Index Type       : {type(loaded_store.index).__name__}")
    print(f"FAISS Index Dimension  : {loaded_store.dimension}")
    print(f"Number of Vectors      : {loaded_store.ntotal}")
    print(f"Metadata Records Count : {len(loaded_store.metadata_map)}")
    print(f"Count Match            : {match_status}")
    print(f"Index File Path        : {idx_path.resolve()}")
    print(f"Metadata File Path     : {meta_path.resolve()}")
    print("-" * 80)

    print("\nSAMPLE FAISS POSITION -> METADATA MAPPINGS:\n")
    for pos in range(min(5, loaded_store.ntotal)):
        meta = loaded_store.get_chunk_by_position(pos)
        print(f"  FAISS Position {pos}:")
        print(f"    Chunk ID    : {meta.get('chunk_id')}")
        print(f"    Document ID : {meta.get('document_id')}")
        print(f"    Domain      : {meta.get('domain')}")
        print(f"    Act         : {meta.get('act')}")
        print(f"    Section     : {meta.get('section')}")
        print(f"    Is Dummy    : {meta.get('is_dummy')}")
        print("  " + "-" * 76)
    print("=" * 80)


if __name__ == "__main__":
    inspect_vector_store()
