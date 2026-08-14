import json

import pytest

from src.retrieval_evaluator import (
    QueryEvaluation,
    RetrievalBenchmark,
)
from src.retriever import LegalRetriever


@pytest.fixture(scope="module")
def benchmark_instance():
    retriever = LegalRetriever()
    return RetrievalBenchmark(retriever=retriever)


def test_1_benchmark_initializes_successfully(benchmark_instance):
    assert benchmark_instance is not None
    assert benchmark_instance.queries_path.is_file()


def test_2_runs_benchmark_over_queries(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    assert report["step"] == "step6_retrieval_benchmark"
    assert report["global_metrics"]["total_queries"] == 15


def test_3_computes_top_metrics(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    gm = report["global_metrics"]
    assert 0.0 <= gm["top1_accuracy_pct"] <= 100.0
    assert 0.0 <= gm["top3_recall_pct"] <= 100.0
    assert 0.0 <= gm["top5_recall_pct"] <= 100.0


def test_4_computes_mrr(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    mrr = report["global_metrics"]["mrr"]
    assert 0.0 <= mrr <= 1.0


def test_5_computes_mean_expected_rank(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    mean_rank = report["global_metrics"]["mean_expected_rank"]
    assert mean_rank is not None
    assert mean_rank >= 1.0


def test_6_computes_success_rates(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    gm = report["global_metrics"]
    assert gm["retrieval_success_rate_pct"] + gm["insufficient_retrieval_rate_pct"] == 100.0


def test_7_domain_wise_metrics(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    doms = report["domain_metrics"]
    dom_keys_lower = {k.lower() for k in doms.keys()}
    assert "consumer" in dom_keys_lower
    assert "labour" in dom_keys_lower
    assert any("tenant" in k for k in dom_keys_lower)
    sample_dom = list(doms.values())[0]
    assert sample_dom["total_queries"] == 5


def test_8_query_eval_reciprocal_rank():
    qe1 = QueryEvaluation(
        "Q1",
        "text",
        "Dom",
        "Issue",
        "C1",
        "success",
        1,
        True,
        True,
        True,
        1.0,
        0.8,
        0.8,
        True,
        ["C1"],
        [0.8],
    )
    assert qe1.reciprocal_rank == 1.0

    qe2 = QueryEvaluation(
        "Q2",
        "text",
        "Dom",
        "Issue",
        "C2",
        "success",
        2,
        False,
        True,
        True,
        0.5,
        0.8,
        0.6,
        True,
        ["C1", "C2"],
        [0.8, 0.6],
    )
    assert qe2.reciprocal_rank == 0.5


def test_9_not_retrieved_chunk_handling(benchmark_instance):
    bm = benchmark_instance
    qe = QueryEvaluation(
        "Q3",
        "text",
        "Dom",
        "Issue",
        "C99",
        "insufficient_retrieval",
        None,
        False,
        False,
        False,
        0.0,
        0.2,
        None,
        False,
        ["C1"],
        [0.2],
    )
    metrics = bm.compute_metrics([qe])
    assert metrics.not_retrieved_count == 1
    assert metrics.mrr == 0.0


def test_10_expected_chunk_score_populated(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    evals = report["query_evaluations"]
    for q in evals:
        if q["actual_rank"] is not None:
            assert q["expected_chunk_score"] is not None


def test_11_expected_chunk_qualified_reflects_threshold(benchmark_instance):
    report = benchmark_instance.run_benchmark(similarity_threshold=0.99)
    evals = report["query_evaluations"]
    assert all(q["expected_chunk_qualified"] is False for q in evals)


def test_12_failure_count_accuracy(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    fa = report["failure_analysis"]
    gm = report["global_metrics"]
    assert fa["failed_top1_count"] == gm["failed_top1_count"]


def test_13_retrieved_chunk_ids_ordered(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    qe0 = report["query_evaluations"][0]
    assert len(qe0["retrieved_chunk_ids"]) > 0
    scores = qe0["retrieved_scores"]
    assert scores == sorted(scores, reverse=True)


def test_14_save_json_report(benchmark_instance, tmp_path):
    report = benchmark_instance.run_benchmark()
    out_json = tmp_path / "test_report.json"
    benchmark_instance.save_report(report, json_path=out_json)
    assert out_json.is_file()

    with open(out_json, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["step"] == "step6_retrieval_benchmark"


def test_15_save_txt_summary_report(benchmark_instance, tmp_path):
    report = benchmark_instance.run_benchmark()
    out_json = tmp_path / "test_report.json"
    out_txt = tmp_path / "test_summary.txt"
    benchmark_instance.save_report(report, json_path=out_json, summary_txt_path=out_txt)
    assert out_txt.is_file()
    assert "LEGAL AID RETRIEVAL BENCHMARK REPORT" in out_txt.read_text(encoding="utf-8")


def test_16_empty_query_dataset_raises_error(tmp_path):
    empty_file = tmp_path / "empty_queries.json"
    empty_file.write_text("[]", encoding="utf-8")

    bm = RetrievalBenchmark(queries_path=empty_file)
    with pytest.raises(ValueError) as exc_info:
        bm.run_benchmark()
    assert "dataset at" in str(exc_info.value) and "is empty" in str(exc_info.value)


def test_17_missing_query_file_raises_error(tmp_path):
    missing_file = tmp_path / "non_existent.json"
    bm = RetrievalBenchmark(queries_path=missing_file)
    with pytest.raises(FileNotFoundError):
        bm.run_benchmark()


def test_18_custom_top_k_and_threshold_respected(benchmark_instance):
    report = benchmark_instance.run_benchmark(top_k=2, similarity_threshold=0.50)
    assert report["benchmark_config"]["top_k"] == 2
    assert report["benchmark_config"]["similarity_threshold"] == 0.50
    for qe in report["query_evaluations"]:
        assert len(qe["retrieved_chunk_ids"]) <= 2


def test_19_regression_threshold_enforcement(benchmark_instance):
    report = benchmark_instance.run_benchmark()
    gm = report["global_metrics"]
    assert gm["top3_recall_pct"] >= 50.0
    assert gm["mrr"] >= 0.40
