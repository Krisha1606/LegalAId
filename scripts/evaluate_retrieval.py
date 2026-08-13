import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval_evaluator import RetrievalBenchmark  # noqa: E402


def evaluate_retrieval() -> dict:
    benchmark = RetrievalBenchmark()
    report = benchmark.run_benchmark()

    gm = report["global_metrics"]
    doms = report["domain_metrics"]

    print("=" * 80)
    print("RETRIEVAL BENCHMARK EVALUATION SUMMARY (DUMMY DATASET)")
    print("=" * 80)
    print(f"Total Test Queries   : {gm['total_queries']}")
    print(f"Top-1 Accuracy       : {gm['top1_accuracy_pct']}%")
    print(f"Top-3 Recall         : {gm['top3_recall_pct']}%")
    print(f"Top-5 Recall         : {gm['top5_recall_pct']}%")
    print(f"Mean Reciprocal Rank : {gm['mrr']}")
    print(f"Mean Expected Rank   : {gm['mean_expected_rank']}")
    print("-" * 80)
    print("\nDomain-wise Evaluation:")
    for dom, metrics in doms.items():
        print(f"  Domain: {dom} ({metrics['total_queries']} queries)")
        print(f"    - Top-1 Accuracy : {metrics['top1_accuracy_pct']}%")
        print(f"    - Top-3 Recall   : {metrics['top3_recall_pct']}%")
        print(f"    - Top-5 Recall   : {metrics['top5_recall_pct']}%")
        print(f"    - MRR            : {metrics['mrr']}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    evaluate_retrieval()
