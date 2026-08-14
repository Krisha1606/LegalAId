import sys
from pathlib import Path

import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.chunker import chunk_dataset  # noqa: E402
from src.data_loader import load_raw_legal_data  # noqa: E402
from src.embedder import LegalEmbedder  # noqa: E402
from src.normalizer import normalize_dataset  # noqa: E402


def inspect_embeddings() -> None:
    print("=" * 80)
    print("LEGAL EMBEDDING PIPELINE INSPECTION TOOL")
    print("=" * 80)

    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)

    embedder = LegalEmbedder()
    print(f"\nModel Name          : {embedder.model_name}")
    print(f"Number of Chunks    : {len(chunks)}")
    print(f"Embedding Dimension : {embedder.embedding_dimension}")

    embedded_chunks = embedder.embed_chunks(chunks)
    matrix = np.array([ec.embedding for ec in embedded_chunks])

    print(f"Matrix Shape        : {matrix.shape}")
    print(f"Vector Dtype        : {matrix.dtype}")
    print("-" * 80)

    print("\nSAMPLE EMBEDDED CHUNKS:\n")
    for ec in embedded_chunks[:3]:
        vec_str = ", ".join(f"{v:.4f}" for v in ec.embedding[:5])
        print(f"  Chunk ID       : {ec.chunk_id}")
        print(f"  Document ID    : {ec.document_id}")
        print(f"  Act            : {ec.chunk.act}")
        print(f"  Section        : {ec.chunk.section}")
        print(f"  Vector Prefix  : [{vec_str}, ...]")
        print("  " + "-" * 76)

    print("\nSAMPLE QUERY EMBEDDING:\n")
    sample_query = "My landlord refuses to return my rental security deposit."
    query_vec = embedder.embed_query(sample_query)
    q_vec_str = ", ".join(f"{v:.4f}" for v in query_vec[:5])

    print(f"  Query Text     : '{sample_query}'")
    print(f"  Query Dimension: {query_vec.shape[0]}")
    print(f"  Query Dtype    : {query_vec.dtype}")
    print(f"  Vector Prefix  : [{q_vec_str}, ...]")
    print("-" * 80)

    print("\nSEMANTIC SANITY CHECK SCORES:")
    cons_ec = next(ec for ec in embedded_chunks if ec.document_id == "DUMMY-CONS-001")
    ten_ec = next(ec for ec in embedded_chunks if ec.document_id == "DUMMY-TEN-001")

    q_cons = "I bought a defective product and the seller refuses to refund me."
    q_cons_vec = embedder.embed_query(q_cons)

    score_cons_to_cons = float(np.dot(q_cons_vec, cons_ec.embedding))
    score_cons_to_ten = float(np.dot(q_cons_vec, ten_ec.embedding))

    print(f"  Query: '{q_cons}'")
    print(f"    vs. Consumer Chunk (DUMMY-CONS-001): {score_cons_to_cons:.4f}")
    print(f"    vs. Tenant Chunk   (DUMMY-TEN-001) : {score_cons_to_ten:.4f}")
    print(
        f"  Result: {'PASS (Consumer > Tenant)' if score_cons_to_cons > score_cons_to_ten else 'FAIL'}"
    )
    print("=" * 80)


if __name__ == "__main__":
    inspect_embeddings()
