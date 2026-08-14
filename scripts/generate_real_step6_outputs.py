import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.retrieval_evaluator import RetrievalBenchmark
from src.retriever import LegalRetriever
from src.vector_store import FAISSVectorStore


def main():
    output_dir = Path("test_outputs/real_data_step6")
    output_dir.mkdir(parents=True, exist_ok=True)

    queries_path = Path("data/real_test_queries.json")
    print(f"Loading real test queries from {queries_path.resolve()}...")

    production_vector_store_path = config.VECTOR_STORE_PATH
    print(f"Loading production vector store from {production_vector_store_path.resolve()}...")
    vector_store = FAISSVectorStore(dir_path=production_vector_store_path)
    vector_store.load()

    retriever = LegalRetriever(vector_store=vector_store, top_k=5, similarity_threshold=0.35)
    benchmark = RetrievalBenchmark(retriever=retriever, queries_path=queries_path)

    print("Running real semantic retrieval benchmark across real legal queries...")
    report = benchmark.run_benchmark(top_k=5, similarity_threshold=0.35)

    json_path = output_dir / "retrieval_benchmark.json"
    txt_path = output_dir / "retrieval_summary.txt"

    benchmark.save_report(report, json_path=json_path, summary_txt_path=txt_path)

    gm = report["global_metrics"]
    print(f"Step 6 real retrieval evaluation saved to {output_dir.resolve()}!")
    print(f"Total Queries: {gm['total_queries']}")
    print(f"Top-1 Accuracy: {gm['top1_accuracy_pct']}%")
    print(f"Top-3 Recall: {gm['top3_recall_pct']}%")
    print(f"Top-5 Recall: {gm['top5_recall_pct']}%")
    print(f"MRR: {gm['mrr']}")
    print(f"Retrieval Success Rate: {gm['retrieval_success_rate_pct']}%")


if __name__ == "__main__":
    main()
