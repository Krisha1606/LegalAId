import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval_evaluator import RetrievalBenchmark  # noqa: E402


def inspect_retrieval_benchmark() -> None:
    print("=" * 80)
    print("RETRIEVAL BENCHMARK DIAGNOSTIC INSPECTOR")
    print("=" * 80)

    benchmark = RetrievalBenchmark()
    report = benchmark.run_benchmark()

    gm = report["global_metrics"]
    evals = report["query_evaluations"]

    print(f"\nTotal Test Queries     : {gm['total_queries']}")
    print(f"Top-1 Accuracy         : {gm['top1_accuracy_pct']}%")
    print(f"Top-3 Recall           : {gm['top3_recall_pct']}%")
    print(f"Top-5 Recall           : {gm['top5_recall_pct']}%")
    print(f"Mean Reciprocal Rank   : {gm['mrr']}")
    print(f"Mean Expected Rank     : {gm['mean_expected_rank']}")
    print(f"Retrieval Success Rate : {gm['retrieval_success_rate_pct']}%")
    print(f"Insufficient Rate      : {gm['insufficient_retrieval_rate_pct']}%")

    print("\n" + "-" * 80)
    print("PER-QUERY RETRIEVAL EVALUATION DETAILS:\n")

    for qe in evals:
        rank_str = f"Rank {qe['actual_rank']}" if qe["actual_rank"] else "NOT RETRIEVED"
        hit_tag = "[TOP-1 MATCH]" if qe["top1_hit"] else (f"[{rank_str}]")

        print(f'  {qe["query_id"]} {hit_tag}: "{qe["query"]}"')
        print(f"    Domain          : {qe['expected_domain']}")
        print(f"    Expected Chunk  : {qe['expected_chunk_id']}")
        print(f"    Actual Rank     : {qe['actual_rank']}")
        print(f"    Reciprocal Rank : {qe['reciprocal_rank']}")
        print(f"    Best Score      : {qe['best_score']}")
        print(f"    Expected Score  : {qe['expected_chunk_score']}")
        print(f"    Status          : {qe['status']}")
        print(f"    Top Chunks      : {', '.join(qe['retrieved_chunk_ids'][:3])}")
        print("  " + "-" * 76)

    print("=" * 80)


if __name__ == "__main__":
    inspect_retrieval_benchmark()
