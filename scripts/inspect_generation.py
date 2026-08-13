import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import LegalGenerator  # noqa: E402


def inspect_generation() -> None:
    print("=" * 80)
    print("LEGAL AID RAG GENERATION INSPECTION TOOL")
    print("=" * 80)

    generator = LegalGenerator()

    # Demonstration 1: Successful RAG Generation
    query1 = (
        "I bought a defective smartphone and the seller refuses to replace it or give me a refund."
    )
    print("\n[DEMO 1: SUCCESSFUL RAG GENERATION]")
    print(f'QUERY: "{query1}"')

    resp1 = generator.generate(query1)

    print(f"RESPONSE STATUS    : {resp1.status.upper()}")
    print(f"RETRIEVAL STATUS   : {resp1.retrieval_status.upper()}")
    print(f"QUALIFIED CHUNKS   : {resp1.qualified_chunk_count}")
    print(f"OLLAMA MODEL       : {resp1.model_name}")

    if resp1.retrieved_chunks:
        top_c = resp1.retrieved_chunks[0]
        print(f"TOP CHUNK ID       : {top_c['chunk_id']}")
        print(f"SIMILARITY SCORE   : {top_c['score']:.4f}")

    print("-" * 80)
    print("GENERATED GROUNDED ANSWER:")
    print(resp1.answer)
    print("-" * 80)
    print("RETAINED SOURCES:")
    for s in resp1.sources:
        print(f"  - [{s['chunk_id']}] {s['act']}, {s['section']} ({s['source_url']})")

    # Demonstration 2: Insufficient Retrieval Short-Circuit
    query2 = "Unrelated random string query test xyz1239999"
    print("\n" + "=" * 80)
    print("[DEMO 2: INSUFFICIENT RETRIEVAL SAFETY SHORT-CIRCUIT]")
    print(f'QUERY: "{query2}"')

    resp2 = generator.generate(query2, similarity_threshold=0.99)

    print(f"RESPONSE STATUS    : {resp2.status.upper()}")
    print(f"RETRIEVAL STATUS   : {resp2.retrieval_status.upper()}")
    print(f"QUALIFIED CHUNKS   : {resp2.qualified_chunk_count}")
    print("OLLAMA CALLED      : False")
    print("-" * 80)
    print("FALLBACK ANSWER:")
    print(resp2.answer)
    print("=" * 80)


if __name__ == "__main__":
    inspect_generation()
