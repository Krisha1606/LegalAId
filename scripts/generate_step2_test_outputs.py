import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.chunker import chunk_dataset  # noqa: E402
from src.data_loader import load_raw_legal_data  # noqa: E402
from src.normalizer import normalize_dataset  # noqa: E402


def generate_step2_artifacts() -> None:
    output_dir = PROJECT_ROOT / "test_outputs" / "step2_chunking"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "tests/test_chunker.py", "-v"],
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

    # 4. Programmatically run chunking and collect metrics
    print("Generating chunking results JSON...")
    raw_records = load_raw_legal_data()
    docs = normalize_dataset(raw_records)
    chunks = chunk_dataset(docs, chunk_size=500, chunk_overlap=100)

    total_docs = len(docs)
    total_chunks = len(chunks)

    domain_counter: Counter[str] = Counter()
    doc_chunk_counter: Counter[str] = Counter()
    chunk_lengths: list[int] = []

    missing_doc_ids = 0
    missing_act = 0
    missing_section = 0
    missing_source = 0
    lost_metadata = 0

    sample_chunks_dict: list[dict] = []

    for c in chunks:
        domain_counter[c.domain] += 1
        doc_chunk_counter[c.document_id] += 1
        chunk_len = len(c.text)
        chunk_lengths.append(chunk_len)

        if not c.document_id or not c.parent_document_id:
            missing_doc_ids += 1
        if not c.act:
            missing_act += 1
        if not c.section:
            missing_section += 1
        if not c.source:
            missing_source += 1

        # Check if metadata was lost compared to parent doc
        parent_doc = next((d for d in docs if d.id == c.document_id), None)
        if parent_doc and c.metadata != parent_doc.metadata:
            lost_metadata += 1

        if len(sample_chunks_dict) < 6:
            sample_chunks_dict.append(c.to_dict())

    min_len = min(chunk_lengths) if chunk_lengths else 0
    max_len = max(chunk_lengths) if chunk_lengths else 0
    avg_len = round(sum(chunk_lengths) / len(chunk_lengths), 2) if chunk_lengths else 0.0

    chunking_json_content = {
        "step": "step2_chunking",
        "total_source_documents": total_docs,
        "total_chunks": total_chunks,
        "chunks_per_domain": dict(domain_counter),
        "chunks_per_source_document": dict(doc_chunk_counter),
        "min_chunk_length": min_len,
        "max_chunk_length": max_len,
        "average_chunk_length": avg_len,
        "missing_document_ids_count": missing_doc_ids,
        "missing_act_count": missing_act,
        "missing_section_count": missing_section,
        "missing_source_count": missing_source,
        "number_of_chunks_with_lost_metadata": lost_metadata,
        "sample_chunks": sample_chunks_dict,
    }

    (output_dir / "chunking_results.json").write_text(
        json.dumps(chunking_json_content, indent=2), encoding="utf-8"
    )
    print("Step 2 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_step2_artifacts()
