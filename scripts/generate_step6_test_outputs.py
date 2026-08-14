import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval_evaluator import RetrievalBenchmark  # noqa: E402


def generate_step6_artifacts() -> None:
    output_dir = PROJECT_ROOT / "test_outputs" / "step6_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest for step 6...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "tests/test_retrieval_evaluator.py", "-v"],
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

    # 4. Save JSON and TXT benchmark reports
    print("Generating retrieval_benchmark_results.json and summary...")
    benchmark = RetrievalBenchmark()
    report = benchmark.run_benchmark()
    report["execution_status"] = "SUCCESS" if pytest_proc.returncode == 0 else "FAILURE"

    benchmark.save_report(
        report=report,
        json_path=output_dir / "retrieval_benchmark_results.json",
        summary_txt_path=output_dir / "retrieval_benchmark_summary.txt",
    )

    print("Step 6 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_step6_artifacts()
