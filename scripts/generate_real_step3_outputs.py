import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunker import chunk_dataset
from src.config import config
from src.data_loader import load_raw_legal_data
from src.normalizer import normalize_dataset


def main():
    output_dir = Path("test_outputs/real_data_step3")
    output_dir.mkdir(parents=True, exist_ok=True)

    kb_path = config.KNOWLEDGE_BASE_PATH
    raw_records = load_raw_legal_data(kb_path)
    normalized_docs = normalize_dataset(raw_records)

    # Ensure is_dummy is set to False for production chunks
    for doc in normalized_docs:
        doc.is_dummy = False

    print(f"Chunking {len(normalized_docs)} normalized documents...")
    chunks = chunk_dataset(normalized_docs, chunk_size=500, chunk_overlap=100)
    total_chunks = len(chunks)

    chunk_ids = [c.chunk_id for c in chunks]
    unique_chunk_ids = len(set(chunk_ids))

    empty_chunks = sum(1 for c in chunks if not c.text.strip())
    chunk_lengths = [len(c.text) for c in chunks]

    domains = Counter(c.domain for c in chunks)
    acts = Counter(c.act for c in chunks)

    summary = {
        "step": "real_data_step3_chunking",
        "total_documents": len(normalized_docs),
        "total_chunks": total_chunks,
        "unique_chunk_ids_count": unique_chunk_ids,
        "empty_chunks_count": empty_chunks,
        "chunk_length_stats": {
            "min_length": min(chunk_lengths) if chunk_lengths else 0,
            "max_length": max(chunk_lengths) if chunk_lengths else 0,
            "avg_length": round(sum(chunk_lengths) / total_chunks, 2) if total_chunks else 0,
        },
        "domain_distribution": dict(domains),
        "act_distribution": dict(acts),
        "sample_chunks": [c.to_dict() for c in chunks[:5]],
        "status": "SUCCESS"
        if (total_chunks == unique_chunk_ids and empty_chunks == 0)
        else "FAILED",
    }

    json_path = output_dir / "chunking_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    report_lines = [
        "=" * 80,
        "LEGAL AID REAL DATA STEP 3 CHUNKING VALIDATION REPORT",
        "=" * 80,
        f"Normalized Documents Chunked : {len(normalized_docs)}",
        f"Total Chunks Generated      : {total_chunks}",
        f"Unique Chunk IDs            : {unique_chunk_ids}",
        f"Empty Chunks                : {empty_chunks}",
        f"Min Chunk Length            : {summary['chunk_length_stats']['min_length']} chars",
        f"Max Chunk Length            : {summary['chunk_length_stats']['max_length']} chars",
        f"Average Chunk Length        : {summary['chunk_length_stats']['avg_length']} chars",
        "-" * 80,
        "CHUNKS PER DOMAIN:",
    ]
    for dom, cnt in domains.items():
        report_lines.append(f"  - {dom}: {cnt} chunks")

    report_lines.append("-" * 80)
    report_lines.append("CHUNKS PER ACT:")
    for act, cnt in acts.items():
        report_lines.append(f"  - {act}: {cnt} chunks")

    report_lines.append("=" * 80)
    report_path = output_dir / "chunking_report.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Step 3 real data outputs saved successfully to {output_dir.resolve()}!")
    print(
        f"Total Chunks: {total_chunks}, Unique Chunk IDs: {unique_chunk_ids}, Status: {summary['status']}"
    )


if __name__ == "__main__":
    main()
