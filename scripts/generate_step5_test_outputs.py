import json
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_retrieval import evaluate_retrieval  # noqa: E402
from src.retriever import LegalRetriever  # noqa: E402


def generate_step5_artifacts() -> None:
    output_dir = PROJECT_ROOT / "test_outputs" / "step5_retrieval"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest for step 5...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "tests/test_retriever.py", "-v"],
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

    # 4. Generate sample retrieval_results.json
    print("Generating retrieval_results.json...")
    retriever = LegalRetriever()
    sample_queries = [
        "I bought a defective product and the seller refuses to replace or refund it.",
        "My employer has not paid my monthly salary for two months.",
        "The landlord refuses to return my rental security deposit after moving out.",
        "Unrelated random string query test xyz1239999",
    ]

    sample_results = []
    for sq in sample_queries:
        res = retriever.retrieve(sq, top_k=5)
        sample_results.append(res.to_dict())

    retrieval_json_content = {
        "step": "step5_retrieval_sample_results",
        "default_top_k": retriever.default_top_k,
        "default_threshold": retriever.default_threshold,
        "sample_retrievals": sample_results,
    }
    (output_dir / "retrieval_results.json").write_text(
        json.dumps(retrieval_json_content, indent=2), encoding="utf-8"
    )

    # 5. Generate retrieval_evaluation.json using evaluate_retrieval()
    print("Generating retrieval_evaluation.json...")
    eval_report = evaluate_retrieval()
    eval_report["execution_status"] = "SUCCESS" if pytest_proc.returncode == 0 else "FAILURE"
    (output_dir / "retrieval_evaluation.json").write_text(
        json.dumps(eval_report, indent=2), encoding="utf-8"
    )

    print("Step 5 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_step5_artifacts()
