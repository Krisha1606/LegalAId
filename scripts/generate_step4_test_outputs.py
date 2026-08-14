import json
import subprocess
import sys
from pathlib import Path

import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.chunker import chunk_dataset  # noqa: E402
from src.data_loader import load_raw_legal_data  # noqa: E402
from src.embedder import EmbeddedChunk, LegalEmbedder  # noqa: E402
from src.normalizer import normalize_dataset  # noqa: E402
from src.vector_store import FAISSVectorStore  # noqa: E402


def generate_step4_artifacts() -> None:
    output_dir = PROJECT_ROOT / "test_outputs" / "step4_vector_store"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest for step 4...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "tests/test_vector_store.py", "-v"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    pytest_out = pytest_proc.stdout
    if pytest_proc.stderr:
        pytest_out += "\nSTDERR:\n" + pytest_proc.stderr
    pytest_out += f"\nExit Code: {pytest_proc.returncode}\n"
    (output_dir / "pytest_output.txt").write_text(pytest_out, encoding="utf-8")

    # 2. Run ruff check
    print("Running ruff check...")
    ruff_check_proc = subprocess.run(
        [python_exe, "-m", "ruff", "check", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    ruff_check_out = ruff_check_proc.stdout
    if ruff_check_proc.stderr:
        ruff_check_out += "\nSTDERR:\n" + ruff_check_proc.stderr
    ruff_check_out += f"\nExit Code: {ruff_check_proc.returncode}\n"
    (output_dir / "ruff_check_output.txt").write_text(ruff_check_out, encoding="utf-8")

    # 3. Run ruff format check
    print("Running ruff format check...")
    ruff_fmt_proc = subprocess.run(
        [python_exe, "-m", "ruff", "format", "--check", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    ruff_fmt_out = ruff_fmt_proc.stdout
    if ruff_fmt_proc.stderr:
        ruff_fmt_out += "\nSTDERR:\n" + ruff_fmt_proc.stderr
    ruff_fmt_out += f"\nExit Code: {ruff_fmt_proc.returncode}\n"
    (output_dir / "ruff_format_output.txt").write_text(ruff_fmt_out, encoding="utf-8")

    # 4. Programmatically run vector store & compute metrics
    print("Generating vector store results JSON...")
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

    # Test duplicate ID validation
    dup_pass = False
    try:
        FAISSVectorStore().build_index([embedded_chunks[0], embedded_chunks[0]])
    except ValueError:
        dup_pass = True

    # Test dimension mismatch validation
    dim_pass = False
    try:
        bad_ec = EmbeddedChunk(
            chunk_id="BAD",
            document_id="BAD",
            embedding=np.zeros((10,), dtype=np.float32),
            embedding_dimension=10,
            chunk=embedded_chunks[0].chunk,
        )
        FAISSVectorStore().build_index([embedded_chunks[0], bad_ec])
    except ValueError:
        dim_pass = True

    # Test self-search validation
    self_search_pass = False
    dists, indices = loaded_store.search_raw_vector(embedded_chunks[0].embedding, top_k=1)
    if indices[0][0] == 0 and float(dists[0][0]) > 0.99:
        self_search_pass = True

    sample_positions = {
        str(pos): loaded_store.get_chunk_by_position(pos)["chunk_id"]
        for pos in range(min(5, loaded_store.ntotal))
    }

    sample_act_section = {
        str(pos): {
            "act": loaded_store.get_chunk_by_position(pos)["act"],
            "section": loaded_store.get_chunk_by_position(pos)["section"],
        }
        for pos in range(min(5, loaded_store.ntotal))
    }

    vector_store_json_content = {
        "step": "step4_vector_store",
        "faiss_index_type": type(loaded_store.index).__name__,
        "embedding_dimension": loaded_store.dimension,
        "number_of_vectors": loaded_store.ntotal,
        "number_of_metadata_records": len(loaded_store.metadata_map),
        "index_metadata_count_match": match_status,
        "sample_position_mappings": sample_positions,
        "sample_act_section_mappings": sample_act_section,
        "index_file_path": str(idx_path.resolve()),
        "metadata_file_path": str(meta_path.resolve()),
        "persistence_roundtrip_status": "PASS" if match_status else "FAIL",
        "duplicate_id_validation_status": "PASS" if dup_pass else "FAIL",
        "dimension_validation_status": "PASS" if dim_pass else "FAIL",
        "self_search_validation_status": "PASS" if self_search_pass else "FAIL",
        "execution_status": "SUCCESS" if pytest_proc.returncode == 0 else "FAILURE",
    }

    (output_dir / "vector_store_results.json").write_text(
        json.dumps(vector_store_json_content, indent=2), encoding="utf-8"
    )
    print("Step 4 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_step4_artifacts()
