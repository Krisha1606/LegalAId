import pytest
from src.reranker import LegalReranker, RerankedChunk
from src.retriever import LegalRetriever, RetrievalResult, RetrievedLegalChunk


def test_reranker_initialization():
    reranker = LegalReranker()
    assert reranker.cross_encoder is not None
    assert reranker.top_n == 20
    assert reranker.rerank_threshold == -2.0


def test_reranker_executes_two_stage():
    reranker = LegalReranker()
    query = "My employer has not paid my salary for two months."
    result = reranker.rerank(query, top_n=10, top_k=3)

    assert isinstance(result, RetrievalResult)
    assert len(result.candidates) > 0
    assert result.top_k == 3

    top1 = result.candidates[0]
    assert hasattr(top1, "rerank_score") or "rerank_score" in top1.metadata
    assert hasattr(top1, "relevance_decision") or "relevance_decision" in top1.metadata


def test_reranker_filters_out_irrelevant_query():
    reranker = LegalReranker()
    query = "How do I bake a chocolate cake at home without using an oven?"
    result = reranker.rerank(query)

    assert result.status == "insufficient_retrieval"
    assert len(result.qualified_chunks) == 0
