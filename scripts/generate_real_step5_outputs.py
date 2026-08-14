import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunker import chunk_dataset
from src.config import config
from src.data_loader import load_raw_legal_data
from src.embedder import LegalEmbedder
from src.normalizer import normalize_dataset
from src.vector_store import FAISSVectorStore


def main():
    output_dir = Path("test_outputs/real_data_step5")
    output_dir.mkdir(parents=True, exist_ok=True)

    production_vector_store_path = config.VECTOR_STORE_PATH
    print(f"Building production FAISS index at {production_vector_store_path.resolve()}...")

    kb_path = config.KNOWLEDGE_BASE_PATH
    raw_records = load_raw_legal_data(kb_path)
    normalized_docs = normalize_dataset(raw_records)
    for doc in normalized_docs:
        doc.is_dummy = False

    chunks = chunk_dataset(normalized_docs, chunk_size=500, chunk_overlap=100)
    print(f"Embedding {len(chunks)} real legal chunks...")

    embedder = LegalEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks, batch_size=64)

    print("Building FAISS IndexFlatIP vector store...")
    vector_store = FAISSVectorStore(dir_path=production_vector_store_path)
    vector_store.build_index(embedded_chunks)

    index_path, metadata_path = vector_store.save()
    print(f"Saved FAISS index binary to {index_path.resolve()}")
    print(f"Saved metadata mapping JSON to {metadata_path.resolve()}")

    # Verify reloading
    verify_store = FAISSVectorStore(dir_path=production_vector_store_path)
    verify_store.load()

    ntotal = verify_store.ntotal
    dimension = verify_store.dimension
    positions_count = len(verify_store.metadata_map)

    # Check contiguous keys 0..ntotal-1
    missing_positions = [pos for pos in range(ntotal) if str(pos) not in verify_store.metadata_map]
    sample_record = verify_store.get_chunk_by_position(0)
    is_dummy_val = sample_record.get("is_dummy")

    summary = {
        "step": "real_data_step5_vector_store",
        "index_path": str(index_path.resolve()),
        "metadata_path": str(metadata_path.resolve()),
        "ntotal": ntotal,
        "dimension": dimension,
        "positions_count": positions_count,
        "missing_positions_count": len(missing_positions),
        "is_dummy_flag_sample": is_dummy_val,
        "sample_metadata": sample_record,
        "status": "SUCCESS"
        if (
            ntotal == len(embedded_chunks)
            and dimension == 384
            and len(missing_positions) == 0
            and is_dummy_val is False
        )
        else "FAILED",
    }

    json_path = output_dir / "vector_store_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    report_lines = [
        "=" * 80,
        "LEGAL AID REAL DATA STEP 5 VECTOR STORE VALIDATION REPORT",
        "=" * 80,
        f"FAISS Index Path     : {index_path.resolve()}",
        f"Metadata JSON Path   : {metadata_path.resolve()}",
        f"Total Vectors (ntotal): {ntotal}",
        f"Vector Dimension     : {dimension}",
        f"Metadata Records     : {positions_count}",
        f"Missing Positions    : {len(missing_positions)}",
        f"is_dummy Flag Sample : {is_dummy_val}",
        "=" * 80,
    ]
    report_path = output_dir / "vector_store_report.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Step 5 real data outputs saved successfully to {output_dir.resolve()}!")
    print(f"nTotal: {ntotal}, Dimension: {dimension}, Status: {summary['status']}")


if __name__ == "__main__":
    main()
