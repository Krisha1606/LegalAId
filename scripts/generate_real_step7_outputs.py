import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.generator import LegalGenerator
from src.retriever import LegalRetriever
from src.vector_store import FAISSVectorStore


def main():
    output_dir = Path("test_outputs/real_data_step7")
    output_dir.mkdir(parents=True, exist_ok=True)

    production_vector_store_path = config.VECTOR_STORE_PATH
    print(f"Loading production vector store from {production_vector_store_path.resolve()}...")
    vector_store = FAISSVectorStore(dir_path=production_vector_store_path)
    vector_store.load()

    retriever = LegalRetriever(vector_store=vector_store, top_k=5, similarity_threshold=0.35)
    generator = LegalGenerator(retriever=retriever)

    queries_path = Path("data/real_test_queries.json")
    with open(queries_path, encoding="utf-8") as f:
        real_queries = json.load(f)

    # Add an ungrounded random query to test safety short-circuit
    safety_query = {
        "query_id": "REAL_Q_SAFETY_UNGROUNDED",
        "query": "Unrelated quantum mechanics spatial warp hypothesis test xyz999",
        "expected_domain": "None",
        "expected_issue": "Safety Short Circuit Test",
        "expected_chunk_id": "NONE",
    }
    eval_queries = list(real_queries) + [safety_query]

    print(
        f"Running generation evaluation across {len(eval_queries)} real queries with Ollama qwen2.5:7b..."
    )

    eval_results = []
    generation_successes = 0
    generation_failures = 0
    insufficient_cases = 0
    ollama_skipped = 0

    for q in eval_queries:
        q_id = q["query_id"]
        q_text = q["query"]

        resp = generator.generate(q_text)

        if resp.status == "success":
            generation_successes += 1
        elif resp.status == "insufficient_retrieval":
            insufficient_cases += 1
            if q_id == "REAL_Q_SAFETY_UNGROUNDED":
                ollama_skipped += 1
        else:
            generation_failures += 1

        eval_results.append(
            {
                "query_id": q_id,
                "query": q_text,
                "status": resp.status,
                "retrieval_status": resp.retrieval_status,
                "qualified_chunk_count": resp.qualified_chunk_count,
                "answer": resp.answer,
                "citations_count": len(resp.sources),
                "sources": resp.sources,
            }
        )

    eval_summary = {
        "step": "real_data_step7_generation_evaluation",
        "model_name": generator.ollama_client.model_name,
        "total_test_queries": len(eval_queries),
        "generation_successes": generation_successes,
        "generation_failures": generation_failures,
        "insufficient_retrievals": insufficient_cases,
        "safety_short_circuits_triggered": ollama_skipped,
        "query_details": eval_results,
        "status": "SUCCESS" if (generation_failures == 0 and ollama_skipped >= 1) else "FAILED",
    }

    eval_json_path = output_dir / "generation_evaluation.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2, ensure_ascii=False)

    results_json_path = output_dir / "generation_results.json"
    sample_payload = {
        "step": "real_data_step7_sample_results",
        "model_name": generator.ollama_client.model_name,
        "sample_responses": [res for res in eval_results[:3]],
    }
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(sample_payload, f, indent=2, ensure_ascii=False)

    print(f"Step 7 real generation evaluation saved to {output_dir.resolve()}!")
    print(
        f"Total: {len(eval_queries)}, Successes: {generation_successes}, Failures: {generation_failures}, Insufficient: {insufficient_cases}, Safety Skipped: {ollama_skipped}"
    )


if __name__ == "__main__":
    main()
