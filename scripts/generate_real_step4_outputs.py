import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunker import chunk_dataset
from src.config import config
from src.data_loader import load_raw_legal_data
from src.embedder import LegalEmbedder
from src.normalizer import normalize_dataset


def main():
    output_dir = Path("test_outputs/real_data_step4")
    output_dir.mkdir(parents=True, exist_ok=True)

    kb_path = config.KNOWLEDGE_BASE_PATH
    raw_records = load_raw_legal_data(kb_path)
    normalized_docs = normalize_dataset(raw_records)
    for doc in normalized_docs:
        doc.is_dummy = False

    chunks = chunk_dataset(normalized_docs, chunk_size=500, chunk_overlap=100)
    print(f"Generating embeddings for {len(chunks)} real legal chunks...")

    embedder = LegalEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks, batch_size=64)

    matrix = np.array([ec.embedding for ec in embedded_chunks], dtype=np.float32)

    has_nan = np.isnan(matrix).any()
    has_inf = np.isinf(matrix).any()
    norms = np.linalg.norm(matrix, axis=1)
    is_normalized = np.allclose(norms, 1.0, atol=1e-4)

    summary = {
        "step": "real_data_step4_embeddings",
        "embedding_model": embedder.model_name,
        "total_chunks": len(chunks),
        "total_embedded_chunks": len(embedded_chunks),
        "matrix_shape": list(matrix.shape),
        "embedding_dimension": embedder.embedding_dimension,
        "dtype": str(matrix.dtype),
        "has_nan": bool(has_nan),
        "has_inf": bool(has_inf),
        "l2_normalized": bool(is_normalized),
        "norm_min": round(float(norms.min()), 6),
        "norm_max": round(float(norms.max()), 6),
        "status": "SUCCESS"
        if (len(embedded_chunks) == len(chunks) and not has_nan and not has_inf and is_normalized)
        else "FAILED",
    }

    json_path = output_dir / "embeddings_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    report_lines = [
        "=" * 80,
        "LEGAL AID REAL DATA STEP 4 EMBEDDINGS VALIDATION REPORT",
        "=" * 80,
        f"Embedding Model      : {embedder.model_name}",
        f"Total Chunks Embedded: {len(embedded_chunks)}",
        f"Embedding Dimension  : {embedder.embedding_dimension}",
        f"Matrix Shape         : {matrix.shape}",
        f"Data Type (dtype)    : {matrix.dtype}",
        f"Has NaN Values       : {has_nan}",
        f"Has Inf Values       : {has_inf}",
        f"L2 Normalized        : {is_normalized}",
        f"Norm Min / Max       : {norms.min():.6f} / {norms.max():.6f}",
        "=" * 80,
    ]
    report_path = output_dir / "embeddings_report.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Step 4 real data outputs saved successfully to {output_dir.resolve()}!")
    print(
        f"Embedded Count: {len(embedded_chunks)}, Matrix: {matrix.shape}, Status: {summary['status']}"
    )


if __name__ == "__main__":
    main()
