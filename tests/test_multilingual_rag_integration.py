import asyncio

import pytest

from phase10_multilingual.src.adapters.real_legal_engine import RealLegalEngineAdapter
from phase10_multilingual.src.adapters.translation_provider import MockTranslationProvider
from phase10_multilingual.src.schemas.language import LanguageCode
from phase10_multilingual.src.schemas.legal_response import (
    MultilingualProcessRequest,
    MultilingualProcessResponse,
)
from phase10_multilingual.src.services.entity_protector import EntityProtector
from phase10_multilingual.src.services.glossary import GlossaryService
from phase10_multilingual.src.services.language_detector import LanguageDetector
from phase10_multilingual.src.services.multilingual_processor import MultilingualProcessor
from phase10_multilingual.src.services.normalizer import Normalizer
from phase10_multilingual.src.services.translator import Translator


@pytest.fixture
def multilingual_processor():
    provider = MockTranslationProvider()
    detector = LanguageDetector(provider=provider)
    normalizer = Normalizer(provider=provider)
    entity_protector = EntityProtector()
    translator = Translator(provider=provider, entity_protector=entity_protector)
    glossary = GlossaryService()
    legal_engine = RealLegalEngineAdapter()

    return MultilingualProcessor(
        detector=detector,
        normalizer=normalizer,
        translator=translator,
        glossary=glossary,
        legal_engine=legal_engine,
    )


def test_1_english_query_end_to_end(multilingual_processor):
    """Test English query end-to-end through Phase 10 MultilingualProcessor with real RAG adapter."""

    async def _run():
        req = MultilingualProcessRequest(
            text="My landlord has not returned my security deposit.",
            output_language=LanguageCode.EN,
        )
        resp = await multilingual_processor.process(req)

        assert isinstance(resp, MultilingualProcessResponse)
        assert resp.language.input == LanguageCode.EN
        assert resp.language.output == LanguageCode.EN
        assert len(resp.rights_explanation) > 10
        assert len(resp.applicable_laws) >= 1
        assert any(
            "Transfer of Property" in law.act or "Registration" in law.act or "Rent" in law.act
            for law in resp.applicable_laws
        )
        assert len(resp.recommended_actions) >= 1
        assert "कानूनी" not in resp.disclaimer

    asyncio.run(_run())


def test_2_hindi_query_end_to_end(multilingual_processor):
    """Test Hindi Devanagari query end-to-end through Phase 10 MultilingualProcessor with real RAG adapter."""

    async def _run():
        req = MultilingualProcessRequest(
            text="मेरे मकान मालिक ने मेरी सिक्योरिटी डिपॉजिट वापस नहीं की है।",
            output_language=LanguageCode.HI,
        )
        resp = await multilingual_processor.process(req)

        assert isinstance(resp, MultilingualProcessResponse)
        assert resp.language.input == LanguageCode.HI
        assert resp.language.output == LanguageCode.HI
        assert len(resp.rights_explanation) > 0
        assert len(resp.applicable_laws) >= 1
        # Verify Act names are preserved strictly in English
        assert any(
            "Transfer of Property" in law.act or "Rent" in law.act or "Registration" in law.act
            for law in resp.applicable_laws
        )
        assert "disclaimer" in resp.model_dump()

    asyncio.run(_run())


def test_3_roman_hindi_query_end_to_end(multilingual_processor):
    """Test Roman Hindi / Hinglish query end-to-end through Phase 10 MultilingualProcessor with real RAG adapter."""

    async def _run():
        req = MultilingualProcessRequest(
            text="Mere landlord ne mera security deposit wapas nahi kiya.",
            output_language=LanguageCode.EN,
        )
        resp = await multilingual_processor.process(req)

        assert isinstance(resp, MultilingualProcessResponse)
        assert resp.language.input == LanguageCode.ROMAN_HI
        assert resp.normalized_text == "My landlord has not returned my security deposit."
        assert len(resp.applicable_laws) >= 1
        assert any(
            "Transfer of Property" in law.act or "Rent" in law.act
            for law in resp.applicable_laws
        )

    asyncio.run(_run())
