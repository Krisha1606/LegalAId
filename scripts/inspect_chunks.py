import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.chunker import chunk_dataset  # noqa: E402
from src.data_loader import load_raw_legal_data  # noqa: E402
from src.normalizer import normalize_dataset  # noqa: E402


def inspect_chunks() -> None:
    print("=" * 80)
    print("LEGAL-AWARE CHUNK INSPECTION TOOL")
    print("=" * 80)

    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)

    print(f"\nTotal Source Documents: {len(docs)}")
    print(f"Total Chunks Generated: {len(chunks)}")
    print("-" * 80)

    domain_counts: dict[str, int] = {}
    for c in chunks:
        domain_counts[c.domain] = domain_counts.get(c.domain, 0) + 1

    print("\nDomain-wise Chunk Distribution:")
    for dom, count in domain_counts.items():
        print(f"  - {dom}: {count} chunks")
    print("-" * 80)

    samples_per_domain: dict[str, list] = {}
    for c in chunks:
        samples_per_domain.setdefault(c.domain, [])
        if len(samples_per_domain[c.domain]) < 2:
            samples_per_domain[c.domain].append(c)

    print("\nSAMPLE CHUNKS FOR MANUAL INSPECTION:\n")
    for domain, sample_list in samples_per_domain.items():
        print(f"=== DOMAIN: {domain} ===")
        for c in sample_list:
            print(f"  Chunk ID     : {c.chunk_id}")
            print(f"  Document ID  : {c.document_id}")
            print(f"  Act          : {c.act}")
            print(f"  Section      : {c.section} - {c.section_title}")
            print(f"  Chunk Index  : {c.chunk_index + 1} of {c.total_chunks}")
            print(f"  Chunk Length : {len(c.text)} characters")
            print(f"  Source       : {c.source} ({c.source_url})")
            print(f"  Is Dummy     : {c.is_dummy}")
            print(f"  Text Snippet : {c.text[:150]}...")
            print("  " + "-" * 76)
        print()


if __name__ == "__main__":
    inspect_chunks()
