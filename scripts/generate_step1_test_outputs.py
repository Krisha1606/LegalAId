import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_raw_legal_data  # noqa: E402
from src.normalizer import normalize_document  # noqa: E402


def generate_artifacts():
    output_dir = PROJECT_ROOT / "test_outputs" / "step1_data_foundation"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "-v"],
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

    # 4. Programmatically test data loader & normalizer
    print("Generating normalization results JSON...")
    raw_records = load_raw_legal_data()
    total_records = len(raw_records)
    success_count = 0
    failure_count = 0
    domain_counter = Counter()
    record_results = []
    failures = []

    for i, raw in enumerate(raw_records):
        rec_id = raw.get("id", f"UNKNOWN_INDEX_{i}")
        domain = raw.get("domain", "UNKNOWN")
        domain_counter[domain] += 1

        try:
            doc = normalize_document(raw)
            success_count += 1
            record_results.append(
                {
                    "id": doc.id,
                    "domain": doc.domain,
                    "status": "SUCCESS",
                    "is_dummy": doc.is_dummy,
                    "has_extra_metadata": bool(doc.metadata),
                }
            )
        except Exception as exc:
            failure_count += 1
            error_info = {
                "id": rec_id,
                "domain": domain,
                "status": "FAILURE",
                "error": str(exc),
            }
            record_results.append(error_info)
            failures.append(error_info)

    norm_json_content = {
        "step": "step1_data_foundation",
        "total_records": total_records,
        "successfully_normalized": success_count,
        "failed_records": failure_count,
        "domain_counts": dict(domain_counter),
        "record_details": record_results,
        "validation_failures": failures,
    }

    (output_dir / "normalization_results.json").write_text(
        json.dumps(norm_json_content, indent=2), encoding="utf-8"
    )
    print("Step 1 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_artifacts()
