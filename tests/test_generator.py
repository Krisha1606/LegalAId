from unittest.mock import MagicMock

import pytest

from src.config import config
from src.generator import (
    LegalGenerator,
    LegalPromptBuilder,
    OllamaClient,
)
from src.retriever import LegalRetriever, RetrievalResult, RetrievedLegalChunk


@pytest.fixture
def mock_ollama_client():
    client = MagicMock(spec=OllamaClient)
    client.model_name = "qwen2.5:7b"
    client.generate.return_value = (
        "Under Section 12 of the Consumer Rights Act, you are entitled to a full refund."
    )
    return client


@pytest.fixture
def sample_qualified_chunk():
    return RetrievedLegalChunk(
        rank=1,
        score=0.82,
        chunk_id="DUMMY-CONS-001-chunk-0",
        document_id="DUMMY-CONS-001",
        parent_document_id="DUMMY-CONS-001",
        chunk_index=0,
        total_chunks=1,
        text="Where any goods sold to a consumer suffer from a manufacturing defect...",
        domain="Consumer",
        issue="Defective product replacement and full refund rights",
        act="Dummy Consumer Rights Act, 2024",
        section="Dummy Section 12",
        section_title="Right to Replacement or Refund for Defective Goods",
        plain_explanation="Your seller must refund your money.",
        applicability="Applies to consumer purchases.",
        jurisdiction="Dummy National Consumer Forum Jurisdiction",
        source="Dummy Legal Knowledge Repository",
        source_url="https://dummy.legalaid.test/acts/consumer/sec12",
        verified=True,
        is_dummy=True,
        metadata={"category": "electronics"},
        is_qualified=True,
    )


def test_1_generator_initialization(mock_ollama_client):
    gen = LegalGenerator(ollama_client=mock_ollama_client)
    assert gen is not None
    assert gen.ollama_client == mock_ollama_client


def test_2_ollama_client_initialization():
    client = OllamaClient(model_name="custom_model", base_url="http://localhost:11434")
    assert client.model_name == "custom_model"
    assert client.base_url == "http://localhost:11434"


def test_3_config_model_loading():
    client = OllamaClient()
    assert client.model_name == config.OLLAMA_MODEL
    assert client.base_url == config.OLLAMA_BASE_URL


def test_4_prompt_builder_creation():
    builder = LegalPromptBuilder()
    assert builder is not None


def test_5_to_10_prompt_builder_content(sample_qualified_chunk):
    builder = LegalPromptBuilder()
    prompt = builder.build_prompt("Defective mobile phone refund", [sample_qualified_chunk])

    assert "Defective mobile phone refund" in prompt
    assert "Dummy Consumer Rights Act, 2024" in prompt
    assert "Dummy Section 12" in prompt
    assert "Right to Replacement or Refund for Defective Goods" in prompt
    assert "Where any goods sold to a consumer" in prompt
    assert "https://dummy.legalaid.test/acts/consumer/sec12" in prompt


def test_11_empty_query_rejected(mock_ollama_client):
    gen = LegalGenerator(ollama_client=mock_ollama_client)
    with pytest.raises(ValueError):
        gen.generate("")


def test_12_whitespace_query_rejected(mock_ollama_client):
    gen = LegalGenerator(ollama_client=mock_ollama_client)
    with pytest.raises(ValueError):
        gen.generate("   \n\t")


def test_13_14_successful_retrieval_calls_ollama(mock_ollama_client, sample_qualified_chunk):
    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Defective phone",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[sample_qualified_chunk],
        qualified_chunks=[sample_qualified_chunk],
        status="success",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=mock_ollama_client)
    resp = gen.generate("Defective phone")

    assert mock_ollama_client.generate.called
    assert resp.status == "success"
    assert resp.qualified_chunk_count == 1


def test_15_unqualified_chunks_not_treated_as_authoritative(
    mock_ollama_client, sample_qualified_chunk
):
    unqual_chunk = sample_qualified_chunk
    unqual_chunk.is_qualified = False
    unqual_chunk.score = 0.20

    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Unrelated query",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[unqual_chunk],
        qualified_chunks=[],
        status="insufficient_retrieval",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=mock_ollama_client)
    resp = gen.generate("Unrelated query")

    assert not mock_ollama_client.generate.called
    assert resp.status == "insufficient_retrieval"


def test_16_17_insufficient_retrieval_does_not_call_ollama(mock_ollama_client):
    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Random nonsense query xyz999",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[],
        qualified_chunks=[],
        status="insufficient_retrieval",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=mock_ollama_client)
    resp = gen.generate("Random nonsense query xyz999")

    assert not mock_ollama_client.generate.called
    assert resp.status == "insufficient_retrieval"
    assert "could not find sufficiently relevant" in resp.answer


def test_18_successful_ollama_response_status(mock_ollama_client, sample_qualified_chunk):
    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Defective phone",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[sample_qualified_chunk],
        qualified_chunks=[sample_qualified_chunk],
        status="success",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=mock_ollama_client)
    resp = gen.generate("Defective phone")

    assert resp.status == "success"
    assert "Section 12" in resp.answer


def test_19_ollama_failure_returns_generation_error(sample_qualified_chunk):
    failing_client = MagicMock(spec=OllamaClient)
    failing_client.model_name = "qwen2.5:7b"
    failing_client.generate.side_effect = RuntimeError("Ollama service timeout")

    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Defective phone",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[sample_qualified_chunk],
        qualified_chunks=[sample_qualified_chunk],
        status="success",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=failing_client)
    resp = gen.generate("Defective phone")

    assert resp.status == "generation_error"
    assert "communicating with the local language model" in resp.answer


def test_20_21_source_metadata_and_chunk_id_preserved(mock_ollama_client, sample_qualified_chunk):
    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Defective phone",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[sample_qualified_chunk],
        qualified_chunks=[sample_qualified_chunk],
        status="success",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=mock_ollama_client)
    resp = gen.generate("Defective phone")

    assert len(resp.sources) == 1
    src = resp.sources[0]
    assert src["chunk_id"] == "DUMMY-CONS-001-chunk-0"
    assert src["act"] == "Dummy Consumer Rights Act, 2024"
    assert src["section"] == "Dummy Section 12"


def test_22_to_dict_serialization(mock_ollama_client, sample_qualified_chunk):
    mock_retriever = MagicMock(spec=LegalRetriever)
    mock_retriever.retrieve.return_value = RetrievalResult(
        query="Defective phone",
        top_k=5,
        similarity_threshold=0.35,
        candidates=[sample_qualified_chunk],
        qualified_chunks=[sample_qualified_chunk],
        status="success",
    )

    gen = LegalGenerator(retriever=mock_retriever, ollama_client=mock_ollama_client)
    resp = gen.generate("Defective phone")
    res_dict = resp.to_dict()

    assert res_dict["status"] == "success"
    assert res_dict["query"] == "Defective phone"
    assert res_dict["qualified_chunk_count"] == 1
    assert len(res_dict["sources"]) == 1
