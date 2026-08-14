import asyncio
from unittest.mock import MagicMock

from phase10_multilingual.src.adapters.real_legal_engine import RealLegalEngineAdapter
from phase10_multilingual.src.schemas.legal_response import LegalEngineResponse
from src.generator import GroundedResponse, LegalGenerator


def test_1_transform_response_structure():
    """Verifies that transform_response converts GroundedResponse into a valid LegalEngineResponse."""
    grounded = GroundedResponse(
        query="Landlord security deposit issue",
        answer="Under Indian property law, landlords must return security deposits upon lease termination.",
        status="success",
        retrieval_status="success",
        qualified_chunk_count=1,
        retrieved_chunks=[],
        sources=[
            {
                "act": "The Transfer of Property Act, 1882",
                "section": "Section 108",
                "section_title": "Rights and Liabilities of Lessor and Lessee",
                "source_url": "https://example.com/topa",
            }
        ],
    )

    adapter = RealLegalEngineAdapter(generator=MagicMock())
    legal_resp = adapter.transform_response(grounded)

    assert isinstance(legal_resp, LegalEngineResponse)
    assert legal_resp.rights_explanation == grounded.answer
    assert len(legal_resp.applicable_laws) == 1
    assert legal_resp.applicable_laws[0].act == "The Transfer of Property Act, 1882"
    assert legal_resp.applicable_laws[0].section == "Section 108"
    assert legal_resp.applicable_laws[0].explanation == "Rights and Liabilities of Lessor and Lessee"
    assert legal_resp.applicable_laws[0].source == "https://example.com/topa"
    assert len(legal_resp.citations) == 1
    assert "Section 108" in legal_resp.citations[0]
    assert len(legal_resp.recommended_actions) >= 1


def test_2_transform_response_insufficient_retrieval():
    """Verifies adapter handling when RAG returns insufficient retrieval status."""
    grounded = GroundedResponse(
        query="Random query",
        answer="I could not find sufficiently relevant legal information to answer this question.",
        status="insufficient_retrieval",
        retrieval_status="insufficient_retrieval",
        qualified_chunk_count=0,
        retrieved_chunks=[],
        sources=[],
    )

    adapter = RealLegalEngineAdapter(generator=MagicMock())
    legal_resp = adapter.transform_response(grounded)

    assert isinstance(legal_resp, LegalEngineResponse)
    assert "could not find" in legal_resp.rights_explanation.lower()
    assert len(legal_resp.applicable_laws) == 0
    assert len(legal_resp.citations) == 0
    assert len(legal_resp.recommended_actions) >= 1


def test_3_async_get_response():
    """Verifies async get_response execution with a mocked generator."""

    async def _run():
        mock_gen = MagicMock(spec=LegalGenerator)
        mock_gen.generate.return_value = GroundedResponse(
            query="Defective product",
            answer="Sellers are liable for defective products under CPA 2019.",
            status="success",
            retrieval_status="success",
            qualified_chunk_count=1,
            retrieved_chunks=[],
            sources=[
                {
                    "act": "The Consumer Protection Act, 2019",
                    "section": "Section 2(10)",
                    "section_title": "Defect",
                    "source_url": "https://consumeraffairs.nic.in",
                }
            ],
        )

        adapter = RealLegalEngineAdapter(generator=mock_gen)
        legal_resp = await adapter.get_response("Defective product refund")

        mock_gen.generate.assert_called_once_with("Defective product refund")
        assert isinstance(legal_resp, LegalEngineResponse)
        assert legal_resp.applicable_laws[0].act == "The Consumer Protection Act, 2019"

    asyncio.run(_run())
