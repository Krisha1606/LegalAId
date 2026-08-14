import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retriever import LegalRetriever  # noqa: E402


def inspect_retrieval() -> None:
    print("=" * 80)
    print("SEMANTIC RETRIEVAL INSPECTION TOOL")
    print("=" * 80)

    retriever = LegalRetriever()

    sample_queries = [
        "I bought a defective product and the seller refuses to replace or refund it.",
        "My employer has not paid my monthly salary for two months.",
        "The landlord refuses to return my rental security deposit after moving out.",
        "An e-commerce app auto-renewed a subscription without my consent.",
        "I was fired on the spot without 30 days notice or severance pay.",
        "The house owner increased my rent by 30% in the middle of a fixed lease.",
    ]

    for q_idx, query in enumerate(sample_queries, start=1):
        print(f'\n[QUERY {q_idx}]: "{query}"')
        result = retriever.retrieve(query, top_k=3)

        print(f"Status          : {result.status.upper()}")
        print(f"Threshold       : {result.similarity_threshold}")
        print(f"Qualified Chunks: {len(result.qualified_chunks)} of {len(result.candidates)}")
        print("-" * 80)

        for c in result.candidates:
            qual_tag = "[QUALIFIED]" if c.is_qualified else "[BELOW THRESHOLD]"
            print(f"  Rank {c.rank} {qual_tag}")
            print(f"    Score     : {c.score:.4f}")
            print(f"    Chunk ID  : {c.chunk_id}")
            print(f"    Domain    : {c.domain}")
            print(f"    Act       : {c.act}")
            print(f"    Section   : {c.section} - {c.section_title}")
            print(f"    Text      : {c.text[:120]}...")
            print("  " + "-" * 76)
    print("=" * 80)


if __name__ == "__main__":
    inspect_retrieval()
