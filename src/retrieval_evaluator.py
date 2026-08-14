import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.retriever import LegalRetriever


@dataclass
class QueryEvaluation:
    """Diagnostic evaluation output for a single legal test query."""

    query_id: str
    query: str
    expected_domain: str
    expected_issue: str
    expected_chunk_id: str
    status: str

    actual_rank: int | None
    top1_hit: bool
    top3_hit: bool
    top5_hit: bool
    reciprocal_rank: float

    best_score: float
    expected_chunk_score: float | None
    expected_chunk_qualified: bool
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    retrieved_scores: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Converts query evaluation object to dictionary."""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "expected_domain": self.expected_domain,
            "expected_issue": self.expected_issue,
            "expected_chunk_id": self.expected_chunk_id,
            "status": self.status,
            "actual_rank": self.actual_rank,
            "top1_hit": self.top1_hit,
            "top3_hit": self.top3_hit,
            "top5_hit": self.top5_hit,
            "reciprocal_rank": round(self.reciprocal_rank, 4),
            "best_score": round(self.best_score, 4),
            "expected_chunk_score": round(self.expected_chunk_score, 4)
            if self.expected_chunk_score is not None
            else None,
            "expected_chunk_qualified": self.expected_chunk_qualified,
            "retrieved_chunk_ids": self.retrieved_chunk_ids,
            "retrieved_scores": [round(s, 4) for s in self.retrieved_scores],
        }


@dataclass
class BenchmarkMetrics:
    """Aggregated retrieval benchmark performance metrics."""

    total_queries: int
    top1_accuracy: float
    top3_recall: float
    top5_recall: float
    mrr: float
    mean_expected_rank: float | None
    retrieval_success_rate: float
    insufficient_retrieval_rate: float
    failed_top1_count: int
    failed_top3_count: int
    failed_top5_count: int
    not_retrieved_count: int

    def to_dict(self) -> dict[str, Any]:
        """Converts benchmark metrics object to dictionary."""
        return {
            "total_queries": self.total_queries,
            "top1_accuracy_pct": round(self.top1_accuracy, 2),
            "top3_recall_pct": round(self.top3_recall, 2),
            "top5_recall_pct": round(self.top5_recall, 2),
            "mrr": round(self.mrr, 4),
            "mean_expected_rank": round(self.mean_expected_rank, 2)
            if self.mean_expected_rank is not None
            else None,
            "retrieval_success_rate_pct": round(self.retrieval_success_rate, 2),
            "insufficient_retrieval_rate_pct": round(self.insufficient_retrieval_rate, 2),
            "failed_top1_count": self.failed_top1_count,
            "failed_top3_count": self.failed_top3_count,
            "failed_top5_count": self.failed_top5_count,
            "not_retrieved_count": self.not_retrieved_count,
        }


class RetrievalBenchmark:
    """Modular Retrieval Benchmark Framework calculating MRR, Recall, and domain-wise metrics."""

    def __init__(
        self,
        retriever: LegalRetriever | None = None,
        queries_path: str | Path | None = None,
    ) -> None:
        """Initializes RetrievalBenchmark.

        Args:
            retriever: LegalRetriever instance. Defaults to new instance.
            queries_path: Path to test queries JSON file. Defaults to data/dummy_test_queries.json.
        """
        self.retriever = retriever or LegalRetriever()
        if queries_path is not None:
            self.queries_path = Path(queries_path)
        elif Path("data/real_test_queries.json").is_file():
            self.queries_path = Path("data/real_test_queries.json")
        else:
            self.queries_path = Path("data/dummy_test_queries.json")

    def compute_metrics(self, evaluations: list[QueryEvaluation]) -> BenchmarkMetrics:
        """Calculates BenchmarkMetrics object from a list of QueryEvaluation records."""
        total = len(evaluations)
        if total == 0:
            return BenchmarkMetrics(
                total_queries=0,
                top1_accuracy=0.0,
                top3_recall=0.0,
                top5_recall=0.0,
                mrr=0.0,
                mean_expected_rank=None,
                retrieval_success_rate=0.0,
                insufficient_retrieval_rate=0.0,
                failed_top1_count=0,
                failed_top3_count=0,
                failed_top5_count=0,
                not_retrieved_count=0,
            )

        top1_hits = sum(1 for e in evaluations if e.top1_hit)
        top3_hits = sum(1 for e in evaluations if e.top3_hit)
        top5_hits = sum(1 for e in evaluations if e.top5_hit)

        mrr_val = sum(e.reciprocal_rank for e in evaluations) / total

        retrieved_ranks = [e.actual_rank for e in evaluations if e.actual_rank is not None]
        mean_rank = (sum(retrieved_ranks) / len(retrieved_ranks)) if retrieved_ranks else None

        successes = sum(1 for e in evaluations if e.status == "success")
        insufficients = sum(1 for e in evaluations if e.status == "insufficient_retrieval")

        return BenchmarkMetrics(
            total_queries=total,
            top1_accuracy=(top1_hits / total) * 100.0,
            top3_recall=(top3_hits / total) * 100.0,
            top5_recall=(top5_hits / total) * 100.0,
            mrr=mrr_val,
            mean_expected_rank=mean_rank,
            retrieval_success_rate=(successes / total) * 100.0,
            insufficient_retrieval_rate=(insufficients / total) * 100.0,
            failed_top1_count=total - top1_hits,
            failed_top3_count=total - top3_hits,
            failed_top5_count=total - top5_hits,
            not_retrieved_count=sum(1 for e in evaluations if e.actual_rank is None),
        )

    def run_benchmark(
        self,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Runs retrieval evaluation across all queries in queries_path and returns full report.

        Args:
            top_k: Override Top-K. Defaults to retriever default.
            similarity_threshold: Override similarity threshold. Defaults to retriever default.

        Returns:
            Dictionary containing global metrics, domain breakdown, per-query evaluations, and failure categories.

        Raises:
            FileNotFoundError: If queries_path file is missing.
            ValueError: If test queries dataset is empty.
        """
        if not self.queries_path.is_file():
            raise FileNotFoundError(
                f"Test queries file not found at: {self.queries_path.resolve()}"
            )

        with open(self.queries_path, encoding="utf-8") as f:
            test_queries = json.load(f)

        if not test_queries:
            raise ValueError(f"Test queries dataset at {self.queries_path.resolve()} is empty.")

        k_val = top_k if top_k is not None else self.retriever.default_top_k
        thresh_val = (
            similarity_threshold
            if similarity_threshold is not None
            else self.retriever.default_threshold
        )

        evaluations: list[QueryEvaluation] = []
        domain_evaluations: dict[str, list[QueryEvaluation]] = {}

        for tq in test_queries:
            q_id = tq["query_id"]
            query_text = tq["query"]
            expected_domain = tq.get("expected_domain", "Unknown")
            expected_issue = tq.get("expected_issue", "")
            expected_chunk_id = tq.get("expected_chunk_id", "")

            result = self.retriever.retrieve(
                query_text, top_k=k_val, similarity_threshold=thresh_val
            )

            retrieved_ids = [c.chunk_id for c in result.candidates]
            retrieved_scores = [c.score for c in result.candidates]

            actual_rank = None
            expected_score = None
            expected_qual = False

            if expected_chunk_id in retrieved_ids:
                idx = retrieved_ids.index(expected_chunk_id)
                actual_rank = idx + 1
                expected_score = retrieved_scores[idx]
                expected_qual = result.candidates[idx].is_qualified

            best_score = retrieved_scores[0] if retrieved_scores else 0.0
            rec_rank = 1.0 / actual_rank if actual_rank is not None else 0.0

            q_eval = QueryEvaluation(
                query_id=q_id,
                query=query_text,
                expected_domain=expected_domain,
                expected_issue=expected_issue,
                expected_chunk_id=expected_chunk_id,
                status=result.status,
                actual_rank=actual_rank,
                top1_hit=actual_rank == 1,
                top3_hit=actual_rank is not None and actual_rank <= 3,
                top5_hit=actual_rank is not None and actual_rank <= 5,
                reciprocal_rank=rec_rank,
                best_score=best_score,
                expected_chunk_score=expected_score,
                expected_chunk_qualified=expected_qual,
                retrieved_chunk_ids=retrieved_ids,
                retrieved_scores=retrieved_scores,
            )
            evaluations.append(q_eval)

            if expected_domain not in domain_evaluations:
                domain_evaluations[expected_domain] = []
            domain_evaluations[expected_domain].append(q_eval)

        global_metrics = self.compute_metrics(evaluations)

        domain_metrics: dict[str, dict[str, Any]] = {}
        for dom, dom_evals in domain_evaluations.items():
            domain_metrics[dom] = self.compute_metrics(dom_evals).to_dict()

        failed_top1 = [e.to_dict() for e in evaluations if not e.top1_hit]
        failed_top3 = [e.to_dict() for e in evaluations if not e.top3_hit]
        failed_top5 = [e.to_dict() for e in evaluations if not e.top5_hit]
        not_retrieved = [e.to_dict() for e in evaluations if e.actual_rank is None]

        report = {
            "step": "step6_retrieval_benchmark",
            "benchmark_config": {
                "top_k": k_val,
                "similarity_threshold": thresh_val,
                "embedding_model": self.retriever.embedder.model_name,
                "faiss_vector_count": self.retriever.vector_store.ntotal,
                "queries_file": str(self.queries_path.resolve()),
            },
            "global_metrics": global_metrics.to_dict(),
            "domain_metrics": domain_metrics,
            "failure_analysis": {
                "failed_top1_count": len(failed_top1),
                "failed_top3_count": len(failed_top3),
                "failed_top5_count": len(failed_top5),
                "not_retrieved_count": len(not_retrieved),
                "failed_top1_queries": failed_top1,
                "not_retrieved_queries": not_retrieved,
            },
            "query_evaluations": [e.to_dict() for e in evaluations],
        }

        return report

    def save_report(
        self,
        report: dict[str, Any],
        json_path: str | Path,
        summary_txt_path: str | Path | None = None,
    ) -> Path:
        """Saves benchmark report JSON and optional human-readable text summary.

        Args:
            report: Benchmark report dictionary.
            json_path: Target JSON output path.
            summary_txt_path: Optional target TXT summary path.

        Returns:
            Path to saved JSON report.
        """
        j_path = Path(json_path)
        j_path.parent.mkdir(parents=True, exist_ok=True)

        with open(j_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        if summary_txt_path is not None:
            s_path = Path(summary_txt_path)
            s_path.parent.mkdir(parents=True, exist_ok=True)

            gm = report.get("global_metrics", {})
            doms = report.get("domain_metrics", {})
            cfg = report.get("benchmark_config", {})

            lines = [
                "=" * 80,
                "LEGAL AID RETRIEVAL BENCHMARK REPORT (STEP 6)",
                "=" * 80,
                f"Embedding Model      : {cfg.get('embedding_model')}",
                f"FAISS Vector Count   : {cfg.get('faiss_vector_count')}",
                f"Top-K Config         : {cfg.get('top_k')}",
                f"Similarity Threshold : {cfg.get('similarity_threshold')}",
                "-" * 80,
                "GLOBAL RETRIEVAL METRICS:",
                f"  Total Queries          : {gm.get('total_queries')}",
                f"  Top-1 Accuracy         : {gm.get('top1_accuracy_pct')}%",
                f"  Top-3 Recall           : {gm.get('top3_recall_pct')}%",
                f"  Top-5 Recall           : {gm.get('top5_recall_pct')}%",
                f"  Mean Reciprocal Rank   : {gm.get('mrr')}",
                f"  Mean Expected Rank     : {gm.get('mean_expected_rank')}",
                f"  Retrieval Success Rate : {gm.get('retrieval_success_rate_pct')}%",
                f"  Insufficient Rate      : {gm.get('insufficient_retrieval_rate_pct')}%",
                "-" * 80,
                "DOMAIN-WISE PERFORMANCE:",
            ]
            for d_name, d_m in doms.items():
                lines.append(f"  [{d_name}] ({d_m.get('total_queries')} queries):")
                lines.append(f"    - Top-1 Accuracy : {d_m.get('top1_accuracy_pct')}%")
                lines.append(f"    - Top-3 Recall   : {d_m.get('top3_recall_pct')}%")
                lines.append(f"    - Top-5 Recall   : {d_m.get('top5_recall_pct')}%")
                lines.append(f"    - MRR            : {d_m.get('mrr')}")

            lines.append("=" * 80)
            s_path.write_text("\n".join(lines), encoding="utf-8")

        return j_path
