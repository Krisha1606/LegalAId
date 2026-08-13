import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import LegalGenerator  # noqa: E402


def evaluate_generation(generator: LegalGenerator | None = None) -> dict:
    queries_path = PROJECT_ROOT / "data" / "dummy_test_queries.json"
    if not queries_path.is_file():
        raise FileNotFoundError(f"Test queries file not found at: {queries_path.resolve()}")

    with open(queries_path, encoding="utf-8") as f:
        test_queries = json.load(f)

    if generator is None:
        generator = LegalGenerator()
    total_queries = len(test_queries)

    retrieval_successes = 0
    insufficient_retrievals = 0
    generation_successes = 0
    generation_failures = 0
    ollama_skipped = 0
    responses_with_sources = 0
    responses_with_chunk_ids = 0
    responses_with_act_sec = 0

    eval_details = []

    for tq in test_queries:
        q_id = tq["query_id"]
        query_text = tq["query"]

        resp = generator.generate(query_text)

        if resp.retrieval_status == "success":
            retrieval_successes += 1
        else:
            insufficient_retrievals += 1

        if resp.status == "success":
            generation_successes += 1
        elif resp.status == "generation_error":
            generation_failures += 1
        elif resp.status == "insufficient_retrieval":
            ollama_skipped += 1

        if resp.sources:
            responses_with_sources += 1
            if all(s.get("chunk_id") for s in resp.sources):
                responses_with_chunk_ids += 1
            if all(s.get("act") and s.get("section") for s in resp.sources):
                responses_with_act_sec += 1

        eval_details.append(
            {
                "query_id": q_id,
                "query": query_text,
                "status": resp.status,
                "retrieval_status": resp.retrieval_status,
                "qualified_chunk_count": resp.qualified_chunk_count,
                "sources_count": len(resp.sources),
                "answer_length": len(resp.answer),
            }
        )

    report = {
        "step": "step7_generation_evaluation",
        "total_test_queries": total_queries,
        "retrieval_successes": retrieval_successes,
        "insufficient_retrievals": insufficient_retrievals,
        "generation_successes": generation_successes,
        "generation_failures": generation_failures,
        "ollama_calls_skipped": ollama_skipped,
        "responses_with_sources": responses_with_sources,
        "responses_with_chunk_ids": responses_with_chunk_ids,
        "responses_with_act_sec": responses_with_act_sec,
        "query_details": eval_details,
    }

    print("=" * 80)
    print("LEGAL AID GENERATION EVALUATION SUMMARY (STRUCTURAL)")
    print("=" * 80)
    print(f"Total Test Queries             : {total_queries}")
    print(f"Retrieval Successes            : {retrieval_successes}")
    print(f"Insufficient Retrievals        : {insufficient_retrievals}")
    print(f"Ollama Generation Successes    : {generation_successes}")
    print(f"Ollama Generation Failures     : {generation_failures}")
    print(f"Ollama Calls Skipped (Safety)  : {ollama_skipped}")
    print(f"Responses with Preserved Srcs  : {responses_with_sources}")
    print(f"Responses with Chunk IDs       : {responses_with_chunk_ids}")
    print(f"Responses with Act/Section     : {responses_with_act_sec}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    evaluate_generation()
