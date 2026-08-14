import json
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_generation import evaluate_generation  # noqa: E402
from src.generator import LegalGenerator  # noqa: E402


def generate_step7_artifacts() -> None:
    output_dir = PROJECT_ROOT / "test_outputs" / "step7_generation"
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable

    # 1. Run pytest
    print("Running pytest for step 7...")
    pytest_proc = subprocess.run(
        [python_exe, "-m", "pytest", "tests/test_generator.py", "-v"],
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

    # 4. Generate sample generation_results.json
    print("Generating generation_results.json...")
    generator = LegalGenerator()
    sample_queries = [
        "I bought a defective smartphone and the seller refuses to replace it or give me a refund.",
        "My employer has not paid my monthly salary for the past two months.",
        "Unrelated random string query test xyz1239999",
    ]

    sample_responses = []
    for sq in sample_queries:
        threshold = 0.99 if "xyz1239999" in sq else None
        resp = generator.generate(sq, similarity_threshold=threshold)
        sample_responses.append(resp.to_dict())

    gen_json_content = {
        "step": "step7_generation_sample_results",
        "model_name": generator.ollama_client.model_name,
        "sample_responses": sample_responses,
    }
    (output_dir / "generation_results.json").write_text(
        json.dumps(gen_json_content, indent=2), encoding="utf-8"
    )

    # 5. Generate generation_evaluation.json
    print("Generating generation_evaluation.json...")
    eval_report = evaluate_generation(generator=generator)
    eval_report["execution_status"] = "SUCCESS" if pytest_proc.returncode == 0 else "FAILURE"
    eval_file = output_dir / "generation_evaluation.json"
    eval_file.write_text(json.dumps(eval_report, indent=2), encoding="utf-8")
    print(f"Written {eval_file} successfully!")

    print("Step 7 test artifacts successfully generated!")


if __name__ == "__main__":
    generate_step7_artifacts()
