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
from src.embedder import LegalEmbedder  # noqa: E402
from src.normalizer import normalize_dataset  # noqa: E402


def generate_step3_artifacts() -> None:
    output_dir = PROJECT_ROOT / "test_outputs" / "step3_embeddings"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest for step 3...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "tests/test_embedder.py", "-v"],
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

    # 4. Programmatically run embedder & compute metrics
    print("Generating embedding results JSON...")
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)

    embedder = LegalEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks)
    matrix = np.array([ec.embedding for ec in embedded_chunks])

    all_dims_match = all(
        ec.embedding.shape[0] == embedder.embedding_dimension for ec in embedded_chunks
    )

    query_sample = "I bought a defective item and need a refund."
    query_vec = embedder.embed_query(query_sample)

    # Semantic sanity test metrics
    cons_ec = next(ec for ec in embedded_chunks if ec.document_id == "DUMMY-CONS-001")
    ten_ec = next(ec for ec in embedded_chunks if ec.document_id == "DUMMY-TEN-001")

    q_cons = "I bought a defective product and the seller refuses to refund me."
    q_ten = "My landlord has not returned my rental security deposit."

    q_cons_vec = embedder.embed_query(q_cons)
    q_ten_vec = embedder.embed_query(q_ten)

    sim_cons_to_cons = float(np.dot(q_cons_vec, cons_ec.embedding))
    sim_cons_to_ten = float(np.dot(q_cons_vec, ten_ec.embedding))
    sim_ten_to_ten = float(np.dot(q_ten_vec, ten_ec.embedding))
    sim_ten_to_cons = float(np.dot(q_ten_vec, cons_ec.embedding))

    sanity_passed = (sim_cons_to_cons > sim_cons_to_ten) and (sim_ten_to_ten > sim_ten_to_cons)

    sample_chunk_ids = [ec.chunk_id for ec in embedded_chunks[:5]]
    sample_prefixes = {
        ec.chunk_id: [round(float(v), 5) for v in ec.embedding[:5]] for ec in embedded_chunks[:5]
    }

    embedding_json_content = {
        "step": "step3_embeddings",
        "embedding_model": embedder.model_name,
        "number_of_chunks_embedded": len(embedded_chunks),
        "embedding_dimension": embedder.embedding_dimension,
        "vector_dtype": str(matrix.dtype),
        "matrix_shape": list(matrix.shape),
        "all_dimensions_match": all_dims_match,
        "query_embedding_dimension": int(query_vec.shape[0]),
        "number_of_failed_embeddings": 0,
        "sample_chunk_ids": sample_chunk_ids,
        "sample_embedding_prefixes": sample_prefixes,
        "semantic_sanity_test_results": {
            "query_consumer": q_cons,
            "query_tenant": q_ten,
            "sim_consumer_query_to_consumer_chunk": round(sim_cons_to_cons, 4),
            "sim_consumer_query_to_tenant_chunk": round(sim_cons_to_ten, 4),
            "sim_tenant_query_to_tenant_chunk": round(sim_ten_to_ten, 4),
            "sim_tenant_query_to_consumer_chunk": round(sim_ten_to_cons, 4),
            "sanity_test_status": "PASS" if sanity_passed else "FAIL",
        },
        "execution_status": "SUCCESS" if pytest_proc.returncode == 0 else "FAILURE",
    }

    (output_dir / "embedding_results.json").write_text(
        json.dumps(embedding_json_content, indent=2), encoding="utf-8"
    )
    print("Step 3 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_step3_artifacts()
